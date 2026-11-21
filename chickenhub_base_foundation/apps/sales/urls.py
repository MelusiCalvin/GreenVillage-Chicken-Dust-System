from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Point of Sale & Walk-in Sales
    path('', views.SaleListView.as_view(), name='list'),
    path('pos/', views.WalkInSalePOSView.as_view(), name='pos'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('<int:pk>/receipt/', views.SaleDetailView.as_view(), name='receipt'),
]
