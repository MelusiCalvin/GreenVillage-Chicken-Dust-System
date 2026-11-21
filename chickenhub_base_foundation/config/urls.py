"""
URL configuration for ChickenHub project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import public_home

# Public customer-facing patterns
public_patterns = [
    path('', public_home, name='home'),
]

urlpatterns = [
    # Public customer pages
    path('', include((public_patterns, 'public'))),

    # Staff authentication & management
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('purchases/', include('apps.purchases.urls', namespace='purchases')),
    path('products/', include('apps.products.urls', namespace='products')),
    path('sales/', include('apps.sales.urls', namespace='sales')),
    path('orders/', include('apps.orders.urls', namespace='orders')),

    # Django built-in admin
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
