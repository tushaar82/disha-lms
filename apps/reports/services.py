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
        
        # Subject metrics
        subjects = Subject.objects.filter(center=c, deleted_at__isnull=True)
        total_subjects = subjects.count()
        active_subjects = subjects.filter(is_active=True).count()
        
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
    total_subjects = Subject.objects.filter(
        center__in=centers,
        deleted_at__isnull=True
    ).count()
    total_attendance = AttendanceRecord.objects.filter(
        student__center__in=centers
    ).count()
    
    return {
        'total_centers': total_centers,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_subjects': total_subjects,
        'total_attendance': total_attendance,
        'avg_students_per_center': round(total_students / total_centers, 1) if total_centers > 0 else 0,
        'avg_faculty_per_center': round(total_faculty / total_centers, 1) if total_centers > 0 else 0,
        'avg_subjects_per_center': round(total_subjects / total_centers, 1) if total_centers > 0 else 0,
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
