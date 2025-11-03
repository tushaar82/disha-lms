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
        is_backdate = kwargs.pop('is_backdate', False)
        center = kwargs.pop('center', None)
        super().__init__(*args, **kwargs)
        
        # Store faculty and center for later use in clean()
        self.faculty = faculty
        self.center = center
        self.is_backdate = is_backdate
        
        # Populate assignment queryset with ALL possible assignments for validation
        # The AJAX will filter the display, but we need all for server-side validation
        if is_backdate and center:
            # Backdate mode: all assignments in the center
            self.fields['assignment'].queryset = Assignment.objects.filter(
                student__center=center,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('student', 'subject', 'faculty')
        elif faculty:
            # Regular mode: only faculty's assignments
            self.fields['assignment'].queryset = Assignment.objects.filter(
                faculty=faculty,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('student', 'subject')
        else:
            # Fallback to empty
            self.fields['assignment'].queryset = Assignment.objects.none()
        
        if is_backdate and center:
            # BACKDATE MODE: Show ALL students from center (no filtering by today's attendance)
            from apps.students.models import Student
            self.fields['student'].queryset = Student.objects.filter(
                center=center,
                deleted_at__isnull=True
            ).order_by('first_name', 'last_name')
            
            # Update help text
            self.fields['student'].help_text = 'All students from your center'
            
            # Make backdated_reason required for backdate mode
            self.fields['backdated_reason'].required = True
            self.fields['backdated_reason'].help_text = 'Required: Reason for backdating this attendance'
            
        elif faculty:
            # REGULAR MODE: Filter students assigned to faculty and exclude today's attendance
            from apps.students.models import Student
            today = timezone.now().date()
            
            # Get students who already have attendance today
            students_with_attendance_today = AttendanceRecord.objects.filter(
                marked_by=faculty.user,
                date=today
            ).values_list('student_id', flat=True).distinct()
            
            student_ids = faculty.assignments.filter(
                is_active=True
            ).values_list('student_id', flat=True).distinct()
            
            self.fields['student'].queryset = Student.objects.filter(
                id__in=student_ids,
                deleted_at__isnull=True
            ).exclude(
                id__in=students_with_attendance_today
            ).order_by('first_name', 'last_name')
            
            # Update help text to inform about filtering
            self.fields['student'].help_text = 'Students who already have attendance today are hidden'
        
        # Set default date to today (unless in backdate mode)
        if not self.instance.pk and not is_backdate:
            self.fields['date'].initial = timezone.now().date()
    
    def clean_assignment(self):
        """Validate assignment and repopulate queryset if needed."""
        assignment_id = self.data.get('assignment')
        print(f"🔍 clean_assignment called with ID: {assignment_id}")
        print(f"   Faculty: {self.faculty}")
        print(f"   Is backdate: {self.is_backdate}")
        print(f"   Center: {self.center}")
        
        if assignment_id:
            try:
                # Repopulate queryset to include the selected assignment
                if self.is_backdate and self.center:
                    # Backdate mode: any assignment in the center
                    print(f"   Looking for assignment in backdate mode...")
                    assignment = Assignment.objects.get(
                        id=assignment_id,
                        student__center=self.center,
                        is_active=True,
                        deleted_at__isnull=True
                    )
                elif self.faculty:
                    # Regular mode: only faculty's assignments
                    print(f"   Looking for assignment in regular mode...")
                    assignment = Assignment.objects.get(
                        id=assignment_id,
                        faculty=self.faculty,
                        is_active=True,
                        deleted_at__isnull=True
                    )
                else:
                    print(f"   ❌ No faculty or center!")
                    raise forms.ValidationError('Invalid assignment')
                
                print(f"   ✅ Found assignment: {assignment}")
                return assignment
            except Assignment.DoesNotExist:
                print(f"   ❌ Assignment not found in database")
                raise forms.ValidationError('Invalid assignment selected')
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise
        
        print(f"   ⚠️ No assignment ID provided")
        return None
    
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
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Calculate duration in minutes
        if instance.in_time and instance.out_time:
            from datetime import datetime, timedelta
            in_datetime = datetime.combine(instance.date, instance.in_time)
            out_datetime = datetime.combine(instance.date, instance.out_time)
            duration = out_datetime - in_datetime
            instance.duration_minutes = int(duration.total_seconds() / 60)
        else:
            # Default to 0 if times are missing
            instance.duration_minutes = 0
        
        # Set is_backdated flag
        if instance.date < timezone.now().date():
            instance.is_backdated = True
        else:
            instance.is_backdated = False
        
        # IMPORTANT: Don't save here if commit=True
        # Let the view's SetCreatedByMixin set created_by/modified_by first
        # The view will call instance.save() after setting those fields
        if commit:
            # Only save if created_by and modified_by are already set
            if hasattr(instance, 'created_by') and instance.created_by:
                try:
                    instance.save()
                    # Save many-to-many relationships
                    self.save_m2m()
                    print(f"✅ Attendance saved: ID={instance.id}, Student={instance.student}, Duration={instance.duration_minutes}min")
                except Exception as e:
                    print(f"❌ Error saving attendance: {e}")
                    raise
            # else: Let the view handle saving after setting created_by
        
        return instance
