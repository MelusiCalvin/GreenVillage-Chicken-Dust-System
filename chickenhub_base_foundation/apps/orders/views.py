from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View
from apps.accounts.decorators import StaffRequiredMixin
from apps.inventory.models import InventoryItem, StockMovement
from apps.products.models import Product, Recipe
from apps.sales.models import Sale, SaleItem
from .forms import GuestOrderForm
from .models import CustomerOrder, OrderItem, OrderStatusHistory


def _cart(request):
    """Return a cleaned session cart as product-id to positive integer quantity."""
    cleaned = {}
    for key, value in request.session.get('order_cart', {}).items():
        try:
            product_id, quantity = int(key), int(value)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and quantity > 0:
            cleaned[str(product_id)] = min(quantity, 999)
    request.session['order_cart'] = cleaned
    return cleaned


def menu(request):
    return render(request, 'orders/menu.html', {
        'products': Product.objects.filter(is_available=True).order_by('category', 'product_name'),
        'cart_count': sum(_cart(request).values()),
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    try:
        quantity = int(request.POST.get('quantity', '1'))
        if quantity < 1 or quantity > 999:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, 'Choose a quantity from 1 to 999.')
        return redirect('orders:menu')
    cart = _cart(request)
    cart[str(product.pk)] = min(cart.get(str(product.pk), 0) + quantity, 999)
    request.session['order_cart'] = cart
    request.session.modified = True
    messages.success(request, f'{product.product_name} added to your cart.')
    return redirect('orders:cart')


def cart(request):
    stored = _cart(request)
    products = Product.objects.filter(pk__in=stored.keys(), is_available=True).order_by('product_name')
    rows = []
    total = Decimal('0.00')
    for product in products:
        quantity = stored[str(product.pk)]
        subtotal = product.selling_price * quantity
        rows.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal
    visible_ids = {str(row['product'].pk) for row in rows}
    removed = set(stored) - visible_ids
    if removed:
        for product_id in removed:
            stored.pop(product_id, None)
        request.session['order_cart'] = stored
        messages.warning(request, 'Unavailable products were removed from your cart.')
    return render(request, 'orders/cart.html', {'rows': rows, 'total': total})


@require_POST
def update_cart(request):
    cart_data = _cart(request)
    for key in list(cart_data):
        field = f'quantity_{key}'
        if field not in request.POST:
            continue
        try:
            quantity = int(request.POST[field])
            if quantity < 0 or quantity > 999:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'Quantities must be whole numbers from 0 to 999.')
            return redirect('orders:cart')
        if quantity:
            cart_data[key] = quantity
        else:
            cart_data.pop(key, None)
    request.session['order_cart'] = cart_data
    request.session.modified = True
    return redirect('orders:cart')


def checkout(request):
    cart_data = _cart(request)
    products = {str(p.pk): p for p in Product.objects.filter(pk__in=cart_data.keys(), is_available=True)}
    if not cart_data or len(products) != len(cart_data):
        request.session['order_cart'] = {key: value for key, value in cart_data.items() if key in products}
        messages.error(request, 'Your cart is empty or contains unavailable products. Please review it.')
        return redirect('orders:cart')
    rows = []
    total = Decimal('0.00')
    for key, quantity in cart_data.items():
        product = products[key]
        subtotal = product.selling_price * quantity
        rows.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal

    form = GuestOrderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Refresh product state and prices before committing the order.
        with transaction.atomic():
            current_products = {
                str(p.pk): p for p in Product.objects.select_for_update()
                .filter(pk__in=cart_data.keys(), is_available=True)
            }
            if len(current_products) != len(cart_data):
                messages.error(request, 'A product became unavailable. Review your cart and try again.')
                return redirect('orders:cart')
            customer = form.save()
            current_total = sum(
                (current_products[key].selling_price * quantity for key, quantity in cart_data.items()),
                Decimal('0.00'),
            )
            order = CustomerOrder.objects.create(customer=customer, total_amount=current_total)
            OrderStatusHistory.objects.create(
                order=order,
                previous_status='',
                new_status=CustomerOrder.OrderStatus.PENDING,
                reason='Order submitted by customer',
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=current_products[key],
                    quantity=quantity,
                    unit_price=current_products[key].selling_price,
                    subtotal=current_products[key].selling_price * quantity,
                )
                for key, quantity in cart_data.items()
            ])
        request.session.pop('order_cart', None)
        return redirect('orders:confirmation', reference=order.order_reference)
    return render(request, 'orders/checkout.html', {'form': form, 'rows': rows, 'total': total})


def confirmation(request, reference):
    order = get_object_or_404(
        CustomerOrder.objects.select_related('customer').prefetch_related('items__product'),
        order_reference=reference,
    )
    return render(request, 'orders/confirmation.html', {'order': order})


class StaffOrderListView(StaffRequiredMixin, View):
    template_name = 'orders/staff_list.html'

    def get(self, request):
        status = request.GET.get('status', '').strip()
        query = request.GET.get('q', '').strip()
        orders = CustomerOrder.objects.select_related('customer').all()
        if status in CustomerOrder.OrderStatus.values:
            orders = orders.filter(order_status=status)
        if query:
            orders = orders.filter(
                Q(order_reference__icontains=query) |
                Q(customer__first_name__icontains=query) |
                Q(customer__last_name__icontains=query) |
                Q(customer__phone_number__icontains=query)
            )
        return render(request, self.template_name, {
            'orders': orders,
            'statuses': CustomerOrder.OrderStatus.choices,
            'selected_status': status,
            'query': query,
        })


