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
