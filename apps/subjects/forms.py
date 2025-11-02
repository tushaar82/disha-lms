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
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }


class TopicForm(forms.ModelForm):
    """Form for creating/editing topics."""
    
    class Meta:
        model = Topic
        fields = ['subject', 'name', 'description', 'sequence_number', 'estimated_duration', 'is_active']
        widgets = {
            'subject': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'sequence_number': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