class StaffOrderDetailView(StaffRequiredMixin, View):
    template_name = 'orders/staff_detail.html'

    def get(self, request, pk):
        order = get_object_or_404(
            CustomerOrder.objects.select_related('customer').prefetch_related(
                'items__product', 'status_history__changed_by'
            ),
            pk=pk,
        )
        return render(request, self.template_name, {
            'order': order,
            'allowed_transitions': _allowed_transitions(order.order_status),
        })

    def post(self, request, pk):
        new_status = request.POST.get('status', '')
        reason = request.POST.get('reason', '').strip()
        try:
            with transaction.atomic():
                order = CustomerOrder.objects.select_for_update().get(pk=pk)
                allowed = _allowed_transitions(order.order_status)
                if new_status not in allowed:
                    messages.error(request, 'That order status change is not allowed.')
                    return redirect('orders:staff_detail', pk=pk)
                if new_status == CustomerOrder.OrderStatus.CANCELLED and not reason:
                    messages.error(request, 'Enter a reason before rejecting this order.')
                    return redirect('orders:staff_detail', pk=pk)

                previous_status = order.order_status
                if new_status == CustomerOrder.OrderStatus.PREPARING:
                    _deduct_order_inventory(order, request.user)
                if new_status == CustomerOrder.OrderStatus.COLLECTED:
                    _record_collected_order_sale(order, request.user)

                order.order_status = new_status
                if new_status == CustomerOrder.OrderStatus.CANCELLED:
                    order.rejection_reason = reason
                order.save(update_fields=[
                    'order_status', 'rejection_reason', 'updated_at', 'inventory_deducted_at',
                ])
                OrderStatusHistory.objects.create(
                    order=order,
                    previous_status=previous_status,
                    new_status=new_status,
                    reason=reason,
                    changed_by=request.user,
                )
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('orders:staff_detail', pk=pk)
        messages.success(request, f'Order {order.order_reference} updated to {order.get_order_status_display()}.')
        return redirect('orders:staff_detail', pk=pk)


def _allowed_transitions(status):
    transitions = {
        CustomerOrder.OrderStatus.PENDING: {
            CustomerOrder.OrderStatus.ACCEPTED,
            CustomerOrder.OrderStatus.CANCELLED,
        },
        CustomerOrder.OrderStatus.ACCEPTED: {
            CustomerOrder.OrderStatus.PREPARING,
            CustomerOrder.OrderStatus.CANCELLED,
        },
        CustomerOrder.OrderStatus.PREPARING: {CustomerOrder.OrderStatus.READY},
        CustomerOrder.OrderStatus.READY: {CustomerOrder.OrderStatus.COLLECTED},
    }
    return transitions.get(status, set())


def _deduct_order_inventory(order, user):
    if order.inventory_deducted_at:
        return
    requirements = {}
    items = order.items.select_related('product').all()
    if not items.exists():
        raise ValueError('This order has no items and cannot be prepared.')
    for order_item in items:
        product = order_item.product
        try:
            recipe = product.recipe
        except Recipe.DoesNotExist:
            raise ValueError(f'{product.product_name} has no recipe; configure its recipe before preparation.')
        recipe_items = list(recipe.items.select_related('inventory_item').all())
        if not recipe_items:
            raise ValueError(f'{product.product_name} has an empty recipe and cannot be prepared.')
        for recipe_item in recipe_items:
            inv_id = recipe_item.inventory_item_id
            needed = recipe_item.quantity_required * order_item.quantity
            if inv_id not in requirements:
                requirements[inv_id] = {'item': recipe_item.inventory_item, 'quantity': Decimal('0.00')}
            requirements[inv_id]['quantity'] += needed

    locked_items = {
        item.pk: item for item in InventoryItem.objects.select_for_update()
        .filter(pk__in=sorted(requirements)).order_by('pk')
    }
    for inv_id, requirement in requirements.items():
        item = locked_items.get(inv_id)
        if item is None or not item.is_active or item.quantity_on_hand < requirement['quantity']:
            name = item.item_name if item else requirement['item'].item_name
            have = item.quantity_on_hand if item else Decimal('0.00')
            raise ValueError(f'Insufficient active stock for {name}: need {requirement["quantity"]}, have {have}.')

    now = timezone.now()
    for inv_id, requirement in requirements.items():
        item = locked_items[inv_id]
        item.quantity_on_hand -= requirement['quantity']
        item.save(update_fields=['quantity_on_hand', 'updated_at'])
        StockMovement.objects.create(
            inventory_item=item,
            movement_type=StockMovement.MovementType.USED,
            quantity=-requirement['quantity'],
            movement_date=now,
            reason=f'Preparation for collection order {order.order_reference}',
            reference_number=order.order_reference,
            recorded_by=user,
        )
    order.inventory_deducted_at = now


def _record_collected_order_sale(order, user):
    # CustomerOrder.sale is OneToOne, so this makes revenue visible once in sales.
    if hasattr(order, 'sale'):
        return
    sale = Sale.objects.create(
        order=order,
        sale_type=Sale.SaleType.ONLINE_COLLECTION,
        sale_date=timezone.now(),
        total_amount=order.total_amount,
        payment_method='',
        recorded_by=user,
        notes=f'Collected online order {order.order_reference}',
    )
    SaleItem.objects.bulk_create([
        SaleItem(
            sale=sale,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
        )
        for item in order.items.select_related('product').all()
    ])


class TrackOrderView(View):
    template_name = 'orders/track.html'

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        reference = request.POST.get('reference', '').strip().upper()
        phone = ''.join(char for char in request.POST.get('phone_number', '') if char.isdigit() or char == '+')
        order = CustomerOrder.objects.filter(
            order_reference__iexact=reference,
            customer__phone_number=phone,
        ).prefetch_related('items__product').first()
        return render(request, self.template_name, {'order': order, 'submitted': True})
