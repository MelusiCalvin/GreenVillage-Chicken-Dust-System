from django.contrib import admin
from .models import Supplier, Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ('inventory_item', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'contact_person', 'phone_number', 'email', 'is_active')
    search_fields = ('supplier_name', 'contact_person', 'phone_number')
    list_filter = ('is_active',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'purchase_date', 'invoice_number', 'total_amount', 'discount', 'final_amount', 'payment_method', 'recorded_by')
    list_filter = ('payment_method', 'purchase_date')
    search_fields = ('supplier__supplier_name', 'invoice_number')
    date_hierarchy = 'purchase_date'
    inlines = [PurchaseItemInline]
