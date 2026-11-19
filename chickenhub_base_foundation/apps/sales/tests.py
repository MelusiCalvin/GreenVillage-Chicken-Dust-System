from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.products.models import Product
from apps.orders.models import Customer, CustomerOrder
from apps.sales.models import Sale, SaleItem

User = get_user_model()


class SaleModelTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='cashier_sipho',
            password='Password123!',
            role=User.Role.EMPLOYEE
        )
        self.product = Product.objects.create(
            product_name='Full Chicken Dust Feast',
            category=Product.Category.BRAAI_MEAL,
            selling_price=Decimal('180.00')
        )
        self.customer = Customer.objects.create(
            first_name='Zanele',
            phone_number='0834567890'
        )

    def test_walk_in_sale_creation(self):
        sale = Sale.objects.create(
            total_amount=Decimal('180.00'),
            payment_method=Sale.PaymentMethod.CASH,
            amount_tendered=Decimal('200.00'),
            change_given=Decimal('20.00'),
            recorded_by=self.staff_user
        )
        self.assertTrue(sale.receipt_number.startswith('REC-'))
        item = SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=1,
            unit_price=Decimal('180.00')
        )
        self.assertEqual(item.subtotal, Decimal('180.00'))
        self.assertIsNone(sale.order)

    def test_sale_linked_to_online_order(self):
        order = CustomerOrder.objects.create(
            customer=self.customer,
            total_amount=Decimal('180.00'),
            order_status=CustomerOrder.OrderStatus.COLLECTED
        )
        sale = Sale.objects.create(
            order=order,
            sale_type=Sale.SaleType.ONLINE_COLLECTION,
            total_amount=Decimal('180.00'),
            payment_method=Sale.PaymentMethod.CARD,
            recorded_by=self.staff_user
        )
        self.assertEqual(sale.order, order)
        self.assertEqual(order.sale, sale)
