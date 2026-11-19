from django.contrib import admin
from .models import Product, Recipe, RecipeItem


class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'selling_price', 'is_available', 'created_at')
    list_filter = ('category', 'is_available')
    search_fields = ('product_name', 'description')
    ordering = ('category', 'product_name')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('product', 'date_created', 'updated_at')
    search_fields = ('product__product_name',)
    inlines = [RecipeItemInline]
