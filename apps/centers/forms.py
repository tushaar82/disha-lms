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
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter center name'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g., MUM001'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'placeholder': 'Enter street address'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter state'}),
            'pincode': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter pincode'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter email address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
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
            'user': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'center': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'employee_id': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter employee ID'}),
            'joining_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
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
