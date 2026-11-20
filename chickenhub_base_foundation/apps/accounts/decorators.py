from functools import wraps
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


def role_required(*allowed_roles, redirect_url='dashboard:index'):
    """
    Decorator that verifies if the logged-in user has one of the allowed roles
    (or is a superuser). If not authenticated, redirects to staff login with ?next=.
    If authenticated but unauthorized, redirects with an access-denied warning message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, "Please log in with your staff account to continue.")
                login_url = reverse_lazy('accounts:login')
                return redirect(f"{login_url}?next={request.path}")

            if not request.user.is_active:
                messages.error(request, "Your staff account has been deactivated. Please contact the owner.")
                return redirect('accounts:logout')

            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.warning(
                request,
                f"Access denied. Your role ({request.user.get_role_display()}) does not have permission to view that section."
            )
            return redirect(redirect_url)

        return _wrapped_view
    return decorator


def owner_required(view_func):
    """Restricts access to Owners (and Superusers) only."""
    from .models import User
    return role_required(User.Role.OWNER)(view_func)


def manager_required(view_func):
    """Restricts access to Managers and Owners."""
    from .models import User
    return role_required(User.Role.OWNER, User.Role.MANAGER)(view_func)


def staff_required(view_func):
    """Allows any authorized staff member (Owner, Manager, Employee)."""
    from .models import User
    return role_required(User.Role.OWNER, User.Role.MANAGER, User.Role.EMPLOYEE)(view_func)


class RoleRequiredMixin(AccessMixin):
    """
    Class-based view mixin that verifies if the user belongs to one of the specified allowed_roles.
    Redirects unauthenticated visitors to login with ?next=.
    Redirects unauthorized staff with a warning message.
    """
    allowed_roles = []
    unauthorized_redirect_url = 'dashboard:index'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in with your staff account to continue.")
            login_url = reverse_lazy('accounts:login')
            return redirect(f"{login_url}?next={request.path}")

        if not request.user.is_active:
            messages.error(request, "Your staff account has been deactivated. Please contact the owner.")
            return redirect('accounts:logout')

        if request.user.is_superuser or request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)

        messages.warning(
            request,
            f"Access denied. Your role ({request.user.get_role_display()}) does not have permission to view that section."
        )
        return redirect(self.unauthorized_redirect_url)


class OwnerRequiredMixin(RoleRequiredMixin):
    """CBV mixin that restricts access strictly to Owners (and Superusers)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import User
        self.allowed_roles = [User.Role.OWNER]


class ManagerRequiredMixin(RoleRequiredMixin):
    """CBV mixin that permits Owners and Managers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import User
        self.allowed_roles = [User.Role.OWNER, User.Role.MANAGER]


class StaffRequiredMixin(RoleRequiredMixin):
    """CBV mixin that permits any active staff member (Owner, Manager, Employee)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import User
        self.allowed_roles = [User.Role.OWNER, User.Role.MANAGER, User.Role.EMPLOYEE]
