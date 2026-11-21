from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import InventoryItem, StockMovement, ChickenProcessing, ProcessingOutput

_BS_INPUT = {'class': 'form-control'}
_BS_SELECT = {'class': 'form-select'}
_BS_TEXTAREA = {'class': 'form-control', 'rows': 3}


class InventoryItemForm(forms.ModelForm):
    """
    Form to register or update an Inventory Item.
    Supports whole chickens, portions, ingredients, and consumables.
    """
    class Meta:
        model = InventoryItem
        fields = [
            'item_name',
            'item_type',
            'unit_of_measure',
            'quantity_on_hand',
            'reorder_level',
            'is_active',
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Tomatoes, Onions, Maize Meal 10kg'}),
            'item_type': forms.Select(attrs=_BS_SELECT),
            'unit_of_measure': forms.Select(attrs=_BS_SELECT),
            'quantity_on_hand': forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'reorder_level': _('When stock drops to or below this amount, low-stock warnings are triggered.'),
            'quantity_on_hand': _('Current physical stock available in the kitchen or storeroom.'),
        }

    def clean_quantity_on_hand(self):
        qty = self.cleaned_data.get('quantity_on_hand')
        if qty is not None and qty < 0:
            raise forms.ValidationError(_('Stock quantity on hand cannot be negative.'))
        return qty

    def clean_reorder_level(self):
        level = self.cleaned_data.get('reorder_level')
        if level is not None and level < 0:
            raise forms.ValidationError(_('Reorder level cannot be negative.'))
        return level


