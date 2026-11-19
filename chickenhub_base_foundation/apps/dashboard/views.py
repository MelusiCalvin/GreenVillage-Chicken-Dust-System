from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from apps.accounts.decorators import staff_required


@login_required
@staff_required
def dashboard_index(request):
    """
    Staff dashboard landing page.
    Displays business overview statistics, quick operational links,
    and recent activity.
    Values are placeholders during this foundation phase until the individual
    inventory, sales, and order management modules are integrated.
    """
    user = request.user
    today = timezone.now().date()

    # Foundation stage placeholders (real database queries will connect
    # in subsequent module development phases)
    context = {
        'today': today,
        'user': user,
        'stats': {
            'today_sales': 'R 0.00',
            'today_sales_count': 0,
            'pending_orders': 0,
            'total_stock_items': 0,
            'low_stock_items': 0,
        },
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
