"""
Views for reporting and analytics.
T123: AllCentersReportView
T132: CenterReportView
T133: StudentReportView
T134: FacultyReportView
T135: InsightsView
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count, Q
import json

from apps.core.mixins import AdminOrFacultyRequiredMixin
from apps.centers.models import Center
from apps.students.models import Student
from apps.faculty.models import Faculty
from .services import (
    calculate_center_metrics, calculate_all_centers_summary, get_top_performing_centers,
    calculate_attendance_velocity, calculate_learning_velocity,
    get_insights_summary, get_at_risk_students, get_extended_students, get_nearing_completion_students,
    prepare_attendance_trend_data, prepare_subject_completion_data,
    prepare_attendance_distribution_data, prepare_faculty_performance_data
)


class MasterAccountRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only master accounts can access reports."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_master_account:
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


class AllCentersReportView(MasterAccountRequiredMixin, TemplateView):
    """
    T123: View for comparing all centers side-by-side.
    Shows metrics, charts, and performance comparison.
    """
    template_name = 'reports/all_centers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all center metrics
        center_metrics = calculate_center_metrics()
        context['center_metrics'] = center_metrics
        
        # Get summary across all centers
        summary = calculate_all_centers_summary()
        context['summary'] = summary
        
        # Get top performing centers
        context['top_attendance'] = get_top_performing_centers('attendance_rate', 5)
        context['top_students'] = get_top_performing_centers('total_students', 5)
        
        # Prepare data for Google Charts (T126)
        # Chart 1: Students per center
        students_chart_data = [['Center', 'Active Students', 'Inactive Students', 'Completed Students']]
        for metric in center_metrics:
            students_chart_data.append([
                metric['center_name'],
                metric['students']['active'],
                metric['students']['inactive'],
                metric['students']['completed'],
            ])
        context['students_chart_data'] = json.dumps(students_chart_data)
        
        # Chart 2: Attendance rate comparison
        attendance_chart_data = [['Center', 'Attendance Rate (%)']]
        for metric in center_metrics:
            attendance_chart_data.append([
                metric['center_name'],
                metric['attendance']['attendance_rate'],
            ])
        context['attendance_chart_data'] = json.dumps(attendance_chart_data)
        
        # Chart 3: Faculty vs Students ratio
        ratio_chart_data = [['Center', 'Students', 'Faculty']]
        for metric in center_metrics:
            ratio_chart_data.append([
                metric['center_name'],
                metric['students']['total'],
                metric['faculty']['total'],
            ])
        context['ratio_chart_data'] = json.dumps(ratio_chart_data)
        
        # Chart 4: Attendance this month
        monthly_attendance_data = [['Center', 'Attendance This Month']]
        for metric in center_metrics:
            monthly_attendance_data.append([
                metric['center_name'],
                metric['attendance']['this_month'],
            ])
        context['monthly_attendance_data'] = json.dumps(monthly_attendance_data)
        
        return context


# T132: Center Report View

class CenterReportView(LoginRequiredMixin, TemplateView):
    """
    T132: Detailed report for a specific center.
    Shows comprehensive metrics, charts, and insights.
    """
    template_name = 'reports/center_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow master accounts and center heads
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_master_account or request.user.is_center_head):
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        center_id = self.kwargs.get('center_id')
        center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        
        # Check permissions for center heads
        if self.request.user.is_center_head:
            if not hasattr(self.request.user, 'center_head_profile') or \
               self.request.user.center_head_profile.center != center:
                messages.error(self.request, 'You do not have permission to view this center.')
                return redirect('accounts:profile')
        
        context['center'] = center
        
        # Get center metrics
        metrics = calculate_center_metrics(center)[0]
        context['metrics'] = metrics
        
        # Get insights
        insights = get_insights_summary(center)
        context['insights'] = insights
        
        # Prepare charts
        # Chart 1: Attendance trend (30 days)
        attendance_trend = prepare_attendance_trend_data(center=center, days=30)
        context['attendance_trend_data'] = json.dumps(attendance_trend)
        
        # Chart 2: Attendance distribution
        attendance_dist = prepare_attendance_distribution_data(center, days=30)
        context['attendance_dist_data'] = json.dumps(attendance_dist)
        
        # Chart 3: Faculty performance
        faculty_perf = prepare_faculty_performance_data(center)
        context['faculty_perf_data'] = json.dumps(faculty_perf)
        
        return context


# T133: Student Report View

class StudentReportView(LoginRequiredMixin, TemplateView):
    """
    T133: Detailed report for a specific student.
    ACCESS: Master Account, Center Head, and Faculty.
    Shows attendance history, learning velocity, subject progress, and Gantt chart.
    """
    template_name = 'reports/student_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Allow master accounts, center heads, and faculty
        if not (request.user.is_master_account or request.user.is_center_head or request.user.is_faculty_member):
            messages.error(request, 'You do not have permission to access student reports.')
            return redirect('accounts:profile')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = self.kwargs.get('student_id')
        student = get_object_or_404(Student, pk=student_id, deleted_at__isnull=True)
        
        # Check permissions based on role
        if self.request.user.is_center_head:
            if not hasattr(self.request.user, 'center_head_profile'):
                messages.error(self.request, 'Your center head profile is not set up.')
                return redirect('accounts:profile')
            if self.request.user.center_head_profile.center != student.center:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You can only view students from your center.")
        
        elif self.request.user.is_faculty_member:
            if not hasattr(self.request.user, 'faculty_profile'):
                messages.error(self.request, 'Your faculty profile is not set up.')
                return redirect('accounts:profile')
            # Faculty can only view students they teach
            from apps.subjects.models import Assignment
            has_assignment = Assignment.objects.filter(
                student=student,
                faculty=self.request.user.faculty_profile,
                is_active=True
            ).exists()
            if not has_assignment:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You can only view students you teach.")
        
        context['student'] = student
        
        # Calculate velocities
        attendance_velocity = calculate_attendance_velocity(student, days=30)
        learning_velocity = calculate_learning_velocity(student)
        context['attendance_velocity'] = attendance_velocity
        context['learning_velocity'] = learning_velocity
        
        # ENHANCED ACADEMIC INSIGHTS
        from apps.attendance.models import AttendanceRecord
        from apps.subjects.models import Assignment
        from django.db.models import Avg, Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        all_records = AttendanceRecord.objects.filter(student=student)
        
        # 1. Attendance Consistency Score (0-100)
        last_30_days = today - timedelta(days=30)
        expected_sessions = 20  # Assume 20 sessions per month is ideal
        actual_sessions = all_records.filter(date__gte=last_30_days).count()
        consistency_score = min(100, (actual_sessions / expected_sessions) * 100)
        context['consistency_score'] = round(consistency_score, 1)
        
        # 2. Learning Efficiency (topics per hour)
        total_topics = 0
        for record in all_records:
            total_topics += record.topics_covered.count()
        total_hours = (all_records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60
        learning_efficiency = round(total_topics / total_hours, 2) if total_hours > 0 else 0
        context['learning_efficiency'] = learning_efficiency
        
        # 3. At-Risk Status
        days_since_last = (today - all_records.order_by('-date').first().date).days if all_records.exists() else 999
        context['at_risk'] = days_since_last >= 7
        context['days_since_last_session'] = days_since_last
        
        # 4. Enrollment Duration vs Progress
        enrollment_days = (today - student.enrollment_date).days if student.enrollment_date else 0
        total_sessions = all_records.count()
        expected_sessions_total = (enrollment_days / 30) * 20  # 20 sessions per month
        progress_vs_expected = (total_sessions / expected_sessions_total * 100) if expected_sessions_total > 0 else 0
        context['enrollment_days'] = enrollment_days
        context['progress_vs_expected'] = round(progress_vs_expected, 1)
        
        # 5. Subject-wise Performance
        assignments = Assignment.objects.filter(student=student, deleted_at__isnull=True)
        subject_performance = []
        for assignment in assignments:
            subject_records = all_records.filter(assignment=assignment)
            # Count topics manually for ManyToMany field
            topics_count = 0
            for record in subject_records:
                topics_count += record.topics_covered.count()
            
            subject_performance.append({
                'subject': assignment.subject.name,
                'sessions': subject_records.count(),
                'hours': round((subject_records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1),
                'topics': topics_count,
                'avg_duration': round(subject_records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0, 1),
                'last_session': subject_records.order_by('-date').first().date if subject_records.exists() else None
            })
        context['subject_performance'] = subject_performance
        
        # 6. Weekly Pattern Analysis
        weekly_pattern = {}
        for i in range(7):
            day_name = (today - timedelta(days=i)).strftime('%A')
            day_sessions = all_records.filter(date__week_day=(today - timedelta(days=i)).isoweekday())
            weekly_pattern[day_name] = day_sessions.count()
        context['weekly_pattern'] = weekly_pattern
        context['most_active_day'] = max(weekly_pattern, key=weekly_pattern.get) if weekly_pattern else 'N/A'
        
        # 7. Comparative Metrics (vs center average)
        center_students = Student.objects.filter(center=student.center, deleted_at__isnull=True)
        center_avg_sessions = AttendanceRecord.objects.filter(
            student__in=center_students
        ).values('student').annotate(count=Count('id')).aggregate(avg=Avg('count'))['avg'] or 0
        context['center_avg_sessions'] = round(center_avg_sessions, 1)
        context['performance_vs_peers'] = 'Above Average' if total_sessions > center_avg_sessions else 'Below Average'
        
        # Prepare charts
        # Chart 1: Attendance trend
        attendance_trend = prepare_attendance_trend_data(student=student, days=30)
        context['attendance_trend_data'] = json.dumps(attendance_trend)
        
        # Debug: Log chart data
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Student {student.id} - Attendance trend rows: {len(attendance_trend)}")
        logger.info(f"Student {student.id} - Total attendance records: {all_records.count()}")
        
        # Chart 2: Subject completion
        subject_completion = prepare_subject_completion_data(student)
        context['subject_completion_data'] = json.dumps(subject_completion)
        logger.info(f"Student {student.id} - Subject completion rows: {len(subject_completion)}")
        
        # NEW CHARTS FOR DETAILED ANALYTICS
        
        # Chart 3: Subject Mastery Pie Chart
        subject_mastery_data = [['Subject', 'Topics Covered']]
        for perf in subject_performance:
            if perf['topics'] > 0:
                subject_mastery_data.append([perf['subject'][:15], perf['topics']])
        context['subject_mastery_data'] = json.dumps(subject_mastery_data)
        
        # Chart 4: Monthly Learning Trend (6 months)
        monthly_learning = [['Month', 'Sessions', 'Hours', 'Topics']]
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            month_records = all_records.filter(date__range=[month_start, month_end])
            
            month_topics = 0
            for record in month_records:
                month_topics += record.topics_covered.count()
            
            monthly_learning.append([
                month_start.strftime('%b'),
                month_records.count(),
                round((month_records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1),
                month_topics
            ])
        context['monthly_learning_data'] = json.dumps(monthly_learning)
        
        # Chart 5: Weekly Learning Pattern (Bar Chart)
        weekly_pattern_chart = [['Day', 'Sessions', 'Hours']]
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days_order:
            day_count = weekly_pattern.get(day, 0)
            day_records = all_records.filter(date__week_day=days_order.index(day) + 1)
            day_hours = round((day_records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1)
            weekly_pattern_chart.append([day[:3], day_count, day_hours])
        context['weekly_pattern_chart'] = json.dumps(weekly_pattern_chart)
        
        # Chart 6: Hourly Learning Preference (Area Chart)
        hourly_preference = [['Hour', 'Sessions']]
        for hour in range(6, 22):
            hour_count = 0
            for record in all_records:
                if record.in_time and record.in_time.hour == hour:
                    hour_count += 1
            hourly_preference.append([f"{hour}:00", hour_count])
        context['hourly_preference_data'] = json.dumps(hourly_preference)
        
        # Chart 7: Learning Velocity Trend (Line Chart - Last 10 sessions)
        velocity_trend = [['Session', 'Topics/Hour']]
        recent_10 = all_records.order_by('-date')[:10]
        session_num = 10
        for record in reversed(list(recent_10)):
            duration_hours = record.duration_minutes / 60 if record.duration_minutes > 0 else 1
            topics_count = record.topics_covered.count()
            velocity = round(topics_count / duration_hours, 2)
            velocity_trend.append([f"S{session_num}", velocity])
            session_num -= 1
        context['velocity_trend_data'] = json.dumps(velocity_trend)
        
        # Chart 8: Progress Over Time (Area Chart)
        progress_over_time = [['Date', 'Cumulative Topics']]
        cumulative_topics = 0
        for record in all_records.order_by('date')[:30]:  # Last 30 sessions
            cumulative_topics += record.topics_covered.count()
            progress_over_time.append([record.date.strftime('%m/%d'), cumulative_topics])
        context['progress_over_time_data'] = json.dumps(progress_over_time)
        
        # Chart 9: Google Calendar Chart (From enrollment date to today)
        # Use enrollment date as start date (can be backdated by admin)
        if student.enrollment_date:
            start_date = student.enrollment_date
        else:
            # Fallback to first attendance or 1 year ago
            first_record = all_records.order_by('date').first()
            if first_record:
                start_date = first_record.date
            else:
                start_date = today - timedelta(days=365)
        
        # Create a dictionary for quick lookup
        attendance_by_date = {}
        for record in all_records:
            date_str = record.date.strftime('%Y-%m-%d')
            topics_list = [topic.name for topic in record.topics_covered.all()]
            
            if date_str not in attendance_by_date:
                attendance_by_date[date_str] = {
                    'sessions': 0,
                    'hours': 0,
                    'topics': [],
                    'subjects': set()
                }
            
            attendance_by_date[date_str]['sessions'] += 1
            attendance_by_date[date_str]['hours'] += record.duration_minutes / 60
            attendance_by_date[date_str]['topics'].extend(topics_list)
            attendance_by_date[date_str]['subjects'].add(record.assignment.subject.name)
        
        # Generate Google Calendar Chart data format: [Date, Hours]
        # Google Calendar expects: new Date(year, month, day), value
        calendar_chart_data = [['Date', 'Hours', {'type': 'string', 'role': 'tooltip', 'p': {'html': True}}]]
        
        current_date = start_date
        while current_date <= today:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in attendance_by_date:
                data = attendance_by_date[date_str]
                hours = round(data['hours'], 1)
                topics = ', '.join(data['topics']) if data['topics'] else 'No topics'
                subjects = ', '.join(data['subjects'])
                
                # Create HTML tooltip
                tooltip = f"<div style='padding:10px;'><b>{current_date.strftime('%b %d, %Y')}</b><br/>" \
                         f"<b>Subjects:</b> {subjects}<br/>" \
                         f"<b>Topics:</b> {topics}<br/>" \
                         f"<b>Sessions:</b> {data['sessions']}<br/>" \
                         f"<b>Hours:</b> {hours}</div>"
                
                calendar_chart_data.append([
                    f"new Date({current_date.year}, {current_date.month - 1}, {current_date.day})",
                    hours,
                    tooltip
                ])
            else:
                # No attendance - value 0
                tooltip = f"<div style='padding:10px;'><b>{current_date.strftime('%b %d, %Y')}</b><br/>" \
                         f"<b>Status:</b> Absent</div>"
                calendar_chart_data.append([
                    f"new Date({current_date.year}, {current_date.month - 1}, {current_date.day})",
                    0,
                    tooltip
                ])
            
            current_date += timedelta(days=1)
        
        context['calendar_chart_data'] = calendar_chart_data
        context['calendar_start_year'] = start_date.year
        context['calendar_end_year'] = today.year
        
        # Get recent attendance records
        recent_attendance = all_records.select_related(
            'assignment__subject', 'marked_by'
        ).order_by('-date')[:10]
        context['recent_attendance'] = recent_attendance
        
        return context


# T134: Faculty Report View

class FacultyReportView(LoginRequiredMixin, TemplateView):
    """
    T134: Detailed report for a specific faculty member.
    Shows teaching statistics, student performance, and session metrics.
    """
    template_name = 'reports/faculty_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow master accounts and center heads
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_master_account or request.user.is_center_head):
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty_id = self.kwargs.get('faculty_id')
        faculty = get_object_or_404(Faculty, pk=faculty_id, deleted_at__isnull=True)
        
        # Check permissions for center heads
        if self.request.user.is_center_head:
            if not hasattr(self.request.user, 'center_head_profile') or \
               self.request.user.center_head_profile.center != faculty.center:
                messages.error(self.request, 'You do not have permission to view this faculty.')
                return redirect('accounts:profile')
        
        context['faculty'] = faculty
        
        # Get teaching statistics
        from apps.attendance.models import AttendanceRecord
        from apps.subjects.models import Assignment
        from django.db.models import Avg, Sum
        
        records = AttendanceRecord.objects.filter(marked_by=faculty.user)
        
        stats = {
            'total_sessions': records.count(),
            'total_students': records.values('student').distinct().count(),
            'total_subjects': Assignment.objects.filter(
                faculty=faculty,
                deleted_at__isnull=True
            ).values('subject').distinct().count(),
            'avg_session_duration': records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
            'total_teaching_hours': (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60,
        }
        context['stats'] = stats
        
        # Get student list
        students = Student.objects.filter(
            id__in=records.values_list('student_id', flat=True).distinct()
        ).annotate(
            session_count=Count('attendancerecord', filter=Q(attendancerecord__marked_by=faculty.user))
        ).order_by('-session_count')[:10]
        context['top_students'] = students
        
        # Prepare charts
        # Chart 1: Attendance trend
        attendance_trend = prepare_attendance_trend_data(center=faculty.center, days=30)
        context['attendance_trend_data'] = json.dumps(attendance_trend)
        
        # Get recent sessions
        recent_sessions = records.select_related('student', 'assignment__subject').order_by('-date')[:10]
        context['recent_sessions'] = recent_sessions
        
        return context


# T135: Insights View

class InsightsView(LoginRequiredMixin, TemplateView):
    """
    T135: Comprehensive insights view showing at-risk students,
    extended students, and students nearing completion.
    """
    template_name = 'reports/insights.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow master accounts and center heads
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_master_account or request.user.is_center_head):
            messages.error(request, 'You do not have permission to access insights.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Determine center
        center = None
        if self.request.user.is_center_head:
            if hasattr(self.request.user, 'center_head_profile'):
                center = self.request.user.center_head_profile.center
        elif self.request.user.is_master_account:
            # Check if center_id is provided in URL
            center_id = self.kwargs.get('center_id')
            if center_id:
                center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        
        context['center'] = center
        
        # Get insights
        insights = get_insights_summary(center)
        context['insights'] = insights
        
        # Get detailed lists
        context['at_risk_students'] = get_at_risk_students(center, days_threshold=7)
        context['extended_students'] = get_extended_students(center, months_threshold=6)
        context['nearing_completion'] = get_nearing_completion_students(center, completion_threshold=80)
        
        # Prepare summary chart
        summary_data = [
            ['Category', 'Count'],
            ['At Risk (7+ days)', insights['at_risk_count']],
            ['Extended (6+ months)', insights['extended_count']],
            ['Nearing Completion', insights['nearing_completion_count']],
        ]
        context['summary_chart_data'] = json.dumps(summary_data)
        
        return context


# T147: Export Report PDF View

class ExportReportPDFView(LoginRequiredMixin, TemplateView):
    """
    T147: Export reports as PDF.
    Uses browser print functionality for PDF generation.
    """
    
    def get(self, request, *args, **kwargs):
        report_type = self.kwargs.get('report_type')
        object_id = self.kwargs.get('object_id')
        
        # Redirect to appropriate report view with print parameter
        if report_type == 'center':
            from django.shortcuts import redirect
            return redirect(f"/reports/center/{object_id}/?print=true")
        elif report_type == 'student':
            return redirect(f"/reports/student/{object_id}/?print=true")
        elif report_type == 'faculty':
            return redirect(f"/reports/faculty/{object_id}/?print=true")
        elif report_type == 'insights':
            if object_id and object_id != '0':
                return redirect(f"/reports/insights/{object_id}/?print=true")
            else:
                return redirect("/reports/insights/?print=true")
        
        messages.error(request, 'Invalid report type')
        return redirect('reports:all_centers')


# T148: Export Report CSV View

class ExportReportCSVView(LoginRequiredMixin, TemplateView):
    """
    T148: Export reports as CSV.
    Generates CSV data for download.
    """
    
    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse
        
        report_type = self.kwargs.get('report_type')
        object_id = self.kwargs.get('object_id')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{object_id}.csv"'
        
        writer = csv.writer(response)
        
        if report_type == 'center':
            center = get_object_or_404(Center, pk=object_id, deleted_at__isnull=True)
            metrics = calculate_center_metrics(center)[0]
            
            writer.writerow(['Center Report'])
            writer.writerow(['Center Name', center.name])
            writer.writerow(['Center Code', center.code])
            writer.writerow(['Location', f"{center.city}, {center.state}"])
            writer.writerow([])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Students', metrics['students']['total']])
            writer.writerow(['Active Students', metrics['students']['active']])
            writer.writerow(['Total Faculty', metrics['faculty']['total']])
            writer.writerow(['Total Subjects', metrics['subjects']['total']])
            writer.writerow(['Total Attendance', metrics['attendance']['total']])
            writer.writerow(['Attendance This Month', metrics['attendance']['this_month']])
            writer.writerow(['Attendance Rate', f"{metrics['attendance']['attendance_rate']}%"])
            
        elif report_type == 'student':
            student = get_object_or_404(Student, pk=object_id, deleted_at__isnull=True)
            velocity = calculate_attendance_velocity(student, days=30)
            learning = calculate_learning_velocity(student)
            
            writer.writerow(['Student Report'])
            writer.writerow(['Student Name', student.get_full_name()])
            writer.writerow(['Roll Number', student.roll_number])
            writer.writerow(['Center', student.center.name])
            writer.writerow([])
            writer.writerow(['Attendance Velocity (Last 30 Days)'])
            writer.writerow(['Sessions per Week', velocity['sessions_per_week']])
            writer.writerow(['Total Sessions', velocity['total_sessions']])
            writer.writerow(['Avg Duration (min)', velocity['avg_session_duration']])
            writer.writerow(['Total Hours', velocity['total_learning_hours']])
            writer.writerow([])
            writer.writerow(['Learning Velocity'])
            writer.writerow(['Topics per Session', learning['topics_per_session']])
            writer.writerow(['Total Topics', learning['total_topics_covered']])
            writer.writerow(['Minutes per Topic', learning['minutes_per_topic']])
            
        elif report_type == 'faculty':
            faculty = get_object_or_404(Faculty, pk=object_id, deleted_at__isnull=True)
            from apps.attendance.models import AttendanceRecord
            from apps.subjects.models import Assignment
            
            records = AttendanceRecord.objects.filter(marked_by=faculty.user)
            stats = {
                'total_sessions': records.count(),
                'total_students': records.values('student').distinct().count(),
                'total_subjects': Assignment.objects.filter(
                    faculty=faculty, deleted_at__isnull=True
                ).values('subject').distinct().count(),
                'avg_session_duration': records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
                'total_teaching_hours': (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60,
            }
            
            writer.writerow(['Faculty Report'])
            writer.writerow(['Faculty Name', faculty.user.get_full_name()])
            writer.writerow(['Email', faculty.user.email])
            writer.writerow(['Center', faculty.center.name])
            writer.writerow([])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Sessions', stats['total_sessions']])
            writer.writerow(['Students Taught', stats['total_students']])
            writer.writerow(['Subjects', stats['total_subjects']])
            writer.writerow(['Avg Duration (min)', round(stats['avg_session_duration'], 1)])
            writer.writerow(['Total Teaching Hours', round(stats['total_teaching_hours'], 1)])
            
        elif report_type == 'insights':
            center = None
            if object_id and object_id != '0':
                center = get_object_or_404(Center, pk=object_id, deleted_at__isnull=True)
            
            insights = get_insights_summary(center)
            
            writer.writerow(['Insights Report'])
            if center:
                writer.writerow(['Center', center.name])
            else:
                writer.writerow(['Scope', 'All Centers'])
            writer.writerow([])
            writer.writerow(['Category', 'Count'])
            writer.writerow(['At Risk Students', insights['at_risk_count']])
            writer.writerow(['Extended Students', insights['extended_count']])
            writer.writerow(['Nearing Completion', insights['nearing_completion_count']])
        
        return response
