from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_description', 'expense_category', 'amount', 'payment_method', 'expense_date', 'receipt_reference', 'recorded_by')
    list_filter = ('expense_category', 'payment_method', 'expense_date')
    search_fields = ('expense_description', 'receipt_reference', 'recorded_by__username')
    date_hierarchy = 'expense_date'
