from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views import View
from apps.accounts.decorators import ManagerRequiredMixin, StaffRequiredMixin
from .forms import ExpenseForm
from .models import Expense, ExpenseRevision


class ExpenseListView(StaffRequiredMixin, View):
    template_name = 'expenses/expense_list.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()
        start_raw = request.GET.get('start_date', '').strip()
        end_raw = request.GET.get('end_date', '').strip()

        expenses = Expense.objects.select_related('recorded_by').all()
        if query:
            expenses = expenses.filter(
                Q(expense_description__icontains=query) |
                Q(receipt_reference__icontains=query) |
                Q(notes__icontains=query) |
                Q(payment_method__icontains=query) |
                Q(recorded_by__username__icontains=query) |
                Q(recorded_by__first_name__icontains=query) |
                Q(recorded_by__last_name__icontains=query)
            )
        if category in Expense.ExpenseCategory.values:
            expenses = expenses.filter(expense_category=category)

        start_date = parse_date(start_raw) if start_raw else None
        end_date = parse_date(end_raw) if end_raw else None
        if start_raw and not start_date:
            messages.warning(request, 'Start date is invalid and was not applied.')
        if end_raw and not end_date:
            messages.warning(request, 'End date is invalid and was not applied.')
        if start_date and end_date and start_date > end_date:
            messages.error(request, 'Start date must be on or before end date.')
        else:
            if start_date:
                expenses = expenses.filter(expense_date__gte=start_date)
            if end_date:
                expenses = expenses.filter(expense_date__lte=end_date)

        total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return render(request, self.template_name, {
            'expenses': expenses,
            'query': query,
            'category': category,
            'categories': Expense.ExpenseCategory.choices,
            'start_date': start_raw,
            'end_date': end_raw,
            'expense_count': expenses.count(),
            'total_amount': total,
        })


class ExpenseCreateView(StaffRequiredMixin, View):
    template_name = 'expenses/expense_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ExpenseForm(), 'page_title': 'Record expense'})

    def post(self, request):
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user
            expense.save()
            messages.success(request, 'Expense recorded.')
            return redirect('expenses:detail', pk=expense.pk)
        return render(request, self.template_name, {'form': form, 'page_title': 'Record expense'})


class ExpenseUpdateView(ManagerRequiredMixin, View):
    template_name = 'expenses/expense_form.html'

    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        return render(request, self.template_name, {
            'form': ExpenseForm(instance=expense),
            'page_title': 'Update expense',
            'expense': expense,
        })

    def post(self, request, pk):
        form = ExpenseForm(request.POST, instance=get_object_or_404(Expense, pk=pk))
        if form.is_valid():
            saved = False
            with transaction.atomic():
                expense = Expense.objects.select_for_update().get(pk=pk)
                locked_form = ExpenseForm(request.POST, instance=expense)
                if locked_form.is_valid():
                    ExpenseRevision.objects.create(
                        expense=expense,
                        changed_by=request.user,
                        snapshot={
                            'expense_description': expense.expense_description,
                            'expense_category': expense.expense_category,
                            'expense_category_label': expense.get_expense_category_display(),
                            'expense_date': expense.expense_date.isoformat(),
                            'amount': str(expense.amount),
                            'payment_method': expense.payment_method,
                            'payment_method_label': expense.get_payment_method_display(),
                            'receipt_reference': expense.receipt_reference,
                            'notes': expense.notes,
                            'recorded_by_id': expense.recorded_by_id,
                        },
                    )
                    updated = locked_form.save(commit=False)
                    updated.recorded_by = expense.recorded_by
                    updated.save()
                    saved = True
                else:
                    form = locked_form
            if not saved:
                return render(request, self.template_name, {
                    'form': form,
                    'page_title': 'Update expense',
                    'expense': form.instance,
                })
            messages.success(request, 'Expense updated. The previous values are retained in its history.')
            return redirect('expenses:detail', pk=pk)
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Update expense',
            'expense': form.instance,
        })


class ExpenseDetailView(StaffRequiredMixin, View):
    template_name = 'expenses/expense_detail.html'

    def get(self, request, pk):
        expense = get_object_or_404(
            Expense.objects.select_related('recorded_by').prefetch_related('revisions__changed_by'),
            pk=pk,
        )
        return render(request, self.template_name, {'expense': expense})
