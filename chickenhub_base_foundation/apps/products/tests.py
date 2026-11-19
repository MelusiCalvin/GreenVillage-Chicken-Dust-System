from decimal import Decimal
from django.test import TestCase
from apps.inventory.models import InventoryItem
from apps.products.models import Product, Recipe, RecipeItem


class ProductModelTests(TestCase):
    def setUp(self):
        self.portion = InventoryItem.objects.create(
            item_name='Quarter Chicken Raw Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('50.00'),
            reorder_level=Decimal('10.00')
        )
        self.pap = InventoryItem.objects.create(
            item_name='Maize Meal (Pap)',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('25.00'),
            reorder_level=Decimal('5.00')
        )
        self.product = Product.objects.create(
            product_name='Quarter Chicken Platter with Pap',
            category=Product.Category.BRAAI_MEAL,
            description='Flame-braaied quarter chicken served with traditional pap.',
            selling_price=Decimal('55.00')
        )

    def test_product_recipe_and_recipe_items(self):
        recipe = Recipe.objects.create(
            product=self.product,
            instructions='Braai over medium coals for 25 minutes.'
        )
        r_item1 = RecipeItem.objects.create(
            recipe=recipe,
            inventory_item=self.portion,
            quantity_required=Decimal('1.00')
        )
        r_item2 = RecipeItem.objects.create(
            recipe=recipe,
            inventory_item=self.pap,
            quantity_required=Decimal('0.25')
        )
        self.assertEqual(self.product.recipe, recipe)
        self.assertEqual(recipe.items.count(), 2)
        self.assertEqual(r_item1.quantity_required, Decimal('1.00'))
