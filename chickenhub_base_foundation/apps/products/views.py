from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.decorators import ManagerRequiredMixin, StaffRequiredMixin
from apps.inventory.models import InventoryItem
from .forms import (
    ProductForm,
    RecipeForm,
    RecipeItemFormSet,
    StockRequirementCalculatorForm,
)
from .models import Product, Recipe, RecipeItem


# ===========================================================================
# Product & Menu Management Views
# ===========================================================================

class ProductListView(StaffRequiredMixin, View):
    """
    List all products / menu items with categories, prices, recipe status,
    and producible servings based on current inventory.
    """
    template_name = 'products/product_list.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        availability = request.GET.get('status', '').strip()

        products = Product.objects.select_related('recipe').prefetch_related(
            'recipe__items__inventory_item'
        ).all().order_by('category', 'product_name')

        if query:
            products = products.filter(
                Q(product_name__icontains=query) | Q(description__icontains=query)
            )

        if category:
            products = products.filter(category=category)

        if availability == 'available':
            products = products.filter(is_available=True)
        elif availability == 'unavailable':
            products = products.filter(is_available=False)

        context = {
            'products': products,
            'categories': Product.Category.choices,
            'current_category': category,
            'current_status': availability,
            'query': query,
            'total_count': Product.objects.count(),
            'available_count': Product.objects.filter(is_available=True).count(),
        }
        return render(request, self.template_name, context)


class ProductCreateView(ManagerRequiredMixin, View):
    """
    Register a new product or meal.
    """
    template_name = 'products/product_form.html'

    def get(self, request):
        form = ProductForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Product / Meal',
            'submit_label': 'Create Product',
        })

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(
                request,
                f"Product '{product.product_name}' created successfully for R {product.selling_price:.2f}. "
                "You can now configure its ingredient recipe."
            )
            # If user checked 'add recipe', redirect to recipe editor
            if 'save_and_add_recipe' in request.POST:
                return redirect('products:recipe_edit', pk=product.pk)
            return redirect('products:detail', pk=product.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Product / Meal',
            'submit_label': 'Create Product',
        })


class ProductUpdateView(ManagerRequiredMixin, View):
    """
    Update an existing product's name, description, price, or category.
    """
    template_name = 'products/product_form.html'

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=product)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Product — {product.product_name}",
            'submit_label': 'Save Changes',
            'product': product,
        })

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.product_name}' updated successfully.")
            return redirect('products:detail', pk=product.pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': f"Edit Product — {product.product_name}",
            'submit_label': 'Save Changes',
            'product': product,
        })


class ProductDetailView(StaffRequiredMixin, View):
    """
    View product profile, retail price, linked recipe, and integrated
    kitchen stock requirement calculator.
    """
    template_name = 'products/product_detail.html'

    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('recipe').prefetch_related('recipe__items__inventory_item'),
            pk=pk
        )

        # Batch stock requirement calculation (default: 10 servings)
        servings = int(request.GET.get('servings', 10))
        if servings < 1:
            servings = 1

        requirements = []
        is_fully_stocked = True

        if product.has_recipe:
            requirements = product.recipe.calculate_requirements(servings_count=servings)
            is_fully_stocked = all(r['sufficient'] for r in requirements)

        calc_form = StockRequirementCalculatorForm(initial={'servings': servings})

        return render(request, self.template_name, {
            'product': product,
            'calc_form': calc_form,
            'servings': servings,
            'requirements': requirements,
            'is_fully_stocked': is_fully_stocked,
        })


class ProductToggleAvailabilityView(ManagerRequiredMixin, View):
    """
    Fast toggle for product menu availability.
    """
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_available = not product.is_available
        product.save(update_fields=['is_available', 'updated_at'])
        status_text = "available on menu" if product.is_available else "marked unavailable / sold out"
        messages.success(request, f"Product '{product.product_name}' is now {status_text}.")
        return redirect('products:detail', pk=pk)


# ===========================================================================
# Recipe Management Views
# ===========================================================================

class RecipeEditView(ManagerRequiredMixin, View):
    """
    Create or edit the recipe for a product:
    - Preparation / cooking instructions
    - Ingredients and required quantities per serving
    - Validates against inventory items and enforces positive quantities
    """
    template_name = 'products/recipe_form.html'

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            recipe = product.recipe
        except Recipe.DoesNotExist:
            recipe = Recipe(product=product)

        recipe_form = RecipeForm(instance=recipe)
        formset = RecipeItemFormSet(instance=recipe)
        inventory_items = InventoryItem.objects.filter(is_active=True).order_by('item_type', 'item_name')

        return render(request, self.template_name, {
            'product': product,
            'recipe': recipe,
            'recipe_form': recipe_form,
            'formset': formset,
            'inventory_items': inventory_items,
        })

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            recipe = product.recipe
        except Recipe.DoesNotExist:
            recipe = Recipe(product=product)

        recipe_form = RecipeForm(request.POST, instance=recipe)
        formset = RecipeItemFormSet(request.POST, instance=recipe)

        if recipe_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                saved_recipe = recipe_form.save(commit=False)
                saved_recipe.product = product
                saved_recipe.save()
                formset.instance = saved_recipe
                formset.save()

            messages.success(
                request,
                f"Recipe for '{product.product_name}' saved successfully with {saved_recipe.items.count()} ingredients."
            )
            return redirect('products:detail', pk=product.pk)

        messages.error(request, "Please correct the errors in the recipe form.")
        inventory_items = InventoryItem.objects.filter(is_active=True).order_by('item_type', 'item_name')
        return render(request, self.template_name, {
            'product': product,
            'recipe': recipe,
            'recipe_form': recipe_form,
            'formset': formset,
            'inventory_items': inventory_items,
        })


class RecipeDetailView(StaffRequiredMixin, View):
    """
    Dedicated view for recipe specifications, ingredient proportions, and cooking notes.
    """
    template_name = 'products/recipe_detail.html'

    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('recipe').prefetch_related('recipe__items__inventory_item'),
            pk=pk
        )
        if not product.has_recipe:
            messages.info(request, f"No recipe has been created for '{product.product_name}' yet.")
            return redirect('products:recipe_edit', pk=product.pk)

        recipe = product.recipe
        requirements_single = recipe.calculate_requirements(servings_count=1)

        return render(request, self.template_name, {
            'product': product,
            'recipe': recipe,
            'requirements': requirements_single,
        })
