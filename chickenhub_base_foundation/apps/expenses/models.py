from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Expense(models.Model):
    """
    Stores non-stock operational expenses incurred by the business
    (e.g. braai charcoal, fuel/transport, electricity, stall fees, maintenance).
    Recorded separately from inventory purchases for accurate gross vs net profit reporting.
    """
    class ExpenseCategory(models.TextChoices):
        WOOD_CHARCOAL = 'WOOD_CHARCOAL', _('Braai Wood & Charcoal')
        TRANSPORT = 'TRANSPORT', _('Transport / Fuel / Delivery')
        UTILITIES = 'UTILITIES', _('Electricity, Gas & Water')
        MAINTENANCE = 'MAINTENANCE', _('Equipment Repairs & Maintenance')
        RENT_STALL = 'RENT_STALL', _('Rent & Stall Fees')
        CLEANING_HYGIENE = 'CLEANING_HYGIENE', _('Cleaning & Hygiene Supplies')
        MARKETING = 'MARKETING', _('Marketing, Banners & Airtime')
        STAFF_WAGES = 'STAFF_WAGES', _('Casual Labor & Staff Allowances')
        MISCELLANEOUS = 'MISCELLANEOUS', _('Miscellaneous / Other')

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Cash')
        CARD = 'CARD', _('Card')
        EFT = 'EFT', _('EFT / Bank Transfer')
        OTHER = 'OTHER', _('Other')

    expense_description = models.CharField(
        max_length=255,
        verbose_name=_('Description'),
        help_text=_('Brief description of the expense (e.g. 2 Bags of Charcoal, Transport to Market).')
    )
    expense_category = models.CharField(
        max_length=30,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.WOOD_CHARCOAL,
        verbose_name=_('Category')
    )
    expense_date = models.DateField(
        default=timezone.now,
        verbose_name=_('Expense Date')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Amount Paid (R)')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name=_('Payment Method')
    )
    receipt_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Receipt / Voucher Reference'),
        help_text=_('Receipt number or till slip reference.')
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_expenses',
        verbose_name=_('Recorded By')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Additional Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'expenses'
        verbose_name = _('Business Expense')
        verbose_name_plural = _('Business Expenses')
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.expense_description} - R {self.amount} ({self.get_expense_category_display()}) on {self.expense_date}"
