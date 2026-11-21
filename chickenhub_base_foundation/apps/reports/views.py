import calendar
from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.db.models import F, Q, Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from apps.accounts.decorators import StaffRequiredMixin
from apps.expenses.models import Expense
from apps.inventory.models import InventoryItem, StockMovement
from apps.orders.models import CustomerOrder
from apps.purchases.models import Purchase, PurchaseItem
from apps.sales.models import Sale


REPORT_TYPES = (
    ('daily_sales', 'Daily sales'),
    ('weekly_sales', 'Weekly sales'),
    ('monthly_sales', 'Monthly sales'),
    ('purchases', 'All stock purchases'),
    ('chicken_purchases', 'Chicken purchases'),
    ('ingredient_purchases', 'Ingredient and supply purchases'),
    ('expenses', 'Operating expenses'),
    ('inventory', 'Current inventory'),
    ('movements', 'Stock movements'),
    ('orders', 'Customer orders'),
)


class ReportsView(StaffRequiredMixin, View):
    template_name = 'reports/index.html'

    def get(self, request):
        report_type = request.GET.get('type', 'daily_sales')
        if report_type not in dict(REPORT_TYPES):
            report_type = 'daily_sales'
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        start_raw = request.GET.get('date_from', '').strip()
        end_raw = request.GET.get('date_to', '').strip()
        start_date = parse_date(start_raw) if start_raw else None
        end_date = parse_date(end_raw) if end_raw else None
        today = timezone.localdate()

        if start_raw and not start_date:
            messages.warning(request, 'The start date was invalid and has been ignored.')
        if end_raw and not end_date:
            messages.warning(request, 'The end date was invalid and has been ignored.')

        # Sales period shortcuts use date_from as their selected anchor.
        if report_type in {'daily_sales', 'weekly_sales', 'monthly_sales'}:
            anchor = start_date or today
            start_raw = anchor.isoformat()
            if report_type == 'daily_sales':
                start_date = end_date = anchor
            elif report_type == 'weekly_sales':
                start_date = anchor - timedelta(days=anchor.weekday())
                end_date = start_date + timedelta(days=6)
            else:
                start_date = anchor.replace(day=1)
                end_date = anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
            end_raw = end_date.isoformat()

        invalid_range = bool(start_date and end_date and start_date > end_date)
        if invalid_range:
            messages.error(request, 'The start date must be on or before the end date.')

        def apply_dates(qs, field):
            if invalid_range:
                return qs.none()
            is_date_field = field in {'purchase_date', 'expense_date'}
            lookup_field = field if is_date_field else f'{field}__date'
            if start_date:
                qs = qs.filter(**{f'{lookup_field}__gte': start_date})
            if end_date:
                qs = qs.filter(**{f'{lookup_field}__lte': end_date})
            return qs

        # Financial summaries deliberately use each source table once. Online
        # orders are represented in revenue only by their linked Sale records.
        sales_period = Sale.objects.all()
        if invalid_range:
            sales_period = sales_period.none()
        else:
            if start_date:
                sales_period = sales_period.filter(sale_date__date__gte=start_date)
            if end_date:
                sales_period = sales_period.filter(sale_date__date__lte=end_date)
        purchases_period = Purchase.objects.all()
        expenses_period = Expense.objects.all()
        if invalid_range:
            purchases_period = purchases_period.none()
            expenses_period = expenses_period.none()
        else:
            if start_date:
                purchases_period = purchases_period.filter(purchase_date__gte=start_date)
                expenses_period = expenses_period.filter(expense_date__gte=start_date)
            if end_date:
                purchases_period = purchases_period.filter(purchase_date__lte=end_date)
                expenses_period = expenses_period.filter(expense_date__lte=end_date)

        sales_revenue = sales_period.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        stock_purchase_cost = purchases_period.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
        operating_expenses = expenses_period.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        estimated_profit = sales_revenue - operating_expenses

        records = []
        categories = []
        report_label = dict(REPORT_TYPES)[report_type]
        report_total = None
        record_count = 0
        inventory_summary = None

        if report_type.endswith('_sales'):
            records_qs = Sale.objects.select_related('recorded_by', 'order').prefetch_related('items__product')
            records_qs = records_qs.filter(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
            if report_type == 'daily_sales':
                categories = Sale.SaleType.choices
            else:
                categories = Sale.SaleType.choices
            if category in Sale.SaleType.values:
                records_qs = records_qs.filter(sale_type=category)
            if query:
                records_qs = records_qs.filter(
                    Q(receipt_number__icontains=query) |
                    Q(recorded_by__username__icontains=query) |
                    Q(recorded_by__first_name__icontains=query) |
                    Q(items__product__product_name__icontains=query)
                ).distinct()
            report_total = records_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            records = list(records_qs.order_by('-sale_date')[:250])
            record_count = records_qs.count()

        elif report_type in {'purchases', 'chicken_purchases', 'ingredient_purchases'}:
            records_qs = Purchase.objects.select_related('supplier', 'recorded_by').prefetch_related('items__inventory_item')
            records_qs = apply_dates(records_qs, 'purchase_date')
            kinds = {
                'chicken_purchases': [InventoryItem.ItemType.WHOLE_CHICKEN, InventoryItem.ItemType.CHICKEN_PORTION],
                'ingredient_purchases': [InventoryItem.ItemType.INGREDIENT, InventoryItem.ItemType.PACKAGING, InventoryItem.ItemType.OTHER],
            }
            if report_type in kinds:
                matching_purchase_ids = PurchaseItem.objects.filter(
                    inventory_item__item_type__in=kinds[report_type]
                ).values('purchase_id')
                records_qs = records_qs.filter(pk__in=matching_purchase_ids)
            categories = [('chicken', 'Chicken'), ('ingredients', 'Ingredients and supplies')]
            if category in {'chicken', 'ingredients'}:
                item_types = kinds['chicken_purchases' if category == 'chicken' else 'ingredient_purchases']
                records_qs = records_qs.filter(pk__in=PurchaseItem.objects.filter(
                    inventory_item__item_type__in=item_types
                ).values('purchase_id'))
            if query:
                records_qs = records_qs.filter(
                    Q(invoice_number__icontains=query) |
                    Q(supplier__supplier_name__icontains=query) |
                    Q(items__inventory_item__item_name__icontains=query)
                ).distinct()
            report_total = records_qs.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
            records = list(records_qs.order_by('-purchase_date', '-created_at')[:250])
            record_count = records_qs.count()

        elif report_type == 'expenses':
            records_qs = Expense.objects.select_related('recorded_by').all()
            records_qs = apply_dates(records_qs, 'expense_date')
            categories = Expense.ExpenseCategory.choices
            if category in Expense.ExpenseCategory.values:
                records_qs = records_qs.filter(expense_category=category)
            if query:
                records_qs = records_qs.filter(
                    Q(expense_description__icontains=query) |
                    Q(receipt_reference__icontains=query) |
                    Q(notes__icontains=query) |
                    Q(recorded_by__username__icontains=query)
                )
            report_total = records_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            records = list(records_qs[:250])
            record_count = records_qs.count()

        elif report_type == 'inventory':
            records_qs = InventoryItem.objects.all()
            categories = InventoryItem.ItemType.choices
            if category in InventoryItem.ItemType.values:
                records_qs = records_qs.filter(item_type=category)
            if query:
                records_qs = records_qs.filter(item_name__icontains=query)
            inventory_summary = {
                'active_count': InventoryItem.objects.filter(is_active=True).count(),
                'low_stock_count': InventoryItem.objects.filter(
                    is_active=True, quantity_on_hand__lte=F('reorder_level')
                ).count(),
            }
            records = list(records_qs.order_by('item_name')[:500])
            record_count = records_qs.count()

        elif report_type == 'movements':
            records_qs = StockMovement.objects.select_related('inventory_item', 'recorded_by').all()
            records_qs = apply_dates(records_qs, 'movement_date')
            categories = StockMovement.MovementType.choices
            if category in StockMovement.MovementType.values:
                records_qs = records_qs.filter(movement_type=category)
            if query:
                records_qs = records_qs.filter(
                    Q(inventory_item__item_name__icontains=query) |
                    Q(reference_number__icontains=query) |
                    Q(reason__icontains=query) |
                    Q(recorded_by__username__icontains=query)
                )
            records = list(records_qs[:500])
            record_count = records_qs.count()

        elif report_type == 'orders':
            records_qs = CustomerOrder.objects.select_related('customer').prefetch_related('items__product').all()
            records_qs = apply_dates(records_qs, 'order_date')
            categories = CustomerOrder.OrderStatus.choices
            if category in CustomerOrder.OrderStatus.values:
                records_qs = records_qs.filter(order_status=category)
            if query:
                records_qs = records_qs.filter(
                    Q(order_reference__icontains=query) |
                    Q(customer__first_name__icontains=query) |
                    Q(customer__last_name__icontains=query) |
                    Q(customer__phone_number__icontains=query)
                )
            records = list(records_qs[:250])
            record_count = records_qs.count()

        return render(request, self.template_name, {
            'report_types': REPORT_TYPES,
            'report_type': report_type,
            'report_label': report_label,
            'query': query,
            'category': category,
            'categories': categories,
            'date_from': start_raw,
            'date_to': end_raw,
            'records': records,
            'record_count': record_count,
            'report_total': report_total,
            'sales_revenue': sales_revenue,
            'stock_purchase_cost': stock_purchase_cost,
            'operating_expenses': operating_expenses,
            'estimated_profit': estimated_profit,
            'inventory_summary': inventory_summary,
        })
