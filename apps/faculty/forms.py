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
            'user': forms.Select(attrs={'class': 'form-select'}),
            'center': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only show those with faculty role
        self.fields['user'].queryset = self.fields['user'].queryset.filter(role='faculty')
