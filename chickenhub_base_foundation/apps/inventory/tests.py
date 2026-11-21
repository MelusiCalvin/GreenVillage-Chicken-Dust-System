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


class ChickenProcessingViewTests(TestCase):
    """
    Tests for Chicken Processing:
    - Select whole chicken item and enter quantity
    - Record processing date and actual portion outputs
    - Check sufficient whole chicken stock is available
    - Deduct whole chicken stock and increase portions stock
    - Record StockMovement for both reduction (PROCESSED_OUT) and additions (PROCESSED_IN)
    - Preserve processing history and details
    - Prevent negative stock quantities
    - Ensure database transaction rollback if invalid
    - Enforce business rule: user enters actual outputs, not assumed fixed yields
    """
    def setUp(self):
        self.manager = User.objects.create_user(
            username='chef_manager',
            password='Password123!',
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='kitchen_employee',
            password='Password123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )

        self.whole_chicken = InventoryItem.objects.create(
            item_name='Fresh Whole Chicken',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('25.00'),
            reorder_level=Decimal('10.00'),
        )
        self.portion_half = InventoryItem.objects.create(
            item_name='Half Chicken Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('0.00'),
            reorder_level=Decimal('5.00'),
        )
        self.portion_quarter = InventoryItem.objects.create(
            item_name='Quarter Chicken Cut',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('4.00'),
            reorder_level=Decimal('10.00'),
        )
        self.portion_wings = InventoryItem.objects.create(
            item_name='Chicken Wings Pack',
            item_type=InventoryItem.ItemType.CHICKEN_PORTION,
            unit_of_measure=InventoryItem.UnitOfMeasure.PACK,
            quantity_on_hand=Decimal('2.00'),
            reorder_level=Decimal('5.00'),
        )

    def test_chicken_processing_success_and_atomic_stock_updates(self):
        """
        Process 10 whole chickens into:
        - 10 Half Chicken Cuts
        - 15 Quarter Chicken Cuts
        - 5 Chicken Wings Packs
        Verifies:
        - Whole chicken reduced: 25.00 - 10.00 = 15.00
        - Portion stocks increased accordingly
        - PROCESSED_OUT and PROCESSED_IN movements logged with matching PROC reference
        """
        self.client.login(username='chef_manager', password='Password123!')
        url = reverse('inventory:processing_create')

        post_data = {
            'whole_chicken_item': self.whole_chicken.pk,
            'whole_chicken_quantity': '10',
            'processing_date': '2026-11-21',
            'notes': 'Morning butchery batch: cut 10 birds into halves, quarters and wings.',

            'outputs-TOTAL_FORMS': '3',
            'outputs-INITIAL_FORMS': '0',
            'outputs-MIN_NUM_FORMS': '1',
            'outputs-MAX_NUM_FORMS': '1000',

            # Output 0: Half chicken
            'outputs-0-inventory_item': self.portion_half.pk,
            'outputs-0-quantity_produced': '10',

            # Output 1: Quarter chicken
            'outputs-1-inventory_item': self.portion_quarter.pk,
            'outputs-1-quantity_produced': '15',

            # Output 2: Wings
            'outputs-2-inventory_item': self.portion_wings.pk,
            'outputs-2-quantity_produced': '5',
        }

        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # 1. Verify ChickenProcessing record created
        processing = ChickenProcessing.objects.latest('created_at')
        self.assertEqual(processing.whole_chicken_item, self.whole_chicken)
        self.assertEqual(processing.whole_chicken_quantity, Decimal('10.00'))
        self.assertEqual(processing.recorded_by, self.manager)
        self.assertEqual(processing.outputs.count(), 3)
        self.assertEqual(processing.total_portions_produced, Decimal('30.00'))

        # 2. Verify whole chicken stock deduction
        self.whole_chicken.refresh_from_db()
        self.assertEqual(self.whole_chicken.quantity_on_hand, Decimal('15.00'))

        # 3. Verify portions stock additions
        self.portion_half.refresh_from_db()
        self.assertEqual(self.portion_half.quantity_on_hand, Decimal('10.00'))  # was 0 + 10

        self.portion_quarter.refresh_from_db()
        self.assertEqual(self.portion_quarter.quantity_on_hand, Decimal('19.00'))  # was 4 + 15

        self.portion_wings.refresh_from_db()
        self.assertEqual(self.portion_wings.quantity_on_hand, Decimal('7.00'))  # was 2 + 5

        # 4. Verify Stock Movements
        # Reduction movement
        out_movement = StockMovement.objects.get(
            inventory_item=self.whole_chicken,
            movement_type=StockMovement.MovementType.PROCESSED_OUT
        )
        self.assertEqual(out_movement.quantity, Decimal('-10.00'))
        self.assertEqual(out_movement.reference_number, f"PROC-{processing.id}")

        # Additions movements
        in_movements = StockMovement.objects.filter(
            movement_type=StockMovement.MovementType.PROCESSED_IN,
            reference_number=f"PROC-{processing.id}"
        )
        self.assertEqual(in_movements.count(), 3)

    def test_processing_fails_when_insufficient_whole_chicken_stock(self):
        """
        Attempting to process more birds than available must be rejected and prevent negative stock.
        """
        self.client.login(username='kitchen_employee', password='Password123!')
        url = reverse('inventory:processing_create')

        # Stock is 25.00, user attempts to process 30.00 birds
        post_data = {
            'whole_chicken_item': self.whole_chicken.pk,
            'whole_chicken_quantity': '30',
            'processing_date': '2026-11-21',
            'notes': 'Over-capacity processing attempt',

            'outputs-TOTAL_FORMS': '1',
            'outputs-INITIAL_FORMS': '0',
            'outputs-MIN_NUM_FORMS': '1',
            'outputs-MAX_NUM_FORMS': '1000',

            'outputs-0-inventory_item': self.portion_half.pk,
            'outputs-0-quantity_produced': '60',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

        # Stock should NOT have changed
        self.whole_chicken.refresh_from_db()
        self.assertEqual(self.whole_chicken.quantity_on_hand, Decimal('25.00'))
        self.portion_half.refresh_from_db()
        self.assertEqual(self.portion_half.quantity_on_hand, Decimal('0.00'))

        # No processing record created
        self.assertFalse(ChickenProcessing.objects.filter(notes='Over-capacity processing attempt').exists())

    def test_processing_rejects_duplicate_portion_selection(self):
        """
        Selecting the same portion item in multiple rows should raise a validation error.
        """
        self.client.login(username='chef_manager', password='Password123!')
        url = reverse('inventory:processing_create')

        post_data = {
            'whole_chicken_item': self.whole_chicken.pk,
            'whole_chicken_quantity': '5',
            'processing_date': '2026-11-21',

            'outputs-TOTAL_FORMS': '2',
            'outputs-INITIAL_FORMS': '0',
            'outputs-MIN_NUM_FORMS': '1',
            'outputs-MAX_NUM_FORMS': '1000',

            # Row 0: Half chicken
            'outputs-0-inventory_item': self.portion_half.pk,
            'outputs-0-quantity_produced': '5',

            # Row 1: Also Half chicken (duplicate)
            'outputs-1-inventory_item': self.portion_half.pk,
            'outputs-1-quantity_produced': '5',
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.whole_chicken.refresh_from_db()
        self.assertEqual(self.whole_chicken.quantity_on_hand, Decimal('25.00'))  # Unchanged

    def test_processing_history_and_detail_views(self):
        """
        Verify that processing history and detail views render correctly with batch outputs.
        """
        self.client.login(username='chef_manager', password='Password123!')

        processing = ChickenProcessing.objects.create(
            whole_chicken_item=self.whole_chicken,
            whole_chicken_quantity=Decimal('8.00'),
            recorded_by=self.manager,
            notes='Friday evening prep'
        )
        ProcessingOutput.objects.create(
            processing=processing,
            inventory_item=self.portion_half,
            quantity_produced=Decimal('16.00')
        )

        # List view
        list_response = self.client.get(reverse('inventory:processing_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Friday evening prep')
        self.assertContains(list_response, '8')

        # Detail view
        detail_response = self.client.get(reverse('inventory:processing_detail', args=[processing.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'PROC-')
        self.assertContains(detail_response, 'Half Chicken Cut')
        self.assertContains(detail_response, '16')
