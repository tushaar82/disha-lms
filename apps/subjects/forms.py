"""
Forms for subject and topic management.
"""

from django import forms
from .models import Subject, Topic


class SubjectForm(forms.ModelForm):
    """Form for creating/editing subjects (common across all centers)."""
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TopicForm(forms.ModelForm):
    """Form for creating/editing topics."""
    
    class Meta:
        model = Topic
        fields = ['subject', 'name', 'description', 'sequence_number', 'estimated_duration', 'is_active']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sequence_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
