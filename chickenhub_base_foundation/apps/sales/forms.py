from decimal import Decimal
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Sale

_BS_INPUT = {'class': 'form-control'}
_BS_SELECT = {'class': 'form-select'}
_BS_TEXTAREA = {'class': 'form-control', 'rows': 2}


class WalkInSaleForm(forms.ModelForm):
    """
    Form for recording a walk-in counter sale at the point of sale.
    Captures payment method, amount tendered (for cash change calculation), and notes.
    """
    payment_method = forms.ChoiceField(
        choices=(), required=False, label=_('Payment Method'),
        widget=forms.Select(attrs={**_BS_SELECT, 'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure with CHICKENHUB_PAYMENT_METHODS = [("code", "Label"), ...].
        self.fields['payment_method'].choices = [('', _('Not specified'))] + list(
            getattr(settings, 'CHICKENHUB_PAYMENT_METHODS', ())
        )

    class Meta:
        model = Sale
        fields = [
            'payment_method',
            'amount_tendered',
            'notes',
        ]
        widgets = {
            'amount_tendered': forms.NumberInput(attrs={
                **_BS_INPUT,
                'step': '0.01',
                'min': '0',
                'placeholder': 'e.g. 200.00'
            }),
            'notes': forms.Textarea(attrs={
                **_BS_TEXTAREA,
                'placeholder': 'Customer requests, special seasoning, takeaway note...'
            }),
        }
        labels = {
            'amount_tendered': _('Amount Tendered (optional)'),
            'notes': _('Order / Customer Notes'),
        }
        help_texts = {
            'amount_tendered': _('Optional. Payment handling can be configured when business preferences are confirmed.'),
        }

    def clean_amount_tendered(self):
        tendered = self.cleaned_data.get('amount_tendered')
        if tendered is not None and tendered < 0:
            raise forms.ValidationError(_('Amount tendered cannot be negative.'))
        return tendered
