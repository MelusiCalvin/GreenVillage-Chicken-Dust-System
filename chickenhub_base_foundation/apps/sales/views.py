from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.decorators import StaffRequiredMixin
from apps.inventory.models import InventoryItem, StockMovement
from apps.products.models import Product
from .forms import WalkInSaleForm
from .models import Sale, SaleItem


class WalkInSalePOSView(StaffRequiredMixin, View):
    """
    Point of Sale (POS) interface for recording walk-in sales.
    Accessible to all authorised staff members (Employees, Managers, Owners).

    Process:
    1. Displays available products grouped by category.
    2. Cashier selects products and enters quantities.
    3. Calculates subtotals and total sale amount.
    4. Validates product availability and inventory stock requirements.
    5. Within an atomic transaction:
       - Creates Sale and SaleItem records with historical selling prices.
       - Generates unique receipt number.
       - Deducts required ingredients according to product recipes.
       - Records StockMovement (SOLD) audit entries.
    """
    template_name = 'sales/pos.html'

    def get(self, request):
        products = Product.objects.filter(is_available=True).select_related('recipe').prefetch_related(
            'recipe__items__inventory_item'
        ).order_by('category', 'product_name')

        form = WalkInSaleForm()

        context = {
            'products': products,
            'form': form,
            'payment_methods': form.fields['payment_method'].choices,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = WalkInSaleForm(request.POST)
        products = Product.objects.filter(is_available=True).select_related('recipe').prefetch_related(
            'recipe__items__inventory_item'
        ).order_by('category', 'product_name')

        # Parse quantities strictly. Invalid or negative input must not silently
        # turn into a smaller sale than the cashier confirmed.
        selected_items = []
        invalid_quantity = False
        for key, value in request.POST.items():
            if key.startswith('qty_'):
                try:
                    product_id = int(key[4:])
                    qty = int(value)
                    if qty < 0:
                        raise ValueError
                    if qty:
                        selected_items.append((product_id, qty))
                except (ValueError, TypeError):
                    invalid_quantity = True

        if invalid_quantity:
            messages.error(request, 'Enter whole product quantities of zero or more.')
            return render(request, self.template_name, {'products': products, 'form': form})

        if not selected_items:
            messages.error(request, "Please select at least one product with a quantity of 1 or more.")
            return render(request, self.template_name, {'products': products, 'form': form})

        # 2. Fetch products and validate availability
        product_map = {}
        for pid, qty in selected_items:
            try:
                prod = Product.objects.select_related('recipe').prefetch_related(
                    'recipe__items__inventory_item'
                ).get(pk=pid)
                if not prod.is_available:
                    messages.error(request, f"Product '{prod.product_name}' is currently unavailable for sale.")
                    return render(request, self.template_name, {'products': products, 'form': form})
                if not prod.has_recipe or not prod.recipe.items.exists():
                    messages.error(request, f"'{prod.product_name}' cannot be sold until its stock recipe is configured.")
                    return render(request, self.template_name, {'products': products, 'form': form})
                product_map[pid] = (prod, qty)
            except Product.DoesNotExist:
                messages.error(request, "Selected product does not exist.")
                return render(request, self.template_name, {'products': products, 'form': form})

        # 3. Calculate recipe inventory requirements
        # required_stock[inventory_item_id] = total_needed
        required_stock = {}
        for pid, (prod, qty) in product_map.items():
            if prod.has_recipe:
                for recipe_item in prod.recipe.items.all():
                    inv_id = recipe_item.inventory_item_id
                    needed = recipe_item.quantity_required * Decimal(str(qty))
                    if inv_id in required_stock:
                        required_stock[inv_id]['quantity'] += needed
                    else:
                        required_stock[inv_id] = {
                            'item': recipe_item.inventory_item,
                            'quantity': needed,
                        }

        # Validate configurable payment value and optional tender before writes.
        if not form.is_valid():
            messages.error(request, "Please correct the form errors.")
            return render(request, self.template_name, {'products': products, 'form': form})

        # 6. Calculate total amount
        total_amount = Decimal('0.00')
        line_items_data = []
        for pid, (prod, qty) in product_map.items():
            subtotal = prod.selling_price * Decimal(str(qty))
            total_amount += subtotal
            line_items_data.append({
                'product': prod,
                'quantity': qty,
                'unit_price': prod.selling_price,
                'subtotal': subtotal,
            })

        payment_method = form.cleaned_data['payment_method']
        amount_tendered = form.cleaned_data.get('amount_tendered')
        change_given = None
        notes = form.cleaned_data.get('notes', '').strip()

        # 7. Atomic transaction: lock all recipe stock in deterministic order,
        # revalidate against current balances, and write sale + movements once.
        try:
            with transaction.atomic():
                locked_items = {
                    item.pk: item for item in InventoryItem.objects.select_for_update()
                    .filter(pk__in=sorted(required_stock)).order_by('pk')
                }
                for inv_id, req in required_stock.items():
                    item = locked_items.get(inv_id)
                    if item is None or not item.is_active or item.quantity_on_hand < req['quantity']:
                        name = item.item_name if item else req['item'].item_name
                        on_hand = item.quantity_on_hand if item else Decimal('0.00')
                        raise ValueError(f"Insufficient active stock for '{name}': need {req['quantity']}, have {on_hand}.")
                # A. Create Sale header
                sale = Sale.objects.create(
                    sale_type=Sale.SaleType.WALK_IN,
                    sale_date=timezone.now(),
                    total_amount=total_amount,
                    payment_method=payment_method,
                    amount_tendered=amount_tendered,
                    change_given=change_given,
                    recorded_by=request.user,
                    notes=notes,
                )

                # B. Create SaleItem records (preserving historical selling price)
                for item_data in line_items_data:
                    SaleItem.objects.create(
                        sale=sale,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        subtotal=item_data['subtotal'],
                    )

                # C. Deduct stock once and record the corresponding movement.
                for inv_id, req in required_stock.items():
                    locked_item = locked_items[inv_id]
                    needed_qty = req['quantity']

                    # Final guard against negative stock
                    if locked_item.quantity_on_hand < needed_qty:
                        raise ValueError(f"Stock changed before sale confirmation for {locked_item.item_name}.")

                    locked_item.quantity_on_hand -= needed_qty
                    locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                    # Log StockMovement
                    StockMovement.objects.create(
                        inventory_item=locked_item,
                        movement_type=StockMovement.MovementType.SOLD,
                        quantity=-needed_qty,
                        movement_date=sale.sale_date,
                        reason=f"Walk-in sale #{sale.receipt_number}",
                        reference_number=sale.receipt_number,
                        recorded_by=request.user,
                    )

        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {'products': products, 'form': form})

        messages.success(
            request,
            f"Sale #{sale.receipt_number} completed! Total: R {sale.total_amount:.2f}. "
            "Stock updated successfully."
        )
        return redirect('sales:receipt', pk=sale.pk)


