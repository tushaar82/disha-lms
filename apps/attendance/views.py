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
    View to mark attendance for a student with enhanced typeahead search.
    """
    model = AttendanceRecord
    form_class = AttendanceForm
    template_name = 'attendance/mark_form_enhanced.html'
    success_url = reverse_lazy('attendance:today')
    audit_action = 'CREATE'
    
    def get_form_kwargs(self):
        """Pass faculty to form."""
        kwargs = super().get_form_kwargs()
        kwargs['faculty'] = self.request.user.faculty_profile
        return kwargs
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        print("=" * 50)
        print("❌ FORM INVALID")
        print(f"Errors: {form.errors}")
        print(f"Non-field errors: {form.non_field_errors()}")
        print("=" * 50)
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """Set marked_by and audit fields before saving and handle status."""
        print("=" * 50)
        print("FORM VALID CALLED")
        print(f"User: {self.request.user}")
        print(f"Student: {form.instance.student}")
        print(f"Assignment: {form.instance.assignment}")
        print(f"Date: {form.instance.date}")
        print(f"In Time: {form.instance.in_time}")
        print(f"Out Time: {form.instance.out_time}")
        print("=" * 50)
        
        # Set marked_by before saving
        form.instance.marked_by = self.request.user
        
        # Set created_by and modified_by (from SetCreatedByMixin logic)
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        
        print(f"Created by: {form.instance.created_by}")
        print(f"Modified by: {form.instance.modified_by}")
        print(f"Marked by: {form.instance.marked_by}")
        
        # Get status from form
        status = form.cleaned_data.get('status', 'present')
        student = form.instance.student
        
        # Save the attendance record first
        try:
            response = super().form_valid(form)
            print("✅ ATTENDANCE SAVED SUCCESSFULLY")
            print(f"Attendance ID: {self.object.id}")
        except Exception as e:
            print(f"❌ ERROR SAVING ATTENDANCE: {e}")
            import traceback
            traceback.print_exc()
            raise
        
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
            except Exception as e:
                print(f"Notification error: {e}")  # Log error
            
            messages.info(
                self.request,
                f'Student {student.get_full_name()} marked as ready to transfer. Center admin has been notified.'
            )
        
        # Count topics covered
        topics_count = len(form.cleaned_data.get('topics_covered', []))
        
        messages.success(
            self.request,
            f'Attendance marked for {student.get_full_name()} - {self.object.duration_minutes} minutes, {topics_count} topics covered'
        )
        
        return response


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


class GetStudentsWithoutTodayAttendanceView(LoginRequiredMixin, FacultyRequiredMixin, View):
    """
    AJAX endpoint to get students who don't have attendance marked today.
    Returns JSON list of students.
    """
    
    def get(self, request):
        try:
            faculty = request.user.faculty_profile
            today = timezone.now().date()
            
            # Get students who already have attendance today
            students_with_attendance_today = AttendanceRecord.objects.filter(
                marked_by=request.user,
                date=today
            ).values_list('student_id', flat=True).distinct()
            
            # Get all active students assigned to this faculty
            student_ids = faculty.assignments.filter(
                is_active=True
            ).values_list('student_id', flat=True).distinct()
            
            # Filter out students who already have attendance
            students = Student.objects.filter(
                id__in=student_ids,
                deleted_at__isnull=True
            ).exclude(
                id__in=students_with_attendance_today
            ).select_related('center')
            
            # Format response
            students_data = [
                {
                    'id': student.id,
                    'name': student.get_full_name(),
                    'enrollment_number': student.enrollment_number,
                    'center': student.center.name if student.center else ''
                }
                for student in students
            ]
            
            return JsonResponse({
                'status': 'success',
                'students': students_data,
                'count': len(students_data)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class GetStudentSubjectsView(LoginRequiredMixin, FacultyRequiredMixin, View):
    """
    AJAX endpoint to get subjects assigned to a specific student for this faculty.
    Returns JSON list of assignments (student-subject pairs).
    """
    
    def get(self, request, student_id):
        try:
            faculty = request.user.faculty_profile
            
            # Get assignments for this student and faculty
            assignments = Assignment.objects.filter(
                student_id=student_id,
                faculty=faculty,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('subject', 'student')
            
            # Verify faculty has access to this student
            if not assignments.exists():
                return JsonResponse({'error': 'No assignments found for this student'}, status=404)
            
            # Format response
            assignments_data = [
                {
                    'id': assignment.id,
                    'subject_id': assignment.subject.id,
                    'subject_name': assignment.subject.name,
                    'subject_code': assignment.subject.code if hasattr(assignment.subject, 'code') else '',
                }
                for assignment in assignments
            ]
            
            return JsonResponse({
                'status': 'success',
                'assignments': assignments_data,
                'student_name': assignments.first().student.get_full_name(),
                'count': len(assignments_data)
            })
            
        except Assignment.DoesNotExist:
            return JsonResponse({'error': 'No assignments found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
