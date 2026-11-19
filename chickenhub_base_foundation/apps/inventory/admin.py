from django.contrib import admin
from .models import InventoryItem, StockMovement, ChickenProcessing, ProcessingOutput


class ProcessingOutputInline(admin.TabularInline):
    model = ProcessingOutput
    extra = 1


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_type', 'quantity_on_hand', 'unit_of_measure', 'reorder_level', 'is_low_stock', 'is_active')
    list_filter = ('item_type', 'is_active')
    search_fields = ('item_name',)
    ordering = ('item_name',)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'movement_type', 'quantity', 'movement_date', 'reference_number', 'recorded_by')
    list_filter = ('movement_type', 'movement_date')
    search_fields = ('inventory_item__item_name', 'reference_number', 'reason')
    date_hierarchy = 'movement_date'


@admin.register(ChickenProcessing)
class ChickenProcessingAdmin(admin.ModelAdmin):
    list_display = ('processing_date', 'whole_chicken_item', 'whole_chicken_quantity', 'recorded_by', 'created_at')
    list_filter = ('processing_date',)
    inlines = [ProcessingOutputInline]
