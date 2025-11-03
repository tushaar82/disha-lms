"""
Service functions for calculating metrics and generating reports.
T124: Center metrics
T136: Attendance/learning velocity services
T137: Insights services (at-risk, extended, nearing completion)
T138: Chart data preparation services
"""

from django.db.models import Count, Q, Avg, Sum, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta, date
from apps.centers.models import Center
from apps.students.models import Student
from apps.faculty.models import Faculty
from apps.subjects.models import Subject, Assignment
from apps.attendance.models import AttendanceRecord


def calculate_center_metrics(center=None):
    """
    Calculate comprehensive metrics for a center or all centers.
    
    Args:
        center: Center instance or None for all centers
    
    Returns:
        dict: Metrics including students, faculty, subjects, attendance
    """
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    if center:
        centers = [center]
    else:
        centers = Center.objects.filter(deleted_at__isnull=True, is_active=True)
    
    metrics = []
    
    for c in centers:
        # Student metrics
        students = Student.objects.filter(center=c, deleted_at__isnull=True)
        total_students = students.count()
        active_students = students.filter(status='active').count()
        inactive_students = students.filter(status='inactive').count()
        completed_students = students.filter(status='completed').count()
        
        # Faculty metrics
        faculty = Faculty.objects.filter(center=c, deleted_at__isnull=True)
        total_faculty = faculty.count()
        active_faculty = faculty.filter(is_active=True).count()
        
        # Subject metrics (subjects being taught at this center through assignments)
        subjects_in_center = Assignment.objects.filter(
            student__center=c,
            deleted_at__isnull=True
        ).values('subject').distinct()
        total_subjects = subjects_in_center.count()
        
        active_subjects = Assignment.objects.filter(
            student__center=c,
            deleted_at__isnull=True,
            is_active=True
        ).values('subject').distinct().count()
        
        # Attendance metrics
        attendance_records = AttendanceRecord.objects.filter(
            student__center=c
        )
        total_attendance = attendance_records.count()
        attendance_this_week = attendance_records.filter(date__gte=week_ago).count()
        attendance_this_month = attendance_records.filter(date__gte=month_ago).count()
        
        # Calculate average session duration (in minutes)
        avg_duration = attendance_records.aggregate(
            avg_duration=Avg('duration_minutes')
        )['avg_duration'] or 0
        
        # Attendance rate (this month)
        if active_students > 0:
            # Expected attendance: active students * days in month
            days_in_month = (today - month_ago).days
            expected_attendance = active_students * days_in_month
            attendance_rate = (attendance_this_month / expected_attendance * 100) if expected_attendance > 0 else 0
        else:
            attendance_rate = 0
        
        # Students needing attention (no attendance in last 7 days)
        students_with_recent_attendance = attendance_records.filter(
            date__gte=week_ago
        ).values_list('student_id', flat=True).distinct()
        
        students_needing_attention = students.filter(
            status='active'
        ).exclude(
            id__in=students_with_recent_attendance
        ).count()
        
        metrics.append({
            'center': c,
            'center_id': c.id,
            'center_name': c.name,
            'center_code': c.code,
            'center_city': c.city,
            'center_state': c.state,
            'students': {
                'total': total_students,
                'active': active_students,
                'inactive': inactive_students,
                'completed': completed_students,
                'needing_attention': students_needing_attention,
            },
            'faculty': {
                'total': total_faculty,
                'active': active_faculty,
            },
            'subjects': {
                'total': total_subjects,
                'active': active_subjects,
            },
            'attendance': {
                'total': total_attendance,
                'this_week': attendance_this_week,
                'this_month': attendance_this_month,
                'avg_duration_minutes': round(avg_duration, 1),
                'attendance_rate': round(attendance_rate, 1),
            },
        })
    
    return metrics


