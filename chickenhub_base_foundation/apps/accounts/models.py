from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user manager that ensures staff users have staff status
    and superusers are automatically assigned the OWNER role.
    """
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.OWNER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Account model for ChickenHub staff members.
    Supports role-based access for Owner, Manager and Employee.
    """
    class Role(models.TextChoices):
        OWNER = 'OWNER', _('Owner')
        MANAGER = 'MANAGER', _('Manager')
        EMPLOYEE = 'EMPLOYEE', _('Employee')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name=_('Role'),
        help_text=_('Staff role determining operational and administrative access.')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number'),
        help_text=_('Contact telephone or mobile number.')
    )

    objects = CustomUserManager()

    class Meta:
        app_label = 'accounts'
        verbose_name = _('User Account')
        verbose_name_plural = _('User Accounts')
        ordering = ['username']

    def __str__(self):
        full = self.get_full_name()
        if full:
            return f"{full} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_owner(self):
        """Owner has full access to the system, user management and reports."""
        return self.is_superuser or self.role == self.Role.OWNER

    @property
    def is_manager(self):
        """Manager has operational oversight across inventory, sales, purchases and orders."""
        return self.is_superuser or self.role in [self.Role.OWNER, self.Role.MANAGER]

    @property
    def is_employee(self):
        """Employee can perform assigned daily operational tasks."""
        return self.is_superuser or self.role in [
            self.Role.OWNER,
            self.Role.MANAGER,
            self.Role.EMPLOYEE
        ]

    @property
    def role_badge_class(self):
        """Returns Bootstrap badge CSS class for visual role display."""
        badge_map = {
            self.Role.OWNER: 'badge bg-danger',
            self.Role.MANAGER: 'badge bg-warning text-dark',
            self.Role.EMPLOYEE: 'badge bg-info text-dark',
        }
        return badge_map.get(self.role, 'badge bg-secondary')
