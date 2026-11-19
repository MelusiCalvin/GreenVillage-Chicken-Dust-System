from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class InventoryItem(models.Model):
    """
    Stores all stock and supplies tracked by ChickenHub:
    whole chickens, chicken portions, raw ingredients, and packaging.
    """
    class ItemType(models.TextChoices):
        WHOLE_CHICKEN = 'WHOLE_CHICKEN', _('Whole Chicken')
        CHICKEN_PORTION = 'CHICKEN_PORTION', _('Chicken Portion')
        INGREDIENT = 'INGREDIENT', _('Raw Ingredient / Spice / Meal')
        PACKAGING = 'PACKAGING', _('Packaging & Consumables')
        OTHER = 'OTHER', _('Other Supplies')

    class UnitOfMeasure(models.TextChoices):
        UNIT = 'UNIT', _('Unit / Bird / Piece')
        KG = 'KG', _('Kilogram (kg)')
        G = 'G', _('Gram (g)')
        L = 'L', _('Litre (L)')
        ML = 'ML', _('Millilitre (ml)')
        PACK = 'PACK', _('Pack / Sachet / Bag')

    item_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Item Name'),
        help_text=_('Unique name of the inventory item (e.g. Whole Fresh Chicken, Pap, Salt).')
    )
    item_type = models.CharField(
        max_length=30,
        choices=ItemType.choices,
        default=ItemType.INGREDIENT,
        verbose_name=_('Item Type'),
        help_text=_('Distinguishes raw ingredients, whole birds, portions, and supplies.')
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.UNIT,
        verbose_name=_('Unit of Measure')
    )
    quantity_on_hand = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Quantity on Hand')
    )
    reorder_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Reorder Level'),
        help_text=_('Minimum quantity threshold triggering a low-stock alert.')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Designates whether this item is currently in use or tracked.')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'inventory'
        verbose_name = _('Inventory Item')
        verbose_name_plural = _('Inventory Items')
        ordering = ['item_name']

    def __str__(self):
        return f"{self.item_name} ({self.get_item_type_display()}) - {self.quantity_on_hand} {self.get_unit_of_measure_display()}"

    @property
    def is_low_stock(self):
        """Returns True if current quantity is at or below the reorder threshold."""
        return self.is_active and self.quantity_on_hand <= self.reorder_level


class StockMovement(models.Model):
    """
    Audit log of every stock movement or adjustment.
    Ensures complete traceability of inventory changes over time.
    """
    class MovementType(models.TextChoices):
        RECEIVED = 'RECEIVED', _('Stock Received (Purchase)')
        USED = 'USED', _('Stock Used (Kitchen Prep)')
        SOLD = 'SOLD', _('Stock Sold')
        WASTED = 'WASTED', _('Stock Wasted / Spoiled')
        ADJUSTMENT = 'ADJUSTMENT', _('Stock Adjustment / Audit')
        PROCESSED_IN = 'PROCESSED_IN', _('Chicken Processing Output (+)')
        PROCESSED_OUT = 'PROCESSED_OUT', _('Chicken Processing Input (-)')

    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Inventory Item')
    )
    movement_type = models.CharField(
        max_length=30,
        choices=MovementType.choices,
        verbose_name=_('Movement Type')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Quantity Change'),
        help_text=_('Quantity added or deducted during this movement.')
    )
    movement_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Movement Date & Time')
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Reason / Note'),
        help_text=_('Required explanation for manual adjustments, wastage or shrinkage.')
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Reference Number'),
        help_text=_('Linked invoice number, order reference or batch code.')
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_stock_movements',
        verbose_name=_('Recorded By')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'inventory'
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
        ordering = ['-movement_date', '-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.inventory_item.item_name} ({self.quantity}) on {self.movement_date.strftime('%Y-%m-%d %H:%M')}"


class ChickenProcessing(models.Model):
    """
    Records the division of whole chickens into smaller cuts/portions.
    Transfers whole bird stock into portion stock to avoid double counting.
    """
    processing_date = models.DateField(
        default=timezone.now,
        verbose_name=_('Processing Date')
    )
    whole_chicken_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        limit_choices_to={'item_type': InventoryItem.ItemType.WHOLE_CHICKEN},
        related_name='processing_inputs',
        verbose_name=_('Whole Chicken Stock Item')
    )
    whole_chicken_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Whole Chickens Processed'),
        help_text=_('Number of whole birds cut into portions.')
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chicken_processings',
        verbose_name=_('Recorded By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Processing Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'inventory'
        verbose_name = _('Chicken Processing')
        verbose_name_plural = _('Chicken Processings')
        ordering = ['-processing_date', '-created_at']

    def __str__(self):
        return f"Processing on {self.processing_date}: {self.whole_chicken_quantity} birds"


class ProcessingOutput(models.Model):
    """
    Stores the specific portion items and quantities produced
    from a chicken processing event.
    """
    processing = models.ForeignKey(
        ChickenProcessing,
        on_delete=models.CASCADE,
        related_name='outputs',
        verbose_name=_('Chicken Processing Event')
    )
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        limit_choices_to={'item_type': InventoryItem.ItemType.CHICKEN_PORTION},
        related_name='processing_outputs',
        verbose_name=_('Produced Portion Item')
    )
    quantity_produced = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Quantity Produced'),
        help_text=_('Quantity of this portion type generated from the batch.')
    )

    class Meta:
        app_label = 'inventory'
        verbose_name = _('Processing Output')
        verbose_name_plural = _('Processing Outputs')
        constraints = [
            models.UniqueConstraint(
                fields=['processing', 'inventory_item'],
                name='unique_portion_per_processing'
            )
        ]

    def __str__(self):
        return f"{self.inventory_item.item_name}: {self.quantity_produced}"
