"""
Service functions for feedback and satisfaction analytics.
T183: Create satisfaction trends service
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.feedback.models import FeedbackResponse, FeedbackSurvey


def calculate_satisfaction_trends(center=None, months=6):
    """
    Calculate satisfaction trends over time.
    T183: Satisfaction trends service
    
    Args:
        center: Center object (optional)
        months: Number of months to analyze (default: 6)
    
    Returns:
        dict: Trend data with monthly averages
    """
    from apps.students.models import Student
    
    # Calculate date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # Get completed responses in date range
    responses = FeedbackResponse.objects.filter(
        is_completed=True,
        satisfaction_score__isnull=False,
        submitted_at__gte=start_date,
        submitted_at__lte=end_date,
        deleted_at__isnull=True
    ).select_related('student', 'survey')
    
    # Filter by center if provided
    if center:
        responses = responses.filter(student__center=center)
    
    # Group by month and calculate averages
    monthly_data = []
    for i in range(months):
        month_start = end_date - timedelta(days=(months - i) * 30)
        month_end = end_date - timedelta(days=(months - i - 1) * 30)
        
        month_responses = responses.filter(
            submitted_at__gte=month_start,
            submitted_at__lt=month_end
        )
        
        avg_score = month_responses.aggregate(
            avg=Avg('satisfaction_score')
        )['avg']
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'avg_satisfaction': round(avg_score, 2) if avg_score else None,
            'response_count': month_responses.count()
        })
    
    return {
        'monthly_trends': monthly_data,
        'overall_avg': responses.aggregate(avg=Avg('satisfaction_score'))['avg'],
        'total_responses': responses.count()
    }


def get_faculty_satisfaction_breakdown(center):
    """
    Get satisfaction breakdown by faculty.
    
    Args:
        center: Center object
    
    Returns:
        list: Faculty satisfaction data
    """
    from apps.faculty.models import Faculty
    
    faculty_list = Faculty.objects.filter(
        center=center,
        deleted_at__isnull=True
    ).select_related('user')
    
    breakdown = []
    for faculty in faculty_list:
        # Get students taught by this faculty
        student_ids = faculty.assignments.values_list('student_id', flat=True)
        
        # Get completed responses for these students
        responses = FeedbackResponse.objects.filter(
            student_id__in=student_ids,
            is_completed=True,
            satisfaction_score__isnull=False,
            deleted_at__isnull=True
        )
        
        if responses.exists():
            avg_satisfaction = responses.aggregate(
                avg=Avg('satisfaction_score')
            )['avg']
            
            breakdown.append({
                'faculty_id': faculty.id,
                'faculty_name': faculty.user.get_full_name(),
                'response_count': responses.count(),
                'avg_satisfaction': round(avg_satisfaction, 2)
            })
    
    # Sort by average satisfaction (descending)
    breakdown.sort(key=lambda x: x['avg_satisfaction'], reverse=True)
    
    return breakdown


def get_subject_satisfaction_breakdown(center):
    """
    Get satisfaction breakdown by subject.
    
    Args:
        center: Center object
    
    Returns:
        list: Subject satisfaction data
    """
    from apps.subjects.models import Subject
    from apps.students.models import Assignment
    
    subjects = Subject.objects.filter(
        center=center,
        deleted_at__isnull=True
    )
    
    breakdown = []
    for subject in subjects:
        # Get students assigned to this subject
        student_ids = Assignment.objects.filter(
            subject=subject,
            deleted_at__isnull=True
        ).values_list('student_id', flat=True)
        
        # Get completed responses for these students
        responses = FeedbackResponse.objects.filter(
            student_id__in=student_ids,
            is_completed=True,
            satisfaction_score__isnull=False,
            deleted_at__isnull=True
        )
        
        if responses.exists():
            avg_satisfaction = responses.aggregate(
                avg=Avg('satisfaction_score')
            )['avg']
            
            breakdown.append({
                'subject_id': subject.id,
                'subject_name': subject.name,
                'response_count': responses.count(),
                'avg_satisfaction': round(avg_satisfaction, 2)
            })
    
    # Sort by average satisfaction (descending)
    breakdown.sort(key=lambda x: x['avg_satisfaction'], reverse=True)
    
    return breakdown


def get_survey_completion_stats(survey):
    """
    Get completion statistics for a survey.
    
    Args:
        survey: FeedbackSurvey object
    
    Returns:
        dict: Completion statistics
    """
    responses = FeedbackResponse.objects.filter(
        survey=survey,
        deleted_at__isnull=True
    )
    
    total = responses.count()
    completed = responses.filter(is_completed=True).count()
    pending = responses.filter(is_completed=False).count()
    
    # Email statistics
    sent = responses.filter(email_sent_at__isnull=False).count()
    opened = responses.filter(email_opened_at__isnull=False).count()
    
    return {
        'total_responses': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': (completed / total * 100) if total > 0 else 0,
        'emails_sent': sent,
        'emails_opened': opened,
        'open_rate': (opened / sent * 100) if sent > 0 else 0
    }


def prepare_satisfaction_chart_data(center, months=6):
    """
    Prepare chart data for satisfaction trends visualization.
    
    Args:
        center: Center object
        months: Number of months (default: 6)
    
    Returns:
        list: Chart data in Google Charts format
    """
    trends = calculate_satisfaction_trends(center, months)
    
    # Prepare data for Google Charts
    chart_data = [['Month', 'Avg Satisfaction', 'Responses']]
    
    for item in trends['monthly_trends']:
        chart_data.append([
            item['month'],
            item['avg_satisfaction'] or 0,
            item['response_count']
        ])
    
    return chart_data
