from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.StaffLoginView.as_view(), name='login'),
    path('logout/', views.StaffLogoutView.as_view(), name='logout'),

    # Staff account management (Owner only)
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/create/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/update/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('staff/<int:pk>/deactivate/', views.StaffDeactivateView.as_view(), name='staff_deactivate'),
    path('staff/<int:pk>/password/', views.StaffPasswordResetView.as_view(), name='staff_password'),
]
