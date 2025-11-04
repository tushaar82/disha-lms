"""
AI-powered analytics module for Disha LMS.
Extends existing analytics with AI capabilities for forecasting and insights.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from apps.core.ai_services import get_gemini_client, cache_ai_result, get_cached_ai_result
from apps.core.decorators import measure_performance, log_errors

logger = logging.getLogger(__name__)


# ============================================================================
# FORECASTING FUNCTIONS
# ============================================================================

@measure_performance
@log_errors
def forecast_attendance(center, days=30):
    """
    Predict attendance trends for a center.
    
    Args:
        center: Center instance
        days: Number of days to forecast
        
    Returns:
        dict: Forecast data with predictions and confidence
    """
    cache_key = f"forecast_attendance_{center.id}_{days}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.attendance.models import Attendance
        
        # Get historical attendance data (last 90 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        historical_data = []
        current_date = start_date
        
        while current_date <= end_date:
            count = Attendance.objects.filter(
                center=center,
                date=current_date,
                deleted_at__isnull=True
            ).count()
            
            historical_data.append({
                'date': current_date.isoformat(),
                'count': count
            })
            current_date += timedelta(days=1)
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available',
                'predictions': []
            }
        
        # Generate forecast
        result = client.forecast_metrics(
            historical_data=historical_data,
            periods=days,
            metric_name="attendance"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to forecast attendance: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'predictions': []
        }


@measure_performance
@log_errors
def forecast_student_performance(student):
    """
    Predict student performance and outcomes.
    
    Args:
        student: Student instance
        
    Returns:
        dict: Performance forecast with predictions
    """
    cache_key = f"forecast_student_{student.id}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.attendance.models import Attendance
        
        # Gather student data
        attendance_count = Attendance.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).count()
        
        # Get attendance history
        recent_attendance = Attendance.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).order_by('-date')[:30]
        
        student_data = {
            'total_sessions': attendance_count,
            'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
            'status': student.status,
            'recent_attendance_count': recent_attendance.count(),
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available'
            }
        
        # Generate insights
        result = client.generate_insights(
            data=student_data,
            context=f"Student performance analysis for {student.get_full_name()}"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to forecast student performance: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@measure_performance
@log_errors
def forecast_center_metrics(center, months=3):
    """
    Predict center performance metrics.
    
    Args:
        center: Center instance
        months: Number of months to forecast
        
    Returns:
        dict: Center metrics forecast
    """
    cache_key = f"forecast_center_{center.id}_{months}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.attendance.models import Attendance
        
        # Gather center metrics
        total_students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True
        ).count()
        
        active_students = Student.objects.filter(
            center=center,
            status='active',
            deleted_at__isnull=True
        ).count()
        
        total_faculty = Faculty.objects.filter(
            center=center,
            deleted_at__isnull=True,
            is_active=True
        ).count()
        
        # Recent attendance trend
        last_30_days = timezone.now().date() - timedelta(days=30)
        recent_attendance = Attendance.objects.filter(
            center=center,
            date__gte=last_30_days,
            deleted_at__isnull=True
        ).count()
        
        center_data = {
            'total_students': total_students,
            'active_students': active_students,
            'total_faculty': total_faculty,
            'recent_attendance_30d': recent_attendance,
            'center_name': center.name,
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available'
            }
        
        # Generate forecast
        result = client.generate_insights(
            data=center_data,
            context=f"Center performance forecast for {center.name} - next {months} months"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to forecast center metrics: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@measure_performance
@log_errors
def predict_at_risk_students(center):
    """
    Identify students likely to drop out or need intervention.
    
    Args:
        center: Center instance
        
    Returns:
        list: At-risk students with risk scores
    """
    cache_key = f"at_risk_students_{center.id}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.students.models import Student
        from apps.attendance.models import Attendance
        from django.db.models import Max
        
        # Get students with low recent attendance
        students = Student.objects.filter(
            center=center,
            status='active',
            deleted_at__isnull=True
        ).annotate(
            last_attendance=Max('attendance__date')
        )
        
        at_risk_list = []
        
        for student in students:
            # Calculate risk factors
            if student.last_attendance:
                days_since_last = (timezone.now().date() - student.last_attendance).days
            else:
                days_since_last = 999
            
            # Count recent attendance
            last_30_days = timezone.now().date() - timedelta(days=30)
            recent_count = Attendance.objects.filter(
                student=student,
                date__gte=last_30_days,
                deleted_at__isnull=True
            ).count()
            
            # Simple risk scoring
            risk_score = 0
            if days_since_last > 7:
                risk_score += 40
            if days_since_last > 14:
                risk_score += 30
            if recent_count < 5:
                risk_score += 30
            
            if risk_score >= 50:
                at_risk_list.append({
                    'student_id': student.id,
                    'student_name': student.get_full_name(),
                    'risk_score': min(risk_score, 100),
                    'days_since_last_attendance': days_since_last,
                    'recent_attendance_count': recent_count,
                    'risk_level': 'high' if risk_score >= 70 else 'medium'
                })
        
        result = {
            'at_risk_students': at_risk_list,
            'total_count': len(at_risk_list),
            'success': True
        }
        
        # Cache result
        cache_ai_result(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to predict at-risk students: {str(e)}")
        return {
            'at_risk_students': [],
            'total_count': 0,
            'success': False,
            'error': str(e)
        }


# ============================================================================
# INSIGHT GENERATION
# ============================================================================

@measure_performance
@log_errors
def generate_center_insights(center):
    """
    Generate AI-powered insights for a center.
    
    Args:
        center: Center instance
        
    Returns:
        dict: AI-generated insights
    """
    cache_key = f"center_insights_{center.id}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.attendance.models import Attendance
        
        # Gather comprehensive center data
        last_30_days = timezone.now().date() - timedelta(days=30)
        last_7_days = timezone.now().date() - timedelta(days=7)
        
        center_data = {
            'center_name': center.name,
            'total_students': Student.objects.filter(
                center=center, deleted_at__isnull=True
            ).count(),
            'active_students': Student.objects.filter(
                center=center, status='active', deleted_at__isnull=True
            ).count(),
            'total_faculty': Faculty.objects.filter(
                center=center, deleted_at__isnull=True, is_active=True
            ).count(),
            'attendance_last_7d': Attendance.objects.filter(
                center=center, date__gte=last_7_days, deleted_at__isnull=True
            ).count(),
            'attendance_last_30d': Attendance.objects.filter(
                center=center, date__gte=last_30_days, deleted_at__isnull=True
            ).count(),
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available',
                'insights': 'AI insights are not available. Please configure Gemini API.'
            }
        
        # Generate insights
        result = client.generate_insights(
            data=center_data,
            context=f"Comprehensive center analysis for {center.name}"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate center insights: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'insights': 'Failed to generate insights.'
        }


@measure_performance
@log_errors
def generate_student_insights(student):
    """
    Generate personalized AI insights for a student.
    
    Args:
        student: Student instance
        
    Returns:
        dict: Personalized insights
    """
    cache_key = f"student_insights_{student.id}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.attendance.models import Attendance
        
        # Gather student data
        total_sessions = Attendance.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).count()
        
        last_30_days = timezone.now().date() - timedelta(days=30)
        recent_sessions = Attendance.objects.filter(
            student=student,
            date__gte=last_30_days,
            deleted_at__isnull=True
        ).count()
        
        student_data = {
            'student_name': student.get_full_name(),
            'enrollment_number': student.enrollment_number,
            'status': student.status,
            'total_sessions': total_sessions,
            'recent_sessions_30d': recent_sessions,
            'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available'
            }
        
        # Generate insights
        result = client.generate_insights(
            data=student_data,
            context=f"Personalized learning insights for {student.get_full_name()}"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate student insights: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@measure_performance
@log_errors
def generate_faculty_insights(faculty):
    """
    Generate AI insights for faculty performance.
    
    Args:
        faculty: Faculty instance
        
    Returns:
        dict: Faculty performance insights
    """
    cache_key = f"faculty_insights_{faculty.id}"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.attendance.models import Attendance
        from apps.students.models import Student
        
        # Gather faculty data
        total_sessions = Attendance.objects.filter(
            faculty=faculty,
            deleted_at__isnull=True
        ).count()
        
        last_30_days = timezone.now().date() - timedelta(days=30)
        recent_sessions = Attendance.objects.filter(
            faculty=faculty,
            date__gte=last_30_days,
            deleted_at__isnull=True
        ).count()
        
        # Get unique students taught
        unique_students = Attendance.objects.filter(
            faculty=faculty,
            deleted_at__isnull=True
        ).values('student').distinct().count()
        
        faculty_data = {
            'faculty_name': faculty.user.get_full_name(),
            'employee_id': faculty.employee_id,
            'total_sessions': total_sessions,
            'recent_sessions_30d': recent_sessions,
            'unique_students_taught': unique_students,
            'specialization': faculty.specialization or 'General',
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available'
            }
        
        # Generate insights
        result = client.generate_insights(
            data=faculty_data,
            context=f"Teaching performance analysis for {faculty.user.get_full_name()}"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate faculty insights: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@measure_performance
@log_errors
def generate_system_insights():
    """
    Generate system-wide AI insights for master account.
    
    Returns:
        dict: System-wide insights
    """
    cache_key = "system_insights"
    cached = get_cached_ai_result(cache_key)
    
    if cached:
        return cached
    
    try:
        from apps.centers.models import Center
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.attendance.models import Attendance
        
        # Gather system-wide data
        last_30_days = timezone.now().date() - timedelta(days=30)
        
        system_data = {
            'total_centers': Center.objects.filter(deleted_at__isnull=True).count(),
            'total_students': Student.objects.filter(deleted_at__isnull=True).count(),
            'active_students': Student.objects.filter(
                status='active', deleted_at__isnull=True
            ).count(),
            'total_faculty': Faculty.objects.filter(
                deleted_at__isnull=True, is_active=True
            ).count(),
            'total_attendance_30d': Attendance.objects.filter(
                date__gte=last_30_days, deleted_at__isnull=True
            ).count(),
        }
        
        # Get AI client
        client = get_gemini_client()
        
        if not client:
            return {
                'success': False,
                'error': 'AI client not available'
            }
        
        # Generate insights
        result = client.generate_insights(
            data=system_data,
            context="System-wide performance analysis across all centers"
        )
        
        # Cache result
        if result.get('success'):
            cache_ai_result(cache_key, result, ttl=7200)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate system insights: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

@measure_performance
@log_errors
def recommend_interventions(student):
    """
    Recommend interventions for at-risk students.
    
    Args:
        student: Student instance
        
    Returns:
        list: Recommended interventions
    """
    try:
        from apps.attendance.models import Attendance
        
        # Analyze student situation
        last_attendance = Attendance.objects.filter(
            student=student,
            deleted_at__isnull=True
        ).order_by('-date').first()
        
        if last_attendance:
            days_absent = (timezone.now().date() - last_attendance.date).days
        else:
            days_absent = 999
        
        # Generate recommendations based on situation
        recommendations = []
        
        if days_absent > 14:
            recommendations.append({
                'priority': 'high',
                'title': 'Immediate Contact Required',
                'description': f'Student has been absent for {days_absent} days. Contact guardian immediately.',
                'action': 'contact_guardian'
            })
        elif days_absent > 7:
            recommendations.append({
                'priority': 'medium',
                'title': 'Follow-up Needed',
                'description': f'Student absent for {days_absent} days. Schedule follow-up call.',
                'action': 'schedule_followup'
            })
        
        # Get AI recommendations
        client = get_gemini_client()
        if client:
            analysis = {
                'student_name': student.get_full_name(),
                'days_absent': days_absent,
                'status': student.status
            }
            
            ai_result = client.generate_recommendations(analysis)
            
            if ai_result.get('success'):
                recommendations.extend(ai_result.get('recommendations', []))
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        return []


@measure_performance
@log_errors
def recommend_schedule_optimizations(center):
    """
    Recommend schedule optimizations for a center.
    
    Args:
        center: Center instance
        
    Returns:
        list: Schedule optimization recommendations
    """
    try:
        # Placeholder for schedule optimization logic
        recommendations = [
            {
                'priority': 'medium',
                'title': 'Optimize Faculty Workload',
                'description': 'Balance teaching hours across faculty members.',
                'expected_impact': 'Improved faculty satisfaction and teaching quality'
            }
        ]
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to generate schedule recommendations: {str(e)}")
        return []


@measure_performance
@log_errors
def recommend_resource_allocation(center):
    """
    Recommend resource allocation improvements.
    
    Args:
        center: Center instance
        
    Returns:
        list: Resource allocation recommendations
    """
    try:
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        
        student_count = Student.objects.filter(
            center=center,
            status='active',
            deleted_at__isnull=True
        ).count()
        
        faculty_count = Faculty.objects.filter(
            center=center,
            deleted_at__isnull=True,
            is_active=True
        ).count()
        
        recommendations = []
        
        # Student-faculty ratio analysis
        if faculty_count > 0:
            ratio = student_count / faculty_count
            
            if ratio > 20:
                recommendations.append({
                    'priority': 'high',
                    'title': 'Hire Additional Faculty',
                    'description': f'Student-faculty ratio is {ratio:.1f}:1. Consider hiring more faculty.',
                    'expected_impact': 'Improved student attention and learning outcomes'
                })
            elif ratio < 10:
                recommendations.append({
                    'priority': 'low',
                    'title': 'Optimize Faculty Utilization',
                    'description': f'Student-faculty ratio is {ratio:.1f}:1. Faculty may be underutilized.',
                    'expected_impact': 'Better resource efficiency'
                })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to generate resource recommendations: {str(e)}")
        return []
