import re
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Customer


class GuestOrderForm(forms.ModelForm):
    last_name = forms.CharField(
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
    )

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone_number', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'phone_number': forms.TelInput(attrs={'class': 'form-control', 'autocomplete': 'tel', 'placeholder': '+27 00 000 0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        }

    def clean_phone_number(self):
        phone = re.sub(r'[\s()\-]', '', self.cleaned_data['phone_number'])
        if not re.fullmatch(r'\+?\d{7,15}', phone):
            raise forms.ValidationError(_('Enter a valid phone number using 7 to 15 digits.'))
        return phone
