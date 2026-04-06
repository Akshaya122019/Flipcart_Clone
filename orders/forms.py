from django import forms
from .models import Address, Order


class AddressForm(forms.ModelForm):
    class Meta:
        model  = Address
        fields = [
            'full_name', 'phone', 'line1', 'line2',
            'city', 'state', 'pincode', 'country', 'address_type'
        ]
        widgets = {
            'full_name':    forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Full Name'
            }),
            'phone':        forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '10-digit mobile'
            }),
            'line1':        forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'House No, Building, Street'
            }),
            'line2':        forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Area, Colony (optional)'
            }),
            'city':         forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City'
            }),
            'state':        forms.Select(attrs={'class': 'form-select'}),
            'pincode':      forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '6-digit pincode'
            }),
            'country':      forms.TextInput(attrs={
                'class': 'form-control', 'value': 'India'
            }),
            'address_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and (not phone.isdigit() or len(phone) != 10):
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode and (not pincode.isdigit() or len(pincode) != 6):
            raise forms.ValidationError('Enter a valid 6-digit pincode.')
        return pincode


# Choices for Indian states
INDIA_STATES = [
    ('', 'Select State'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Puducherry', 'Puducherry'),
    ('Chandigarh', 'Chandigarh'),
]


class AddressFormWithStates(AddressForm):
    state = forms.ChoiceField(
        choices=INDIA_STATES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )