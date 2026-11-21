from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.inventory.models import InventoryItem, StockMovement, ChickenProcessing, ProcessingOutput

User = get_user_model()


class InventoryModelTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='inventory_tester',
            password='Password123!',
            role=User.Role.MANAGER
        )
        self.whole_chicken = InventoryItem.objects.create(
            item_name='Fresh Whole Chicken',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('50.00'),
            reorder_level=Decimal('10.00'),
        )
        self.portion_quarter = InventoryItem.objects.create(
            item_name='Quarter Chicken Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('5.00'),
            reorder_level=Decimal('15.00'),
        )

    def test_low_stock_property(self):
        self.assertFalse(self.whole_chicken.is_low_stock)
        self.assertTrue(self.portion_quarter.is_low_stock)

    def test_stock_movement_creation(self):
        movement = StockMovement.objects.create(
            inventory_item=self.whole_chicken,
            movement_type=StockMovement.MovementType.RECEIVED,
            quantity=Decimal('20.00'),
            reason='Weekly supplier batch delivery',
            recorded_by=self.staff_user
        )
        self.assertEqual(movement.inventory_item, self.whole_chicken)
        self.assertEqual(movement.quantity, Decimal('20.00'))

    def test_chicken_processing_and_output(self):
        processing = ChickenProcessing.objects.create(
            whole_chicken_item=self.whole_chicken,
            whole_chicken_quantity=Decimal('10.00'),
            recorded_by=self.staff_user,
            notes='Morning prep for braai stand'
        )
        output = ProcessingOutput.objects.create(
            processing=processing,
            inventory_item=self.portion_quarter,
            quantity_produced=Decimal('40.00')
        )
        self.assertEqual(processing.outputs.count(), 1)
        self.assertEqual(output.quantity_produced, Decimal('40.00'))


class InventoryViewTests(TestCase):
    """
    Tests for Inventory views:
    - Displaying current stock levels
    - Low-stock warnings
    - Recording stock used
    - Recording wastage
    - Authorised stock adjustments
    - Complete stock movement audit history
    - Permission checks across Employee, Manager, Owner
    """
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_user',
            password='Password123!',
            role=User.Role.OWNER,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username='manager_user',
            password='Password123!',
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='employee_user',
            password='Password123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )

        self.chicken = InventoryItem.objects.create(
            item_name='Whole Fresh Chicken',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('30.00'),
            reorder_level=Decimal('10.00'),
        )
        self.tomatoes = InventoryItem.objects.create(
            item_name='Fresh Tomatoes',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('4.00'),  # Low stock (reorder = 5.00)
            reorder_level=Decimal('5.00'),
        )
        self.maize = InventoryItem.objects.create(
            item_name='Maize Meal 10kg',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.PACK,
            quantity_on_hand=Decimal('15.00'),
            reorder_level=Decimal('5.00'),
        )

    def test_inventory_dashboard_displays_stock_and_low_stock_warning(self):
        self.client.login(username='employee_user', password='Password123!')
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Whole Fresh Chicken')
        self.assertContains(response, 'Fresh Tomatoes')
        self.assertContains(response, 'Low Stock Alert')
        self.assertIn(self.tomatoes, response.context['low_stock_list'])
        self.assertNotIn(self.chicken, response.context['low_stock_list'])

    def test_record_stock_used_decrements_inventory(self):
        """Frontline employee records usage during cooking."""
        self.client.login(username='employee_user', password='Password123!')
        url = reverse('inventory:record_used')
        response = self.client.post(url, {
            'inventory_item': self.chicken.pk,
            'quantity': '10.00',
            'reason': 'Lunch braai preparation',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        self.chicken.refresh_from_db()
        self.assertEqual(self.chicken.quantity_on_hand, Decimal('20.00'))

        # Check movement record
        movement = StockMovement.objects.filter(
            inventory_item=self.chicken,
            movement_type=StockMovement.MovementType.USED
        ).latest('created_at')
        self.assertEqual(movement.quantity, Decimal('-10.00'))
        self.assertEqual(movement.recorded_by, self.employee)

    def test_record_stock_used_rejects_exceeding_stock(self):
        """Cannot use more stock than is on hand."""
        self.client.login(username='employee_user', password='Password123!')
        url = reverse('inventory:record_used')
        response = self.client.post(url, {
            'inventory_item': self.tomatoes.pk,
            'quantity': '10.00',  # Only 4.00 on hand
            'reason': 'Excessive usage attempt',
        })
        self.assertEqual(response.status_code, 200)
        self.tomatoes.refresh_from_db()
        self.assertEqual(self.tomatoes.quantity_on_hand, Decimal('4.00'))  # Unchanged

    def test_record_stock_wastage_by_manager(self):
        """Manager records burned / spoiled stock with explanation."""
        self.client.login(username='manager_user', password='Password123!')
        url = reverse('inventory:record_wasted')
        response = self.client.post(url, {
            'inventory_item': self.chicken.pk,
            'quantity': '2.00',
            'reason': 'Burned on braai grill during flame flare-up',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        self.chicken.refresh_from_db()
        self.assertEqual(self.chicken.quantity_on_hand, Decimal('28.00'))

        movement = StockMovement.objects.filter(
            inventory_item=self.chicken,
            movement_type=StockMovement.MovementType.WASTED
        ).latest('created_at')
        self.assertEqual(movement.quantity, Decimal('-2.00'))
        self.assertEqual(movement.recorded_by, self.manager)

    def test_record_stock_adjustment_updates_balance_and_records_delta(self):
        """Stocktake recount: updates balance and calculates audit delta."""
        self.client.login(username='manager_user', password='Password123!')
        url = reverse('inventory:record_adjustment')
        # Tomatoes was 4.00, physical recount finds 6.00 (+2.00 difference)
        response = self.client.post(url, {
            'inventory_item': self.tomatoes.pk,
            'new_counted_quantity': '6.00',
            'reason': 'Weekly Friday afternoon stocktake recount',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        self.tomatoes.refresh_from_db()
        self.assertEqual(self.tomatoes.quantity_on_hand, Decimal('6.00'))

        movement = StockMovement.objects.filter(
            inventory_item=self.tomatoes,
            movement_type=StockMovement.MovementType.ADJUSTMENT
        ).latest('created_at')
        self.assertEqual(movement.quantity, Decimal('2.00'))
        self.assertIn('Weekly Friday afternoon stocktake recount', movement.reason)

    def test_employee_cannot_access_adjustment_view(self):
        """Employee role should be redirected when trying to adjust stock."""
        self.client.login(username='employee_user', password='Password123!')
        response = self.client.get(reverse('inventory:record_adjustment'))
        self.assertEqual(response.status_code, 302)  # Redirects unauthorized

    def test_stock_movement_audit_log_view(self):
        """All staff can review traceable stock movement history."""
        self.client.login(username='employee_user', password='Password123!')
        StockMovement.objects.create(
            inventory_item=self.maize,
            movement_type=StockMovement.MovementType.USED,
            quantity=Decimal('-3.00'),
            reason='Lunch prep batch pap',
            reference_number='KITCHEN-PREP',
            recorded_by=self.employee,
        )
        response = self.client.get(reverse('inventory:movement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lunch prep batch pap')
        self.assertContains(response, 'Maize Meal 10kg')