def calculate_all_centers_summary():
    """
    Calculate summary metrics across all centers.
    
    Returns:
        dict: Aggregated metrics for all centers
    """
    centers = Center.objects.filter(deleted_at__isnull=True, is_active=True)
    
    total_centers = centers.count()
    total_students = Student.objects.filter(
        center__in=centers,
        deleted_at__isnull=True
    ).count()
    total_faculty = Faculty.objects.filter(
        center__in=centers,
        deleted_at__isnull=True
    ).count()
    # Count unique subjects being taught across all centers
    total_subjects = Assignment.objects.filter(
        student__center__in=centers,
        deleted_at__isnull=True
    ).values('subject').distinct().count()
    
    total_attendance = AttendanceRecord.objects.filter(
        student__center__in=centers
    ).count()
    
    # Calculate average attendance rate across all centers
    center_metrics = calculate_center_metrics()
    if center_metrics:
        avg_attendance_rate = sum(m['attendance']['attendance_rate'] for m in center_metrics) / len(center_metrics)
    else:
        avg_attendance_rate = 0
    
    return {
        'total_centers': total_centers,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_subjects': total_subjects,
        'total_attendance': total_attendance,
        'avg_students_per_center': round(total_students / total_centers, 1) if total_centers > 0 else 0,
        'avg_faculty_per_center': round(total_faculty / total_centers, 1) if total_centers > 0 else 0,
        'avg_subjects_per_center': round(total_subjects / total_centers, 1) if total_centers > 0 else 0,
        'avg_attendance_rate': round(avg_attendance_rate, 1),
    }


def get_top_performing_centers(metric='attendance_rate', limit=5):
    """
    Get top performing centers based on a specific metric.
    
    Args:
        metric: 'attendance_rate', 'total_students', 'total_attendance'
        limit: Number of centers to return
    
    Returns:
        list: Top performing centers with their metrics
    """
    all_metrics = calculate_center_metrics()
    
    # Sort based on metric
    if metric == 'attendance_rate':
        sorted_metrics = sorted(
            all_metrics,
            key=lambda x: x['attendance']['attendance_rate'],
            reverse=True
        )
    elif metric == 'total_students':
        sorted_metrics = sorted(
            all_metrics,
            key=lambda x: x['students']['total'],
            reverse=True
        )
    elif metric == 'total_attendance':
        sorted_metrics = sorted(
            all_metrics,
            key=lambda x: x['attendance']['total'],
            reverse=True
        )
    else:
        sorted_metrics = all_metrics
    
    return sorted_metrics[:limit]


# T136: Attendance and Learning Velocity Services

