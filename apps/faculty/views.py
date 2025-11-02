"""
Views for faculty management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, datetime, time
import json

from apps.core.mixins import CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin, AdminOrMasterRequiredMixin
from .models import Faculty
from .forms import FacultyForm


class FacultyListView(LoginRequiredMixin, ListView):
    """
    List all faculty.
    - Master Account: Can view all faculty across all centers with filter
    - Center Head: Can view only their center's faculty
    """
    model = Faculty
    template_name = 'faculty/faculty_list.html'
    context_object_name = 'faculty_members'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Allow master account and center heads
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not (request.user.is_master_account or request.user.is_center_head):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account or Center Head to access this page.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Faculty.objects.filter(deleted_at__isnull=True).select_related('user', 'center').annotate(
            student_count=Count('assignments', distinct=True)
        )
        
        # Filter by center for center heads
        if self.request.user.is_center_head and hasattr(self.request.user, 'center_head_profile'):
            queryset = queryset.filter(center=self.request.user.center_head_profile.center)
        
        # Filter by center for master account (optional)
        center_filter = self.request.GET.get('center')
        if center_filter and self.request.user.is_master_account:
            queryset = queryset.filter(center_id=center_filter)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(specialization__icontains=search)
            )
        
        # Filter by active status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-joining_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['center_filter'] = self.request.GET.get('center', '')
        
        # Add centers list for master account
        if self.request.user.is_master_account:
            from apps.centers.models import Center
            context['centers'] = Center.objects.filter(deleted_at__isnull=True).order_by('name')
        
        return context


class FacultyCreateView(LoginRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Create a new faculty member."""
    model = Faculty
    form_class = FacultyForm
    template_name = 'faculty/faculty_form.html'
    success_url = reverse_lazy('faculty:list')
    audit_action = 'CREATE'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_master_account or request.user.is_center_head):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account or Center Head to create faculty.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # For center heads, limit to their center
        if self.request.user.is_center_head and hasattr(self.request.user, 'center_head_profile'):
            form.fields['center'].initial = self.request.user.center_head_profile.center
            form.fields['center'].widget.attrs['readonly'] = True
        return form
    
    def form_valid(self, form):
        messages.success(self.request, f'Faculty {form.instance.user.get_full_name()} created successfully!')
        return super().form_valid(form)


class FacultyDetailView(LoginRequiredMixin, DetailView):
    """View faculty details."""
    model = Faculty
    template_name = 'faculty/faculty_detail.html'
    context_object_name = 'faculty'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_master_account or request.user.is_center_head):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account or Center Head to view faculty.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Faculty.objects.filter(deleted_at__isnull=True).select_related('user', 'center')
        
        # Filter by center for center heads
        if self.request.user.is_center_head and hasattr(self.request.user, 'center_head_profile'):
            queryset = queryset.filter(center=self.request.user.center_head_profile.center)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get faculty's assignments
        from apps.subjects.models import Assignment
        context['assignments'] = Assignment.objects.filter(
            faculty=self.object,
            is_active=True
        ).select_related('student', 'subject')
        
        # Get attendance statistics
        from apps.attendance.services import get_faculty_attendance_stats
        context['attendance_stats'] = get_faculty_attendance_stats(self.object)
        
        # Get subjects taught
        context['subjects_taught'] = Assignment.objects.filter(
            faculty=self.object
        ).values_list('subject__name', flat=True).distinct()
        
        return context


class FacultyUpdateView(LoginRequiredMixin, AuditLogMixin, UpdateView):
    """Update faculty information."""
    model = Faculty
    form_class = FacultyForm
    template_name = 'faculty/faculty_form.html'
    audit_action = 'UPDATE'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_master_account or request.user.is_center_head):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account or Center Head to edit faculty.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Faculty.objects.filter(deleted_at__isnull=True)
        
        # Filter by center for center heads
        if self.request.user.is_center_head and hasattr(self.request.user, 'center_head_profile'):
            queryset = queryset.filter(center=self.request.user.center_head_profile.center)
        
        return queryset
    
    def get_success_url(self):
        return reverse_lazy('faculty:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Faculty {form.instance.user.get_full_name()} updated successfully!')
        return super().form_valid(form)


