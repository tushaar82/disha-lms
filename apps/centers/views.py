"""
Views for center management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from datetime import timedelta

from apps.core.mixins import CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin
from .models import Center, CenterHead
from .forms import CenterForm


class CenterDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for center heads showing key statistics and insights.
    Supports master accounts viewing any center via session context.
    """
    template_name = 'centers/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow center heads and master accounts
        if not (request.user.is_center_head or request.user.is_master_account):
            messages.error(request, 'You do not have permission to access the dashboard.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_center(self):
        """Get the center for the current user or from session context."""
        # Master accounts can view any center via session
        if self.request.user.is_master_account:
            center_id = self.request.session.get('active_center_id')
            if center_id:
                return get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
            # If no center in session, redirect to centers list
            messages.info(self.request, 'Please select a center to view its dashboard.')
            return None
        
        # Center heads see their own center
        if hasattr(self.request.user, 'center_head_profile'):
            return self.request.user.center_head_profile.center
        
        return None
    
    def get(self, request, *args, **kwargs):
        center = self.get_center()
        if center is None and request.user.is_master_account:
            return redirect('centers:list')
        if center is None:
            messages.error(request, 'No center assigned to your account.')
            return redirect('accounts:profile')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        center = self.get_center()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Student Statistics
        from apps.students.models import Student
        students = Student.objects.filter(center=center, deleted_at__isnull=True)
        context['total_students'] = students.count()
        context['active_students'] = students.filter(status='active').count()
        context['inactive_students'] = students.filter(status='inactive').count()
        context['completed_students'] = students.filter(status='completed').count()
        
        # Faculty Statistics
        from apps.faculty.models import Faculty
        faculty = Faculty.objects.filter(center=center, deleted_at__isnull=True)
        context['total_faculty'] = faculty.count()
        context['active_faculty'] = faculty.filter(is_active=True).count()
        
        # Subject Statistics (subjects are common across all centers)
        from apps.subjects.models import Subject
        subjects = Subject.objects.filter(deleted_at__isnull=True)
        context['total_subjects'] = subjects.count()
        context['active_subjects'] = subjects.filter(is_active=True).count()
        
        # Assignment Statistics
        from apps.subjects.models import Assignment
        assignments = Assignment.objects.filter(student__center=center)
        context['total_assignments'] = assignments.count()
        context['active_assignments'] = assignments.filter(is_active=True).count()
        
        # Attendance Statistics
        from apps.attendance.models import AttendanceRecord
        attendance_records = AttendanceRecord.objects.filter(
            student__center=center
        )
        context['total_attendance_records'] = attendance_records.count()
        context['attendance_this_week'] = attendance_records.filter(
            date__gte=week_ago
        ).count()
        context['attendance_this_month'] = attendance_records.filter(
            date__gte=month_ago
        ).count()
        
        # Recent Students (last 5)
        context['recent_students'] = students.order_by('-created_at')[:5]
        
        # Recent Attendance (today)
        context['today_attendance'] = attendance_records.filter(
            date=today
        ).select_related('student', 'marked_by').order_by('-in_time')[:10]
        
        # Students needing attention (no attendance in 7 days)
        students_with_recent_attendance = attendance_records.filter(
            date__gte=week_ago
        ).values_list('student_id', flat=True).distinct()
        
        context['students_needing_attention'] = students.filter(
            status='active'
        ).exclude(
            id__in=students_with_recent_attendance
        )[:10]
        
        # Faculty performance (attendance marked this month)
        from django.db.models import Count
        context['faculty_performance'] = faculty.filter(
            is_active=True
        ).annotate(
            attendance_count=Count(
                'user__marked_attendance_records',
                filter=Q(user__marked_attendance_records__date__gte=month_ago)
            )
        ).order_by('-attendance_count')[:5]
        
        # Chart data for attendance trend (last 7 days)
        attendance_trend = []
        labels = []
        data = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = attendance_records.filter(date=date).count()
            labels.append(date.strftime('%a'))
            data.append(count)
            attendance_trend.append({
                'date': date.strftime('%a'),
                'count': count
            })
        context['attendance_trend'] = attendance_trend
        
        # Prepare JSON data for Chart.js
        import json
        context['attendance_trend_json'] = json.dumps({
            'labels': labels,
            'data': data
        })
        
        # Center information
        context['center'] = center
        context['is_master_account'] = self.request.user.is_master_account
        
        # For master accounts, provide list of all centers for switching
        if self.request.user.is_master_account:
            context['all_centers'] = Center.objects.filter(
                deleted_at__isnull=True,
                is_active=True
            ).order_by('name')
        
        # Enhanced insights - Students absent > 4 days
        from apps.reports.services import (
            get_at_risk_students, get_delayed_students, get_irregular_students,
            get_faculty_free_slots, get_skipped_topics, prepare_gantt_chart_data
        )
        
        at_risk_4days = get_at_risk_students(center, days_threshold=4)
        context['students_absent_4days'] = list(at_risk_4days[:10])
        context['students_absent_4days_count'] = at_risk_4days.count()
        
        # Delayed students (enrolled > 6 months, low progress)
        delayed = get_delayed_students(center, months_threshold=6, progress_threshold=50)
        context['delayed_students'] = delayed[:10]
        context['delayed_students_count'] = len(delayed)
        
        # Irregular students
        irregular = get_irregular_students(center, days_window=30, gap_threshold=3)
        context['irregular_students'] = irregular[:10]
        context['irregular_students_count'] = len(irregular)
        
        # Faculty insights with free time slots (for today)
        faculty_slots = get_faculty_free_slots(center=center, date=today)
        context['faculty_free_slots'] = faculty_slots[:5]  # Top 5 faculty
        
        # Gantt chart data for faculty schedules (last 7 days)
        faculty_list = faculty.filter(is_active=True)[:3]  # Top 3 active faculty
        gantt_data_all = []
        for fac in faculty_list:
            gantt_data = prepare_gantt_chart_data(faculty=fac, days=7)
            if len(gantt_data) > 1:  # Has data beyond header
                gantt_data_all.append({
                    'faculty': fac,
                    'data': json.dumps(gantt_data)
                })
        context['faculty_gantt_data'] = gantt_data_all
        
        # Skipped topics
        skipped = get_skipped_topics(center=center, days=30)
        context['skipped_topics'] = skipped[:15]
        context['skipped_topics_count'] = len(skipped)
        
        # Feedback integration - average satisfaction
        from apps.feedback.models import FeedbackResponse
        from django.db.models import Avg
        avg_satisfaction = FeedbackResponse.objects.filter(
            survey__center=center
        ).aggregate(avg=Avg('satisfaction_score'))['avg']
        context['avg_satisfaction'] = round(avg_satisfaction, 1) if avg_satisfaction else 0
        
        # Recent feedback count
        context['recent_feedback_count'] = FeedbackResponse.objects.filter(
            survey__center=center,
            created_at__gte=month_ago
        ).count()
        
        # Faculty performance with satisfaction scores
        faculty_with_satisfaction = []
        for fac in context['faculty_performance']:
            # Note: FeedbackResponse doesn't have a direct faculty field
            # We'll skip this for now or need to adjust based on actual model structure
            faculty_with_satisfaction.append({
                'faculty': fac,
                'attendance_count': fac.attendance_count,
                'satisfaction': 0  # Placeholder - needs proper faculty-feedback relationship
            })
        context['faculty_with_satisfaction'] = faculty_with_satisfaction
        
        return context


# T116: AccessCenterDashboardView - Master Account Center Switching
class AccessCenterDashboardView(LoginRequiredMixin, View):
    """
    View for master accounts to switch to a specific center's dashboard.
    Sets the center in session and redirects to dashboard.
    """
    
    def get(self, request, center_id):
        # Only master accounts can switch centers
        if not request.user.is_master_account:
            messages.error(request, 'You do not have permission to access this feature.')
            return redirect('accounts:profile')
        
        # Get the center
        center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        
        # Set center in session (T117: Session-based center context)
        request.session['active_center_id'] = center.id
        request.session['active_center_name'] = center.name
        
        # T121: Create audit log for center access
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='ACCESS_CENTER',
            model_name='Center',
            object_id=center.id,
            changes={
                'center_id': center.id,
                'center_name': center.name,
                'center_code': center.code,
                'action': 'Master account accessed center dashboard'
            }
        )
        
        messages.success(request, f'Switched to {center.name} dashboard.')
        return redirect('centers:dashboard')