def calculate_attendance_velocity(student, days=30):
    """
    Calculate attendance velocity (sessions per week) for a student.
    
    Args:
        student: Student instance
        days: Number of days to look back (default 30)
    
    Returns:
        dict: Velocity metrics
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    attendance_records = AttendanceRecord.objects.filter(
        student=student,
        date__gte=start_date
    )
    
    total_sessions = attendance_records.count()
    weeks = days / 7
    sessions_per_week = total_sessions / weeks if weeks > 0 else 0
    
    # Calculate average session duration
    avg_duration = attendance_records.aggregate(
        avg=Avg('duration_minutes')
    )['avg'] or 0
    
    # Calculate total learning time
    total_minutes = attendance_records.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    
    return {
        'total_sessions': total_sessions,
        'sessions_per_week': round(sessions_per_week, 1),
        'avg_session_duration': round(avg_duration, 1),
        'total_learning_minutes': total_minutes,
        'total_learning_hours': round(total_minutes / 60, 1),
        'period_days': days,
    }


def calculate_learning_velocity(student):
    """
    Calculate learning velocity based on topics covered and time spent.
    
    Args:
        student: Student instance
    
    Returns:
        dict: Learning velocity metrics
    """
    attendance_records = AttendanceRecord.objects.filter(student=student)
    
    # Count unique topics covered
    total_topics = 0
    for record in attendance_records:
        total_topics += record.topics_covered.count()
    
    total_sessions = attendance_records.count()
    total_minutes = attendance_records.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    
    # Topics per session
    topics_per_session = total_topics / total_sessions if total_sessions > 0 else 0
    
    # Minutes per topic
    minutes_per_topic = total_minutes / total_topics if total_topics > 0 else 0
    
    return {
        'total_topics_covered': total_topics,
        'topics_per_session': round(topics_per_session, 1),
        'minutes_per_topic': round(minutes_per_topic, 1),
        'total_sessions': total_sessions,
        'total_minutes': total_minutes,
    }


# T137: Insights Services (at-risk, extended, nearing completion)

def get_at_risk_students(center=None, days_threshold=7):
    """
    Identify students at risk (no attendance in X days).
    
    Args:
        center: Center instance or None for all centers
        days_threshold: Days without attendance to be considered at-risk
    
    Returns:
        QuerySet: Students at risk
    """
    today = timezone.now().date()
    threshold_date = today - timedelta(days=days_threshold)
    
    # Get students with recent attendance
    students_with_recent_attendance = AttendanceRecord.objects.filter(
        date__gte=threshold_date
    ).values_list('student_id', flat=True).distinct()
    
    # Get active students without recent attendance
    at_risk = Student.objects.filter(
        status='active',
        deleted_at__isnull=True
    ).exclude(
        id__in=students_with_recent_attendance
    )
    
    if center:
        at_risk = at_risk.filter(center=center)
    
    # Annotate with last attendance date
    at_risk = at_risk.annotate(
        last_attendance_date=AttendanceRecord.objects.filter(
            student=F('id')
        ).order_by('-date').values('date')[:1]
    )
    
    return at_risk


def get_extended_students(center=None, months_threshold=6):
    """
    Identify students who have been enrolled for extended periods.
    
    Args:
        center: Center instance or None for all centers
        months_threshold: Months enrolled to be considered extended
    
    Returns:
        QuerySet: Extended students with metrics
    """
    today = timezone.now().date()
    threshold_date = today - timedelta(days=months_threshold * 30)
    
    extended = Student.objects.filter(
        enrollment_date__lte=threshold_date,
        status='active',
        deleted_at__isnull=True
    )
    
    if center:
        extended = extended.filter(center=center)
    
    # Annotate with enrollment duration and attendance count
    extended = extended.annotate(
        days_enrolled=ExpressionWrapper(
            timezone.now().date() - F('enrollment_date'),
            output_field=fields.DurationField()
        ),
        attendance_count=Count('attendance_records')
    )
    
    return extended.order_by('enrollment_date')


def get_nearing_completion_students(center=None, completion_threshold=80):
    """
    Identify students nearing completion based on attendance and progress.
    
    Args:
        center: Center instance or None for all centers
        completion_threshold: Percentage threshold for completion
    
    Returns:
        list: Students nearing completion with metrics
    """
    students = Student.objects.filter(
        status='active',
        deleted_at__isnull=True
    )
    
    if center:
        students = students.filter(center=center)
    
    nearing_completion = []
    
    for student in students:
        # Get total assignments and attendance
        total_assignments = Assignment.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).count()
        
        if total_assignments == 0:
            continue
        
        # Count attendance records
        attendance_count = AttendanceRecord.objects.filter(
            student=student
        ).count()
        
        # Simple completion metric: attendance per assignment
        # (In real scenario, you'd have more sophisticated completion tracking)
        if attendance_count > 0:
            # Assume average 20 sessions per subject for completion
            expected_sessions = total_assignments * 20
            completion_percentage = (attendance_count / expected_sessions * 100) if expected_sessions > 0 else 0
            
            if completion_percentage >= completion_threshold:
                nearing_completion.append({
                    'student': student,
                    'completion_percentage': round(completion_percentage, 1),
                    'attendance_count': attendance_count,
                    'total_assignments': total_assignments,
                    'days_enrolled': (timezone.now().date() - student.enrollment_date).days,
                })
    
    return sorted(nearing_completion, key=lambda x: x['completion_percentage'], reverse=True)


def get_insights_summary(center=None):
    """
    Get comprehensive insights summary for a center.
    
    Args:
        center: Center instance or None for all centers
    
    Returns:
        dict: Insights summary
    """
    at_risk = get_at_risk_students(center, days_threshold=7)
    extended = get_extended_students(center, months_threshold=6)
    nearing_completion = get_nearing_completion_students(center, completion_threshold=80)
    
    return {
        'at_risk_count': at_risk.count(),
        'at_risk_students': at_risk[:10],  # Top 10
        'extended_count': extended.count(),
        'extended_students': extended[:10],  # Top 10
        'nearing_completion_count': len(nearing_completion),
        'nearing_completion_students': nearing_completion[:10],  # Top 10
    }


# T138: Chart Data Preparation Services

def prepare_attendance_trend_data(student=None, center=None, days=30):
    """
    Prepare data for attendance trend chart.
    
    Args:
        student: Student instance (optional)
        center: Center instance (optional)
        days: Number of days to include
    
    Returns:
        list: Chart data in Google Charts format
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    # Initialize data structure
    chart_data = [['Date', 'Sessions', 'Duration (hours)']]
    
    # Get attendance records
    records = AttendanceRecord.objects.filter(date__gte=start_date)
    
    if student:
        records = records.filter(student=student)
    elif center:
        records = records.filter(student__center=center)
    
    # Group by date
    date_range = [start_date + timedelta(days=x) for x in range(days + 1)]
    
    for current_date in date_range:
        day_records = records.filter(date=current_date)
        session_count = day_records.count()
        total_duration = day_records.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        chart_data.append([
            current_date.strftime('%Y-%m-%d'),
            session_count,
            round(total_duration / 60, 1)
        ])
    
    return chart_data


