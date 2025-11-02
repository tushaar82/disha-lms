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
    """
    form_class = BackdateAttendanceForm
    template_name = 'students/backdate_attendance.html'
    success_url = reverse_lazy('students:backdate-attendance')
    audit_action = 'BACKDATE_ATTENDANCE'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter students and assignments for current center
        center = self.request.user.center_head_profile.center
        form.fields['student'].queryset = Student.objects.filter(
            center=center,
            deleted_at__isnull=True
        ).order_by('user__first_name')
        form.fields['assignment'].queryset = Assignment.objects.filter(
            student__center=center,
            is_active=True
        ).select_related('student', 'subject', 'faculty').order_by('student__user__first_name')
        return form
    
    def form_valid(self, form):
        # Create backdated attendance record
        student = form.cleaned_data['student']
        assignment = form.cleaned_data['assignment']
        date = form.cleaned_data['date']
        in_time = form.cleaned_data['in_time']
        out_time = form.cleaned_data['out_time']
        notes = form.cleaned_data.get('notes', '')
        topics_text = form.cleaned_data.get('topics_covered', '')
        
        # Calculate duration
        in_datetime = datetime.combine(date, in_time)
        out_datetime = datetime.combine(date, out_time)
        duration_minutes = int((out_datetime - in_datetime).total_seconds() / 60)
        
        # Create attendance record
        attendance = AttendanceRecord.objects.create(
            student=student,
            assignment=assignment,
            date=date,
            in_time=in_time,
            out_time=out_time,
            duration_minutes=duration_minutes,
            marked_by=self.request.user,
            notes=f"[BACKDATED by {self.request.user.get_full_name()}] {notes}"
        )
        
        # Add topics if provided
        if topics_text:
            from apps.subjects.models import Topic
            topic_names = [name.strip() for name in topics_text.split(',') if name.strip()]
            for topic_name in topic_names:
                topic, created = Topic.objects.get_or_create(
                    subject=assignment.subject,
                    name=topic_name
                )
                attendance.topics_covered.add(topic)
        
        messages.success(
            self.request,
            f'Backdated attendance created for {student.get_full_name()} on {date}'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backdate Attendance'
        
        # Get recent backdated records
        center = self.request.user.center_head_profile.center
        context['recent_backdated'] = AttendanceRecord.objects.filter(
            student__center=center,
            notes__icontains='BACKDATED'
        ).select_related('student', 'assignment__subject', 'marked_by').order_by('-date')[:10]
        
        return context
