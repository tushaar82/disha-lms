"""
Views for reporting and analytics.
T123: AllCentersReportView
T132: CenterReportView
T133: StudentReportView
T134: FacultyReportView
T135: InsightsView
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView, ListView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count, Q, Max, Sum, Avg
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
    prepare_attendance_distribution_data, prepare_faculty_performance_data,
    get_low_performing_centers, get_irregular_students, get_delayed_students,
    calculate_profitability_metrics, get_faculty_free_slots, get_skipped_topics,
    prepare_gantt_chart_data, prepare_heatmap_data, get_center_performance_score
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
        from django.utils import timezone
        from datetime import timedelta
        from apps.faculty.models import Faculty
        from apps.attendance.models import AttendanceRecord
        
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
        
        # INACTIVE FACULTY INSIGHTS - Faculty who haven't marked attendance in last 4 days (across all centers)
        today = timezone.now().date()
        four_days_ago = today - timedelta(days=4)
        
        # Get all active faculty
        all_faculty = Faculty.objects.filter(
            deleted_at__isnull=True,
            is_active=True
        ).select_related('user', 'center')
        
        # Get faculty who have marked attendance in last 4 days
        active_faculty_ids = AttendanceRecord.objects.filter(
            date__gte=four_days_ago
        ).values_list('marked_by_id', flat=True).distinct()
        
        # Get inactive faculty (haven't marked attendance in 4+ days)
        inactive_faculty = all_faculty.exclude(
            user_id__in=active_faculty_ids
        ).annotate(
            last_attendance_date=Max('user__marked_attendance_records__date'),
            total_students=Count('assignments__student', filter=Q(
                assignments__is_active=True,
                assignments__student__status='active',
                assignments__deleted_at__isnull=True
            ), distinct=True)
        ).order_by('center__name', 'last_attendance_date')
        
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
                'center_id': fac.center.id,
                'employee_id': fac.employee_id,
                'last_attendance_date': fac.last_attendance_date,
                'days_inactive': days_inactive,
                'total_students': fac.total_students
            })
        
        context['inactive_faculty'] = inactive_faculty_list
        context['inactive_faculty_count'] = len(inactive_faculty_list)
        
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
        
        # Enhanced insights - Students absent > 4 days
        at_risk_4days = get_at_risk_students(center, days_threshold=4)
        context['students_absent_4days'] = at_risk_4days[:10]
        context['students_absent_4days_count'] = at_risk_4days.count()
        
        # Delayed students (enrolled > 6 months, low progress)
        delayed = get_delayed_students(center, months_threshold=6, progress_threshold=50)
        context['delayed_students'] = delayed[:10]
        context['delayed_students_count'] = len(delayed)
        
        # Irregular students
        irregular = get_irregular_students(center, days_window=30, gap_threshold=3)
        context['irregular_students'] = irregular[:10]
        context['irregular_students_count'] = len(irregular)
        
        # Faculty insights with free time slots
        faculty_slots = get_faculty_free_slots(center=center)
        context['faculty_free_slots'] = faculty_slots
        
        # Gantt chart data for faculty schedules (last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        
        # Get faculty list for Gantt
        faculty_list = Faculty.objects.filter(center=center, deleted_at__isnull=True, is_active=True)[:5]
        gantt_data_all = []
        for fac in faculty_list:
            gantt_data = prepare_gantt_chart_data(faculty=fac, days=7)
            if len(gantt_data) > 1:  # Has data beyond header
                gantt_data_all.append({
                    'faculty': fac,
                    'data': gantt_data
                })
        context['faculty_gantt_data'] = gantt_data_all
        
        # Feedback integration - average satisfaction by faculty
        from apps.feedback.models import FeedbackResponse
        faculty_satisfaction = []
        for fac in Faculty.objects.filter(center=center, deleted_at__isnull=True):
            # Note: FeedbackResponse doesn't have a direct faculty field
            # Using satisfaction_score instead of rating
            avg_rating = FeedbackResponse.objects.filter(
                survey__center=center
            ).aggregate(avg=Avg('satisfaction_score'))['avg']
            if avg_rating:
                faculty_satisfaction.append({
                    'faculty': fac,
                    'avg_rating': round(avg_rating, 1)
                })
        context['faculty_satisfaction'] = sorted(faculty_satisfaction, key=lambda x: x['avg_rating'], reverse=True) if faculty_satisfaction else []
        
        # Skipped topics
        skipped = get_skipped_topics(center=center, days=30)
        context['skipped_topics'] = skipped[:20]
        context['skipped_topics_count'] = len(skipped)
        
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
        
        # ENHANCED STUDENT INSIGHTS & RECOMMENDATIONS
        
        # 1. Calculate Total Sessions (Attended / Expected)
        days_enrolled = (today - student.enrollment_date).days if student.enrollment_date else 0
        weeks_enrolled = days_enrolled / 7
        expected_total_sessions = int(weeks_enrolled * 3)  # Assuming 3 sessions per week is ideal
        actual_total_sessions = all_records.count()
        attendance_completion_rate = round((actual_total_sessions / expected_total_sessions * 100), 1) if expected_total_sessions > 0 else 0
        
        context['expected_total_sessions'] = expected_total_sessions
        context['actual_total_sessions'] = actual_total_sessions
        context['attendance_completion_rate'] = attendance_completion_rate
        context['sessions_behind'] = max(0, expected_total_sessions - actual_total_sessions)
        
        # 2. Consistency Score (0-100) - Based on regularity of attendance
        # Check attendance pattern over last 60 days
        sixty_days_ago = today - timedelta(days=60)
        recent_60_days = all_records.filter(date__gte=sixty_days_ago).order_by('date')
        
        if recent_60_days.count() >= 3:
            dates_list = list(recent_60_days.values_list('date', flat=True))
            gaps = []
            for i in range(1, len(dates_list)):
                gap = (dates_list[i] - dates_list[i-1]).days
                gaps.append(gap)
            
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            max_gap = max(gaps) if gaps else 0
            
            # Ideal gap is 2-3 days, penalize larger gaps
            if avg_gap <= 3:
                gap_score = 100
            elif avg_gap <= 5:
                gap_score = 80
            elif avg_gap <= 7:
                gap_score = 60
            else:
                gap_score = 40
            
            # Penalize if max gap is too large
            if max_gap > 14:
                gap_score -= 20
            elif max_gap > 10:
                gap_score -= 10
            
            consistency_percentage = max(0, min(100, gap_score))
        else:
            consistency_percentage = 0
            avg_gap = 0
            max_gap = 0
        
        context['consistency_percentage'] = round(consistency_percentage, 1)
        context['avg_gap_days'] = round(avg_gap, 1)
        context['max_gap_days'] = max_gap
        
        # 3. Learning Patterns Analysis
        learning_patterns = []
        
        # Pattern 1: Preferred learning time
        morning_sessions = all_records.filter(in_time__hour__lt=12).count()
        afternoon_sessions = all_records.filter(in_time__hour__gte=12, in_time__hour__lt=17).count()
        evening_sessions = all_records.filter(in_time__hour__gte=17).count()
        
        if morning_sessions > afternoon_sessions and morning_sessions > evening_sessions:
            preferred_time = "Morning (before 12 PM)"
        elif afternoon_sessions > evening_sessions:
            preferred_time = "Afternoon (12 PM - 5 PM)"
        else:
            preferred_time = "Evening (after 5 PM)"
        
        learning_patterns.append({
            'title': 'Preferred Learning Time',
            'value': preferred_time,
            'detail': f'Morning: {morning_sessions}, Afternoon: {afternoon_sessions}, Evening: {evening_sessions}'
        })
        
        # Pattern 2: Average session duration
        avg_duration = all_records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0
        if avg_duration >= 90:
            duration_assessment = "Excellent - Long focused sessions"
        elif avg_duration >= 60:
            duration_assessment = "Good - Standard session length"
        elif avg_duration >= 45:
            duration_assessment = "Moderate - Consider longer sessions"
        else:
            duration_assessment = "Short - Increase session duration"
        
        learning_patterns.append({
            'title': 'Session Duration Pattern',
            'value': f'{round(avg_duration, 0)} minutes average',
            'detail': duration_assessment
        })
        
        # Pattern 3: Learning velocity trend
        if actual_total_sessions >= 10:
            first_half = all_records.order_by('date')[:actual_total_sessions//2]
            second_half = all_records.order_by('date')[actual_total_sessions//2:]
            
            first_half_topics = sum(r.topics_covered.count() for r in first_half)
            second_half_topics = sum(r.topics_covered.count() for r in second_half)
            
            if second_half_topics > first_half_topics * 1.2:
                velocity_trend = "Improving - Learning pace is accelerating"
            elif second_half_topics < first_half_topics * 0.8:
                velocity_trend = "Declining - Learning pace has slowed"
            else:
                velocity_trend = "Stable - Consistent learning pace"
            
            learning_patterns.append({
                'title': 'Learning Velocity Trend',
                'value': velocity_trend,
                'detail': f'Early: {first_half_topics} topics, Recent: {second_half_topics} topics'
            })
        
        # Pattern 4: Subject focus
        subject_sessions = {}
        for record in all_records:
            subject_name = record.assignment.subject.name
            subject_sessions[subject_name] = subject_sessions.get(subject_name, 0) + 1
        
        if subject_sessions:
            most_focused_subject = max(subject_sessions, key=subject_sessions.get)
            learning_patterns.append({
                'title': 'Most Focused Subject',
                'value': most_focused_subject,
                'detail': f'{subject_sessions[most_focused_subject]} sessions completed'
            })
        
        context['learning_patterns'] = learning_patterns
        
        # 4. Deep Insights
        deep_insights = []
        
        # Insight 1: Attendance completion
        if attendance_completion_rate >= 100:
            deep_insights.append({
                'type': 'success',
                'title': 'Excellent Attendance Record',
                'message': f'Attended {actual_total_sessions} sessions, exceeding the expected {expected_total_sessions} sessions. Outstanding commitment!'
            })
        elif attendance_completion_rate >= 80:
            deep_insights.append({
                'type': 'success',
                'title': 'Good Attendance Progress',
                'message': f'Completed {attendance_completion_rate}% of expected sessions. On track for success!'
            })
        elif attendance_completion_rate >= 60:
            deep_insights.append({
                'type': 'warning',
                'title': 'Moderate Attendance',
                'message': f'Attended {actual_total_sessions} out of {expected_total_sessions} expected sessions ({attendance_completion_rate}%). Room for improvement.'
            })
        else:
            deep_insights.append({
                'type': 'error',
                'title': 'Low Attendance Rate',
                'message': f'Only {attendance_completion_rate}% attendance. Missing {context["sessions_behind"]} sessions. Immediate action needed!'
            })
        
        # Insight 2: Consistency
        if consistency_percentage >= 80:
            deep_insights.append({
                'type': 'success',
                'title': 'Highly Consistent Attendance',
                'message': f'{consistency_percentage}% consistency score. Regular attendance pattern with average {avg_gap:.1f} days between sessions.'
            })
        elif consistency_percentage >= 60:
            deep_insights.append({
                'type': 'info',
                'title': 'Moderately Consistent',
                'message': f'{consistency_percentage}% consistency. Average gap of {avg_gap:.1f} days between sessions. Try to maintain more regular schedule.'
            })
        else:
            deep_insights.append({
                'type': 'warning',
                'title': 'Irregular Attendance Pattern',
                'message': f'Low consistency ({consistency_percentage}%). Maximum gap of {max_gap} days detected. Establish a regular study routine.'
            })
        
        # Insight 3: Learning efficiency
        if learning_efficiency >= 3:
            deep_insights.append({
                'type': 'success',
                'title': 'High Learning Efficiency',
                'message': f'Covering {learning_efficiency} topics per hour. Excellent pace and comprehension!'
            })
        elif learning_efficiency >= 1.5:
            deep_insights.append({
                'type': 'info',
                'title': 'Good Learning Pace',
                'message': f'Average of {learning_efficiency} topics per hour. Steady progress maintained.'
            })
        else:
            deep_insights.append({
                'type': 'warning',
                'title': 'Slow Learning Pace',
                'message': f'Only {learning_efficiency} topics per hour. Consider more focused study sessions or additional support.'
            })
        
        # Insight 4: Progress vs enrollment duration
        if progress_vs_expected >= 100:
            deep_insights.append({
                'type': 'success',
                'title': 'Ahead of Schedule',
                'message': f'Progress is {progress_vs_expected:.0f}% of expected pace. Excellent time management!'
            })
        elif progress_vs_expected >= 70:
            deep_insights.append({
                'type': 'info',
                'title': 'On Track',
                'message': f'Making good progress at {progress_vs_expected:.0f}% of expected pace for {enrollment_days} days enrolled.'
            })
        else:
            deep_insights.append({
                'type': 'error',
                'title': 'Behind Schedule',
                'message': f'Only {progress_vs_expected:.0f}% of expected progress. Enrolled for {enrollment_days} days but need to accelerate learning.'
            })
        
        context['deep_insights'] = deep_insights
        
        # 5. Performance Improvement Recommendations
        recommendations = []
        
        # Recommendation based on attendance
        if attendance_completion_rate < 80:
            recommendations.append({
                'priority': 'high',
                'category': 'Attendance',
                'title': 'Increase Session Frequency',
                'action': f'Schedule {context["sessions_behind"]} additional sessions to catch up. Aim for at least 3 sessions per week.',
                'impact': 'Will improve overall progress and knowledge retention'
            })
        
        # Recommendation based on consistency
        if consistency_percentage < 70:
            recommendations.append({
                'priority': 'high',
                'category': 'Consistency',
                'title': 'Establish Regular Schedule',
                'action': 'Create a fixed weekly schedule (e.g., Mon-Wed-Fri at same time). Avoid gaps longer than 3 days.',
                'impact': 'Better retention and faster progress through regular practice'
            })
        
        # Recommendation based on session duration
        if avg_duration < 60:
            recommendations.append({
                'priority': 'medium',
                'category': 'Session Quality',
                'title': 'Extend Session Duration',
                'action': f'Current average is {avg_duration:.0f} minutes. Increase to 60-90 minutes for better depth.',
                'impact': 'Deeper understanding and more topics covered per session'
            })
        
        # Recommendation based on learning efficiency
        if learning_efficiency < 2:
            recommendations.append({
                'priority': 'medium',
                'category': 'Learning Efficiency',
                'title': 'Improve Focus and Preparation',
                'action': 'Review previous topics before sessions. Minimize distractions. Ask more questions during sessions.',
                'impact': 'Increase topics covered per hour and improve comprehension'
            })
        
        # Recommendation based on at-risk status
        if context['at_risk']:
            recommendations.append({
                'priority': 'critical',
                'category': 'Engagement',
                'title': 'Immediate Re-engagement Required',
                'action': f'No session in {context["days_since_last_session"]} days! Schedule a session within 48 hours. Contact faculty/guardian.',
                'impact': 'Prevent knowledge loss and maintain learning momentum'
            })
        
        # Recommendation for subject balance
        if subject_sessions and len(subject_sessions) > 1:
            min_sessions = min(subject_sessions.values())
            max_sessions = max(subject_sessions.values())
            if max_sessions > min_sessions * 2:
                least_focused = min(subject_sessions, key=subject_sessions.get)
                recommendations.append({
                    'priority': 'low',
                    'category': 'Subject Balance',
                    'title': 'Balance Subject Focus',
                    'action': f'Increase sessions for {least_focused} (only {subject_sessions[least_focused]} sessions). Aim for balanced coverage.',
                    'impact': 'Well-rounded knowledge across all subjects'
                })
        
        # Positive reinforcement
        if attendance_completion_rate >= 90 and consistency_percentage >= 80:
            recommendations.append({
                'priority': 'positive',
                'category': 'Recognition',
                'title': 'Excellent Performance!',
                'action': 'Keep up the great work! Your dedication and consistency are exemplary.',
                'impact': 'Continue this momentum to achieve outstanding results'
            })
        
        context['recommendations'] = recommendations
        
        # 6. Overall Performance Score (0-100)
        # Weighted scoring: Attendance (30%), Consistency (25%), Learning Efficiency (25%), Progress (20%)
        attendance_score = min(100, attendance_completion_rate)
        consistency_score = consistency_percentage
        efficiency_score = min(100, (learning_efficiency / 4) * 100)  # Normalized to 4 topics/hour max
        progress_score = min(100, progress_vs_expected)
        
        overall_score = (
            attendance_score * 0.30 +
            consistency_score * 0.25 +
            efficiency_score * 0.25 +
            progress_score * 0.20
        )
        
        context['overall_performance_score'] = round(overall_score, 1)
        context['score_breakdown'] = {
            'attendance': round(attendance_score * 0.30, 1),
            'consistency': round(consistency_score * 0.25, 1),
            'efficiency': round(efficiency_score * 0.25, 1),
            'progress': round(progress_score * 0.20, 1)
        }
        
        # Performance grade
        if overall_score >= 90:
            performance_grade = 'A+'
            grade_color = 'success'
            grade_message = 'Outstanding Performance'
        elif overall_score >= 80:
            performance_grade = 'A'
            grade_color = 'success'
            grade_message = 'Excellent Performance'
        elif overall_score >= 70:
            performance_grade = 'B+'
            grade_color = 'info'
            grade_message = 'Good Performance'
        elif overall_score >= 60:
            performance_grade = 'B'
            grade_color = 'info'
            grade_message = 'Satisfactory Performance'
        elif overall_score >= 50:
            performance_grade = 'C'
            grade_color = 'warning'
            grade_message = 'Needs Improvement'
        else:
            performance_grade = 'D'
            grade_color = 'error'
            grade_message = 'Requires Immediate Attention'
        
        context['performance_grade'] = performance_grade
        context['grade_color'] = grade_color
        context['grade_message'] = grade_message
        
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
        
        total_sessions = records.count()
        total_students = records.values('student').distinct().count()
        
        stats = {
            'total_sessions': total_sessions,
            'total_students': total_students,
            'total_subjects': Assignment.objects.filter(
                faculty=faculty,
                deleted_at__isnull=True
            ).values('subject').distinct().count(),
            'avg_session_duration': records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
            'total_teaching_hours': (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60,
            'sessions_per_student': round(total_sessions / total_students, 1) if total_students > 0 else 0,
        }
        context['stats'] = stats
        
        # Get student list
        students = Student.objects.filter(
            id__in=records.values_list('student_id', flat=True).distinct()
        ).annotate(
            session_count=Count('attendance_records', filter=Q(attendance_records__marked_by=faculty.user))
        ).order_by('-session_count')[:10]
        context['top_students'] = students
        
        # Prepare charts
        # Chart 1: Attendance trend
        attendance_trend = prepare_attendance_trend_data(center=faculty.center, days=30)
        context['attendance_trend_data'] = json.dumps(attendance_trend)
        
        # Get recent sessions
        recent_sessions = records.select_related('student', 'assignment__subject').order_by('-date')[:10]
        context['recent_sessions'] = recent_sessions
        
        # Get batch schedule (active assignments with student details)
        from django.db.models import Max, Min
        batch_schedule = Assignment.objects.filter(
            faculty=faculty,
            is_active=True,
            deleted_at__isnull=True
        ).select_related(
            'student', 'subject'
        ).annotate(
            total_sessions=Count('attendance_records'),
            last_session_date=Max('attendance_records__date'),
            first_session_date=Min('attendance_records__date'),
            total_hours=Sum('attendance_records__duration_minutes')
        ).order_by('subject__name', 'student__first_name')
        
        context['batch_schedule'] = batch_schedule
        
        # Group batch schedule by subject for better display
        from collections import defaultdict
        schedule_by_subject = defaultdict(list)
        for assignment in batch_schedule:
            schedule_by_subject[assignment.subject.name].append({
                'assignment': assignment,
                'student': assignment.student,
                'total_sessions': assignment.total_sessions or 0,
                'last_session': assignment.last_session_date,
                'first_session': assignment.first_session_date,
                'total_hours': round((assignment.total_hours or 0) / 60, 1),
                'start_date': assignment.start_date,
            })
        
        context['schedule_by_subject'] = dict(schedule_by_subject)
        
        # Identify at-risk students (no session in last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)
        
        # Get all active students taught by this faculty
        active_students = Assignment.objects.filter(
            faculty=faculty,
            is_active=True,
            deleted_at__isnull=True
        ).values_list('student_id', flat=True)
        
        # Find students with no recent attendance
        students_with_recent_attendance = AttendanceRecord.objects.filter(
            student_id__in=active_students,
            marked_by=faculty.user,
            date__gte=seven_days_ago
        ).values_list('student_id', flat=True).distinct()
        
        # At-risk students are those without recent attendance
        at_risk_students = Student.objects.filter(
            id__in=active_students
        ).exclude(
            id__in=students_with_recent_attendance
        ).select_related('center').annotate(
            last_session_date=Max('attendance_records__date', filter=Q(attendance_records__marked_by=faculty.user)),
            total_sessions=Count('attendance_records', filter=Q(attendance_records__marked_by=faculty.user)),
            total_hours=Sum('attendance_records__duration_minutes', filter=Q(attendance_records__marked_by=faculty.user))
        ).order_by('last_session_date')
        
        # Calculate days since last session for each at-risk student
        at_risk_list = []
        for student in at_risk_students:
            if student.last_session_date:
                days_since = (today - student.last_session_date).days
            else:
                days_since = None  # Never attended
            
            # Get their subject assignments
            student_subjects = Assignment.objects.filter(
                student=student,
                faculty=faculty,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('subject')
            
            at_risk_list.append({
                'student': student,
                'last_session': student.last_session_date,
                'days_since': days_since,
                'total_sessions': student.total_sessions or 0,
                'total_hours': round((student.total_hours or 0) / 60, 1),
                'subjects': [a.subject for a in student_subjects],
                'risk_level': 'critical' if days_since and days_since >= 14 else 'high' if days_since and days_since >= 7 else 'never_attended' if not days_since else 'moderate'
            })
        
        context['at_risk_students'] = at_risk_list
        context['at_risk_count'] = len(at_risk_list)
        
        # Enhanced performance metrics
        # Session quality score (topics per hour)
        total_topics = 0
        for record in records:
            total_topics += record.topics_covered.count()
        
        total_hours = stats['total_teaching_hours']
        session_quality_score = round(total_topics / total_hours, 2) if total_hours > 0 else 0
        context['session_quality_score'] = session_quality_score
        
        # Student satisfaction from feedback
        from apps.feedback.models import FeedbackResponse
        # Note: FeedbackResponse doesn't have a direct faculty field
        # Getting center-wide satisfaction as a proxy
        if hasattr(faculty, 'center'):
            avg_satisfaction = FeedbackResponse.objects.filter(
                survey__center=faculty.center
            ).aggregate(avg=Avg('satisfaction_score'))['avg'] or 0
        else:
            avg_satisfaction = 0
        context['avg_satisfaction'] = round(avg_satisfaction, 1)
        
        # Consistency score (regular teaching pattern)
        # Calculate sessions per week over last 8 weeks
        eight_weeks_ago = today - timedelta(days=56)
        recent_records = records.filter(date__gte=eight_weeks_ago)
        weeks_with_sessions = recent_records.values('date__week').distinct().count()
        consistency_score = round((weeks_with_sessions / 8) * 100, 1)
        context['consistency_score'] = consistency_score
        
        # Student Attendance Rate (present vs total students)
        total_active_students = len(active_students)
        students_with_attendance = records.filter(
            date__gte=seven_days_ago
        ).values('student').distinct().count()
        attendance_rate = round((students_with_attendance / total_active_students * 100), 1) if total_active_students > 0 else 0
        context['student_attendance_rate'] = attendance_rate
        context['students_present'] = students_with_attendance
        context['total_active_students'] = total_active_students
        
        # Irregular Students Count (gaps > 5 days in last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        irregular_students_list = []
        
        for student_id in active_students:
            student = Student.objects.get(id=student_id)
            student_records = records.filter(
                student_id=student_id,
                date__gte=thirty_days_ago
            ).order_by('date')
            
            if student_records.count() < 3:  # Less than 3 sessions in 30 days
                continue
            
            # Check for gaps
            dates = list(student_records.values_list('date', flat=True))
            has_large_gap = False
            max_gap = 0
            
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                if gap > max_gap:
                    max_gap = gap
                if gap > 5:
                    has_large_gap = True
            
            if has_large_gap:
                irregular_students_list.append({
                    'student': student,
                    'max_gap': max_gap,
                    'sessions': student_records.count()
                })
        
        context['irregular_students_count'] = len(irregular_students_list)
        context['irregular_students_list'] = irregular_students_list[:10]  # Top 10
        
        # Teaching Performance Score (0-100)
        # Based on: consistency (30%), session quality (30%), student engagement (20%), attendance rate (20%)
        
        # Session quality component (topics per hour)
        quality_component = min(30, (session_quality_score / 5) * 30)  # Max 30 points, normalized to 5 topics/hour
        
        # Consistency component
        consistency_component = (consistency_score / 100) * 30  # Max 30 points
        
        # Student engagement (sessions per student)
        avg_sessions_per_student = stats['sessions_per_student']
        engagement_component = min(20, (avg_sessions_per_student / 10) * 20)  # Max 20 points, normalized to 10 sessions
        
        # Attendance rate component
        attendance_component = (attendance_rate / 100) * 20  # Max 20 points
        
        performance_score = round(quality_component + consistency_component + engagement_component + attendance_component, 1)
        context['performance_score'] = performance_score
        context['performance_breakdown'] = {
            'quality': round(quality_component, 1),
            'consistency': round(consistency_component, 1),
            'engagement': round(engagement_component, 1),
            'attendance': round(attendance_component, 1)
        }
        
        # Performance Grade
        if performance_score >= 90:
            performance_grade = 'A+'
            grade_color = 'success'
        elif performance_score >= 80:
            performance_grade = 'A'
            grade_color = 'success'
        elif performance_score >= 70:
            performance_grade = 'B+'
            grade_color = 'info'
        elif performance_score >= 60:
            performance_grade = 'B'
            grade_color = 'info'
        elif performance_score >= 50:
            performance_grade = 'C'
            grade_color = 'warning'
        else:
            performance_grade = 'D'
            grade_color = 'error'
        
        context['performance_grade'] = performance_grade
        context['grade_color'] = grade_color
        
        # Detailed Insights & Recommendations
        insights = []
        recommendations = []
        
        # Attendance insights
        if attendance_rate < 50:
            insights.append({
                'type': 'error',
                'title': 'Low Student Attendance',
                'message': f'Only {attendance_rate}% of students attended in the last week. This is below the 50% threshold.'
            })
            recommendations.append('Contact absent students immediately and schedule makeup sessions.')
        elif attendance_rate < 75:
            insights.append({
                'type': 'warning',
                'title': 'Moderate Attendance',
                'message': f'{attendance_rate}% attendance rate. Room for improvement.'
            })
            recommendations.append('Follow up with irregular students to improve consistency.')
        else:
            insights.append({
                'type': 'success',
                'title': 'Excellent Attendance',
                'message': f'{attendance_rate}% of students are actively attending. Great job!'
            })
        
        # Irregular students insights
        if context['irregular_students_count'] > 5:
            insights.append({
                'type': 'warning',
                'title': 'High Irregular Student Count',
                'message': f'{context["irregular_students_count"]} students showing irregular attendance patterns.'
            })
            recommendations.append('Create a structured schedule and send reminders to irregular students.')
        
        # Session quality insights
        if session_quality_score < 2:
            insights.append({
                'type': 'warning',
                'title': 'Low Session Quality',
                'message': f'Average of {session_quality_score} topics/hour. Consider covering more topics per session.'
            })
            recommendations.append('Prepare detailed lesson plans to cover more topics efficiently.')
        elif session_quality_score > 4:
            insights.append({
                'type': 'success',
                'title': 'High Session Quality',
                'message': f'Excellent coverage of {session_quality_score} topics/hour!'
            })
        
        # Consistency insights
        if consistency_score < 60:
            insights.append({
                'type': 'error',
                'title': 'Inconsistent Teaching Pattern',
                'message': f'Only {consistency_score}% consistency over the last 8 weeks.'
            })
            recommendations.append('Maintain a regular teaching schedule to improve student outcomes.')
        
        # At-risk students insights
        if context['at_risk_count'] > 0:
            insights.append({
                'type': 'error',
                'title': 'Students Need Attention',
                'message': f'{context["at_risk_count"]} students haven\'t attended in 7+ days.'
            })
            recommendations.append('Prioritize reaching out to at-risk students listed above.')
        
        context['insights'] = insights
        context['recommendations'] = recommendations
        
        # Summary Text
        summary_parts = []
        summary_parts.append(f"Teaching {total_active_students} active students across {stats['total_subjects']} subjects.")
        summary_parts.append(f"Conducted {total_sessions} sessions totaling {stats['total_teaching_hours']:.1f} hours.")
        summary_parts.append(f"Current attendance rate: {attendance_rate}%.")
        summary_parts.append(f"Performance score: {performance_score}/100 (Grade {performance_grade}).")
        
        if context['at_risk_count'] > 0:
            summary_parts.append(f"⚠️ {context['at_risk_count']} students need immediate attention.")
        
        context['performance_summary'] = ' '.join(summary_parts)
        
        # Free time slots visualization
        free_slots = get_faculty_free_slots(faculty=faculty)
        context['free_slots'] = free_slots[0] if free_slots else None
        
        # Gantt chart for weekly schedule
        gantt_data = prepare_gantt_chart_data(faculty=faculty, days=7)
        context['faculty_gantt_data'] = json.dumps(gantt_data)
        
        # ============================================================================
        # COMPREHENSIVE FACULTY FEEDBACK ANALYTICS
        # ============================================================================
        from apps.feedback.models import FacultyFeedback
        
        # Get all feedback for this faculty
        all_feedback = FacultyFeedback.objects.filter(
            faculty=faculty,
            deleted_at__isnull=True
        )
        
        completed_feedback = all_feedback.filter(is_completed=True)
        pending_feedback = all_feedback.filter(is_completed=False)
        
        # Basic feedback statistics
        context['feedback_total'] = all_feedback.count()
        context['feedback_completed'] = completed_feedback.count()
        context['feedback_pending'] = pending_feedback.count()
        context['feedback_completion_rate'] = round(
            (context['feedback_completed'] / context['feedback_total'] * 100) 
            if context['feedback_total'] > 0 else 0, 1
        )
        
        # Calculate average scores for each question
        if completed_feedback.exists():
            feedback_scores = {
                'teaching_quality': completed_feedback.aggregate(avg=Avg('teaching_quality'))['avg'] or 0,
                'subject_knowledge': completed_feedback.aggregate(avg=Avg('subject_knowledge'))['avg'] or 0,
                'explanation_clarity': completed_feedback.aggregate(avg=Avg('explanation_clarity'))['avg'] or 0,
                'student_engagement': completed_feedback.aggregate(avg=Avg('student_engagement'))['avg'] or 0,
                'doubt_resolution': completed_feedback.aggregate(avg=Avg('doubt_resolution'))['avg'] or 0,
                'overall': completed_feedback.aggregate(avg=Avg('overall_score'))['avg'] or 0,
            }
            
            # Round all scores to 2 decimal places
            for key in feedback_scores:
                feedback_scores[key] = round(feedback_scores[key], 2)
            
            context['feedback_scores'] = feedback_scores
            
            # Rating distribution for overall score
            rating_distribution = {}
            for rating in range(1, 6):
                count = completed_feedback.filter(overall_score__gte=rating, overall_score__lt=rating+1).count()
                rating_distribution[rating] = count
            
            context['feedback_rating_distribution'] = rating_distribution
            
            # Calculate percentages for each rating
            total_completed = context['feedback_completed']
            rating_percentages = {}
            for rating, count in rating_distribution.items():
                rating_percentages[rating] = round((count / total_completed * 100) if total_completed > 0 else 0, 1)
            context['feedback_rating_percentages'] = rating_percentages
            
            # Feedback trends (last 30 days vs previous 30 days)
            sixty_days_ago = today - timedelta(days=60)
            
            recent_feedback = completed_feedback.filter(submitted_at__gte=thirty_days_ago)
            previous_feedback = completed_feedback.filter(
                submitted_at__gte=sixty_days_ago,
                submitted_at__lt=thirty_days_ago
            )
            
            recent_avg = recent_feedback.aggregate(avg=Avg('overall_score'))['avg'] or 0
            previous_avg = previous_feedback.aggregate(avg=Avg('overall_score'))['avg'] or 0
            
            feedback_trend = 'stable'
            feedback_trend_change = 0
            if previous_avg > 0:
                feedback_trend_change = round(((recent_avg - previous_avg) / previous_avg * 100), 1)
                if feedback_trend_change > 5:
                    feedback_trend = 'improving'
                elif feedback_trend_change < -5:
                    feedback_trend = 'declining'
            
            context['feedback_trend'] = feedback_trend
            context['feedback_trend_change'] = feedback_trend_change
            context['recent_feedback_avg'] = round(recent_avg, 2)
            context['previous_feedback_avg'] = round(previous_avg, 2)
            
            # Strengths and weaknesses analysis
            strengths = []
            weaknesses = []
            
            for key, value in feedback_scores.items():
                if key == 'overall':
                    continue
                
                label_map = {
                    'teaching_quality': 'Teaching Quality',
                    'subject_knowledge': 'Subject Knowledge',
                    'explanation_clarity': 'Explanation Clarity',
                    'student_engagement': 'Student Engagement',
                    'doubt_resolution': 'Doubt Resolution'
                }
                
                if value >= 4.5:
                    strengths.append({
                        'area': label_map[key],
                        'score': value,
                        'message': f'Excellent performance in {label_map[key].lower()}'
                    })
                elif value < 3.0:
                    weaknesses.append({
                        'area': label_map[key],
                        'score': value,
                        'message': f'Needs improvement in {label_map[key].lower()}'
                    })
            
            context['feedback_strengths'] = strengths
            context['feedback_weaknesses'] = weaknesses
            
            # Student satisfaction level
            overall_avg = feedback_scores['overall']
            if overall_avg >= 4.5:
                satisfaction_level = 'Excellent'
                satisfaction_color = 'success'
                satisfaction_message = 'Students are highly satisfied with teaching quality'
            elif overall_avg >= 4.0:
                satisfaction_level = 'Very Good'
                satisfaction_color = 'success'
                satisfaction_message = 'Students are very satisfied with teaching quality'
            elif overall_avg >= 3.5:
                satisfaction_level = 'Good'
                satisfaction_color = 'info'
                satisfaction_message = 'Students are satisfied with teaching quality'
            elif overall_avg >= 3.0:
                satisfaction_level = 'Satisfactory'
                satisfaction_color = 'warning'
                satisfaction_message = 'Teaching quality meets basic expectations'
            else:
                satisfaction_level = 'Needs Improvement'
                satisfaction_color = 'error'
                satisfaction_message = 'Teaching quality requires significant improvement'
            
            context['satisfaction_level'] = satisfaction_level
            context['satisfaction_color'] = satisfaction_color
            context['satisfaction_message'] = satisfaction_message
            
            # Recent feedback with comments
            recent_feedback_with_comments = completed_feedback.exclude(
                comments=''
            ).order_by('-submitted_at')[:5]
            context['recent_feedback_comments'] = recent_feedback_with_comments
            
            # Feedback insights
            feedback_insights = []
            
            # Insight 1: Overall feedback score
            if overall_avg >= 4.5:
                feedback_insights.append({
                    'type': 'success',
                    'title': 'Outstanding Student Feedback',
                    'message': f'Average rating of {overall_avg:.2f}/5 from {context["feedback_completed"]} students. Exceptional teaching quality!'
                })
            elif overall_avg >= 4.0:
                feedback_insights.append({
                    'type': 'success',
                    'title': 'Excellent Student Feedback',
                    'message': f'Average rating of {overall_avg:.2f}/5. Students highly appreciate your teaching.'
                })
            elif overall_avg >= 3.0:
                feedback_insights.append({
                    'type': 'info',
                    'title': 'Good Student Feedback',
                    'message': f'Average rating of {overall_avg:.2f}/5. Room for improvement in some areas.'
                })
            else:
                feedback_insights.append({
                    'type': 'warning',
                    'title': 'Feedback Needs Attention',
                    'message': f'Average rating of {overall_avg:.2f}/5. Focus on improving teaching quality.'
                })
            
            # Insight 2: Feedback completion rate
            if context['feedback_completion_rate'] < 50:
                feedback_insights.append({
                    'type': 'warning',
                    'title': 'Low Feedback Response Rate',
                    'message': f'Only {context["feedback_completion_rate"]}% of students have submitted feedback. Encourage more participation.'
                })
            
            # Insight 3: Trend analysis
            if feedback_trend == 'improving':
                feedback_insights.append({
                    'type': 'success',
                    'title': 'Improving Feedback Trend',
                    'message': f'Feedback scores improved by {feedback_trend_change}% in the last 30 days. Great progress!'
                })
            elif feedback_trend == 'declining':
                feedback_insights.append({
                    'type': 'error',
                    'title': 'Declining Feedback Trend',
                    'message': f'Feedback scores declined by {abs(feedback_trend_change)}% in the last 30 days. Needs attention.'
                })
            
            # Insight 4: Specific weaknesses
            if weaknesses:
                weak_areas = ', '.join([w['area'] for w in weaknesses])
                feedback_insights.append({
                    'type': 'warning',
                    'title': 'Areas for Improvement',
                    'message': f'Focus on improving: {weak_areas}'
                })
            
            context['feedback_insights'] = feedback_insights
            
            # Feedback recommendations
            feedback_recommendations = []
            
            if feedback_scores['teaching_quality'] < 4.0:
                feedback_recommendations.append({
                    'priority': 'high',
                    'category': 'Teaching Quality',
                    'action': 'Enhance teaching methods with interactive activities and real-world examples',
                    'impact': 'Improve student engagement and understanding'
                })
            
            if feedback_scores['explanation_clarity'] < 4.0:
                feedback_recommendations.append({
                    'priority': 'high',
                    'category': 'Explanation Clarity',
                    'action': 'Break down complex topics into simpler concepts. Use visual aids and diagrams.',
                    'impact': 'Better comprehension and reduced confusion'
                })
            
            if feedback_scores['student_engagement'] < 4.0:
                feedback_recommendations.append({
                    'priority': 'medium',
                    'category': 'Student Engagement',
                    'action': 'Incorporate more interactive sessions, Q&A, and hands-on practice',
                    'impact': 'Increased student participation and motivation'
                })
            
            if feedback_scores['doubt_resolution'] < 4.0:
                feedback_recommendations.append({
                    'priority': 'medium',
                    'category': 'Doubt Resolution',
                    'action': 'Allocate dedicated time for doubt clearing. Encourage questions during sessions.',
                    'impact': 'Better understanding and student confidence'
                })
            
            if context['feedback_completion_rate'] < 70:
                feedback_recommendations.append({
                    'priority': 'low',
                    'category': 'Feedback Collection',
                    'action': 'Request more students to provide feedback. Follow up with pending responses.',
                    'impact': 'More comprehensive feedback data for improvement'
                })
            
            if overall_avg >= 4.5:
                feedback_recommendations.append({
                    'priority': 'positive',
                    'category': 'Recognition',
                    'action': 'Excellent work! Continue maintaining high teaching standards.',
                    'impact': 'Sustained student satisfaction and learning outcomes'
                })
            
            context['feedback_recommendations'] = feedback_recommendations
            
        else:
            # No completed feedback yet
            context['feedback_scores'] = None
            context['feedback_insights'] = [{
                'type': 'info',
                'title': 'No Feedback Data',
                'message': 'No student feedback has been submitted yet. Request students to provide feedback.'
            }]
            context['feedback_recommendations'] = [{
                'priority': 'high',
                'category': 'Feedback Collection',
                'action': 'Create feedback requests and send them to students via WhatsApp',
                'impact': 'Gather valuable insights to improve teaching quality'
            }]
        
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
        from django.shortcuts import redirect
        
        report_type = self.kwargs.get('report_type')
        object_id = self.kwargs.get('object_id')
        
        # Redirect to appropriate report view with print parameter
        if report_type == 'center':
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


# Master Account Dashboard

class MasterAccountDashboardView(MasterAccountRequiredMixin, TemplateView):
    """
    Master Account Dashboard - Redirects to insights page as default.
    """
    
    def get(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        # Redirect master account to insights page by default
        return redirect('reports:insights')
    
    def get_context_data_old(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        from datetime import timedelta
        from apps.attendance.models import AttendanceRecord
        
        # Get all centers
        centers = Center.objects.filter(deleted_at__isnull=True).order_by('name')
        context['centers'] = centers
        
        # Get selected center from session or URL
        center_id = self.request.GET.get('center') or self.request.session.get('master_selected_center')
        selected_center = None
        
        if center_id:
            selected_center = Center.objects.filter(id=center_id, deleted_at__isnull=True).first()
            if selected_center:
                self.request.session['master_selected_center'] = center_id
        
        context['selected_center'] = selected_center
        
        # Get overall summary across all centers
        summary = calculate_all_centers_summary()
        context['overall_summary'] = summary
        
        # Get all center metrics for comparison and analytics
        all_center_metrics = calculate_center_metrics()
        context['all_center_metrics'] = all_center_metrics
        
        # Identify centers at risk (low attendance, inactive students, low faculty)
        centers_at_risk = []
        high_performing_centers = []
        
        for metric in all_center_metrics:
            risk_score = 0
            risk_factors = []
            
            # Check attendance rate
            if metric['attendance']['attendance_rate'] < 70:
                risk_score += 3
                risk_factors.append(f"Low attendance ({metric['attendance']['attendance_rate']:.1f}%)")
            
            # Check inactive students ratio
            if metric['students']['total'] > 0:
                inactive_ratio = (metric['students']['inactive'] / metric['students']['total']) * 100
                if inactive_ratio > 30:
                    risk_score += 2
                    risk_factors.append(f"High inactive students ({inactive_ratio:.0f}%)")
            
            # Check faculty to student ratio
            if metric['students']['total'] > 0 and metric['faculty']['total'] > 0:
                ratio = metric['students']['total'] / metric['faculty']['total']
                if ratio > 20:  # More than 20 students per faculty
                    risk_score += 2
                    risk_factors.append(f"High student-faculty ratio ({ratio:.1f}:1)")
            elif metric['students']['total'] > 0 and metric['faculty']['total'] == 0:
                risk_score += 3
                risk_factors.append("No active faculty")
            
            # Check recent activity (last 7 days)
            if metric['attendance']['this_week'] == 0:
                risk_score += 2
                risk_factors.append("No attendance this week")
            
            if risk_score >= 4:
                centers_at_risk.append({
                    'center': metric['center_name'],
                    'center_id': metric['center_id'],
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'metrics': metric
                })
            elif metric['attendance']['attendance_rate'] >= 85 and metric['students']['active'] > 10:
                high_performing_centers.append({
                    'center': metric['center_name'],
                    'center_id': metric['center_id'],
                    'attendance_rate': metric['attendance']['attendance_rate'],
                    'active_students': metric['students']['active']
                })
        
        # Sort by risk score
        centers_at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        high_performing_centers.sort(key=lambda x: x['attendance_rate'], reverse=True)
        
        context['centers_at_risk'] = centers_at_risk[:5]  # Top 5 at-risk centers
        context['high_performing_centers'] = high_performing_centers[:5]  # Top 5 performing
        
        # Calculate growth trends (compare last 30 days vs previous 30 days)
        today = timezone.now().date()
        last_30_days_start = today - timedelta(days=30)
        previous_30_days_start = today - timedelta(days=60)
        previous_30_days_end = today - timedelta(days=31)
        
        # Overall attendance trend
        recent_attendance = AttendanceRecord.objects.filter(
            date__gte=last_30_days_start,
            date__lte=today
        ).count()
        
        previous_attendance = AttendanceRecord.objects.filter(
            date__gte=previous_30_days_start,
            date__lte=previous_30_days_end
        ).count()
        
        if previous_attendance > 0:
            attendance_growth = ((recent_attendance - previous_attendance) / previous_attendance) * 100
        else:
            attendance_growth = 100 if recent_attendance > 0 else 0
        
        context['attendance_growth'] = attendance_growth
        
        # Student enrollment trend
        recent_students = Student.objects.filter(
            created_at__gte=last_30_days_start,
            deleted_at__isnull=True
        ).count()
        
        previous_students = Student.objects.filter(
            created_at__gte=previous_30_days_start,
            created_at__lte=previous_30_days_end,
            deleted_at__isnull=True
        ).count()
        
        if previous_students > 0:
            student_growth = ((recent_students - previous_students) / previous_students) * 100
        else:
            student_growth = 100 if recent_students > 0 else 0
        
        context['student_growth'] = student_growth
        context['recent_students_count'] = recent_students
        
        # If a center is selected, get its detailed statistics
        if selected_center:
            # Get center metrics
            metrics = calculate_center_metrics(selected_center)[0]
            context['metrics'] = metrics
            
            # Get faculty list for the center
            faculty_list = Faculty.objects.filter(
                center=selected_center,
                deleted_at__isnull=True
            ).select_related('user').annotate(
                student_count=Count('assignments', filter=Q(assignments__is_active=True, assignments__deleted_at__isnull=True), distinct=True),
                session_count=Count('assignments__attendance_records', distinct=True)
            ).order_by('-is_active', 'user__first_name')[:10]
            
            context['faculty_list'] = faculty_list
            
            # Get recent activity
            recent_activity = AttendanceRecord.objects.filter(
                student__center=selected_center
            ).select_related(
                'student', 'assignment__subject', 'marked_by'
            ).order_by('-date', '-in_time')[:10]
            context['recent_activity'] = recent_activity
            
            # Get students needing attention (no attendance in last 14 days)
            two_weeks_ago = today - timedelta(days=14)
            students_with_recent_attendance = AttendanceRecord.objects.filter(
                student__center=selected_center,
                date__gte=two_weeks_ago
            ).values_list('student_id', flat=True).distinct()
            
            students_needing_attention = Student.objects.filter(
                center=selected_center,
                status='active',
                deleted_at__isnull=True
            ).exclude(
                id__in=students_with_recent_attendance
            ).annotate(
                last_attendance=Max('attendance_records__date')
            ).order_by('last_attendance')[:10]
            
            context['students_needing_attention'] = students_needing_attention
            
            # Prepare chart data for attendance trend (last 30 days)
            attendance_trend_data = prepare_attendance_trend_data(center=selected_center, days=30)
            context['attendance_trend_json'] = json.dumps(attendance_trend_data)
        
        return context


class MasterFacultyListView(MasterAccountRequiredMixin, ListView):
    """
    Faculty list view for master account with center filter and search.
    """
    model = Faculty
    template_name = 'reports/master_faculty_list.html'
    context_object_name = 'faculty_members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Faculty.objects.filter(deleted_at__isnull=True).select_related(
            'user', 'center'
        ).annotate(
            student_count=Count('assignments', filter=Q(assignments__is_active=True, assignments__deleted_at__isnull=True), distinct=True),
            session_count=Count('assignments__attendance_records', distinct=True)
        )
        
        # Filter by center
        center_id = self.request.GET.get('center')
        if center_id:
            queryset = queryset.filter(center_id=center_id)
        
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
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-is_active', 'user__first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all centers for filter
        context['centers'] = Center.objects.filter(deleted_at__isnull=True).order_by('name')
        
        # Get filter values
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['center_filter'] = self.request.GET.get('center', '')
        
        # Get selected center
        center_id = self.request.GET.get('center')
        if center_id:
            context['selected_center'] = Center.objects.filter(id=center_id, deleted_at__isnull=True).first()
        
        return context


class MasterStudentSearchView(MasterAccountRequiredMixin, TemplateView):
    """
    Student search view for master account.
    Allows searching students across a selected center.
    """
    template_name = 'reports/master_student_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all centers
        context['centers'] = Center.objects.filter(deleted_at__isnull=True).order_by('name')
        
        # Get search parameters
        center_id = self.request.GET.get('center')
        search_query = self.request.GET.get('search', '').strip()
        
        context['center_filter'] = center_id
        context['search_query'] = search_query
        
        # Get selected center
        selected_center = None
        if center_id:
            selected_center = Center.objects.filter(id=center_id, deleted_at__isnull=True).first()
            context['selected_center'] = selected_center
        
        # Perform search if both center and query are provided
        students = []
        if selected_center and search_query:
            from apps.attendance.models import AttendanceRecord
            from django.db.models import Count, Sum, Max
            
            students = Student.objects.filter(
                center=selected_center,
                deleted_at__isnull=True
            ).filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(enrollment_number__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(guardian_name__icontains=search_query) |
                Q(guardian_phone__icontains=search_query)
            ).annotate(
                total_sessions=Count('attendance_records'),
                total_hours=Sum('attendance_records__duration_minutes'),
                last_session=Max('attendance_records__date')
            ).order_by('first_name', 'last_name')[:50]  # Limit to 50 results
        
        context['students'] = students
        context['student_count'] = len(students)
        
        return context
