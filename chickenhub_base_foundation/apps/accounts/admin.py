from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for ChickenHub custom User model.
    Includes role and phone number fields in management views.
    """
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('username',)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _('ChickenHub Role & Details'),
            {
                'fields': ('role', 'phone_number'),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            _('ChickenHub Role & Details'),
            {
                'fields': ('role', 'phone_number'),
            },
        ),
    )
