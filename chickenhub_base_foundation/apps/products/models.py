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

    @property
    def has_recipe(self):
        """Returns True if this product has a configured recipe saved in the database."""
        try:
            return hasattr(self, 'recipe') and self.recipe is not None and self.recipe.pk is not None
        except (AttributeError, models.ObjectDoesNotExist):
            return False

    @property
    def max_producible_servings(self):
        """
        Calculates maximum number of meal servings that can be prepared
        based on current stock levels of all required ingredients.
        Returns None if no recipe is configured.
        """
        if not self.has_recipe:
            return None
        return self.recipe.max_producible_servings


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

    @property
    def max_producible_servings(self):
        """
        Calculates maximum number of meals that can be prepared
        based on current inventory of each ingredient.
        """
        items = self.items.select_related('inventory_item').all()
        if not items:
            return None
        servings_list = []
        for item in items:
            if item.quantity_required > 0:
                servings = int(item.inventory_item.quantity_on_hand // item.quantity_required)
                servings_list.append(servings)
        return min(servings_list) if servings_list else 0

    def calculate_requirements(self, servings_count=1):
        """
        Calculates total stock required for preparing a batch of meals,
        comparing against current stock on hand and identifying any shortages.
        """
        servings = Decimal(str(servings_count))
        result = []
        for item in self.items.select_related('inventory_item').all():
            total_needed = (item.quantity_required * servings).quantize(Decimal('0.01'))
            on_hand = item.inventory_item.quantity_on_hand
            sufficient = on_hand >= total_needed
            shortage = max(Decimal('0.00'), total_needed - on_hand).quantize(Decimal('0.01'))
            result.append({
                'recipe_item': item,
                'inventory_item': item.inventory_item,
                'unit_of_measure': item.inventory_item.get_unit_of_measure_display(),
                'per_serving': item.quantity_required,
                'total_required': total_needed,
                'stock_on_hand': on_hand,
                'sufficient': sufficient,
                'shortage': shortage,
            })
        return result


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
