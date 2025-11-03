"""
Forms for authentication and user management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth import authenticate
from .models import User


class LoginForm(forms.Form):
    """Form for user login."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise forms.ValidationError('This account is inactive.')
            cleaned_data['user'] = user
        
        return cleaned_data


class UserCreationForm(BaseUserCreationForm):
    """Form for creating new users."""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'role': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }


class UserChangeForm(BaseUserChangeForm):
    """Form for updating users."""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role', 'is_active')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'role': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }


class CenterManagerCreationForm(forms.Form):
    """Form for master account to create center managers (center heads)."""
    
    # User fields
    email = forms.EmailField(
        label='Email (Username)',
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'manager@example.com',
        })
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Last Name',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Phone Number',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Password',
        }),
        help_text='Minimum 8 characters'
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm Password',
        })
    )
    
    # Center Head specific fields
    center = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
        })
    )
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Employee ID (optional)',
        })
    )
    joining_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'input input-bordered w-full',
            'type': 'date',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.centers.models import Center
        self.fields['center'].queryset = Center.objects.filter(
            deleted_at__isnull=True,
            is_active=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Passwords do not match.')
            if len(password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        # Check if email already exists
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        
        return cleaned_data


class FacultyCreationForm(forms.Form):
    """Form for center heads to create faculty members."""
    
    # User fields
    email = forms.EmailField(
        label='Email (Username)',
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'faculty@example.com',
        })
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Last Name',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Phone Number',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Password',
        }),
        help_text='Minimum 8 characters'
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm Password',
        })
    )
    
    # Faculty specific fields
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Employee ID (optional)',
        })
    )
    joining_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'input input-bordered w-full',
            'type': 'date',
        })
    )
    qualification = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., M.Sc. Mathematics',
        })
    )
    specialization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., Algebra, Calculus',
        })
    )
    experience_years = forms.IntegerField(
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'min': '0',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Passwords do not match.')
            if len(password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        # Check if email already exists
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        
        return cleaned_data