class FacultyDashboardView(LoginRequiredMixin, AdminOrMasterRequiredMixin, TemplateView):
    """
    Comprehensive Faculty Performance Dashboard with detailed analytics.
    ACCESS: Master Account and Center Head (Admin) only.
    Shows faculty performance, batch schedule, utilization, and effectiveness metrics.
    """
    template_name = 'faculty/faculty_dashboard.html'
    
    def get_faculty(self):
        """Get faculty from URL parameter or return None for overview."""
        faculty_id = self.kwargs.get('faculty_id')
        if faculty_id:
            from apps.faculty.models import Faculty
            return Faculty.objects.filter(id=faculty_id, deleted_at__isnull=True).first()
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get faculty from URL or default to first faculty in center
        faculty = self.get_faculty()
        if not faculty:
            # If no faculty specified, get first faculty in center (for admin)
            from apps.faculty.models import Faculty
            if self.request.user.is_center_head:
                faculty = Faculty.objects.filter(
                    center=self.request.user.center_head_profile.center,
                    deleted_at__isnull=True
                ).first()
            else:
                # Master account - get first faculty
                faculty = Faculty.objects.filter(deleted_at__isnull=True).first()
        
        if not faculty:
            context['no_faculty'] = True
            return context
        
        today = timezone.now().date()
        
        # Date ranges
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        last_5_days = today - timedelta(days=5)
        
        # Get all attendance records for this faculty
        from apps.attendance.models import AttendanceRecord
        from apps.subjects.models import Assignment
        from apps.students.models import Student
        
        all_records = AttendanceRecord.objects.filter(
            assignment__faculty=faculty
        ).select_related('student', 'assignment__subject', 'assignment__student')
        
        # 1. TEACHING STATISTICS
        context['total_students'] = Assignment.objects.filter(
            faculty=faculty,
            is_active=True,
            deleted_at__isnull=True
        ).values('student').distinct().count()
        
        context['total_sessions_all_time'] = all_records.count()
        context['sessions_last_7_days'] = all_records.filter(date__gte=last_7_days).count()
        context['sessions_last_30_days'] = all_records.filter(date__gte=last_30_days).count()
        
        total_hours = all_records.aggregate(total=Sum('duration_minutes'))['total'] or 0
        context['total_teaching_hours'] = round(total_hours / 60, 1)
        
        # 2. ABSENT STUDENTS (Last 5 days)
        active_assignments = Assignment.objects.filter(
            faculty=faculty,
            is_active=True,
            deleted_at__isnull=True
        ).select_related('student', 'subject')
        
        absent_students = []
        for assignment in active_assignments:
            last_attendance = all_records.filter(
                student=assignment.student,
                date__gte=last_5_days
            ).order_by('-date').first()
            
            if not last_attendance:
                days_absent = 5
            else:
                days_absent = (today - last_attendance.date).days
            
            if days_absent >= 3:  # Absent for 3+ days
                absent_students.append({
                    'student': assignment.student,
                    'subject': assignment.subject,
                    'days_absent': days_absent,
                    'last_seen': last_attendance.date if last_attendance else None
                })
        
        context['absent_students'] = sorted(absent_students, key=lambda x: x['days_absent'], reverse=True)[:10]
        context['total_absent_students'] = len(absent_students)
        
        # 3. TEACHING REGULARITY
        # Check if faculty is teaching regularly (sessions in last 7 days)
        sessions_by_day = {}
        for i in range(7):
            date = today - timedelta(days=i)
            count = all_records.filter(date=date).count()
            sessions_by_day[date.strftime('%a')] = count
        
        context['sessions_by_day'] = sessions_by_day
        context['avg_sessions_per_day'] = round(context['sessions_last_7_days'] / 7, 1)
        
        # Teaching streak (consecutive days with sessions)
        streak = 0
        for i in range(30):
            date = today - timedelta(days=i)
            if all_records.filter(date=date).exists():
                streak += 1
            else:
                break
        context['teaching_streak'] = streak
        
        # 4. TIME SLOT ANALYSIS (Today's schedule)
        today_sessions = all_records.filter(date=today).order_by('in_time')
        
        # Build time slots (6 AM to 10 PM in 1-hour slots)
        time_slots = []
        for hour in range(6, 22):  # 6 AM to 10 PM
            slot_start = time(hour, 0)
            slot_end = time(hour + 1, 0) if hour < 23 else time(23, 59)
            
            # Check if this slot is occupied
            occupied = False
            session_info = None
            
            for session in today_sessions:
                if session.in_time and session.out_time:
                    if session.in_time.hour <= hour < session.out_time.hour:
                        occupied = True
                        session_info = {
                            'student': session.student.get_full_name(),
                            'subject': session.assignment.subject.name,
                            'time': f"{session.in_time.strftime('%I:%M %p')} - {session.out_time.strftime('%I:%M %p')}"
                        }
                        break
            
            time_slots.append({
                'hour': hour,
                'time_range': f"{slot_start.strftime('%I %p')} - {slot_end.strftime('%I %p')}",
                'occupied': occupied,
                'session': session_info
            })
        
        context['time_slots'] = time_slots
        context['free_slots_today'] = sum(1 for slot in time_slots if not slot['occupied'])
        context['occupied_slots_today'] = sum(1 for slot in time_slots if slot['occupied'])
        
        # 5. GANTT CHART DATA (Last 7 days schedule)
        gantt_data = [['Task', 'Student', 'Start', 'End']]
        
        for i in range(7):
            date = today - timedelta(days=i)
            day_sessions = all_records.filter(date=date).order_by('in_time')
            
            for session in day_sessions:
                if session.in_time and session.out_time:
                    # Create datetime objects for Gantt chart
                    start_datetime = datetime.combine(date, session.in_time)
                    end_datetime = datetime.combine(date, session.out_time)
                    
                    gantt_data.append([
                        session.assignment.subject.name,
                        session.student.get_full_name(),
                        start_datetime.isoformat(),
                        end_datetime.isoformat()
                    ])
        
        context['gantt_chart_data'] = json.dumps(gantt_data)
        
        # 6. RECENT SESSIONS
        context['recent_sessions'] = all_records.order_by('-date', '-in_time')[:10]
        
        # 7. SUBJECT-WISE BREAKDOWN
        subject_stats = {}
        for assignment in active_assignments:
            subject_name = assignment.subject.name
            if subject_name not in subject_stats:
                subject_stats[subject_name] = {
                    'students': 0,
                    'sessions': 0,
                    'hours': 0
                }
            
            subject_stats[subject_name]['students'] += 1
            sessions = all_records.filter(assignment=assignment)
            subject_stats[subject_name]['sessions'] += sessions.count()
            duration = sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
            subject_stats[subject_name]['hours'] += round(duration / 60, 1)
        
        context['subject_stats'] = subject_stats
        
        # 8. WEEKLY ACTIVITY CHART
        weekly_data = [['Day', 'Sessions', 'Hours']]
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_sessions = all_records.filter(date=date)
            session_count = day_sessions.count()
            hours = round((day_sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1)
            
            weekly_data.append([
                date.strftime('%a %d'),
                session_count,
                hours
            ])
        
        context['weekly_activity_data'] = json.dumps(weekly_data)
        
        # 9. STUDENT PROGRESS DISTRIBUTION (for pie chart)
        progress_distribution = {'on_track': 0, 'needs_attention': 0, 'at_risk': 0}
        for assignment in active_assignments:
            student_records = all_records.filter(student=assignment.student)
            if student_records.exists():
                last_session = student_records.order_by('-date').first()
                days_since = (today - last_session.date).days
                
                if days_since >= 7:
                    progress_distribution['at_risk'] += 1
                elif days_since >= 3:
                    progress_distribution['needs_attention'] += 1
                else:
                    progress_distribution['on_track'] += 1
            else:
                progress_distribution['at_risk'] += 1
        
        context['progress_distribution'] = progress_distribution
        context['progress_chart_data'] = json.dumps([
            ['Status', 'Students'],
            ['On Track', progress_distribution['on_track']],
            ['Needs Attention', progress_distribution['needs_attention']],
            ['At Risk', progress_distribution['at_risk']]
        ])
        
        # 10. SUBJECT PERFORMANCE DATA (for radar/column chart)
        subject_performance_chart = [['Subject', 'Sessions', 'Hours', 'Students']]
        for subject_name, stats in subject_stats.items():
            subject_performance_chart.append([
                subject_name[:15],  # Truncate long names
                stats['sessions'],
                stats['hours'],
                stats['students']
            ])
        context['subject_performance_chart'] = json.dumps(subject_performance_chart)
        
        # 11. MONTHLY TREND DATA (last 6 months)
        monthly_trend = [['Month', 'Sessions', 'Hours', 'Students']]
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            month_sessions = all_records.filter(date__range=[month_start, month_end])
            
            monthly_trend.append([
                month_start.strftime('%b'),
                month_sessions.count(),
                round((month_sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1),
                month_sessions.values('student').distinct().count()
            ])
        context['monthly_trend_data'] = json.dumps(monthly_trend)
        
        # 12. DAILY PATTERN (hours of day)
        hourly_pattern = [['Hour', 'Sessions']]
        for hour in range(6, 22):
            hour_sessions = 0
            for session in all_records:
                if session.in_time and session.in_time.hour == hour:
                    hour_sessions += 1
            hourly_pattern.append([f"{hour}:00", hour_sessions])
        context['hourly_pattern_data'] = json.dumps(hourly_pattern)
        
        context['faculty'] = faculty
        context['today'] = today
        
        return context
