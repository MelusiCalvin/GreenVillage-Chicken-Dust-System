import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Sale(models.Model):
    """
    Completed sales transaction.
    Covers both in-store walk-in sales (POS) and collected online orders.
    Linking to an order prevents duplicate revenue counting.
    """
    class SaleType(models.TextChoices):
        WALK_IN = 'WALK_IN', _('Walk-in Counter Sale')
        ONLINE_COLLECTION = 'ONLINE_COLLECTION', _('Online Order Collection')

    receipt_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name=_('Receipt / Till Slip Number')
    )
    order = models.OneToOneField(
        'orders.CustomerOrder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sale',
        verbose_name=_('Linked Customer Order'),
        help_text=_('Prevents double-counting by connecting completed collection order directly to sale.')
    )
    sale_type = models.CharField(
        max_length=20,
        choices=SaleType.choices,
        default=SaleType.WALK_IN,
        verbose_name=_('Sale Type')
    )
    sale_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Sale Date & Time')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total Amount (R)')
    )
    payment_method = models.CharField(
        max_length=40,
        blank=True,
        default='',
        verbose_name=_('Payment Method')
    )
    amount_tendered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Amount Tendered (R)')
    )
    change_given = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Change Given (R)')
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_sales',
        verbose_name=_('Cashier / Recorded By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'sales'
        verbose_name = _('Sale Transaction')
        verbose_name_plural = _('Sale Transactions')
        ordering = ['-sale_date']

    def __str__(self):
        return f"Sale #{self.receipt_number} - R {self.total_amount}"

    @property
    def items_count(self):
        """Returns total quantity of meals/products in this sale."""
        return sum(item.quantity for item in self.items.all())

    @property
    def items_summary(self):
        """Returns readable summary of items sold."""
        items = self.items.select_related('product').all()
        if not items:
            return "No items"
        return ", ".join(f"{i.quantity} x {i.product.product_name}" for i in items)

    @classmethod
    def generate_receipt_number(cls):
        """Generates receipt number like REC-261119-A1B2."""
        today_str = timezone.now().strftime('%y%m%d')
        unique_suffix = uuid.uuid4().hex[:4].upper()
        return f"REC-{today_str}-{unique_suffix}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            num = self.generate_receipt_number()
            while Sale.objects.filter(receipt_number=num).exists():
                num = self.generate_receipt_number()
            self.receipt_number = num
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """
    Individual product sold in a sales transaction.
    Preserves exact historical retail price at time of sale.
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Sale Transaction')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items',
        verbose_name=_('Product Sold')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Unit Price Sold (R)'),
        help_text=_('Preserved price at the time of transaction.')
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Subtotal (R)')
    )

    class Meta:
        app_label = 'sales'
        verbose_name = _('Sale Item')
        verbose_name_plural = _('Sale Items')

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} @ R {self.unit_price}"

    def clean(self):
        super().clean()
        self.subtotal = self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
