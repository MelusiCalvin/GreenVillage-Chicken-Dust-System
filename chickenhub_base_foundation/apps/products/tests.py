from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import InventoryItem
from apps.products.models import Product, Recipe, RecipeItem

User = get_user_model()


class ProductModelTests(TestCase):
    def setUp(self):
        self.portion = InventoryItem.objects.create(
            item_name='Quarter Chicken Raw Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('10.00'),
            reorder_level=Decimal('10.00'),
        )
        self.pap = InventoryItem.objects.create(
            item_name='Maize Meal (Pap)',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('2.50'),
            reorder_level=Decimal('5.00'),
        )
        self.product = Product.objects.create(
            product_name='Quarter Chicken Platter with Pap',
            category=Product.Category.BRAAI_MEAL,
            description='Flame-braaied quarter chicken served with traditional pap.',
            selling_price=Decimal('55.00'),
            is_available=True,
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

    def test_max_producible_servings_calculation(self):
        """
        Stock:
        10 portions / 1 per serving = 10 servings
        2.50 kg pap / 0.25 per serving = 10 servings
        Max producible = 10
        """
        recipe = Recipe.objects.create(product=self.product)
        RecipeItem.objects.create(recipe=recipe, inventory_item=self.portion, quantity_required=Decimal('1.00'))
        RecipeItem.objects.create(recipe=recipe, inventory_item=self.pap, quantity_required=Decimal('0.25'))

        self.assertEqual(self.product.max_producible_servings, 10)

        # Now reduce portion stock to 4
        self.portion.quantity_on_hand = Decimal('4.00')
        self.portion.save()
        self.assertEqual(self.product.max_producible_servings, 4)

    def test_calculate_requirements_with_shortage(self):
        """
        Calculate stock requirements for 20 meals:
        Needed:
        - 20 portions (Stock: 10) -> Shortage: 10
        - 5.00 kg pap (Stock: 2.50) -> Shortage: 2.50
        """
        recipe = Recipe.objects.create(product=self.product)
        RecipeItem.objects.create(recipe=recipe, inventory_item=self.portion, quantity_required=Decimal('1.00'))
        RecipeItem.objects.create(recipe=recipe, inventory_item=self.pap, quantity_required=Decimal('0.25'))

        reqs = recipe.calculate_requirements(servings_count=20)
        self.assertEqual(len(reqs), 2)

        portion_req = next(r for r in reqs if r['inventory_item'] == self.portion)
        self.assertEqual(portion_req['total_required'], Decimal('20.00'))
        self.assertEqual(portion_req['stock_on_hand'], Decimal('10.00'))
        self.assertFalse(portion_req['sufficient'])
        self.assertEqual(portion_req['shortage'], Decimal('10.00'))

        pap_req = next(r for r in reqs if r['inventory_item'] == self.pap)
        self.assertEqual(pap_req['total_required'], Decimal('5.00'))
        self.assertEqual(pap_req['stock_on_hand'], Decimal('2.50'))
        self.assertFalse(pap_req['sufficient'])
        self.assertEqual(pap_req['shortage'], Decimal('2.50'))


class ProductAndRecipeViewTests(TestCase):
    """
    Tests for product list, creation, update, details, recipe formulation,
    and access control.
    """
    def setUp(self):
        self.manager = User.objects.create_user(
            username='kitchen_manager',
            password='Password123!',
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='waiter_sipho',
            password='Password123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )

        self.portion_full = InventoryItem.objects.create(
            item_name='Whole Braai Chicken Cut',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('15.00'),
            reorder_level=Decimal('5.00'),
        )
        self.portion_half = InventoryItem.objects.create(
            item_name='Half Chicken Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('20.00'),
            reorder_level=Decimal('5.00'),
        )
        self.portion_quarter = InventoryItem.objects.create(
            item_name='Quarter Chicken Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('30.00'),
            reorder_level=Decimal('10.00'),
        )
        self.pap = InventoryItem.objects.create(
            item_name='Maize Meal',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('50.00'),
            reorder_level=Decimal('10.00'),
        )
        self.salsa = InventoryItem.objects.create(
            item_name='Tomato Salsa / Chakalaka',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('10.00'),
            reorder_level=Decimal('2.00'),
        )

        # Products
        self.full_platter = Product.objects.create(
            product_name='Full Chicken Platter',
            category=Product.Category.BRAAI_MEAL,
            description='Whole flame-braaied chicken with double pap and homemade salsa.',
            selling_price=Decimal('165.00'),
            is_available=True,
        )
        self.half_platter = Product.objects.create(
            product_name='Half Chicken Platter',
            category=Product.Category.BRAAI_MEAL,
            description='Half braaied chicken with pap and salsa.',
            selling_price=Decimal('95.00'),
            is_available=True,
        )
        self.quarter_platter = Product.objects.create(
            product_name='Quarter Chicken Platter',
            category=Product.Category.BRAAI_MEAL,
            description='Quarter braaied chicken served with pap and salsa.',
            selling_price=Decimal('55.00'),
            is_available=True,
        )

    # -----------------------------------------------------------------------
    # Product View Tests
    # -----------------------------------------------------------------------

    def test_product_list_view_for_staff(self):
        self.client.login(username='waiter_sipho', password='Password123!')
        response = self.client.get(reverse('products:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full Chicken Platter')
        self.assertContains(response, 'Half Chicken Platter')
        self.assertContains(response, 'Quarter Chicken Platter')
        self.assertContains(response, '165.00')

    def test_product_creation_by_manager(self):
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:create')
        response = self.client.post(url, {
            'product_name': 'Chicken Wings & Chips Combo',
            'category': Product.Category.COMBO,
            'description': '6 crispy braaied wings with potato chips.',
            'selling_price': '75.00',
            'is_available': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(product_name='Chicken Wings & Chips Combo').exists())

    def test_product_creation_rejects_negative_price(self):
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:create')
        response = self.client.post(url, {
            'product_name': 'Invalid Free Platter',
            'category': Product.Category.BRAAI_MEAL,
            'description': 'Test',
            'selling_price': '-10.00',
            'is_available': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(product_name='Invalid Free Platter').exists())

    def test_employee_cannot_create_product(self):
        self.client.login(username='waiter_sipho', password='Password123!')
        response = self.client.get(reverse('products:create'))
        self.assertEqual(response.status_code, 302)  # Redirects unauthorized

    def test_product_update(self):
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:update', args=[self.quarter_platter.pk])
        response = self.client.post(url, {
            'product_name': 'Quarter Chicken Platter (Special)',
            'category': Product.Category.BRAAI_MEAL,
            'description': 'Updated description.',
            'selling_price': '50.00',  # Promo discount
            'is_available': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.quarter_platter.refresh_from_db()
        self.assertEqual(self.quarter_platter.selling_price, Decimal('50.00'))

    def test_product_toggle_availability(self):
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:toggle_availability', args=[self.full_platter.pk])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.full_platter.refresh_from_db()
        self.assertFalse(self.full_platter.is_available)

    # -----------------------------------------------------------------------
    # Recipe Management Tests
    # -----------------------------------------------------------------------

    def test_create_recipe_with_ingredients(self):
        """
        Manager creates a recipe for Quarter Chicken Platter:
        - 1 Quarter chicken cut
        - 0.25 kg Pap
        - 0.10 kg Salsa
        """
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:recipe_edit', args=[self.quarter_platter.pk])

        post_data = {
            'instructions': 'Flame-grill quarter chicken over hot coals for 20 minutes, basting with peri-peri glaze.',

            'items-TOTAL_FORMS': '3',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',

            # Item 0: Quarter chicken
            'items-0-inventory_item': self.portion_quarter.pk,
            'items-0-quantity_required': '1.00',

            # Item 1: Pap
            'items-1-inventory_item': self.pap.pk,
            'items-1-quantity_required': '0.25',

            # Item 2: Salsa
            'items-2-inventory_item': self.salsa.pk,
            'items-2-quantity_required': '0.10',
        }

        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify recipe created
        self.quarter_platter.refresh_from_db()
        self.assertTrue(self.quarter_platter.has_recipe)
        recipe = self.quarter_platter.recipe
        self.assertEqual(recipe.items.count(), 3)
        self.assertIn('Flame-grill', recipe.instructions)

        # Verify max producible:
        # 30 quarters / 1 = 30
        # 50 kg pap / 0.25 = 200
        # 10 kg salsa / 0.10 = 100
        # Lowest is 30
        self.assertEqual(self.quarter_platter.max_producible_servings, 30)

    def test_recipe_rejects_duplicate_ingredient_selection(self):
        """Selecting the same ingredient twice in a recipe must fail validation."""
        self.client.login(username='kitchen_manager', password='Password123!')
        url = reverse('products:recipe_edit', args=[self.half_platter.pk])

        post_data = {
            'instructions': 'Grill half chicken.',

            'items-TOTAL_FORMS': '2',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',

            # Item 0: Pap
            'items-0-inventory_item': self.pap.pk,
            'items-0-quantity_required': '0.20',

            # Item 1: Also Pap (duplicate!)
            'items-1-inventory_item': self.pap.pk,
            'items-1-quantity_required': '0.10',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.half_platter.refresh_from_db()
        self.assertFalse(self.half_platter.has_recipe)

    def test_product_detail_calculator_with_query_param(self):
        """
        Verify that ?servings=20 computes requirements on the detail page.
        """
        self.client.login(username='waiter_sipho', password='Password123!')
        recipe = Recipe.objects.create(
            product=self.quarter_platter,
            instructions='Standard braai.'
        )
        RecipeItem.objects.create(
            recipe=recipe,
            inventory_item=self.portion_quarter,
            quantity_required=Decimal('1.00')
        )

        response = self.client.get(f"{reverse('products:detail', args=[self.quarter_platter.pk])}?servings=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['servings'], 20)
        self.assertEqual(len(response.context['requirements']), 1)
        self.assertEqual(response.context['requirements'][0]['total_required'], Decimal('20.00'))
