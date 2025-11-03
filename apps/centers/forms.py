"""
Forms for center management.
"""

from django import forms
from .models import Center, CenterHead


class CenterForm(forms.ModelForm):
    """Form for creating and updating centers."""
    
    class Meta:
        model = Center
        fields = ['name', 'code', 'address', 'city', 'state', 'pincode', 'phone', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter center name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MUM001'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pincode'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_code(self):
        """Ensure center code is unique."""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            # Check if code exists (excluding current instance if updating)
            queryset = Center.objects.filter(code=code, deleted_at__isnull=True)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('A center with this code already exists.')
        return code


class CenterHeadAssignmentForm(forms.ModelForm):
    """Form for assigning center heads to centers."""
    
    class Meta:
        model = CenterHead
        fields = ['user', 'center', 'employee_id', 'joining_date', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'center': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter employee ID'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only show center_head role
        from apps.accounts.models import User
        self.fields['user'].queryset = User.objects.filter(
            role='center_head',
            is_active=True
        )
        # Filter centers to only show active centers
        self.fields['center'].queryset = Center.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        )
