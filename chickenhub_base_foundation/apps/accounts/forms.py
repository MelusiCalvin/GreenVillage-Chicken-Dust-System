from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class StaffLoginForm(AuthenticationForm):
    """
    Login form for ChickenHub staff members.
    Styled with Bootstrap 5 classes and field placeholders.
    """
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your staff username',
                'autocomplete': 'username',
                'autofocus': True,
            }
        ),
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your password',
                'autocomplete': 'current-password',
            }
        ),
    )

    def confirm_login_allowed(self, user):
        """
        Verify that user is active and is an authorized staff member.
        """
        super().confirm_login_allowed(user)
        if not (user.is_staff or user.is_superuser or user.role in [
            user.Role.OWNER,
            user.Role.MANAGER,
            user.Role.EMPLOYEE,
        ]):
            raise forms.ValidationError(
                _('This account does not have access to the staff management portal.'),
                code='inactive_staff',
            )