class StockUsageForm(forms.Form):
    """
    Form for recording stock used during kitchen cooking or daily preparation.
    Accessible to frontline employees, managers and owners.
    """
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True),
        label=_('Inventory Item Used'),
        widget=forms.Select(attrs=_BS_SELECT),
    )
    quantity = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label=_('Quantity Consumed / Used'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'placeholder': 'e.g. 5.00'}),
        help_text=_('Quantity consumed for cooking or preparation.')
    )
    movement_date = forms.DateTimeField(
        initial=timezone.now,
        label=_('Date & Time Used'),
        widget=forms.DateTimeInput(attrs={**_BS_INPUT, 'type': 'datetime-local'}),
        required=False
    )
    reason = forms.CharField(
        max_length=255,
        required=False,
        label=_('Prep Batch / Meal Notes'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Daily lunch pap prep, salsa batch'}),
        help_text=_('Optional note describing the prep batch.')
    )

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('inventory_item')
        qty = cleaned_data.get('quantity')
        if item and qty:
            if qty > item.quantity_on_hand:
                raise forms.ValidationError({
                    'quantity': _(
                        f"Cannot use {qty} {item.get_unit_of_measure_display()}. "
                        f"Only {item.quantity_on_hand} currently available on hand."
                    )
                })
        return cleaned_data


class StockWastageForm(forms.Form):
    """
    Form for recording spoiled, burned, damaged or expired stock.
    Requires a detailed explanation for business accountability.
    """
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True),
        label=_('Wasted / Spoiled Item'),
        widget=forms.Select(attrs=_BS_SELECT),
    )
    quantity = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label=_('Quantity Wasted'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'placeholder': 'e.g. 2.00'}),
    )
    movement_date = forms.DateTimeField(
        initial=timezone.now,
        label=_('Date & Time'),
        widget=forms.DateTimeInput(attrs={**_BS_INPUT, 'type': 'datetime-local'}),
        required=False
    )
    reason = forms.CharField(
        max_length=255,
        required=True,
        label=_('Reason for Wastage (Required)'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Burned on braai grill, spoiled tomatoes, dropped'}),
        help_text=_('Mandatory reason for audit and loss tracking.')
    )

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('inventory_item')
        qty = cleaned_data.get('quantity')
        if item and qty:
            if qty > item.quantity_on_hand:
                raise forms.ValidationError({
                    'quantity': _(
                        f"Cannot record wastage of {qty} {item.get_unit_of_measure_display()}. "
                        f"Only {item.quantity_on_hand} available on hand."
                    )
                })
        return cleaned_data


class StockAdjustmentForm(forms.Form):
    """
    Form for recording physical stock counts / audits.
    Computes discrepancy delta and records an ADJUSTMENT movement.
    """
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True),
        label=_('Inventory Item'),
        widget=forms.Select(attrs=_BS_SELECT),
    )
    new_counted_quantity = forms.DecimalField(
        min_value=Decimal('0.00'),
        max_digits=10,
        decimal_places=2,
        label=_('Actual Counted Stock (Physical Count)'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'placeholder': 'e.g. 15.00'}),
        help_text=_('Enter the actual quantity currently on shelves.')
    )
    movement_date = forms.DateTimeField(
        initial=timezone.now,
        label=_('Audit Date & Time'),
        widget=forms.DateTimeInput(attrs={**_BS_INPUT, 'type': 'datetime-local'}),
        required=False
    )
    reason = forms.CharField(
        max_length=255,
        required=True,
        label=_('Adjustment Reason (Required)'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Weekly stocktake variance, broken bag write-off'}),
        help_text=_('Mandatory reason for stock balance correction.')
    )


class ManualStockReceiveForm(forms.Form):
    """
    Form for manually recording received stock outside standard purchase flow
    (e.g., supplier bonus items, transfers, return corrections).
    """
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True),
        label=_('Inventory Item Received'),
        widget=forms.Select(attrs=_BS_SELECT),
    )
    quantity = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label=_('Quantity Received'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'step': '0.01', 'placeholder': 'e.g. 10.00'}),
    )
    movement_date = forms.DateTimeField(
        initial=timezone.now,
        label=_('Received Date & Time'),
        widget=forms.DateTimeInput(attrs={**_BS_INPUT, 'type': 'datetime-local'}),
        required=False
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        label=_('Reference / Delivery Note Number'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. DN-8842'}),
    )
    reason = forms.CharField(
        max_length=255,
        required=False,
        label=_('Notes / Details'),
        widget=forms.TextInput(attrs={**_BS_INPUT, 'placeholder': 'e.g. Direct delivery, supplier promotion'}),
    )


# ===========================================================================
# Chicken Processing Forms
# ===========================================================================

class ChickenProcessingForm(forms.ModelForm):
    """
    Header form for Chicken Processing.
    Allows selecting whole chicken item, quantity processed, date, and notes.
    Validates that the quantity does not exceed current whole chicken stock.
    """
    class Meta:
        model = ChickenProcessing
        fields = [
            'whole_chicken_item',
            'whole_chicken_quantity',
            'processing_date',
            'notes',
        ]
        widgets = {
            'whole_chicken_item': forms.Select(attrs=_BS_SELECT),
            'whole_chicken_quantity': forms.NumberInput(attrs={**_BS_INPUT, 'step': '1', 'min': '1', 'placeholder': 'e.g. 10'}),
            'processing_date': forms.DateInput(attrs={**_BS_INPUT, 'type': 'date'}),
            'notes': forms.Textarea(attrs={**_BS_TEXTAREA, 'placeholder': 'e.g. Morning prep: cut 10 birds into portions for lunch braai service.'}),
        }
        labels = {
            'whole_chicken_item': _('Whole Chicken Stock Item'),
            'whole_chicken_quantity': _('Quantity of Whole Chickens to Process'),
            'processing_date': _('Processing Date'),
            'notes': _('Processing Notes (Optional)'),
        }
        help_texts = {
            'whole_chicken_quantity': _('Number of whole birds taken from storage to be cut into portions.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['whole_chicken_item'].queryset = InventoryItem.objects.filter(
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            is_active=True,
        )
        self.fields['processing_date'].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('whole_chicken_item')
        qty = cleaned_data.get('whole_chicken_quantity')

        if item and qty:
            if qty <= 0:
                raise forms.ValidationError({
                    'whole_chicken_quantity': _('Quantity of whole chickens processed must be greater than zero.')
                })
            if qty > item.quantity_on_hand:
                raise forms.ValidationError({
                    'whole_chicken_quantity': _(
                        f"Insufficient stock: cannot process {qty} whole chickens because only "
                        f"{item.quantity_on_hand} birds are currently available in inventory."
                    )
                })

        return cleaned_data


class ProcessingOutputForm(forms.ModelForm):
    """
    Line item form for portions produced during chicken processing.
    """
    class Meta:
        model = ProcessingOutput
        fields = ['inventory_item', 'quantity_produced']
        widgets = {
            'inventory_item': forms.Select(attrs=_BS_SELECT),
            'quantity_produced': forms.NumberInput(attrs={**_BS_INPUT, 'step': '1', 'min': '1', 'placeholder': 'Qty produced'}),
        }
        labels = {
            'inventory_item': _('Portion Type'),
            'quantity_produced': _('Quantity Produced'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inventory_item'].queryset = InventoryItem.objects.filter(
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            is_active=True,
        ).order_by('item_name')


class BaseProcessingOutputFormSet(BaseInlineFormSet):
    """
    FormSet validator ensuring:
    1. At least one portion output is entered.
    2. No duplicate portion items are selected in the same batch.
    """
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        portion_items = set()
        total_valid_outputs = 0

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                item = form.cleaned_data.get('inventory_item')
                qty = form.cleaned_data.get('quantity_produced')

                if item and qty and qty > 0:
                    if item.pk in portion_items:
                        raise forms.ValidationError(
                            _(f"The portion '{item.item_name}' was selected more than once. "
                              "Please combine quantities into a single row.")
                        )
                    portion_items.add(item.pk)
                    total_valid_outputs += 1

        if total_valid_outputs == 0:
            raise forms.ValidationError(
                _("You must enter at least one portion output produced from this processing batch.")
            )


ProcessingOutputFormSet = inlineformset_factory(
    ChickenProcessing,
    ProcessingOutput,
    form=ProcessingOutputForm,
    formset=BaseProcessingOutputFormSet,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