# Master Account - Center Management Views (T110)

class MasterAccountRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only master accounts can access."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_master_account:
            messages.error(request, 'You do not have permission to access this page.')
            from django.shortcuts import redirect
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


class CenterListView(MasterAccountRequiredMixin, ListView):
    """List all centers (Master Account only)."""
    model = Center
    template_name = 'centers/center_list.html'
    context_object_name = 'centers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Center.objects.filter(
            deleted_at__isnull=True
        ).annotate(
            student_count=Count('students', filter=Q(students__deleted_at__isnull=True)),
            faculty_count=Count('faculty_members', filter=Q(faculty_members__deleted_at__isnull=True))
        )
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search)
            )
        
        # Filter by active status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class CenterCreateView(MasterAccountRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Create a new center (Master Account only)."""
    model = Center
    form_class = CenterForm
    template_name = 'centers/center_form.html'
    success_url = reverse_lazy('centers:list')
    audit_action = 'CREATE'
    
    def form_valid(self, form):
        messages.success(self.request, f'Center "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class CenterDetailView(MasterAccountRequiredMixin, DetailView):
    """View center details (Master Account only)."""
    model = Center
    template_name = 'centers/center_detail.html'
    context_object_name = 'center'
    
    def get_queryset(self):
        return Center.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get center statistics
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.subjects.models import Subject
        from apps.attendance.models import AttendanceRecord
        
        center = self.object
        
        context['students'] = Student.objects.filter(
            center=center,
            deleted_at__isnull=True
        )
        context['faculty'] = Faculty.objects.filter(
            center=center,
            deleted_at__isnull=True
        )
        # Subjects are common across all centers
        context['subjects'] = Subject.objects.filter(
            deleted_at__isnull=True
        )
        
        # Attendance statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        attendance_records = AttendanceRecord.objects.filter(
            student__center=center
        )
        context['attendance_this_week'] = attendance_records.filter(date__gte=week_ago).count()
        context['attendance_this_month'] = attendance_records.filter(date__gte=month_ago).count()
        
        # Center heads
        context['center_heads'] = CenterHead.objects.filter(
            center=center,
            deleted_at__isnull=True
        ).select_related('user')
        
        return context


class CenterUpdateView(MasterAccountRequiredMixin, AuditLogMixin, UpdateView):
    """Update center information (Master Account only)."""
    model = Center
    form_class = CenterForm
    template_name = 'centers/center_form.html'
    audit_action = 'UPDATE'
    
    def get_queryset(self):
        return Center.objects.filter(deleted_at__isnull=True)
    
    def get_success_url(self):
        return reverse_lazy('centers:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Center "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class CenterDeleteView(MasterAccountRequiredMixin, AuditLogMixin, DeleteView):
    """Soft delete a center (Master Account only)."""
    model = Center
    template_name = 'centers/center_confirm_delete.html'
    success_url = reverse_lazy('centers:list')
    audit_action = 'DELETE'
    
    def get_queryset(self):
        return Center.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Soft delete
        self.object.deleted_at = timezone.now()
        self.object.deleted_by = request.user
        self.object.save()
        
        messages.success(request, f'Center "{self.object.name}" deleted successfully!')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(success_url)
