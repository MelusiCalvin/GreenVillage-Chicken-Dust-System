from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from apps.expenses.models import Expense

User = get_user_model()


class ExpenseModelTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='expense_manager',
            password='Password123!',
            role=User.Role.MANAGER
        )

    def test_expense_creation(self):
        expense = Expense.objects.create(
            expense_description='5 Bags of Hardwood Braai Charcoal',
            expense_category=Expense.ExpenseCategory.WOOD_CHARCOAL,
            expense_date=timezone.now().date(),
            amount=Decimal('450.00'),
            payment_method=Expense.PaymentMethod.CASH,
            receipt_reference='INV-CHAR-001',
            recorded_by=self.staff_user
        )
        self.assertEqual(expense.amount, Decimal('450.00'))
        self.assertEqual(expense.expense_category, Expense.ExpenseCategory.WOOD_CHARCOAL)
        self.assertEqual(expense.recorded_by, self.staff_user)
