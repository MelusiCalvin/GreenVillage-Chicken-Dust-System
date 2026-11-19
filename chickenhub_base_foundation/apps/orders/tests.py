from decimal import Decimal
from django.test import TestCase
from apps.products.models import Product
from apps.orders.models import Customer, CustomerOrder, OrderItem


class OrderModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Thabo',
            last_name='Mokoena',
            phone_number='0719876543',
            email='thabo@example.com'
        )
        self.product = Product.objects.create(
            product_name='Half Chicken Dust Platter',
            category=Product.Category.BRAAI_MEAL,
            selling_price=Decimal('95.00')
        )

    def test_customer_order_reference_generation(self):
        order = CustomerOrder.objects.create(
            customer=self.customer,
            collection_time='13:30',
            total_amount=Decimal('190.00')
        )
        self.assertTrue(order.order_reference.startswith('CH-'))
        self.assertEqual(order.order_status, CustomerOrder.OrderStatus.PENDING)

    def test_order_item_subtotal_calculation(self):
        order = CustomerOrder.objects.create(
            customer=self.customer,
            total_amount=Decimal('190.00')
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('95.00')
        )
        self.assertEqual(item.subtotal, Decimal('190.00'))
        self.assertEqual(order.items.count(), 1)