def prepare_subject_completion_data(student):
    """
    Prepare data for subject completion chart.
    
    Args:
        student: Student instance
    
    Returns:
        list: Chart data in Google Charts format
    """
    chart_data = [['Subject', 'Sessions Completed', 'Progress %']]
    
    assignments = Assignment.objects.filter(
        student=student,
        deleted_at__isnull=True
    ).select_related('subject')
    
    for assignment in assignments:
        session_count = AttendanceRecord.objects.filter(
            student=student,
            assignment=assignment
        ).count()
        
        # Assume 20 sessions = 100% completion
        progress = min((session_count / 20 * 100), 100)
        
        chart_data.append([
            assignment.subject.name,
            session_count,
            round(progress, 1)
        ])
    
    return chart_data


def prepare_attendance_distribution_data(center=None, days=30):
    """
    Prepare data for attendance distribution pie chart.
    
    Args:
        center: Center instance (optional)
        days: Number of days to include
    
    Returns:
        list: Chart data in Google Charts format
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    records = AttendanceRecord.objects.filter(date__gte=start_date)
    
    if center:
        records = records.filter(student__center=center)
    
    # Group by student status
    active_students = records.filter(student__status='active').count()
    inactive_students = records.filter(student__status='inactive').count()
    completed_students = records.filter(student__status='completed').count()
    
    chart_data = [
        ['Status', 'Sessions'],
        ['Active Students', active_students],
        ['Inactive Students', inactive_students],
        ['Completed Students', completed_students],
    ]
    
    return chart_data


def prepare_faculty_performance_data(center=None):
    """
    Prepare data for faculty performance comparison.
    
    Args:
        center: Center instance (optional)
    
    Returns:
        list: Chart data in Google Charts format
    """
    chart_data = [['Faculty', 'Total Sessions', 'Avg Duration (min)', 'Students Taught']]
    
    faculty_members = Faculty.objects.filter(deleted_at__isnull=True)
    
    if center:
        faculty_members = faculty_members.filter(center=center)
    
    for faculty in faculty_members:
        # Get attendance records marked by this faculty
        records = AttendanceRecord.objects.filter(marked_by=faculty.user)
        
        total_sessions = records.count()
        avg_duration = records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0
        students_taught = records.values('student').distinct().count()
        
        if total_sessions > 0:  # Only include faculty with sessions
            chart_data.append([
                faculty.user.get_full_name(),
                total_sessions,
                round(avg_duration, 1),
                students_taught
            ])
    
    return chart_data


# New Analytics Functions for Enhanced Dashboards

def get_low_performing_centers(attendance_threshold=60, satisfaction_threshold=3.5):
    """
    Identify centers with low performance based on multiple criteria.
    
    Args:
        attendance_threshold: Minimum attendance rate percentage
        satisfaction_threshold: Minimum satisfaction score
    
    Returns:
        list: Low performing centers with metrics
    """
    center_metrics = calculate_center_metrics()
    low_performing = []
    
    for metric in center_metrics:
        center = metric['center']
        attendance_rate = metric['attendance']['attendance_rate']
        at_risk_count = metric['students']['needing_attention']
        total_students = metric['students']['active']
        
        # Calculate at-risk percentage
        at_risk_percentage = (at_risk_count / total_students * 100) if total_students > 0 else 0
        
        # Get average satisfaction from feedback
        from apps.feedback.models import FeedbackResponse
        avg_satisfaction = FeedbackResponse.objects.filter(
            survey__center=center
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Determine if low performing
        is_low_performing = (
            attendance_rate < attendance_threshold or
            avg_satisfaction < satisfaction_threshold or
            at_risk_percentage > 30
        )
        
        if is_low_performing:
            low_performing.append({
                'center': center,
                'attendance_rate': attendance_rate,
                'satisfaction_score': round(avg_satisfaction, 1),
                'at_risk_percentage': round(at_risk_percentage, 1),
                'at_risk_count': at_risk_count,
                'total_students': total_students,
                'performance_score': round((attendance_rate + avg_satisfaction * 20) / 2, 1),
            })
    
    return sorted(low_performing, key=lambda x: x['performance_score'])


def get_irregular_students(center=None, days_window=30, gap_threshold=3):
    """
    Identify students with inconsistent attendance patterns.
    
    Args:
        center: Center instance or None for all centers
        days_window: Number of days to analyze
        gap_threshold: Days gap to consider irregular
    
    Returns:
        list: Students with irregular attendance
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days_window)
    
    students = Student.objects.filter(
        status='active',
        deleted_at__isnull=True
    )
    
    if center:
        students = students.filter(center=center)
    
    irregular_students = []
    
    for student in students:
        records = AttendanceRecord.objects.filter(
            student=student,
            date__gte=start_date
        ).order_by('date')
        
        if records.count() < 2:
            continue
        
        # Calculate gaps between sessions
        dates = list(records.values_list('date', flat=True))
        gaps = []
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            gaps.append(gap)
        
        if gaps:
            max_gap = max(gaps)
            avg_gap = sum(gaps) / len(gaps)
            
            # Consider irregular if max gap > threshold or high variance
            if max_gap > gap_threshold:
                irregular_students.append({
                    'student': student,
                    'max_gap_days': max_gap,
                    'avg_gap_days': round(avg_gap, 1),
                    'total_sessions': records.count(),
                    'last_session': dates[-1] if dates else None,
                })
    
    return sorted(irregular_students, key=lambda x: x['max_gap_days'], reverse=True)


