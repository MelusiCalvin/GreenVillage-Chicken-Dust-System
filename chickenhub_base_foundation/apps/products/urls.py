from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product / Menu Management
    path('', views.ProductListView.as_view(), name='list'),
    path('new/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/toggle-availability/', views.ProductToggleAvailabilityView.as_view(), name='toggle_availability'),

    # Recipe Management
    path('<int:pk>/recipe/', views.RecipeEditView.as_view(), name='recipe_edit'),
    path('<int:pk>/recipe/view/', views.RecipeDetailView.as_view(), name='recipe_detail'),
]
