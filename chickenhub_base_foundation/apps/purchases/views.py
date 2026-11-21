from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.decorators import ManagerRequiredMixin
from apps.inventory.models import InventoryItem, StockMovement
from .forms import (
    ChickenPurchaseForm,
    PurchaseItemFormSet,
    SupplierForm,
    SuppliesPurchaseHeaderForm,
)
from .models import Purchase, PurchaseItem, Supplier


# ===========================================================================
# A. Supplier Management Views
# ===========================================================================

class SupplierListView(ManagerRequiredMixin, View):
    """
    Lists all registered suppliers with purchase counts and contact info.
    """
    template_name = 'purchases/supplier_list.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        status = request.GET.get('status', 'active')

        suppliers = Supplier.objects.all().order_by('supplier_name')

        if query:
            suppliers = suppliers.filter(
                Q(supplier_name__icontains=query) |
                Q(contact_person__icontains=query) |
                Q(phone_number__icontains=query)
            )

        if status == 'active':
            suppliers = suppliers.filter(is_active=True)
        elif status == 'inactive':
            suppliers = suppliers.filter(is_active=False)

        context = {
            'suppliers': suppliers,
            'query': query,
            'status': status,
            'total_count': Supplier.objects.count(),
            'active_count': Supplier.objects.filter(is_active=True).count(),
        }
        return render(request, self.template_name, context)


class SupplierCreateView(ManagerRequiredMixin, View):
    """
    Register a new poultry, ingredient or consumables supplier.
    """
    template_name = 'purchases/supplier_form.html'

    def get(self, request):
        form = SupplierForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Register New Supplier',
            'submit_label': 'Register Supplier',
        })

    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' registered successfully.")
            return redirect('purchases:supplier_detail', pk=supplier.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Register New Supplier',
            'submit_label': 'Register Supplier',
        })


class SupplierUpdateView(ManagerRequiredMixin, View):
    """
    Update an existing supplier's contact and address information.
    """
    template_name = 'purchases/supplier_form.html'

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(instance=supplier)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Supplier — {supplier.supplier_name}",
            'submit_label': 'Save Changes',
            'supplier': supplier,
        })

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' updated successfully.")
            return redirect('purchases:supplier_detail', pk=supplier.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Supplier — {supplier.supplier_name}",
            'submit_label': 'Save Changes',
            'supplier': supplier,
        })


class SupplierDetailView(ManagerRequiredMixin, View):
    """
    View a supplier's full profile and historical purchase records.
    """
    template_name = 'purchases/supplier_detail.html'

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        purchases = supplier.purchases.all().order_by('-purchase_date', '-created_at')
        total_spent = purchases.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')

        return render(request, self.template_name, {
            'supplier': supplier,
            'purchases': purchases,
            'total_spent': total_spent,
            'total_orders': purchases.count(),
        })


class SupplierToggleActiveView(ManagerRequiredMixin, View):
    """
    Toggle a supplier's active status.
    """
    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.is_active = not supplier.is_active
        supplier.save(update_fields=['is_active', 'updated_at'])
        action = "activated" if supplier.is_active else "deactivated"
        messages.success(request, f"Supplier '{supplier.supplier_name}' has been {action}.")
        return redirect('purchases:supplier_detail', pk=pk)


# ===========================================================================
# B. Chicken Purchasing Views (UC-01)
# ===========================================================================

