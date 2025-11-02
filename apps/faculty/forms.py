"""
Forms for faculty management.
"""

from django import forms
from .models import Faculty


class FacultyForm(forms.ModelForm):
    """Form for creating/editing faculty members."""
    
    class Meta:
        model = Faculty
        fields = [
            'user', 'center', 'employee_id', 'joining_date',
            'specialization', 'qualification', 'experience_years',
            'is_active'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'center': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'employee_id': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'joining_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'specialization': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'qualification': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'experience_years': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only show those with faculty role
        self.fields['user'].queryset = self.fields['user'].queryset.filter(role='faculty')
