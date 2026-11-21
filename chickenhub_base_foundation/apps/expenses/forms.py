from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = (
            'expense_description',
            'expense_category',
            'expense_date',
            'amount',
            'payment_method',
            'receipt_reference',
            'notes',
        )
        widgets = {
            'expense_description': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 255}),
            'expense_category': forms.Select(attrs={'class': 'form-select'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'receipt_reference': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_expense_description(self):
        description = self.cleaned_data['expense_description'].strip()
        if not description:
            raise forms.ValidationError(_('Enter an expense description.'))
        return description

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError(_('Expense amount must be greater than zero.'))
        return amount
