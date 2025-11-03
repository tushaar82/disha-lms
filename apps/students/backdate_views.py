"""
Admin-only views for backdating attendance and admission dates.
Only Center Heads (Admins) can access these views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime

from apps.core.mixins import CenterHeadRequiredMixin, AuditLogMixin
from apps.students.models import Student
from apps.attendance.models import AttendanceRecord
from apps.subjects.models import Assignment
from django import forms


class BackdateAdmissionForm(forms.ModelForm):
    """Form to backdate student enrollment date."""
    
    class Meta:
        model = Student
        fields = ['enrollment_date']
        widgets = {
            'enrollment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full'
            })
        }
        labels = {
            'enrollment_date': 'Enrollment Date'
        }
        help_texts = {
            'enrollment_date': 'Set the backdated enrollment date for this student'
        }


class BackdateAttendanceForm(forms.ModelForm):
    """Form to create backdated attendance record."""
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(deleted_at__isnull=True),
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label='Student'
    )
    
    assignment = forms.ModelChoiceField(
        queryset=Assignment.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label='Subject Assignment',
        help_text='Select the subject and faculty assignment'
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input input-bordered w-full'
        }),
        label='Attendance Date',
        help_text='Backdated attendance date'
    )
    
    in_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'input input-bordered w-full'
        }),
        label='In Time'
    )
    
    out_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'input input-bordered w-full'
        }),
        label='Out Time'
    )
    
    topics_covered = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Enter topics covered (comma-separated)'
        }),
        required=False,
        label='Topics Covered',
        help_text='Enter topic names separated by commas'
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 2,
            'placeholder': 'Optional notes about this backdated session'
        }),
        required=False,
        label='Notes'
    )
    
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'assignment', 'date', 'in_time', 'out_time', 'notes']


class BackdateAdmissionView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, UpdateView):
    """
    Admin-only view to backdate student admission date.
    Only Center Heads can access this.
    """
    model = Student
    form_class = BackdateAdmissionForm
    template_name = 'students/backdate_admission.html'
    audit_action = 'BACKDATE_ADMISSION'
    
    def get_queryset(self):
        # Center heads can only backdate for their center
        return Student.objects.filter(
            center=self.request.user.center_head_profile.center,
            deleted_at__isnull=True
        )
    
    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        old_date = self.object.enrollment_date
        new_date = form.cleaned_data['enrollment_date']
        
        messages.success(
            self.request,
            f'Enrollment date updated from {old_date} to {new_date} for {self.object.get_full_name()}'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backdate Admission'
        context['student'] = self.object
        return context


class BackdateAttendanceView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, FormView):
    """
    Admin-only view to create backdated attendance records.
    Only Center Heads can access this.
    Uses the enhanced attendance form with typeahead and auto-filtering.
    """
    template_name = 'attendance/mark_form_enhanced.html'
    success_url = reverse_lazy('students:backdate-attendance')
    audit_action = 'BACKDATE_ATTENDANCE'
    
    def get_form_class(self):
        # Use the enhanced attendance form
        from apps.attendance.forms import AttendanceForm
        return AttendanceForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass a special flag to indicate this is backdate mode
        kwargs['is_backdate'] = True
        kwargs['center'] = self.request.user.center_head_profile.center
        return kwargs
    
    def form_valid(self, form):
        # Set marked_by before saving
        form.instance.marked_by = self.request.user
        
        # Set created_by and modified_by (required for TimeStampedModel)
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        
        # Get status from form
        status = form.cleaned_data.get('status', 'present')
        student = form.instance.student
        
        # Add BACKDATED prefix to notes
        backdated_reason = form.cleaned_data.get('backdated_reason', '')
        original_notes = form.cleaned_data.get('notes', '')
        form.instance.notes = f"[BACKDATED by {self.request.user.get_full_name()}] Reason: {backdated_reason}. {original_notes}"
        
        # Handle Complete status
        if status == 'complete':
            student.status = 'completed'
            student.save()
            messages.success(
                self.request,
                f'Student {student.get_full_name()} marked as COMPLETED!'
            )
        
        # Handle Ready to Transfer status
        elif status == 'ready_to_transfer':
            from apps.core.services import create_notification
            try:
                center_head = student.center.center_heads.first()
                if center_head and center_head.user != self.request.user:
                    create_notification(
                        user=center_head.user,
                        title=f"Student Ready for Transfer: {student.get_full_name()}",
                        message=f"Student {student.get_full_name()} has been marked as ready to transfer (backdated).",
                        notification_type='info',
                        action_url=f'/students/{student.id}/'
                    )
            except:
                pass
            
            messages.info(
                self.request,
                f'Student {student.get_full_name()} marked as ready to transfer.'
            )
        
        # Count topics covered
        topics_count = form.cleaned_data.get('topics_covered', []).count() if hasattr(form.cleaned_data.get('topics_covered', []), 'count') else len(form.cleaned_data.get('topics_covered', []))
        
        messages.success(
            self.request,
            f'Backdated attendance created for {student.get_full_name()} on {form.instance.date} - {form.instance.duration_minutes} minutes, {topics_count} topics covered'
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backdate Attendance'
        context['is_backdate_mode'] = True
        context['page_description'] = 'Create backdated attendance records for any student in your center'
        
        # Get recent backdated records
        center = self.request.user.center_head_profile.center
        context['recent_backdated'] = AttendanceRecord.objects.filter(
            student__center=center,
            notes__icontains='BACKDATED'
        ).select_related('student', 'assignment__subject', 'marked_by').order_by('-date')[:10]
        
        return context