class ChickenPurchaseCreateView(ManagerRequiredMixin, View):
    """
    Captures Chicken Purchases:
    - Purchase date
    - Supplier
    - Quantity of chickens purchased
    - Total stock price (gross)
    - Average chicken price (calculated)
    - Discount
    - Final purchase amount (calculated)
    - Payment method
    - Staff member (recorded_by)
    - Automatically updates whole chicken stock balance atomically!
    """
    template_name = 'purchases/chicken_purchase_form.html'

    def get(self, request):
        form = ChickenPurchaseForm()
        # Find available suppliers
        suppliers = Supplier.objects.filter(is_active=True)
        return render(request, self.template_name, {
            'form': form,
            'suppliers_count': suppliers.count(),
        })

    def post(self, request):
        form = ChickenPurchaseForm(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']
            purchase_date = form.cleaned_data['purchase_date']
            quantity = form.cleaned_data['quantity']
            total_amount = form.cleaned_data['total_amount']
            discount = form.cleaned_data.get('discount') or Decimal('0.00')
            payment_method = form.cleaned_data['payment_method']
            invoice_number = form.cleaned_data.get('invoice_number', '').strip()
            notes = form.cleaned_data.get('notes', '').strip()
            item = form.cleaned_data.get('inventory_item')

            # Calculate average and final amounts
            final_amount = total_amount - discount
            unit_price = (total_amount / quantity).quantize(Decimal('0.01'))
            net_unit_price = (final_amount / quantity).quantize(Decimal('0.01'))

            with transaction.atomic():
                # 1. Resolve whole chicken inventory item
                if not item:
                    item, _ = InventoryItem.objects.get_or_create(
                        item_name='Whole Fresh Chicken',
                        defaults={
                            'item_type': InventoryItem.ItemType.WHOLE_CHICKEN,
                            'unit_of_measure': InventoryItem.UnitOfMeasure.UNIT,
                            'quantity_on_hand': Decimal('0.00'),
                            'reorder_level': Decimal('15.00'),
                            'is_active': True,
                        }
                    )

                # 2. Lock item for update
                locked_item = InventoryItem.objects.select_for_update().get(pk=item.pk)

                # 3. Create Purchase header
                purchase = Purchase.objects.create(
                    supplier=supplier,
                    purchase_date=purchase_date,
                    invoice_number=invoice_number,
                    total_amount=total_amount,
                    discount=discount,
                    final_amount=final_amount,
                    payment_method=payment_method,
                    recorded_by=request.user,
                    notes=notes,
                )

                # 4. Create PurchaseItem line
                PurchaseItem.objects.create(
                    purchase=purchase,
                    inventory_item=locked_item,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=total_amount,
                )

                # 5. Update inventory quantity
                locked_item.quantity_on_hand += quantity
                locked_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                # 6. Record StockMovement
                movement_note = f"Chicken purchase from {supplier.supplier_name}"
                if invoice_number:
                    movement_note += f" (Inv #{invoice_number})"

                StockMovement.objects.create(
                    inventory_item=locked_item,
                    movement_type=StockMovement.MovementType.RECEIVED,
                    quantity=quantity,
                    movement_date=timezone.now(),
                    reason=movement_note,
                    reference_number=f"PUR-{purchase.id}",
                    recorded_by=request.user,
                )

            messages.success(
                request,
                f"Successfully recorded purchase of {quantity} chickens from {supplier.supplier_name}. "
                f"Total: R {final_amount:.2f} (Avg: R {unit_price:.2f}/bird, Net: R {net_unit_price:.2f}/bird). "
                f"Updated '{locked_item.item_name}' stock to {locked_item.quantity_on_hand} birds."
            )
            return redirect('purchases:detail', pk=purchase.pk)

        messages.error(request, "Please correct the errors in the chicken purchase form.")
        return render(request, self.template_name, {'form': form})


# ===========================================================================
# C. Ingredient & Supplies Purchasing Views (UC-02)
# ===========================================================================

class SuppliesPurchaseCreateView(ManagerRequiredMixin, View):
    """
    Captures purchases of ingredients and other supplies:
    Tomatoes, Onions, Maize meal, Soup sachets, Spices, Packaging, etc.
    Supports recording multiple items on a single purchase transaction.
    Atomically updates stock and logs movements.
    """
    template_name = 'purchases/supplies_purchase_form.html'

    def get(self, request):
        header_form = SuppliesPurchaseHeaderForm()
        formset = PurchaseItemFormSet()
        inventory_items = InventoryItem.objects.filter(is_active=True).order_by('item_type', 'item_name')

        return render(request, self.template_name, {
            'header_form': header_form,
            'formset': formset,
            'inventory_items': inventory_items,
        })

    def post(self, request):
        header_form = SuppliesPurchaseHeaderForm(request.POST)
        purchase_dummy = Purchase()
        formset = PurchaseItemFormSet(request.POST, instance=purchase_dummy)

        if header_form.is_valid() and formset.is_valid():
            # Check line items and calculate total gross
            valid_item_forms = [
                f for f in formset
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('inventory_item')
            ]
            if not valid_item_forms:
                messages.error(request, "At least one purchase line item is required.")
                return render(request, self.template_name, {
                    'header_form': header_form,
                    'formset': formset,
                })

            total_gross = sum(
                f.cleaned_data['quantity'] * f.cleaned_data['unit_price']
                for f in valid_item_forms
            )
            discount = header_form.cleaned_data.get('discount') or Decimal('0.00')
            if discount > total_gross:
                header_form.add_error(
                    'discount',
                    f"Discount (R {discount:.2f}) cannot exceed the total purchase amount (R {total_gross:.2f})."
                )
                return render(request, self.template_name, {
                    'header_form': header_form,
                    'formset': formset,
                })

            with transaction.atomic():
                # 1. Create Purchase Header
                purchase = header_form.save(commit=False)
                purchase.recorded_by = request.user
                purchase.total_amount = total_gross
                purchase.final_amount = max(Decimal('0.00'), total_gross - discount)
                purchase.save()

                # 2. Process line items
                items = formset.save(commit=False)
                for item in items:
                    item.purchase = purchase
                    item.subtotal = item.quantity * item.unit_price
                    item.save()

                    # 3. Update inventory item stock with lock
                    locked_inv_item = InventoryItem.objects.select_for_update().get(pk=item.inventory_item.pk)
                    locked_inv_item.quantity_on_hand += item.quantity
                    locked_inv_item.save(update_fields=['quantity_on_hand', 'updated_at'])

                    # 4. Record stock movement
                    StockMovement.objects.create(
                        inventory_item=locked_inv_item,
                        movement_type=StockMovement.MovementType.RECEIVED,
                        quantity=item.quantity,
                        movement_date=timezone.now(),
                        reason=f"Supplies purchase from {purchase.supplier.supplier_name}",
                        reference_number=f"PUR-{purchase.id}",
                        recorded_by=request.user,
                    )

            messages.success(
                request,
                f"Successfully recorded purchase #{purchase.id} from {purchase.supplier.supplier_name} "
                f"with {len(items)} items for R {purchase.final_amount:.2f}."
            )
            return redirect('purchases:detail', pk=purchase.pk)

            messages.success(
                request,
                f"Successfully recorded purchase #{purchase.id} from {purchase.supplier.supplier_name} "
                f"with {len(items)} items for R {purchase.final_amount:.2f}."
            )
            return redirect('purchases:detail', pk=purchase.pk)

        messages.error(request, "Please correct the errors in the purchase form.")
        return render(request, self.template_name, {
            'header_form': header_form,
            'formset': formset,
        })


# ===========================================================================
# Purchase History & Details
# ===========================================================================

class PurchaseListView(ManagerRequiredMixin, View):
    """
    List all purchases (chicken and supplies) with filters, search, and totals.
    """
    template_name = 'purchases/purchase_list.html'

    def get(self, request):
        supplier_id = request.GET.get('supplier', '').strip()
        payment_method = request.GET.get('payment', '').strip()
        query = request.GET.get('q', '').strip()

        purchases = Purchase.objects.select_related('supplier', 'recorded_by').prefetch_related('items__inventory_item').all()

        if supplier_id:
            purchases = purchases.filter(supplier_id=supplier_id)

        if payment_method:
            purchases = purchases.filter(payment_method=payment_method)

        if query:
            purchases = purchases.filter(
                Q(invoice_number__icontains=query) |
                Q(supplier__supplier_name__icontains=query) |
                Q(notes__icontains=query)
            )

        total_spend = purchases.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')

        context = {
            'purchases': purchases[:100],
            'suppliers': Supplier.objects.filter(is_active=True).order_by('supplier_name'),
            'payment_methods': Purchase.PaymentMethod.choices,
            'current_supplier_id': supplier_id,
            'current_payment': payment_method,
            'total_spend': total_spend,
            'query': query,
        }
        return render(request, self.template_name, context)


class PurchaseDetailView(ManagerRequiredMixin, View):
    """
    View individual purchase transaction with line items and stock movements.
    """
    template_name = 'purchases/purchase_detail.html'

    def get(self, request, pk):
        purchase = get_object_or_404(
            Purchase.objects.select_related('supplier', 'recorded_by').prefetch_related('items__inventory_item'),
            pk=pk
        )
        movements = StockMovement.objects.filter(reference_number=f"PUR-{purchase.id}")

        return render(request, self.template_name, {
            'purchase': purchase,
            'movements': movements,
        })
