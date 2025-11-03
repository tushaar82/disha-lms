"""
Forms for attendance management.
"""

from django import forms
from django.utils import timezone
from datetime import time
from .models import AttendanceRecord
from apps.subjects.models import Assignment, Topic


def generate_time_choices():
    """Generate 12-hour format time choices from 6:00 AM to 10:00 PM in 30-minute intervals."""
    choices = []
    for hour in range(6, 22):  # 6 AM to 10 PM
        for minute in [0, 30]:
            time_obj = time(hour, minute)
            # Convert to 12-hour format
            hour_12 = hour if hour <= 12 else hour - 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            am_pm = 'AM' if hour < 12 else 'PM'
            label = f"{hour_12:02d}:{minute:02d} {am_pm}"
            choices.append((time_obj.strftime('%H:%M'), label))
    return choices


class AttendanceForm(forms.ModelForm):
    """Form for marking attendance with 12-hour time format."""
    
    # Override time fields with Select widgets
    in_time = forms.ChoiceField(
        choices=generate_time_choices(),
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        help_text='Select session start time'
    )
    out_time = forms.ChoiceField(
        choices=generate_time_choices(),
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        help_text='Select session end time'
    )
    
    # Add status field
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('complete', 'Complete'),
        ('ready_to_transfer', 'Ready to Transfer'),
    ]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial='present',
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        help_text='Mark student status'
    )
    
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'assignment', 'date', 'in_time', 'out_time', 'topics_covered', 'notes', 'backdated_reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'assignment': forms.Select(attrs={'class': 'select select-bordered w-full', 'id': 'id_assignment'}),
            'date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'topics_covered': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full', 'size': '5', 'id': 'id_topics_covered'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'maxlength': '500', 'id': 'id_notes'}),
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
        in_time_str = cleaned_data.get('in_time')
        out_time_str = cleaned_data.get('out_time')
        
        # Convert time strings to time objects for validation
        if in_time_str and out_time_str:
            from datetime import datetime
            in_time = datetime.strptime(in_time_str, '%H:%M').time()
            out_time = datetime.strptime(out_time_str, '%H:%M').time()
            
            # Validate out_time is after in_time
            if out_time <= in_time:
                raise forms.ValidationError('Out time must be after in time.')
            
            # Store as time objects
            cleaned_data['in_time'] = in_time
            cleaned_data['out_time'] = out_time
        
        # Check if backdated and require reason
        if date and date < timezone.now().date():
            backdated_reason = cleaned_data.get('backdated_reason')
            if not backdated_reason:
                raise forms.ValidationError('Backdated reason is required for past dates.')
        
        return cleaned_data
