"""
Views for center management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q, Max, Avg, Sum
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from datetime import timedelta, date

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
        
        # ENHANCED ANALYTICS FOR CENTER ADMIN DASHBOARD
        
        # 1. Center Performance Score (0-100)
        # Based on: Student Attendance (30%), Faculty Activity (25%), Student Progress (25%), Feedback (20%)
        
        # Student attendance component
        total_expected_attendance = context['active_students'] * 12  # 12 sessions per month expected
        attendance_rate = (context['attendance_this_month'] / total_expected_attendance * 100) if total_expected_attendance > 0 else 0
        attendance_component = min(30, (attendance_rate / 100) * 30)
        
        # Faculty activity component
        avg_faculty_sessions = context['attendance_this_month'] / context['active_faculty'] if context['active_faculty'] > 0 else 0
        faculty_component = min(25, (avg_faculty_sessions / 40) * 25)  # 40 sessions per month is ideal
        
        # Student progress component (based on active vs total)
        progress_rate = (context['active_students'] / context['total_students'] * 100) if context['total_students'] > 0 else 0
        progress_component = (progress_rate / 100) * 25
        
        # Feedback component
        feedback_component = (context['avg_satisfaction'] / 5) * 20 if context['avg_satisfaction'] > 0 else 10
        
        center_performance_score = round(attendance_component + faculty_component + progress_component + feedback_component, 1)
        context['center_performance_score'] = center_performance_score
        context['performance_breakdown'] = {
            'attendance': round(attendance_component, 1),
            'faculty': round(faculty_component, 1),
            'progress': round(progress_component, 1),
            'feedback': round(feedback_component, 1)
        }
        
        # Performance grade
        if center_performance_score >= 90:
            context['performance_grade'] = 'A+'
            context['grade_color'] = 'success'
        elif center_performance_score >= 80:
            context['performance_grade'] = 'A'
            context['grade_color'] = 'success'
        elif center_performance_score >= 70:
            context['performance_grade'] = 'B+'
            context['grade_color'] = 'info'
        elif center_performance_score >= 60:
            context['performance_grade'] = 'B'
            context['grade_color'] = 'info'
        else:
            context['performance_grade'] = 'C'
            context['grade_color'] = 'warning'
        
        # 2. Faculty Workload Analysis
        faculty_workload = []
        for fac in faculty.filter(is_active=True):
            # Get student count
            student_count = Student.objects.filter(
                assignments__faculty=fac,
                center=center,
                status='active',
                deleted_at__isnull=True
            ).distinct().count()
            
            # Get sessions this month
            sessions_count = attendance_records.filter(
                marked_by=fac.user,
                date__gte=month_ago
            ).count()
            
            # Calculate workload score (sessions + students)
            workload_score = sessions_count + (student_count * 2)
            
            faculty_workload.append({
                'faculty': fac,
                'student_count': student_count,
                'sessions_count': sessions_count,
                'workload_score': workload_score,
                'status': 'overloaded' if workload_score > 60 else ('balanced' if workload_score > 30 else 'underutilized')
            })
        
        faculty_workload.sort(key=lambda x: x['workload_score'], reverse=True)
        context['faculty_workload'] = faculty_workload[:10]
        context['overloaded_faculty'] = [f for f in faculty_workload if f['status'] == 'overloaded']
        context['underutilized_faculty'] = [f for f in faculty_workload if f['status'] == 'underutilized']
        
        # 3. Student Engagement Metrics
        # Active students (attended in last 7 days)
        active_last_week = len(students_with_recent_attendance)
        engagement_rate = (active_last_week / context['active_students'] * 100) if context['active_students'] > 0 else 0
        context['engagement_rate'] = round(engagement_rate, 1)
        context['active_last_week'] = active_last_week
        
        # Average sessions per student (this month)
        avg_sessions_per_student = context['attendance_this_month'] / context['active_students'] if context['active_students'] > 0 else 0
        context['avg_sessions_per_student'] = round(avg_sessions_per_student, 1)
        
        # 4. Revenue & Financial Insights (if applicable)
        # Assuming each session generates revenue
        estimated_monthly_revenue = context['attendance_this_month'] * 500  # ₹500 per session
        context['estimated_monthly_revenue'] = estimated_monthly_revenue
        context['projected_annual_revenue'] = estimated_monthly_revenue * 12
        
        # 5. Trend Analysis (Week over Week)
        last_week_start = week_ago - timedelta(days=7)
        last_week_attendance = attendance_records.filter(
            date__gte=last_week_start,
            date__lt=week_ago
        ).count()
        
        if last_week_attendance > 0:
            wow_change = ((context['attendance_this_week'] - last_week_attendance) / last_week_attendance * 100)
            context['wow_attendance_change'] = round(wow_change, 1)
            context['wow_trend'] = 'up' if wow_change > 0 else ('down' if wow_change < 0 else 'stable')
        else:
            context['wow_attendance_change'] = 0
            context['wow_trend'] = 'stable'
        
        # 6. Action Items & Alerts
        action_items = []
        
        # Alert for low attendance
        if attendance_rate < 50:
            action_items.append({
                'priority': 'critical',
                'category': 'Attendance',
                'title': 'Low Center Attendance',
                'message': f'Only {attendance_rate:.0f}% attendance rate. Immediate action needed!',
                'action': 'Contact absent students and schedule makeup sessions.'
            })
        
        # Alert for students needing attention
        if context['students_absent_4days_count'] > 5:
            action_items.append({
                'priority': 'high',
                'category': 'Student Care',
                'title': f'{context["students_absent_4days_count"]} Students Absent 4+ Days',
                'message': 'Multiple students haven\'t attended recently.',
                'action': 'Review absent student list and initiate contact immediately.'
            })
        
        # Alert for overloaded faculty
        if len(context['overloaded_faculty']) > 0:
            action_items.append({
                'priority': 'medium',
                'category': 'Faculty Management',
                'title': f'{len(context["overloaded_faculty"])} Overloaded Faculty',
                'message': 'Some faculty members have excessive workload.',
                'action': 'Redistribute students or hire additional faculty.'
            })
        
        # Alert for underutilized faculty
        if len(context['underutilized_faculty']) > 2:
            action_items.append({
                'priority': 'low',
                'category': 'Resource Optimization',
                'title': f'{len(context["underutilized_faculty"])} Underutilized Faculty',
                'message': 'Some faculty members have low workload.',
                'action': 'Assign more students or review faculty scheduling.'
            })
        
        # Alert for low feedback
        if context['recent_feedback_count'] < 10:
            action_items.append({
                'priority': 'medium',
                'category': 'Feedback',
                'title': 'Low Feedback Collection',
                'message': f'Only {context["recent_feedback_count"]} feedback responses this month.',
                'action': 'Encourage students to provide feedback after sessions.'
            })
        
        context['action_items'] = action_items
        context['critical_actions'] = [a for a in action_items if a['priority'] == 'critical']
        context['high_actions'] = [a for a in action_items if a['priority'] == 'high']
        
        # 7. Quick Stats Summary
        context['quick_stats'] = {
            'total_sessions_today': attendance_records.filter(date=today).count(),
            'total_hours_this_month': round(attendance_records.filter(date__gte=month_ago).aggregate(
                total=Sum('duration_minutes'))['total'] or 0 / 60, 1),
            'avg_session_duration': round(attendance_records.filter(date__gte=month_ago).aggregate(
                avg=Avg('duration_minutes'))['avg'] or 0, 0),
            'completion_rate': round((context['completed_students'] / context['total_students'] * 100) if context['total_students'] > 0 else 0, 1)
        }
        
        # 8. INACTIVE FACULTY INSIGHTS - Faculty who haven't marked attendance in last 4 days
        four_days_ago = today - timedelta(days=4)
        
        # Get faculty who have marked attendance in last 4 days
        active_faculty_ids = attendance_records.filter(
            date__gte=four_days_ago
        ).values_list('marked_by_id', flat=True).distinct()
        
        # Get inactive faculty (haven't marked attendance in 4+ days)
        inactive_faculty = faculty.filter(
            is_active=True
        ).exclude(
            user_id__in=active_faculty_ids
        ).select_related('user', 'center').annotate(
            last_attendance_date=Max('user__marked_attendance_records__date'),
            total_students=Count('assignments__student', filter=Q(
                assignments__is_active=True,
                assignments__student__status='active',
                assignments__deleted_at__isnull=True
            ), distinct=True)
        ).order_by('last_attendance_date')
        
        # Calculate days since last attendance for each inactive faculty
        inactive_faculty_list = []
        for fac in inactive_faculty:
            days_inactive = (today - fac.last_attendance_date).days if fac.last_attendance_date else 999
            inactive_faculty_list.append({
                'faculty': fac,
                'name': fac.user.get_full_name(),
                'email': fac.user.email,
                'phone': fac.user.phone,
                'center': fac.center.name,
                'employee_id': fac.employee_id,
                'last_attendance_date': fac.last_attendance_date,
                'days_inactive': days_inactive,
                'total_students': fac.total_students
            })
        
        context['inactive_faculty'] = inactive_faculty_list
        context['inactive_faculty_count'] = len(inactive_faculty_list)
        
        # Add to action items if there are inactive faculty
        if len(inactive_faculty_list) > 0:
            action_items.append({
                'priority': 'high',
                'category': 'Faculty Management',
                'title': f'{len(inactive_faculty_list)} Faculty Inactive (4+ Days)',
                'message': f'{len(inactive_faculty_list)} faculty members haven\'t marked attendance in the last 4 days.',
                'action': 'Contact inactive faculty immediately to check on their status and schedule.'
            })
            context['action_items'] = action_items
            context['high_actions'] = [a for a in action_items if a['priority'] == 'high']
        
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


# Enhanced Center Admin Dashboard Views

class CenterAdminDashboardView(LoginRequiredMixin, View):
    """Enhanced dashboard for center admins with student tracking."""
    template_name = 'centers/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_center_head or request.user.is_master_account):
            messages.error(request, 'You do not have permission to access the dashboard.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_center(self):
        """Get the center for the current user."""
        if self.request.user.is_master_account:
            center_id = self.request.session.get('active_center_id')
            if center_id:
                return get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
            return None
        
        if hasattr(self.request.user, 'center_head_profile'):
            return self.request.user.center_head_profile.center
        return None
    
    def get(self, request):
        center = self.get_center()
        if center is None:
            if request.user.is_master_account:
                return redirect('centers:list')
            messages.error(request, 'No center assigned to your account.')
            return redirect('accounts:profile')
        
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        today = timezone.now().date()
        three_days_ago = today - timedelta(days=3)
        thirty_days_ago = today - timedelta(days=30)
        
        # Get all active students
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        )
        
        # Students absent for last 3 days
        students_with_recent_attendance = AttendanceRecord.objects.filter(
            student__center=center,
            date__gte=three_days_ago
        ).values_list('student_id', flat=True).distinct()
        
        absent_students = students.exclude(
            id__in=students_with_recent_attendance
        ).select_related('center').annotate(
            last_attendance=Max('attendance_records__date'),
            total_sessions=Count('attendance_records'),
            total_hours=Sum('attendance_records__duration_minutes')
        )
        
        # Irregular students (inconsistent attendance in last 30 days)
        irregular_students = self.get_irregular_students(center, students, thirty_days_ago, today)
        
        # On-track students (regular attendance, good progress)
        on_track_students = self.get_on_track_students(center, students, thirty_days_ago, today)
        
        # Extended students (enrolled > 6 months, still active)
        six_months_ago = today - timedelta(days=180)
        extended_students = students.filter(
            enrollment_date__lte=six_months_ago
        ).select_related('center').annotate(
            total_sessions=Count('attendance_records'),
            total_hours=Sum('attendance_records__duration_minutes'),
            last_attendance=Max('attendance_records__date')
        )
        
        # INACTIVE FACULTY INSIGHTS - Faculty who haven't marked attendance in last 4 days
        from apps.faculty.models import Faculty
        four_days_ago = today - timedelta(days=4)
        
        # Get attendance records for this center
        attendance_records = AttendanceRecord.objects.filter(
            student__center=center
        )
        
        # Get faculty who have marked attendance in last 4 days
        active_faculty_ids = attendance_records.filter(
            date__gte=four_days_ago
        ).values_list('marked_by_id', flat=True).distinct()
        
        # Get inactive faculty (haven't marked attendance in 4+ days)
        inactive_faculty = Faculty.objects.filter(
            center=center,
            is_active=True,
            deleted_at__isnull=True
        ).exclude(
            user_id__in=active_faculty_ids
        ).select_related('user', 'center').annotate(
            last_attendance_date=Max('user__marked_attendance_records__date'),
            total_students=Count('assignments__student', filter=Q(
                assignments__is_active=True,
                assignments__student__status='active',
                assignments__deleted_at__isnull=True
            ), distinct=True)
        ).order_by('last_attendance_date')
        
        # Calculate days since last attendance for each inactive faculty
        inactive_faculty_list = []
        for fac in inactive_faculty:
            days_inactive = (today - fac.last_attendance_date).days if fac.last_attendance_date else 999
            inactive_faculty_list.append({
                'faculty': fac,
                'name': fac.user.get_full_name(),
                'email': fac.user.email,
                'phone': fac.user.phone,
                'center': fac.center.name,
                'employee_id': fac.employee_id,
                'last_attendance_date': fac.last_attendance_date,
                'days_inactive': days_inactive,
                'total_students': fac.total_students
            })
        
        # Summary statistics
        context = {
            'center': center,
            'today': today,
            'total_students': students.count(),
            'absent_3days_count': absent_students.count(),
            'irregular_count': len(irregular_students),
            'on_track_count': len(on_track_students),
            'extended_count': extended_students.count(),
            
            # Preview lists (first 5)
            'absent_students_preview': absent_students[:5],
            'irregular_students_preview': irregular_students[:5],
            'on_track_students_preview': on_track_students[:5],
            'extended_students_preview': extended_students[:5],
            
            # Inactive faculty insights
            'inactive_faculty': inactive_faculty_list,
            'inactive_faculty_count': len(inactive_faculty_list),
        }
        
        return render(request, self.template_name, context)
    
    def get_irregular_students(self, center, students, start_date, end_date):
        """Get students with irregular attendance patterns."""
        from apps.attendance.models import AttendanceRecord
        
        irregular = []
        for student in students:
            attendance_dates = list(AttendanceRecord.objects.filter(
                student=student,
                date__gte=start_date,
                date__lte=end_date
            ).values_list('date', flat=True).order_by('date'))
            
            if len(attendance_dates) < 5:  # Less than 5 sessions in 30 days
                continue
            
            # Check for gaps > 5 days
            has_large_gap = False
            for i in range(1, len(attendance_dates)):
                gap = (attendance_dates[i] - attendance_dates[i-1]).days
                if gap > 5:
                    has_large_gap = True
                    break
            
            if has_large_gap:
                student.attendance_gap = True
                student.total_sessions = len(attendance_dates)
                student.last_attendance = attendance_dates[-1] if attendance_dates else None
                irregular.append(student)
        
        return irregular
    
    def get_on_track_students(self, center, students, start_date, end_date):
        """Get students with regular attendance."""
        from apps.attendance.models import AttendanceRecord
        
        on_track = []
        for student in students:
            attendance_count = AttendanceRecord.objects.filter(
                student=student,
                date__gte=start_date,
                date__lte=end_date
            ).count()
            
            # On track: at least 12 sessions in 30 days (3 per week average)
            if attendance_count >= 12:
                student.total_sessions = attendance_count
                student.last_attendance = AttendanceRecord.objects.filter(
                    student=student
                ).aggregate(Max('date'))['date__max']
                on_track.append(student)
        
        return on_track


class StudentCategoryListView(LoginRequiredMixin, View):
    """List view for specific student categories with pagination."""
    template_name = 'centers/student_category_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_center_head or request.user.is_master_account):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_center(self):
        """Get the center for the current user."""
        if self.request.user.is_master_account:
            center_id = self.request.session.get('active_center_id')
            if center_id:
                return get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
            return None
        
        if hasattr(self.request.user, 'center_head_profile'):
            return self.request.user.center_head_profile.center
        return None
    
    def get(self, request, category):
        center = self.get_center()
        if center is None:
            if request.user.is_master_account:
                return redirect('centers:list')
            messages.error(request, 'No center assigned to your account.')
            return redirect('accounts:profile')
        
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        today = timezone.now().date()
        
        # Get students based on category
        if category == 'absent':
            students_list = self.get_absent_students(center, today)
            title = "Students Absent for 3+ Days"
            description = "Students who haven't attended any sessions in the last 3 days"
        elif category == 'irregular':
            students_list = self.get_irregular_students_full(center, today)
            title = "Irregular Students"
            description = "Students with inconsistent attendance patterns (gaps > 5 days)"
        elif category == 'on-track':
            students_list = self.get_on_track_students_full(center, today)
            title = "On-Track Students"
            description = "Students with regular attendance (12+ sessions in last 30 days)"
        elif category == 'extended':
            students_list = self.get_extended_students(center, today)
            title = "Extended Students"
            description = "Students enrolled for more than 6 months"
        else:
            messages.error(request, 'Invalid category.')
            return redirect('centers:admin_dashboard')
        
        # Pagination
        paginator = Paginator(students_list, 20)  # 20 students per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'center': center,
            'category': category,
            'title': title,
            'description': description,
            'page_obj': page_obj,
            'students': page_obj.object_list,
            'total_count': paginator.count,
        }
        
        return render(request, self.template_name, context)
    
    def get_absent_students(self, center, today):
        """Get students absent for 3+ days with details."""
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        three_days_ago = today - timedelta(days=3)
        
        students_with_recent_attendance = AttendanceRecord.objects.filter(
            student__center=center,
            date__gte=three_days_ago
        ).values_list('student_id', flat=True).distinct()
        
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        ).exclude(
            id__in=students_with_recent_attendance
        ).select_related('center').annotate(
            last_attendance=Max('attendance_records__date'),
            total_sessions=Count('attendance_records'),
            total_hours=Sum('attendance_records__duration_minutes')
        ).order_by('last_attendance')
        
        # Calculate days absent
        for student in students:
            if student.last_attendance:
                student.days_absent = (today - student.last_attendance).days
            else:
                student.days_absent = (today - student.enrollment_date).days
        
        return list(students)
    
    def get_irregular_students_full(self, center, today):
        """Get all irregular students with details."""
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        thirty_days_ago = today - timedelta(days=30)
        
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        )
        
        irregular = []
        for student in students:
            attendance_dates = list(AttendanceRecord.objects.filter(
                student=student,
                date__gte=thirty_days_ago,
                date__lte=today
            ).values_list('date', flat=True).order_by('date'))
            
            if len(attendance_dates) < 5:
                continue
            
            # Check for gaps > 5 days
            max_gap = 0
            for i in range(1, len(attendance_dates)):
                gap = (attendance_dates[i] - attendance_dates[i-1]).days
                if gap > max_gap:
                    max_gap = gap
            
            if max_gap > 5:
                student.max_gap_days = max_gap
                student.total_sessions = len(attendance_dates)
                student.last_attendance = attendance_dates[-1] if attendance_dates else None
                student.total_hours = AttendanceRecord.objects.filter(
                    student=student
                ).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
                irregular.append(student)
        
        return irregular
    
    def get_on_track_students_full(self, center, today):
        """Get all on-track students with details."""
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        thirty_days_ago = today - timedelta(days=30)
        
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        )
        
        on_track = []
        for student in students:
            attendance_count = AttendanceRecord.objects.filter(
                student=student,
                date__gte=thirty_days_ago,
                date__lte=today
            ).count()
            
            if attendance_count >= 12:
                student.total_sessions = attendance_count
                student.last_attendance = AttendanceRecord.objects.filter(
                    student=student
                ).aggregate(Max('date'))['date__max']
                student.total_hours = AttendanceRecord.objects.filter(
                    student=student
                ).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
                on_track.append(student)
        
        return on_track
    
    def get_extended_students(self, center, today):
        """Get students enrolled for 6+ months."""
        from apps.students.models import Student
        from apps.attendance.models import AttendanceRecord
        
        six_months_ago = today - timedelta(days=180)
        
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active',
            enrollment_date__lte=six_months_ago
        ).select_related('center').annotate(
            total_sessions=Count('attendance_records'),
            total_hours=Sum('attendance_records__duration_minutes'),
            last_attendance=Max('attendance_records__date')
        ).order_by('enrollment_date')
        
        # Calculate months enrolled
        for student in students:
            days_enrolled = (today - student.enrollment_date).days
            student.months_enrolled = days_enrolled // 30
        
        return list(students)