def get_delayed_students(center=None, months_threshold=6, progress_threshold=50):
    """
    Identify students enrolled for extended periods with low progress.
    
    Args:
        center: Center instance or None for all centers
        months_threshold: Months enrolled to check
        progress_threshold: Expected progress percentage
    
    Returns:
        list: Delayed students with metrics
    """
    today = timezone.now().date()
    threshold_date = today - timedelta(days=months_threshold * 30)
    
    students = Student.objects.filter(
        enrollment_date__lte=threshold_date,
        status='active',
        deleted_at__isnull=True
    )
    
    if center:
        students = students.filter(center=center)
    
    delayed_students = []
    
    for student in students:
        enrollment_days = (today - student.enrollment_date).days
        
        # Get total assignments and attendance
        from apps.subjects.models import Assignment
        total_assignments = Assignment.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).count()
        
        if total_assignments == 0:
            continue
        
        attendance_count = AttendanceRecord.objects.filter(
            student=student
        ).count()
        
        # Calculate expected sessions (assume 20 sessions per month per subject)
        months_enrolled = enrollment_days / 30
        expected_sessions = total_assignments * months_enrolled * 20 / 6  # Normalize
        actual_progress = (attendance_count / expected_sessions * 100) if expected_sessions > 0 else 0
        
        if actual_progress < progress_threshold:
            delayed_students.append({
                'student': student,
                'enrollment_days': enrollment_days,
                'months_enrolled': round(months_enrolled, 1),
                'expected_sessions': round(expected_sessions, 0),
                'actual_sessions': attendance_count,
                'progress_percentage': round(actual_progress, 1),
                'assignments_count': total_assignments,
            })
    
    return sorted(delayed_students, key=lambda x: x['progress_percentage'])


def calculate_profitability_metrics(center=None):
    """
    Calculate profitability metrics for centers.
    
    Args:
        center: Center instance or None for all centers
    
    Returns:
        dict: Profitability metrics
    """
    if center:
        centers = [center]
    else:
        centers = Center.objects.filter(deleted_at__isnull=True, is_active=True)
    
    metrics = []
    
    for c in centers:
        students = Student.objects.filter(center=c, deleted_at__isnull=True)
        faculty = Faculty.objects.filter(center=c, deleted_at__isnull=True, is_active=True)
        
        total_students = students.count()
        total_faculty = faculty.count()
        
        # Assume average fee per student per month (placeholder - should come from actual data)
        avg_fee_per_student = 5000  # INR
        monthly_revenue = total_students * avg_fee_per_student
        revenue_per_student = avg_fee_per_student
        
        # Faculty utilization: sessions conducted vs capacity
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        total_sessions = AttendanceRecord.objects.filter(
            student__center=c,
            date__gte=month_ago
        ).count()
        
        # Assume each faculty can handle 100 sessions per month
        faculty_capacity = total_faculty * 100
        faculty_utilization = (total_sessions / faculty_capacity * 100) if faculty_capacity > 0 else 0
        
        # Center occupancy: students vs capacity
        # Assume each center can handle 100 students (placeholder)
        center_capacity = 100
        center_occupancy = (total_students / center_capacity * 100) if center_capacity > 0 else 0
        
        metrics.append({
            'center': c,
            'monthly_revenue': monthly_revenue,
            'revenue_per_student': revenue_per_student,
            'faculty_utilization_rate': round(faculty_utilization, 1),
            'center_occupancy': round(min(center_occupancy, 100), 1),
            'total_students': total_students,
            'total_faculty': total_faculty,
            'sessions_this_month': total_sessions,
        })
    
    return metrics


