"""
Business logic services for attendance management.
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import AttendanceRecord


def calculate_session_duration(in_time, out_time):
    """
    Calculate session duration in minutes.
    
    Args:
        in_time: Session start time (time or datetime)
        out_time: Session end time (time or datetime)
        
    Returns:
        int: Duration in minutes
    """
    from apps.core.utils import calculate_session_duration as core_calc
    return core_calc(in_time, out_time)


def check_if_backdated(date, threshold_hours=24):
    """
    Check if a date is backdated.
    
    Args:
        date: Date to check
        threshold_hours: Hours threshold (default 24)
        
    Returns:
        bool: True if backdated
    """
    from apps.core.utils import is_backdated
    return is_backdated(date, threshold_hours)


def get_today_attendance_for_faculty(faculty):
    """
    Get today's attendance records for a faculty member.
    
    Args:
        faculty: Faculty instance
        
    Returns:
        QuerySet: Attendance records for today
    """
    today = timezone.now().date()
    return AttendanceRecord.objects.filter(
        marked_by=faculty.user,
        date=today
    ).select_related('student', 'assignment__subject').prefetch_related('topics_covered')


def get_student_attendance_summary(student, start_date=None, end_date=None):
    """
    Get attendance summary for a student.
    
    Args:
        student: Student instance
        start_date: Start date (optional)
        end_date: End date (optional)
        
    Returns:
        dict: Summary with total sessions, total minutes, etc.
    """
    queryset = AttendanceRecord.objects.filter(student=student)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    summary = queryset.aggregate(
        total_sessions=Count('id'),
        total_minutes=Sum('duration_minutes')
    )
    
    return {
        'total_sessions': summary['total_sessions'] or 0,
        'total_minutes': summary['total_minutes'] or 0,
        'total_hours': round((summary['total_minutes'] or 0) / 60, 2),
    }


def get_students_absent_for_days(center, days=3):
    """
    Get students who haven't attended for specified number of days.
    
    Args:
        center: Center instance
        days: Number of days (default 3)
        
    Returns:
        QuerySet: Students who haven't attended
    """
    from apps.students.models import Student
    
    threshold_date = timezone.now().date() - timedelta(days=days)
    
    # Get students who have attendance records after threshold
    students_with_recent_attendance = AttendanceRecord.objects.filter(
        student__center=center,
        date__gte=threshold_date
    ).values_list('student_id', flat=True).distinct()
    
    # Return active students without recent attendance
    return Student.objects.filter(
        center=center,
        status='active'
    ).exclude(
        id__in=students_with_recent_attendance
    )


def get_faculty_attendance_stats(faculty, start_date=None, end_date=None):
    """
    Get attendance statistics for a faculty member.
    
    Args:
        faculty: Faculty instance
        start_date: Start date (optional)
        end_date: End date (optional)
        
    Returns:
        dict: Statistics
    """
    queryset = AttendanceRecord.objects.filter(marked_by=faculty.user)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    stats = queryset.aggregate(
        total_sessions=Count('id'),
        total_students=Count('student', distinct=True),
        total_minutes=Sum('duration_minutes'),
        backdated_count=Count('id', filter=Q(is_backdated=True))
    )
    
    return {
        'total_sessions': stats['total_sessions'] or 0,
        'total_students': stats['total_students'] or 0,
        'total_minutes': stats['total_minutes'] or 0,
        'total_hours': round((stats['total_minutes'] or 0) / 60, 2),
        'backdated_count': stats['backdated_count'] or 0,
    }
