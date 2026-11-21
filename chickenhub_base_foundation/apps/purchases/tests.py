from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from apps.inventory.models import InventoryItem, StockMovement
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
        self.assertEqual(purchase.average_chicken_price, Decimal('50.00'))
        self.assertEqual(purchase.net_average_chicken_price, Decimal('45.00'))

    def test_discount_cannot_exceed_total_amount(self):
        purchase = Purchase(
            supplier=self.supplier,
            total_amount=Decimal('100.00'),
            discount=Decimal('150.00'),
            recorded_by=self.staff_user
        )
        with self.assertRaises(ValidationError):
            purchase.clean()


class SupplierAndPurchasingViewTests(TestCase):
    """
    Tests for:
    - Supplier registration, updating, and viewing
    - Chicken purchasing with automatic average price calculation and stock update
    - Ingredient/supplies purchasing (tomatoes, onions, maize meal, soup sachets) with stock updates
    - Database transactions ensuring atomic stock and purchase creation
    - Role permissions (Owner & Manager access, Employee restriction)
    """
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager_buyer',
            password='Password123!',
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='employee_worker',
            password='Password123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )
        self.supplier = Supplier.objects.create(
            supplier_name='Valley Fresh Farm',
            contact_person='Sipho Zondi',
            phone_number='0711234567',
            email='orders@valleyfresh.co.za',
        )
        self.whole_chicken = InventoryItem.objects.create(
            item_name='Whole Fresh Chicken',
            item_type=InventoryItem.ItemType.WHOLE_CHICKEN,
            unit_of_measure=InventoryItem.UnitOfMeasure.UNIT,
            quantity_on_hand=Decimal('10.00'),
            reorder_level=Decimal('15.00'),
        )
        self.tomatoes = InventoryItem.objects.create(
            item_name='Fresh Tomatoes',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('5.00'),
            reorder_level=Decimal('10.00'),
        )
        self.onions = InventoryItem.objects.create(
            item_name='Fresh Onions',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.KG,
            quantity_on_hand=Decimal('8.00'),
            reorder_level=Decimal('10.00'),
        )
        self.maize = InventoryItem.objects.create(
            item_name='Maize Meal 10kg',
            item_type=InventoryItem.ItemType.INGREDIENT,
            unit_of_measure=InventoryItem.UnitOfMeasure.PACK,
            quantity_on_hand=Decimal('3.00'),
            reorder_level=Decimal('5.00'),
        )

    # -----------------------------------------------------------------------
    # A. Supplier Management Tests
    # -----------------------------------------------------------------------

    def test_supplier_list_and_detail(self):
        self.client.login(username='manager_buyer', password='Password123!')
        response = self.client.get(reverse('purchases:supplier_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Valley Fresh Farm')

        detail_response = self.client.get(reverse('purchases:supplier_detail', args=[self.supplier.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Valley Fresh Farm')
        self.assertContains(detail_response, 'Sipho Zondi')

    def test_supplier_registration(self):
        self.client.login(username='manager_buyer', password='Password123!')
        url = reverse('purchases:supplier_create')
        response = self.client.post(url, {
            'supplier_name': 'Ethekwini Poultry Supplies',
            'contact_person': 'Bongani',
            'phone_number': '0315551234',
            'email': 'bongani@ethekwinipoultry.co.za',
            'address': '12 Market St, Durban',
            'is_active': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Supplier.objects.filter(supplier_name='Ethekwini Poultry Supplies').exists())

    def test_supplier_update(self):
        self.client.login(username='manager_buyer', password='Password123!')
        url = reverse('purchases:supplier_update', args=[self.supplier.pk])
        response = self.client.post(url, {
            'supplier_name': 'Valley Fresh Farm (Updated)',
            'contact_person': 'Sipho Zondi',
            'phone_number': '0799998888',
            'email': 'orders@valleyfresh.co.za',
            'address': 'Farm 42, Camperdown',
            'is_active': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.supplier_name, 'Valley Fresh Farm (Updated)')
        self.assertEqual(self.supplier.phone_number, '0799998888')

    # -----------------------------------------------------------------------
    # B. Chicken Purchasing Tests
    # -----------------------------------------------------------------------

    def test_record_chicken_purchase_and_inventory_update(self):
        """
        Record chicken purchase:
        - 50 birds
        - Total gross price R 2500.00
        - Discount R 100.00
        - Final amount R 2400.00
        - Average price: R 50.00 / bird
        - Net average price: R 48.00 / bird
        - Stock balance increments by 50 (from 10 to 60)
        - Stock movement created atomically
        """
        self.client.login(username='manager_buyer', password='Password123!')
        url = reverse('purchases:chicken_create')
        response = self.client.post(url, {
            'supplier': self.supplier.pk,
            'purchase_date': '2026-11-20',
            'quantity': '50',
            'total_amount': '2500.00',
            'discount': '100.00',
            'payment_method': 'EFT',
            'invoice_number': 'INV-CHICK-101',
            'inventory_item': self.whole_chicken.pk,
            'notes': 'Fresh morning batch, excellent quality.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify purchase created
        purchase = Purchase.objects.get(invoice_number='INV-CHICK-101')
        self.assertEqual(purchase.total_amount, Decimal('2500.00'))
        self.assertEqual(purchase.discount, Decimal('100.00'))
        self.assertEqual(purchase.final_amount, Decimal('2400.00'))
        self.assertEqual(purchase.average_chicken_price, Decimal('50.00'))
        self.assertEqual(purchase.net_average_chicken_price, Decimal('48.00'))
        self.assertEqual(purchase.recorded_by, self.manager)

        # Verify stock updated atomically (was 10.00, added 50.00 -> 60.00)
        self.whole_chicken.refresh_from_db()
        self.assertEqual(self.whole_chicken.quantity_on_hand, Decimal('60.00'))

        # Verify stock movement record created
        movement = StockMovement.objects.get(reference_number=f"PUR-{purchase.id}")
        self.assertEqual(movement.inventory_item, self.whole_chicken)
        self.assertEqual(movement.movement_type, StockMovement.MovementType.RECEIVED)
        self.assertEqual(movement.quantity, Decimal('50.00'))
        self.assertEqual(movement.recorded_by, self.manager)

    def test_chicken_purchase_rejects_discount_exceeding_total(self):
        self.client.login(username='manager_buyer', password='Password123!')
        url = reverse('purchases:chicken_create')
        response = self.client.post(url, {
            'supplier': self.supplier.pk,
            'purchase_date': '2026-11-20',
            'quantity': '10',
            'total_amount': '500.00',
            'discount': '600.00',  # Exceeds total
            'payment_method': 'CASH',
        })
        self.assertEqual(response.status_code, 200)
        # Stock should not change
        self.whole_chicken.refresh_from_db()
        self.assertEqual(self.whole_chicken.quantity_on_hand, Decimal('10.00'))

    # -----------------------------------------------------------------------
    # C. Ingredient and Supplies Purchasing Tests
    # -----------------------------------------------------------------------

    def test_record_supplies_purchase_updates_inventory_for_all_items(self):
        """
        Record purchases of tomatoes, onions, maize meal.
        Captures quantities, unit prices, totals.
        Updates stock for all purchased items.
        """
        self.client.login(username='manager_buyer', password='Password123!')
        url = reverse('purchases:supplies_create')

        # Formset data for 3 items:
        # Tomatoes: 20kg @ R 15/kg = R 300
        # Onions: 15kg @ R 12/kg = R 180
        # Maize meal: 5 packs @ R 90/pack = R 450
        # Gross = R 930, Discount = R 30 -> Net = R 900
        post_data = {
            'supplier': self.supplier.pk,
            'purchase_date': '2026-11-20',
            'invoice_number': 'REC-SUPPLIES-55',
            'payment_method': 'CASH',
            'discount': '30.00',
            'notes': 'Weekly wholesale veggies & maize meal trip',

            'items-TOTAL_FORMS': '3',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',

            # Item 0: Tomatoes
            'items-0-inventory_item': self.tomatoes.pk,
            'items-0-quantity': '20.00',
            'items-0-unit_price': '15.00',

            # Item 1: Onions
            'items-1-inventory_item': self.onions.pk,
            'items-1-quantity': '15.00',
            'items-1-unit_price': '12.00',

            # Item 2: Maize Meal
            'items-2-inventory_item': self.maize.pk,
            'items-2-quantity': '5.00',
            'items-2-unit_price': '90.00',
        }

        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify purchase
        purchase = Purchase.objects.get(invoice_number='REC-SUPPLIES-55')
        self.assertEqual(purchase.total_amount, Decimal('930.00'))
        self.assertEqual(purchase.discount, Decimal('30.00'))
        self.assertEqual(purchase.final_amount, Decimal('900.00'))
        self.assertEqual(purchase.items.count(), 3)

        # Verify stock updates
        # Tomatoes: was 5.00 + 20.00 = 25.00
        self.tomatoes.refresh_from_db()
        self.assertEqual(self.tomatoes.quantity_on_hand, Decimal('25.00'))

        # Onions: was 8.00 + 15.00 = 23.00
        self.onions.refresh_from_db()
        self.assertEqual(self.onions.quantity_on_hand, Decimal('23.00'))

        # Maize: was 3.00 + 5.00 = 8.00
        self.maize.refresh_from_db()
        self.assertEqual(self.maize.quantity_on_hand, Decimal('8.00'))

        # Verify movements
        movements = StockMovement.objects.filter(reference_number=f"PUR-{purchase.id}")
        self.assertEqual(movements.count(), 3)
        for m in movements:
            self.assertEqual(m.movement_type, StockMovement.MovementType.RECEIVED)

    def test_employee_cannot_access_purchases(self):
        """Frontline employee cannot record purchases."""
        self.client.login(username='employee_worker', password='Password123!')
        response = self.client.get(reverse('purchases:chicken_create'))
        self.assertEqual(response.status_code, 302)  # Redirects with warning
