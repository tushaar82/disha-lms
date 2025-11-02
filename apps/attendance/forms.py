"""
Forms for attendance management.
"""

from django import forms
from django.utils import timezone
from .models import AttendanceRecord
from apps.subjects.models import Assignment, Topic


class AttendanceForm(forms.ModelForm):
    """Form for marking attendance."""
    
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'assignment', 'date', 'in_time', 'out_time', 'topics_covered', 'notes', 'backdated_reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'assignment': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'in_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'out_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'topics_covered': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full', 'size': '5'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'backdated_reason': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        faculty = kwargs.pop('faculty', None)
        super().__init__(*args, **kwargs)
        
        if faculty:
            # Filter assignments to only show those for this faculty
            self.fields['assignment'].queryset = Assignment.objects.filter(
                faculty=faculty,
                is_active=True
            ).select_related('student', 'subject')
            
            # Filter students to only show those assigned to this faculty
            from apps.students.models import Student
            student_ids = faculty.assignments.filter(
                is_active=True
            ).values_list('student_id', flat=True).distinct()
            self.fields['student'].queryset = Student.objects.filter(
                id__in=student_ids,
                deleted_at__isnull=True
            )
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        in_time = cleaned_data.get('in_time')
        out_time = cleaned_data.get('out_time')
        
        # Validate out_time is after in_time
        if in_time and out_time and out_time <= in_time:
            raise forms.ValidationError('Out time must be after in time.')
        
        # Check if backdated and require reason
        if date and date < timezone.now().date():
            backdated_reason = cleaned_data.get('backdated_reason')
            if not backdated_reason:
                raise forms.ValidationError('Backdated reason is required for past dates.')
        
        return cleaned_data
