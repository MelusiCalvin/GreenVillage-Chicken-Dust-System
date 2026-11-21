from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import InventoryItem
from .models import Product, Recipe, RecipeItem

_BS_INPUT = {'class': 'form-control'}
_BS_SELECT = {'class': 'form-select'}
_BS_TEXTAREA = {'class': 'form-control', 'rows': 3}


class ProductForm(forms.ModelForm):
    """
    Form for creating and editing Products/Meals.
    Supports Full Chicken, Half Chicken, Quarter Chicken platters and other meals.
    """
    class Meta:
        model = Product
        fields = [
            'product_name',
            'category',
            'description',
            'selling_price',
            'is_available',
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={
                **_BS_INPUT,
                'placeholder': 'e.g. Quarter Chicken Platter, Full Braai Feast, Pap & Relish'
            }),
            'category': forms.Select(attrs=_BS_SELECT),
            'description': forms.Textarea(attrs={
                **_BS_TEXTAREA,
                'placeholder': 'Describe meal contents, cooking style (flame-braaied), accompaniments...'
            }),
            'selling_price': forms.NumberInput(attrs={
                **_BS_INPUT,
                'step': '0.01',
                'min': '0',
                'placeholder': 'e.g. 65.00'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'product_name': _('Product / Meal Name'),
            'category': _('Menu Category'),
            'description': _('Description'),
            'selling_price': _('Selling Price (R)'),
            'is_available': _('Available on Menu'),
        }
        help_texts = {
            'selling_price': _('Retail selling price charged to customers.'),
            'is_available': _('Uncheck to temporarily hide or mark this item sold out on customer menus.'),
        }

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price < 0:
            raise forms.ValidationError(_('Selling price cannot be negative.'))
        return price


class RecipeForm(forms.ModelForm):
    """
    Header form for Recipe preparation instructions.
    """
    class Meta:
        model = Recipe
        fields = ['instructions']
        widgets = {
            'instructions': forms.Textarea(attrs={
                **_BS_TEXTAREA,
                'rows': 4,
                'placeholder': 'Step-by-step preparation and braai instructions for the kitchen staff...'
            }),
        }
        labels = {
            'instructions': _('Preparation & Cooking Instructions'),
        }


class RecipeItemForm(forms.ModelForm):
    """
    Line item form specifying an ingredient/portion required per serving of a meal.
    """
    class Meta:
        model = RecipeItem
        fields = ['inventory_item', 'quantity_required']
        widgets = {
            'inventory_item': forms.Select(attrs=_BS_SELECT),
            'quantity_required': forms.NumberInput(attrs={
                **_BS_INPUT,
                'step': '0.001',
                'min': '0.001',
                'placeholder': 'e.g. 1.00 or 0.250'
            }),
        }
        labels = {
            'inventory_item': _('Inventory Item / Ingredient'),
            'quantity_required': _('Quantity Required (per serving)'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inventory_item'].queryset = InventoryItem.objects.filter(
            is_active=True
        ).order_by('item_type', 'item_name')

    def clean_quantity_required(self):
        qty = self.cleaned_data.get('quantity_required')
        if qty is not None and qty <= 0:
            raise forms.ValidationError(_('Quantity required must be greater than zero.'))
        return qty


class BaseRecipeItemFormSet(BaseInlineFormSet):
    """
    FormSet validator ensuring:
    1. At least one ingredient is specified in the recipe.
    2. No duplicate ingredients in the same recipe.
    3. Validates positive quantity requirements.
    """
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        used_items = set()
        total_valid = 0

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                item = form.cleaned_data.get('inventory_item')
                qty = form.cleaned_data.get('quantity_required')

                if item and qty:
                    if item.pk in used_items:
                        raise forms.ValidationError(
                            _(f"The ingredient '{item.item_name}' was selected more than once in this recipe. "
                              "Please combine the quantities into a single row.")
                        )
                    used_items.add(item.pk)
                    total_valid += 1

        if total_valid == 0:
            raise forms.ValidationError(
                _("A recipe must include at least one required inventory ingredient or portion.")
            )


RecipeItemFormSet = inlineformset_factory(
    Recipe,
    RecipeItem,
    form=RecipeItemForm,
    formset=BaseRecipeItemFormSet,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class StockRequirementCalculatorForm(forms.Form):
    """
    Kitchen calculator to compute inventory requirements for preparing a batch of meals.
    """
    servings = forms.IntegerField(
        min_value=1,
        initial=10,
        label=_('Number of Meal Servings to Prepare'),
        widget=forms.NumberInput(attrs={**_BS_INPUT, 'min': '1', 'step': '1'}),
        help_text=_('Enter planned batch quantity to check total stock requirements and ingredient shortages.')
    )