class SaleListView(StaffRequiredMixin, View):
    """
    Searchable sales transaction history with date filters and totals.
    """
    template_name = 'sales/sale_list.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        payment_method = request.GET.get('payment', '').strip()
        date_filter = request.GET.get('date', '').strip()

        sales = Sale.objects.select_related('recorded_by', 'order').prefetch_related(
            'items__product'
        ).all().order_by('-sale_date')

        if query:
            sales = sales.filter(
                Q(receipt_number__icontains=query) |
                Q(recorded_by__username__icontains=query) |
                Q(recorded_by__first_name__icontains=query) |
                Q(items__product__product_name__icontains=query)
            ).distinct()

        if payment_method:
            sales = sales.filter(payment_method=payment_method)

        today = timezone.now().date()
        if date_filter == 'today':
            sales = sales.filter(sale_date__date=today)

        # Revenue calculations
        total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        today_sales_qs = Sale.objects.filter(sale_date__date=today)
        today_revenue = today_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        context = {
            'sales': sales[:100],
            'query': query,
            'payment_method': payment_method,
            'date_filter': date_filter,
            'payment_methods': [('', 'Not specified')] + list(getattr(settings, 'CHICKENHUB_PAYMENT_METHODS', ())),
            'total_sales_count': sales.count(),
            'total_revenue': total_revenue,
            'today_sales_count': today_sales_qs.count(),
            'today_revenue': today_revenue,
        }
        return render(request, self.template_name, context)


class SaleDetailView(StaffRequiredMixin, View):
    """
    Detailed transaction view / till slip receipt.
    Shows line items, historical prices, subtotals, tender/change,
    cashier details, and linked stock movement deductions.
    """
    template_name = 'sales/sale_detail.html'

    def get(self, request, pk):
        sale = get_object_or_404(
            Sale.objects.select_related('recorded_by', 'order').prefetch_related('items__product'),
            pk=pk
        )
        movements = StockMovement.objects.filter(
            reference_number=sale.receipt_number
        ).select_related('inventory_item')

        return render(request, self.template_name, {
            'sale': sale,
            'movements': movements,
        })
