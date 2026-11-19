from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
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