def get_faculty_free_slots(faculty=None, center=None, date=None):
    """
    Analyze faculty schedules and return available time slots.
    
    Args:
        faculty: Faculty instance or None for all faculty
        center: Center instance to filter faculty
        date: Date to check (default today)
    
    Returns:
        list: Faculty with their free slots
    """
    if date is None:
        date = timezone.now().date()
    
    if faculty:
        faculty_members = [faculty]
    elif center:
        faculty_members = Faculty.objects.filter(center=center, deleted_at__isnull=True, is_active=True)
    else:
        faculty_members = Faculty.objects.filter(deleted_at__isnull=True, is_active=True)
    
    faculty_slots = []
    
    for f in faculty_members:
        # Get today's attendance records
        records = AttendanceRecord.objects.filter(
            marked_by=f.user,
            date=date
        ).order_by('in_time')
        
        # Define working hours (6 AM to 10 PM)
        busy_slots = []
        for record in records:
            if record.in_time and record.out_time:
                busy_slots.append({
                    'start': record.in_time,
                    'end': record.out_time,
                    'student': record.student,
                })
        
        # Calculate free slots (simplified - just show if busy or free)
        total_busy_minutes = sum([
            (slot['end'].hour * 60 + slot['end'].minute) - 
            (slot['start'].hour * 60 + slot['start'].minute)
            for slot in busy_slots
        ])
        
        # Working hours: 6 AM to 10 PM = 16 hours = 960 minutes
        total_available_minutes = 960
        free_minutes = total_available_minutes - total_busy_minutes
        
        faculty_slots.append({
            'faculty': f,
            'date': date,
            'busy_slots': busy_slots,
            'total_sessions': len(busy_slots),
            'busy_hours': round(total_busy_minutes / 60, 1),
            'free_hours': round(free_minutes / 60, 1),
            'utilization_percentage': round((total_busy_minutes / total_available_minutes * 100), 1),
        })
    
    return faculty_slots


