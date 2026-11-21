from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard & Stock List
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),
    path('items/new/', views.InventoryItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.InventoryItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.InventoryItemUpdateView.as_view(), name='item_update'),

    # Stock Movements & Actions
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/used/', views.RecordStockUsedView.as_view(), name='record_used'),
    path('movements/wasted/', views.RecordStockWastedView.as_view(), name='record_wasted'),
    path('movements/adjust/', views.RecordStockAdjustmentView.as_view(), name='record_adjustment'),
    path('movements/receive/', views.RecordStockReceivedManualView.as_view(), name='record_receive'),

    # Chicken Processing (Whole Chickens -> Portions)
    path('processing/', views.ChickenProcessingListView.as_view(), name='processing_list'),
    path('processing/new/', views.ChickenProcessingCreateView.as_view(), name='processing_create'),
    path('processing/<int:pk>/', views.ChickenProcessingDetailView.as_view(), name='processing_detail'),
]
