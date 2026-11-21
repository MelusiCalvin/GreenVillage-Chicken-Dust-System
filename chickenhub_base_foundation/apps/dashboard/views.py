from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone
from apps.accounts.decorators import staff_required
from apps.inventory.models import InventoryItem
from apps.orders.models import CustomerOrder
from apps.purchases.models import Purchase
from apps.sales.models import Sale


@login_required
@staff_required
def dashboard_index(request):
    """
    Staff dashboard landing page.
    Displays business overview statistics, quick operational links,
    and recent activity with real-time stock alerts.
    """
    user = request.user
    today = timezone.now().date()

    # Current inventory snapshot
    active_items = InventoryItem.objects.filter(is_active=True)
    total_stock_items = active_items.count()
    low_stock_list = active_items.filter(quantity_on_hand__lte=F('reorder_level')).order_by(
        'quantity_on_hand', 'item_name'
    )
    low_stock_count = low_stock_list.count()

    # Query real today's sales stats
    today_sales_qs = Sale.objects.filter(sale_date__date=today)
    today_revenue = today_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_sales_count = today_sales_qs.count()
    recent_sales = Sale.objects.select_related('recorded_by', 'order').prefetch_related(
        'items__product'
    ).order_by('-sale_date')[:5]
    recent_purchases = Purchase.objects.select_related('supplier', 'recorded_by').prefetch_related(
        'items__inventory_item'
    ).order_by('-purchase_date', '-created_at')[:5]
    recent_orders = CustomerOrder.objects.select_related('customer').prefetch_related(
        'items__product'
    ).order_by('-order_date')[:5]
    pending_orders = CustomerOrder.objects.filter(
        order_status=CustomerOrder.OrderStatus.PENDING
    ).count()

    context = {
        'today': today,
        'user': user,
        'stats': {
            'today_sales': f'R {today_revenue:.2f}',
            'today_sales_count': today_sales_count,
            'pending_orders': pending_orders,
            'total_stock_items': total_stock_items,
            'low_stock_items': low_stock_count,
        },
        'low_stock_alerts': low_stock_list[:8],
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'recent_orders': recent_orders,
    }

    return render(request, 'dashboard/overview.html', context)
