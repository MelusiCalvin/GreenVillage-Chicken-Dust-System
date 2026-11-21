from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import InventoryItem
from .models import Purchase, PurchaseItem, Supplier

_BS_INPUT = {'class': 'form-control'}
_BS_SELECT = {'class': 'form-select'}
_BS_TEXTAREA = {'class': 'form-control', 'rows': 2}


class SupplierForm(forms.ModelForm):
    """
    Form for registering or updating Supplier records.
    """
    class Meta:
        model = Supplier
        fields = [
            'supplier_name',
            'contact_person',
            'phone_number',
            'email',
            'address',
            'is_active',
        ]
        widgets = {
            'supplier_name': forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Midlands Poultry Farm'}),
            'contact_person': forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Johan van der Merwe'}),
            'phone_number': forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. 082 123 4567'}),
            'email': forms.EmailInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. sales@midlandspoultry.co.za'}),
            'address': forms.Textarea(attrs={**_BS_TEXTAREA, 'placeholder': 'Farm / Depot physical address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ChickenPurchaseForm(forms.Form):
    """
    Specialized form for capturing Chicken Purchases (UC-01).
    Captures:
    - Purchase date
    - Supplier
    - Quantity of chickens purchased
    - Total stock price (gross)
    - Discount
    - Final purchase amount (calculated)
    - Average chicken price (calculated)
    - Payment method
    - Invoice / slip number
    - Notes
    """
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        label=_('Poultry Supplier'),
        widget=forms.Select(attrs=_BS_SELECT),
        empty_label=_('— Select Poultry Supplier —'),
    )
    purchase_date = forms.DateField(
        initial=timezone.now,
        label=_('Purchase Date'),
        widget=forms.DateInput(attrs={**_BS_INPUT, 'type': 'date'}),
    )
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(item_type=InventoryItem.ItemType.WHOLE_CHICKEN, is_active=True),
        required=False,
        label=_('Whole Chicken Stock Item'),
        widget=forms.Select(attrs=_BS_SELECT),
        help_text=_('Select the whole chicken stock category to update (or leave blank to use default).')
    )
    quantity = forms.DecimalField(
        min_value=Decimal('1.00'),
        max_digits=10,
        decimal_places=2,
        label=_('Quantity of Chickens (Birds)'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '1', 'min': '1', 'placeholder': 'e.g. 50'}),
        help_text=_('Total number of whole chickens delivered.')
    )
    total_amount = forms.DecimalField(
        min_value=Decimal('0.00'),
        max_digits=10,
        decimal_places=2,
        label=_('Total Stock Price (Gross R)'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0', 'placeholder': 'e.g. 2750.00'}),
        help_text=_('Total invoice/slip amount before any discount.')
    )
    discount = forms.DecimalField(
        min_value=Decimal('0.00'),
        max_digits=10,
        decimal_places=2,
        initial=Decimal('0.00'),
        required=False,
        label=_('Discount Received (R)'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
        help_text=_('Optional discount granted by supplier.')
    )
    payment_method = forms.ChoiceField(
        choices=Purchase.PaymentMethod.choices,
        label=_('Payment Method'),
        widget=forms.Select(attrs=_BS_SELECT),
    )
    invoice_number = forms.CharField(
        max_length=50,
        required=False,
        label=_('Invoice / Receipt Number'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. INV-2026-0042'}),
    )
    notes = forms.CharField(
        required=False,
        label=_('Notes / Batch Details'),
        widget=forms.Textarea(attrs={**_BS_TEXTAREA, 'placeholder': 'Batch quality notes, delivery conditions, etc.'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_amount') or Decimal('0.00')
        discount = cleaned_data.get('discount') or Decimal('0.00')
        qty = cleaned_data.get('quantity') or Decimal('0.00')

        if discount > total:
            raise forms.ValidationError({
                'discount': _('Discount cannot exceed the total purchase price.')
            })

        if qty <= 0:
            raise forms.ValidationError({
                'quantity': _('Quantity of chickens must be greater than zero.')
            })

        # Calculate average and final amounts
        cleaned_data['final_amount'] = total - discount
        cleaned_data['average_chicken_price'] = (total / qty).quantize(Decimal('0.01'))
        if total > 0:
            cleaned_data['net_average_chicken_price'] = (cleaned_data['final_amount'] / qty).quantize(Decimal('0.01'))
        else:
            cleaned_data['net_average_chicken_price'] = Decimal('0.00')

        return cleaned_data


class SuppliesPurchaseHeaderForm(forms.ModelForm):
    """
    Header form for Ingredient and Supplies Purchasing (UC-02).
    """
    class Meta:
        model = Purchase
        fields = [
            'supplier',
            'purchase_date',
            'invoice_number',
            'payment_method',
            'discount',
            'notes',
        ]
        widgets = {
            'supplier': forms.Select(attrs=_BS_SELECT),
            'purchase_date': forms.DateInput(attrs={**_BS_INPUT, 'type': 'date'}),
            'invoice_number': forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. REC-9921'}),
            'payment_method': forms.Select(attrs=_BS_SELECT),
            'discount': forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs=_BS_TEXTAREA),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['discount'].initial = Decimal('0.00')

    def _post_clean(self):
        # Exclude 'discount' check against 0 total_amount during header-only validation,
        # because total_amount is calculated from line items in the formset.
        orig_total = self.instance.total_amount
        self.instance.total_amount = Decimal('999999999.00')
        super()._post_clean()
        self.instance.total_amount = orig_total


class PurchaseItemForm(forms.ModelForm):
    """
    Line item form for purchasing tomatoes, onions, maize meal, soup sachets, etc.
    """
    class Meta:
        model = PurchaseItem
        fields = ['inventory_item', 'quantity', 'unit_price']
        widgets = {
            'inventory_item': forms.Select(attrs=_BS_SELECT),
            'quantity': forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0.01', 'placeholder': 'Qty'}),
            'unit_price': forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0', 'placeholder': 'Price per unit'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inventory_item'].queryset = InventoryItem.objects.filter(is_active=True)


PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
