from django.contrib import admin
from .models import Customer, CustomerOrder, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('previous_status', 'new_status', 'reason', 'changed_by', 'changed_at')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email', 'date_registered')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')
    ordering = ('-date_registered',)


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('order_reference', 'customer', 'order_status', 'total_amount', 'collection_time', 'order_date')
    list_filter = ('order_status', 'order_date')
    search_fields = ('order_reference', 'customer__first_name', 'customer__last_name', 'customer__phone_number')
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ('order_reference', 'inventory_deducted_at', 'rejection_reason')
