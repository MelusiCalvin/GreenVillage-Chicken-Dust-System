from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()


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


# ---------------------------------------------------------------------------
# Staff Account Management Forms (Owner only)
# ---------------------------------------------------------------------------

_BS_INPUT = {'class': 'form-control'}
_BS_SELECT = {'class': 'form-select'}


class StaffUserCreationForm(UserCreationForm):
    """
    Form for the Owner to create a new staff account.
    Extends Django's UserCreationForm with ChickenHub role and contact fields.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label=_('First Name'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Sipho'}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label=_('Last Name'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Dlamini'}),
    )
    email = forms.EmailField(
        required=False,
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={**_BS_INPUT, 'placeholder': 'staff@chickenhub.co.za'}),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label=_('Phone Number'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': '060 123 4567'}),
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        label=_('Staff Role'),
        widget=forms.Select(attrs=_BS_SELECT),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to inherited password fields
        self.fields['username'].widget.attrs.update({**_BS_INPUT, 'placeholder': 'e.g. sipho_chef'})
        self.fields['username'].help_text = _(
            'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        )
        self.fields['password1'].widget.attrs.update({**_BS_INPUT, 'placeholder': 'Set a secure password'})
        self.fields['password1'].label = _('Password')
        self.fields['password2'].widget.attrs.update({**_BS_INPUT, 'placeholder': 'Confirm password'})
        self.fields['password2'].label = _('Confirm Password')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # All ChickenHub staff need Django staff flag
        if commit:
            user.save()
        return user


class StaffUserUpdateForm(forms.ModelForm):
    """
    Form for the Owner to update an existing staff member's profile and role.
    Password changes are handled by a separate form.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'role', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs=_BS_INPUT),
            'last_name': forms.TextInput(attrs=_BS_INPUT),
            'email': forms.EmailInput(attrs=_BS_INPUT),
            'phone_number': forms.TextInput(attrs=_BS_INPUT),
            'role': forms.Select(attrs=_BS_SELECT),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': _('Account Active'),
        }
        help_texts = {
            'is_active': _('Uncheck to deactivate this account without deleting it.'),
        }


class StaffPasswordResetForm(SetPasswordForm):
    """
    Allows the Owner to set a new password for any staff member.
    Uses Django's SetPasswordForm (no old-password required).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({**_BS_INPUT, 'placeholder': 'Enter new password'})
        self.fields['new_password1'].label = _('New Password')
        self.fields['new_password2'].widget.attrs.update({**_BS_INPUT, 'placeholder': 'Confirm new password'})
        self.fields['new_password2'].label = _('Confirm New Password')
