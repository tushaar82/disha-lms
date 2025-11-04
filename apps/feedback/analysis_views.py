"""
Faculty feedback analysis views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from apps.faculty.models import Faculty
from .models import FacultyFeedback


class FacultyFeedbackAnalysisView(LoginRequiredMixin, DetailView):
    """
    Comprehensive faculty-wise feedback analysis report.
    Shows detailed analytics for a specific faculty member.
    Accessible by:
    - Master accounts (all faculty across all centers)
    - Center heads (faculty in their center)
    - Faculty members (their own feedback + other faculty in their center)
    """
    model = Faculty
    template_name = 'feedback/faculty_feedback_analysis.html'
    context_object_name = 'faculty'
    pk_url_kwarg = 'faculty_id'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow master accounts, center heads, and faculty members
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.is_master_account or request.user.is_center_head or request.user.is_faculty_member):
            messages.error(request, 'You do not have permission to access feedback analysis.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Faculty.objects.filter(deleted_at__isnull=True)
        
        # Center heads can only view their center's faculty
        if self.request.user.is_center_head:
            if hasattr(self.request.user, 'center_head_profile'):
                queryset = queryset.filter(center=self.request.user.center_head_profile.center)
        
        # Faculty members can view their own center's faculty (including themselves)
        elif self.request.user.is_faculty_member:
            if hasattr(self.request.user, 'faculty_profile'):
                queryset = queryset.filter(center=self.request.user.faculty_profile.center)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.object
        
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        
        # Get all feedback for this faculty
        all_feedback = FacultyFeedback.objects.filter(
            faculty=faculty,
            deleted_at__isnull=True
        ).select_related('student', 'center')
        
        completed_feedback = all_feedback.filter(is_completed=True)
        
        # Basic statistics
        context['total_feedbacks'] = all_feedback.count()
        context['completed_feedbacks'] = completed_feedback.count()
        context['pending_feedbacks'] = all_feedback.filter(is_completed=False).count()
        context['completion_rate'] = round(
            (context['completed_feedbacks'] / context['total_feedbacks'] * 100) 
            if context['total_feedbacks'] > 0 else 0, 1
        )
        
        if completed_feedback.exists():
            # Average scores for each question
            feedback_scores = {
                'teaching_quality': round(completed_feedback.aggregate(avg=Avg('teaching_quality'))['avg'] or 0, 2),
                'subject_knowledge': round(completed_feedback.aggregate(avg=Avg('subject_knowledge'))['avg'] or 0, 2),
                'explanation_clarity': round(completed_feedback.aggregate(avg=Avg('explanation_clarity'))['avg'] or 0, 2),
                'student_engagement': round(completed_feedback.aggregate(avg=Avg('student_engagement'))['avg'] or 0, 2),
                'doubt_resolution': round(completed_feedback.aggregate(avg=Avg('doubt_resolution'))['avg'] or 0, 2),
                'overall': round(completed_feedback.aggregate(avg=Avg('overall_score'))['avg'] or 0, 2),
            }
            context['feedback_scores'] = feedback_scores
            
            # Time-based analysis
            last_30_days = completed_feedback.filter(submitted_at__gte=thirty_days_ago)
            last_60_days = completed_feedback.filter(submitted_at__gte=sixty_days_ago)
            
            context['feedback_last_30_days'] = last_30_days.count()
            context['feedback_last_60_days'] = last_60_days.count()
            
            # Average scores by time period
            if last_30_days.exists():
                context['avg_score_30_days'] = round(last_30_days.aggregate(avg=Avg('overall_score'))['avg'], 2)
            else:
                context['avg_score_30_days'] = None
            
            if last_60_days.exists():
                context['avg_score_60_days'] = round(last_60_days.aggregate(avg=Avg('overall_score'))['avg'], 2)
            else:
                context['avg_score_60_days'] = None
            
            # Trend analysis (30 days vs previous 30 days)
            previous_30_days = completed_feedback.filter(
                submitted_at__gte=sixty_days_ago,
                submitted_at__lt=thirty_days_ago
            )
            
            if last_30_days.exists() and previous_30_days.exists():
                recent_avg = last_30_days.aggregate(avg=Avg('overall_score'))['avg']
                previous_avg = previous_30_days.aggregate(avg=Avg('overall_score'))['avg']
                
                if previous_avg > 0:
                    trend_change = round(((recent_avg - previous_avg) / previous_avg * 100), 1)
                    if trend_change > 5:
                        trend = 'improving'
                    elif trend_change < -5:
                        trend = 'declining'
                    else:
                        trend = 'stable'
                    
                    context['feedback_trend'] = trend
                    context['feedback_trend_change'] = trend_change
                else:
                    context['feedback_trend'] = 'stable'
                    context['feedback_trend_change'] = 0
            else:
                context['feedback_trend'] = 'insufficient_data'
                context['feedback_trend_change'] = 0
            
            # Rating distribution
            rating_distribution = {}
            for rating in range(1, 6):
                count = completed_feedback.filter(
                    overall_score__gte=rating,
                    overall_score__lt=rating + 1
                ).count()
                rating_distribution[rating] = count
            
            context['rating_distribution'] = rating_distribution
            
            # Calculate percentages for rating distribution
            total_completed = context['completed_feedbacks']
            rating_percentages = {}
            for rating, count in rating_distribution.items():
                rating_percentages[rating] = round((count / total_completed * 100) if total_completed > 0 else 0, 1)
            context['rating_percentages'] = rating_percentages
            
            # Student participation analysis
            unique_students = completed_feedback.values('student').distinct().count()
            context['unique_students_feedback'] = unique_students
            
            # Average feedbacks per student
            if unique_students > 0:
                context['avg_feedbacks_per_student'] = round(
                    context['completed_feedbacks'] / unique_students, 1
                )
            else:
                context['avg_feedbacks_per_student'] = 0
            
            # Top and bottom performing areas
            scores_list = [
                ('Teaching Quality', feedback_scores['teaching_quality']),
                ('Subject Knowledge', feedback_scores['subject_knowledge']),
                ('Explanation Clarity', feedback_scores['explanation_clarity']),
                ('Student Engagement', feedback_scores['student_engagement']),
                ('Doubt Resolution', feedback_scores['doubt_resolution']),
            ]
            
            sorted_scores = sorted(scores_list, key=lambda x: x[1], reverse=True)
            context['top_strengths'] = sorted_scores[:3]
            context['areas_for_improvement'] = sorted_scores[-2:]
            
            # Recent feedback (last 10)
            context['recent_feedbacks'] = completed_feedback.order_by('-submitted_at')[:10]
            
            # Feedback with comments
            context['feedbacks_with_comments'] = completed_feedback.exclude(
                comments=''
            ).order_by('-submitted_at')[:10]
            
            # Monthly breakdown (last 6 months)
            monthly_data = []
            for i in range(6):
                month_start = today - timedelta(days=30 * (i + 1))
                month_end = today - timedelta(days=30 * i)
                
                month_feedback = completed_feedback.filter(
                    submitted_at__gte=month_start,
                    submitted_at__lt=month_end
                )
                
                if month_feedback.exists():
                    monthly_data.append({
                        'month': month_start.strftime('%b %Y'),
                        'count': month_feedback.count(),
                        'avg_score': round(month_feedback.aggregate(avg=Avg('overall_score'))['avg'], 2)
                    })
            
            context['monthly_breakdown'] = list(reversed(monthly_data))
            
            # Satisfaction level
            overall_avg = feedback_scores['overall']
            if overall_avg >= 4.5:
                satisfaction_level = 'Excellent'
                satisfaction_color = 'success'
                satisfaction_icon = '🌟'
                satisfaction_message = 'Outstanding teaching quality! Students are highly satisfied.'
            elif overall_avg >= 4.0:
                satisfaction_level = 'Very Good'
                satisfaction_color = 'success'
                satisfaction_icon = '😊'
                satisfaction_message = 'Very good teaching quality. Students are very satisfied.'
            elif overall_avg >= 3.5:
                satisfaction_level = 'Good'
                satisfaction_color = 'info'
                satisfaction_icon = '👍'
                satisfaction_message = 'Good teaching quality. Students are satisfied.'
            elif overall_avg >= 3.0:
                satisfaction_level = 'Satisfactory'
                satisfaction_color = 'warning'
                satisfaction_icon = '😐'
                satisfaction_message = 'Satisfactory teaching quality. Room for improvement.'
            else:
                satisfaction_level = 'Needs Improvement'
                satisfaction_color = 'error'
                satisfaction_icon = '⚠️'
                satisfaction_message = 'Teaching quality needs significant improvement.'
            
            context['satisfaction_level'] = satisfaction_level
            context['satisfaction_color'] = satisfaction_color
            context['satisfaction_icon'] = satisfaction_icon
            context['satisfaction_message'] = satisfaction_message
            
        else:
            # No completed feedback
            context['feedback_scores'] = None
            context['no_feedback'] = True
        
        return context
