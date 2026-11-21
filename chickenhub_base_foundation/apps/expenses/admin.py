from django.contrib import admin
from .models import Expense, ExpenseRevision


class ExpenseRevisionInline(admin.TabularInline):
    model = ExpenseRevision
    extra = 0
    can_delete = False
    readonly_fields = ('snapshot', 'changed_by', 'changed_at')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_description', 'expense_category', 'amount', 'payment_method', 'expense_date', 'receipt_reference', 'recorded_by')
    list_filter = ('expense_category', 'payment_method', 'expense_date')
    search_fields = ('expense_description', 'receipt_reference', 'recorded_by__username')
    date_hierarchy = 'expense_date'
    inlines = [ExpenseRevisionInline]
    readonly_fields = (
        'expense_description', 'expense_category', 'expense_date', 'amount',
        'payment_method', 'receipt_reference', 'recorded_by', 'notes',
        'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
