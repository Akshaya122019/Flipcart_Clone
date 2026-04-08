from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password'
        })
    )

    class Meta:
        model  = User
        fields = ['full_name', 'username', 'email', 'phone']  # role removed
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number'
            }),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and (not phone.isdigit() or len(phone) != 10):
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'buyer'   # always buyer on self-registration
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class':       'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autofocus':   True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class':       'form-control form-control-lg',
            'placeholder': 'Your password',
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['full_name', 'username', 'phone', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username':  forms.TextInput(attrs={'class': 'form-control'}),
            'phone':     forms.TextInput(attrs={'class': 'form-control'}),
            'avatar':    forms.FileInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


# ── Admin creates seller/admin ────────────────────────────
class AdminUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Set a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat password'
        })
    )

    ALLOWED_ROLES = (
        ('seller', 'Seller'),
        ('admin',  'Admin'),
    )
    role = forms.ChoiceField(
        choices=ALLOWED_ROLES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model  = User
        fields = ['full_name', 'username', 'email', 'phone', 'role']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile'
            }),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already taken.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if user.role == 'admin':
            user.is_staff      = True
            user.is_superuser  = False  # limited admin
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    ALLOWED_ROLES = (
        ('buyer',  'Buyer'),
        ('seller', 'Seller'),
        ('admin',  'Admin'),
    )
    role = forms.ChoiceField(
        choices=ALLOWED_ROLES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model  = User
        fields = ['full_name', 'username', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':     forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':     forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Sync is_staff with admin role
        user.is_staff = (user.role == 'admin')
        if commit:
            user.save()
        return user