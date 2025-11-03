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
from django.http import JsonResponse

from apps.core.mixins import FacultyRequiredMixin, SetCreatedByMixin, AuditLogMixin
from .models import AttendanceRecord
from .forms import AttendanceForm
from .services import get_today_attendance_for_faculty, get_faculty_attendance_stats
from apps.subjects.models import Topic, Assignment
from apps.students.models import Student


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
        """Set marked_by before saving and handle status."""
        form.instance.marked_by = self.request.user
        
        # Get status from form
        status = form.cleaned_data.get('status', 'present')
        student = form.instance.student
        
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
            # Create notification for center admin
            from apps.core.services import create_notification
            try:
                center_head = student.center.center_heads.first()
                if center_head:
                    create_notification(
                        user=center_head.user,
                        title=f"Student Ready for Transfer: {student.get_full_name()}",
                        message=f"Student {student.get_full_name()} has been marked as ready to transfer by {self.request.user.get_full_name()}.",
                        notification_type='info',
                        action_url=f'/students/{student.id}/'
                    )
            except:
                pass  # Silently fail if no center head
            
            messages.info(
                self.request,
                f'Student {student.get_full_name()} marked as ready to transfer. Center admin has been notified.'
            )
        
        # Count topics covered
        topics_count = form.cleaned_data.get('topics_covered', []).count() if hasattr(form.cleaned_data.get('topics_covered', []), 'count') else len(form.cleaned_data.get('topics_covered', []))
        
        messages.success(
            self.request,
            f'Attendance marked for {student.get_full_name()} - {form.instance.duration_minutes} minutes, {topics_count} topics covered'
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


class GetTopicsBySubjectView(LoginRequiredMixin, FacultyRequiredMixin, View):
    """
    AJAX endpoint to get topics for a given subject (assignment).
    Returns JSON list of topics.
    """
    
    def get(self, request, assignment_id):
        try:
            # Get the assignment
            assignment = get_object_or_404(Assignment, pk=assignment_id)
            
            # Verify faculty has access to this assignment
            if assignment.faculty != request.user.faculty_profile:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Get topics for the subject
            topics = Topic.objects.filter(
                subject=assignment.subject,
                deleted_at__isnull=True
            ).order_by('sequence_number', 'name')
            
            # Format response
            topics_data = [
                {
                    'id': topic.id,
                    'name': topic.name,
                    'sequence_number': topic.sequence_number or 0
                }
                for topic in topics
            ]
            
            return JsonResponse({
                'status': 'success',
                'topics': topics_data,
                'subject_name': assignment.subject.name
            })
            
        except Assignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
