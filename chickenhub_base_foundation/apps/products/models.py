from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """
    Stores customer-facing meals and goods offered for sale:
    Full/Half/Quarter Braaied Chicken Platters, Raw Poultry cuts,
    Accompaniments (pap, chakalaka, gravy), and Drinks.
    """
    class Category(models.TextChoices):
        BRAAI_MEAL = 'BRAAI_MEAL', _('Braaied Chicken Meal')
        RAW_POULTRY = 'RAW_POULTRY', _('Fresh / Raw Poultry')
        SIDE_ACCOMPANIMENT = 'SIDE_ACCOMPANIMENT', _('Side & Accompaniment')
        BEVERAGE = 'BEVERAGE', _('Beverage / Drink')
        COMBO = 'COMBO', _('Combo / Platter Special')
        OTHER = 'OTHER', _('Other')

    product_name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name=_('Product Name')
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.BRAAI_MEAL,
        verbose_name=_('Category')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Selling Price (R)'),
        help_text=_('Current standard retail price.')
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Is Available'),
        help_text=_('Toggles visibility and ordering availability on customer menu.')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['category', 'product_name']

    def __str__(self):
        return f"{self.product_name} - R {self.selling_price}"


class Recipe(models.Model):
    """
    Links a sellable product to its raw inventory requirements.
    Enables automatic stock deduction when sales are recorded.
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name=_('Product / Meal')
    )
    instructions = models.TextField(
        blank=True,
        verbose_name=_('Cooking / Preparation Instructions')
    )
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'products'
        verbose_name = _('Recipe')
        verbose_name_plural = _('Recipes')

    def __str__(self):
        return f"Recipe for {self.product.product_name}"


class RecipeItem(models.Model):
    """
    Specifies an inventory ingredient or chicken portion required
    to prepare a single serving of the parent product recipe.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Recipe')
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='recipe_items',
        verbose_name=_('Required Inventory Item')
    )
    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Quantity Required'),
        help_text=_('Quantity consumed per unit of product prepared.')
    )

    class Meta:
        app_label = 'products'
        verbose_name = _('Recipe Item')
        verbose_name_plural = _('Recipe Items')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'inventory_item'],
                name='unique_inventory_item_per_recipe'
            )
        ]

    def __str__(self):
        return f"{self.inventory_item.item_name} ({self.quantity_required} {self.inventory_item.get_unit_of_measure_display()}) for {self.recipe.product.product_name}"
