from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from apps.accounts.decorators import staff_required
from apps.inventory.models import InventoryItem
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

    # Query real inventory stats
    active_items = InventoryItem.objects.filter(is_active=True)
    total_stock_items = active_items.count()
    low_stock_list = [i for i in active_items if i.is_low_stock]
    low_stock_count = len(low_stock_list)

    # Query real today's sales stats
    today_sales_qs = Sale.objects.filter(sale_date__date=today)
    today_revenue = today_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_sales_count = today_sales_qs.count()

    context = {
        'today': today,
        'user': user,
        'stats': {
            'today_sales': f'R {today_revenue:.2f}',
            'today_sales_count': today_sales_count,
            'pending_orders': 0,
            'total_stock_items': total_stock_items,
            'low_stock_items': low_stock_count,
        },
        'low_stock_alerts': low_stock_list[:5],
        'system_status': {
            'version': '1.0.0-foundation',
            'environment': 'Development',
            'db_status': 'Connected (SQLite)',
        },
        'recent_activities': [
            {
                'title': 'System Foundation Initialized',
                'description': 'ChickenHub core authentication and role-based dashboard activated.',
                'timestamp': 'Just now',
                'icon': 'bi-shield-check',
                'badge': 'System',
                'badge_class': 'bg-success',
            },
            {
                'title': 'Staff Access Configured',
                'description': f'User {user.username} authenticated with {user.get_role_display()} permissions.',
                'timestamp': 'Active session',
                'icon': 'bi-person-check',
                'badge': 'Security',
                'badge_class': 'bg-primary',
            },
        ],
    }

    return render(request, 'dashboard/index.html', context)
