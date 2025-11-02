"""
Forms for student management.
"""

from django import forms
from .models import Student
from apps.subjects.models import Assignment


class StudentForm(forms.ModelForm):
    """Form for creating/editing students."""
    
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'center', 'enrollment_number', 'enrollment_date', 'status',
            'guardian_name', 'guardian_phone', 'guardian_email',
            'address', 'city', 'state', 'pincode', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'center': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'enrollment_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'guardian_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'state': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'pincode': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }


class AssignmentForm(forms.ModelForm):
    """Form for creating/editing assignments."""
    
    class Meta:
        model = Assignment
        fields = ['student', 'subject', 'faculty', 'start_date', 'end_date', 'is_active']
        widgets = {
            'student': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'subject': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'faculty': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
