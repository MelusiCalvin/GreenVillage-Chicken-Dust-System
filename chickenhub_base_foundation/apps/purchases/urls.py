from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    # Purchases
    path('', views.PurchaseListView.as_view(), name='list'),
    path('chicken/new/', views.ChickenPurchaseCreateView.as_view(), name='chicken_create'),
    path('supplies/new/', views.SuppliesPurchaseCreateView.as_view(), name='supplies_create'),
    path('<int:pk>/', views.PurchaseDetailView.as_view(), name='detail'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/new/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/toggle-active/', views.SupplierToggleActiveView.as_view(), name='supplier_toggle_active'),
]
