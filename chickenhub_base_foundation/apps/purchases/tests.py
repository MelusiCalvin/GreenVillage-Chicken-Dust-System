from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.inventory.models import InventoryItem
from apps.purchases.models import Supplier, Purchase, PurchaseItem

User = get_user_model()


class PurchaseModelTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='purchase_tester',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.supplier = Supplier.objects.create(
            supplier_name='Midlands Poultry Farm',
            contact_person='Johan',
            phone_number='0821234567'
        )
        self.item = InventoryItem.objects.create(
            item_name='Live Broiler Chicken',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('0.00'),
            reorder_level=Decimal('10.00')
        )

    def test_purchase_creation_and_item_subtotal(self):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            total_amount=Decimal('500.00'),
            discount=Decimal('50.00'),
            final_amount=Decimal('450.00'),
            recorded_by=self.staff_user
        )
        item = PurchaseItem.objects.create(
            purchase=purchase,
            inventory_item=self.item,
            quantity=Decimal('10.00'),
            unit_price=Decimal('50.00')
        )
        self.assertEqual(item.subtotal, Decimal('500.00'))
        self.assertEqual(purchase.items.count(), 1)
        self.assertEqual(purchase.final_amount, Decimal('450.00'))

    def test_discount_cannot_exceed_total_amount(self):
        purchase = Purchase(
            supplier=self.supplier,
            total_amount=Decimal('100.00'),
            discount=Decimal('150.00'),
            recorded_by=self.staff_user
        )
        with self.assertRaises(ValidationError):
            purchase.clean()
