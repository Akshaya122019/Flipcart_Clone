from django import forms
from .models import Product, Category, ProductImage, ProductVariant


class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'slug', 'parent', 'image', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated if empty'
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required    = False
        self.fields['parent'].required  = False
        self.fields['image'].required   = False
        # Exclude self from parent choices when editing
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(
                pk=self.instance.pk
            )


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = [
            'name', 'slug', 'category', 'brand',
            'description', 'price', 'discount',
            'stock', 'is_active', 'is_featured'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated if empty'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brand name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Full product description'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
                'max': '100'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        )


class ProductImageForm(forms.ModelForm):
    class Meta:
        model  = ProductImage
        fields = ['image', 'is_primary', 'alt_text']
        widgets = {
            'image':    forms.FileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image description (optional)'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model  = ProductVariant
        fields = ['name', 'value', 'extra_price', 'stock']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Size, Color'
            }),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. XL, Red'
            }),
            'extra_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }