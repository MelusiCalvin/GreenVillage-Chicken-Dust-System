import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    """
    Stores contact information for customers placing online orders.
    Customers order without needing a permanent user account or password.
    """
    first_name = models.CharField(
        max_length=60,
        verbose_name=_('First Name')
    )
    last_name = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('Last Name')
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number'),
        help_text=_('Contact number used to verify and notify customer for collection.')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email Address')
    )
    date_registered = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date Registered')
    )

    class Meta:
        app_label = 'orders'
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-date_registered']

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name} ({self.phone_number})"


class CustomerOrder(models.Model):
    """
    Customer online order submitted for advance preparation and collection.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        PREPARING = 'PREPARING', _('Preparing')
        READY = 'READY', _('Ready for Collection')
        COLLECTED = 'COLLECTED', _('Collected')
        CANCELLED = 'CANCELLED', _('Cancelled')

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Customer')
    )
    order_reference = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name=_('Order Reference')
    )
    order_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Order Placed At')
    )
    collection_time = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('Requested Collection Time'),
        help_text=_('Customer chosen pickup time window.')
    )
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name=_('Order Status')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total Amount')
    )
    special_instructions = models.TextField(
        blank=True,
        verbose_name=_('Special Instructions / Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'orders'
        verbose_name = _('Customer Order')
        verbose_name_plural = _('Customer Orders')
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.order_reference} - {self.customer.first_name} ({self.get_order_status_display()})"

    @classmethod
    def generate_reference(cls):
        """Generates a unique reference code like CH-261119-A1B2."""
        today_str = timezone.now().strftime('%y%m%d')
        unique_suffix = uuid.uuid4().hex[:4].upper()
        return f"CH-{today_str}-{unique_suffix}"

    def save(self, *args, **kwargs):
        if not self.order_reference:
            ref = self.generate_reference()
            while CustomerOrder.objects.filter(order_reference=ref).exists():
                ref = self.generate_reference()
            self.order_reference = ref
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Individual meal line item within an online customer order.
    Preserves historical product price at time of order submission.
    """
    order = models.ForeignKey(
        CustomerOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Ordered Product')
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
        verbose_name=_('Unit Price (R)'),
        help_text=_('Unit price captured at time of ordering.')
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Subtotal (R)')
    )

    class Meta:
        app_label = 'orders'
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} (R {self.subtotal})"

    def clean(self):
        super().clean()
        self.subtotal = self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
