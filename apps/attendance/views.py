"""
Views for attendance management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone

from apps.core.mixins import FacultyRequiredMixin, SetCreatedByMixin, AuditLogMixin
from .models import AttendanceRecord
from .forms import AttendanceForm
from .services import get_today_attendance_for_faculty, get_faculty_attendance_stats


class TodayAttendanceView(LoginRequiredMixin, FacultyRequiredMixin, ListView):
    """
    View to show today's attendance for faculty.
    """
    model = AttendanceRecord
    template_name = 'attendance/today.html'
    context_object_name = 'attendance_records'
    
    def get_queryset(self):
        """Get today's attendance for this faculty."""
        faculty = self.request.user.faculty_profile
        return get_today_attendance_for_faculty(faculty)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.request.user.faculty_profile
        
        # Get today's stats
        today = timezone.now().date()
        stats = get_faculty_attendance_stats(faculty, start_date=today, end_date=today)
        
        context['today'] = today
        context['stats'] = stats
        context['faculty'] = faculty
        
        return context


class MarkAttendanceView(LoginRequiredMixin, FacultyRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """
    View to mark attendance for a student.
    """
    model = AttendanceRecord
    form_class = AttendanceForm
    template_name = 'attendance/mark_form.html'
    success_url = reverse_lazy('attendance:today')
    audit_action = 'CREATE'
    
    def get_form_kwargs(self):
        """Pass faculty to form."""
        kwargs = super().get_form_kwargs()
        kwargs['faculty'] = self.request.user.faculty_profile
        return kwargs
    
    def form_valid(self, form):
        """Set marked_by before saving."""
        form.instance.marked_by = self.request.user
        
        messages.success(
            self.request,
            f'Attendance marked for {form.instance.student.get_full_name()} - {form.instance.duration_minutes} minutes'
        )
        
        return super().form_valid(form)


class AttendanceHistoryView(LoginRequiredMixin, FacultyRequiredMixin, ListView):
    """
    View to show attendance history for faculty.
    """
    model = AttendanceRecord
    template_name = 'attendance/history.html'
    context_object_name = 'attendance_records'
    paginate_by = 20
    
    def get_queryset(self):
        """Get attendance history for this faculty."""
        faculty = self.request.user.faculty_profile
        return AttendanceRecord.objects.filter(
            marked_by=faculty.user
        ).select_related(
            'student', 'assignment__subject'
        ).prefetch_related(
            'topics_covered'
        ).order_by('-date', '-in_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.request.user.faculty_profile
        
        # Get overall stats
        stats = get_faculty_attendance_stats(faculty)
        
        context['stats'] = stats
        context['faculty'] = faculty
        
        return context