def get_skipped_topics(student=None, center=None, days=30):
    """
    Identify topics in syllabus not covered recently.
    
    Args:
        student: Student instance
        center: Center instance
        days: Number of days to look back
    
    Returns:
        list: Skipped topics
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    from apps.subjects.models import Assignment, Topic
    
    if student:
        # Get student's assignments
        assignments = Assignment.objects.filter(
            student=student,
            is_active=True,
            deleted_at__isnull=True
        )
    elif center:
        # Get all active assignments in center
        assignments = Assignment.objects.filter(
            student__center=center,
            is_active=True,
            deleted_at__isnull=True
        )
    else:
        assignments = Assignment.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        )
    
    skipped_topics = []
    
    for assignment in assignments:
        # Get all topics for this subject
        all_topics = Topic.objects.filter(
            subject=assignment.subject,
            deleted_at__isnull=True
        )
        
        # Get covered topics in the time period
        covered_topic_ids = AttendanceRecord.objects.filter(
            student=assignment.student,
            assignment=assignment,
            date__gte=start_date
        ).values_list('topics_covered', flat=True)
        
        # Find skipped topics
        for topic in all_topics:
            if topic.id not in covered_topic_ids:
                # Check if ever covered
                ever_covered = AttendanceRecord.objects.filter(
                    student=assignment.student,
                    assignment=assignment,
                    topics_covered=topic
                ).exists()
                
                skipped_topics.append({
                    'topic': topic,
                    'subject': assignment.subject,
                    'student': assignment.student if student else None,
                    'days_skipped': days,
                    'ever_covered': ever_covered,
                })
    
    return skipped_topics


def prepare_gantt_chart_data(faculty=None, student=None, days=7):
    """
    Prepare Gantt chart data for faculty schedules or student progress.
    
    Args:
        faculty: Faculty instance for schedule
        student: Student instance for progress
        days: Number of days to include
    
    Returns:
        list: Gantt chart data in Google Charts format
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    # Format: [Task, Start Date, End Date]
    gantt_data = [['Task', 'Start', 'End']]
    
    if faculty:
        # Faculty schedule
        records = AttendanceRecord.objects.filter(
            marked_by=faculty.user,
            date__gte=start_date
        ).select_related('student', 'assignment__subject').order_by('date', 'in_time')
        
        for record in records:
            if record.in_time and record.out_time:
                task_name = f"{record.student.first_name} - {record.assignment.subject.name}"
                start_datetime = timezone.datetime.combine(record.date, record.in_time)
                end_datetime = timezone.datetime.combine(record.date, record.out_time)
                
                gantt_data.append([
                    task_name,
                    start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    end_datetime.strftime('%Y-%m-%d %H:%M:%S')
                ])
    
    elif student:
        # Student progress
        records = AttendanceRecord.objects.filter(
            student=student,
            date__gte=start_date
        ).select_related('assignment__subject').order_by('date', 'in_time')
        
        for record in records:
            if record.in_time and record.out_time:
                task_name = record.assignment.subject.name
                start_datetime = timezone.datetime.combine(record.date, record.in_time)
                end_datetime = timezone.datetime.combine(record.date, record.out_time)
                
                gantt_data.append([
                    task_name,
                    start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    end_datetime.strftime('%Y-%m-%d %H:%M:%S')
                ])
    
    return gantt_data


def prepare_heatmap_data(student, start_date=None, end_date=None):
    """
    Prepare heatmap data for student attendance calendar.
    
    Args:
        student: Student instance
        start_date: Start date (default: enrollment date or 1 year ago)
        end_date: End date (default: today)
    
    Returns:
        list: Heatmap data with intensity levels
    """
    today = timezone.now().date()
    
    if end_date is None:
        end_date = today
    
    if start_date is None:
        if student.enrollment_date:
            start_date = student.enrollment_date
        else:
            start_date = today - timedelta(days=365)
    
    # Get all attendance records
    records = AttendanceRecord.objects.filter(
        student=student,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Create date-to-hours mapping
    date_hours = {}
    for record in records:
        date_str = record.date.strftime('%Y-%m-%d')
        hours = record.duration_minutes / 60
        
        if date_str in date_hours:
            date_hours[date_str] += hours
        else:
            date_hours[date_str] = hours
    
    # Format for Google Calendar Chart: [Date, Hours]
    heatmap_data = [['Date', 'Hours']]
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        hours = date_hours.get(date_str, 0)
        
        heatmap_data.append([date_str, round(hours, 1)])
        current_date += timedelta(days=1)
    
    return heatmap_data


def get_center_performance_score(center):
    """
    Calculate overall performance score for a center.
    
    Args:
        center: Center instance
    
    Returns:
        dict: Performance score and breakdown
    """
    metrics = calculate_center_metrics(center)[0]
    
    # Get satisfaction score
    from apps.feedback.models import FeedbackResponse
    avg_satisfaction = FeedbackResponse.objects.filter(
        survey__center=center
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Calculate completion rate
    total_students = Student.objects.filter(center=center, deleted_at__isnull=True).count()
    completed_students = Student.objects.filter(center=center, status='completed', deleted_at__isnull=True).count()
    completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0
    
    # Weighted performance score
    # 40% attendance, 30% satisfaction, 30% completion
    attendance_score = metrics['attendance']['attendance_rate']
    satisfaction_score = avg_satisfaction * 20  # Convert 5-point scale to 100
    completion_score = completion_rate
    
    overall_score = (
        attendance_score * 0.4 +
        satisfaction_score * 0.3 +
        completion_score * 0.3
    )
    
    return {
        'center': center,
        'overall_score': round(overall_score, 1),
        'attendance_score': round(attendance_score, 1),
        'satisfaction_score': round(satisfaction_score, 1),
        'completion_score': round(completion_score, 1),
        'grade': 'A' if overall_score >= 80 else 'B' if overall_score >= 60 else 'C' if overall_score >= 40 else 'D',
    }
