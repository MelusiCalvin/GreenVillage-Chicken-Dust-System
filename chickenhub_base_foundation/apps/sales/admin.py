from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'sale_type', 'total_amount', 'payment_method', 'order', 'recorded_by', 'sale_date')
    list_filter = ('sale_type', 'payment_method', 'sale_date')
    search_fields = ('receipt_number', 'order__order_reference', 'recorded_by__username')
    date_hierarchy = 'sale_date'
    inlines = [SaleItemInline]
