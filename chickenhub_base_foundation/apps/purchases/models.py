from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Supplier(models.Model):
    """
    Stores vendor details for chicken suppliers, wholesalers,
    and ingredient/consumable merchants.
    """
    supplier_name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_('Supplier Name')
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Contact Person')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email Address')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Physical Address')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'purchases'
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['supplier_name']

    def __str__(self):
        return self.supplier_name


class Purchase(models.Model):
    """
    Header record of a purchase transaction with a supplier.
    Captures overall cost, discount, payment method, and creator.
    """
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Cash')
        CARD = 'CARD', _('Card')
        EFT = 'EFT', _('EFT / Bank Transfer')
        CREDIT = 'CREDIT', _('Supplier Account / Credit')
        OTHER = 'OTHER', _('Other')

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name=_('Supplier')
    )
    purchase_date = models.DateField(
        default=timezone.now,
        verbose_name=_('Purchase Date')
    )
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Invoice / Receipt Number'),
        help_text=_('Supplier invoice or till slip reference.')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total Amount (Gross)')
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Discount Received')
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Final Amount (Net Paid)')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name=_('Payment Method')
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_purchases',
        verbose_name=_('Recorded By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'purchases'
        verbose_name = _('Purchase')
        verbose_name_plural = _('Purchases')
        ordering = ['-purchase_date', '-created_at']

    def __str__(self):
        return f"Purchase #{self.id} - {self.supplier.supplier_name} on {self.purchase_date} (R {self.final_amount})"

    def clean(self):
        super().clean()
        if self.discount > self.total_amount:
            raise ValidationError({'discount': _('Discount cannot exceed the total purchase amount.')})
        self.final_amount = self.total_amount - self.discount

    def calculate_totals(self):
        """Calculates total_amount and final_amount from child items."""
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.final_amount = max(Decimal('0.00'), total - self.discount)

    @property
    def total_chickens_purchased(self):
        """Returns total quantity of whole chickens in this purchase."""
        chicken_items = self.items.filter(
            inventory_item__item_type='WHOLE_CHICKEN'
        )
        return sum(item.quantity for item in chicken_items)

    @property
    def average_chicken_price(self):
        """
        Calculates average price per chicken before discount:
        total chicken subtotal / quantity.
        """
        qty = self.total_chickens_purchased
        if qty and qty > 0:
            chicken_subtotal = sum(
                item.subtotal for item in self.items.filter(inventory_item__item_type='WHOLE_CHICKEN')
            )
            return (chicken_subtotal / qty).quantize(Decimal('0.01'))
        return None

    @property
    def net_average_chicken_price(self):
        """
        Calculates effective net price per chicken after discount.
        Handles discounts proportionally:
        (chicken_subtotal * (final_amount / total_amount)) / quantity.
        """
        qty = self.total_chickens_purchased
        if qty and qty > 0:
            chicken_subtotal = sum(
                item.subtotal for item in self.items.filter(inventory_item__item_type='WHOLE_CHICKEN')
            )
            if self.total_amount > 0:
                effective_share = self.final_amount / self.total_amount
                net_chicken_total = chicken_subtotal * effective_share
            else:
                net_chicken_total = chicken_subtotal
            return (net_chicken_total / qty).quantize(Decimal('0.01'))
        return None


class PurchaseItem(models.Model):
    """
    Line item for each product or supply acquired in a purchase.
    Preserves historical purchase prices for average cost calculation.
    """
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Purchase Transaction')
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name=_('Inventory Item')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Quantity Purchased')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Unit Price (Paid)'),
        help_text=_('Historical price paid per unit at the time of purchase.')
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Subtotal')
    )

    class Meta:
        app_label = 'purchases'
        verbose_name = _('Purchase Item')
        verbose_name_plural = _('Purchase Items')

    def __str__(self):
        return f"{self.inventory_item.item_name} x {self.quantity} @ R {self.unit_price}"

    def clean(self):
        super().clean()
        self.subtotal = self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
