from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.menu, name='menu'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
    path('track/', views.TrackOrderView.as_view(), name='track'),
    path('staff/', views.StaffOrderListView.as_view(), name='staff_list'),
    path('staff/<int:pk>/', views.StaffOrderDetailView.as_view(), name='staff_detail'),
]
