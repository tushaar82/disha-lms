"""
Views for feedback and survey management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.core.mixins import CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin
from apps.students.models import Student
from .models import FeedbackSurvey, FeedbackResponse
from .forms import SurveyForm
from .tasks import send_survey_email, send_bulk_survey_emails


class SurveyListView(LoginRequiredMixin, CenterHeadRequiredMixin, ListView):
    """List all surveys."""
    model = FeedbackSurvey
    template_name = 'feedback/survey_list.html'
    context_object_name = 'surveys'
    paginate_by = 20
    
    def get_queryset(self):
        center = self.request.user.center_head_profile.center
        
        # Show global surveys and center-specific surveys
        queryset = FeedbackSurvey.objects.filter(
            Q(center__isnull=True) | Q(center=center),
            deleted_at__isnull=True
        ).annotate(
            response_count=Count('responses', distinct=True)
        )
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'published':
            queryset = queryset.filter(is_published=True)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class SurveyCreateView(LoginRequiredMixin, CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Create a new survey."""
    model = FeedbackSurvey
    form_class = SurveyForm
    template_name = 'feedback/survey_form.html'
    success_url = reverse_lazy('feedback:list')
    audit_action = 'CREATE'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set default center to user's center
        if not self.request.user.is_master_account:
            form.fields['center'].initial = self.request.user.center_head_profile.center
        return form
    
    def form_valid(self, form):
        messages.success(self.request, f'Survey "{form.instance.title}" created successfully!')
        return super().form_valid(form)


class SurveyDetailView(LoginRequiredMixin, CenterHeadRequiredMixin, DetailView):
    """View survey details."""
    model = FeedbackSurvey
    template_name = 'feedback/survey_detail.html'
    context_object_name = 'survey'
    
    def get_queryset(self):
        center = self.request.user.center_head_profile.center
        return FeedbackSurvey.objects.filter(
            Q(center__isnull=True) | Q(center=center),
            deleted_at__isnull=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get responses for this survey
        context['responses'] = FeedbackResponse.objects.filter(
            survey=self.object
        ).select_related('student').order_by('-created_at')
        
        # Statistics
        context['total_responses'] = context['responses'].count()
        context['completed_responses'] = context['responses'].filter(is_completed=True).count()
        context['pending_responses'] = context['responses'].filter(is_completed=False).count()
        
        # Average satisfaction score
        completed = context['responses'].filter(is_completed=True, satisfaction_score__isnull=False)
        if completed.exists():
            from django.db.models import Avg
            context['avg_satisfaction'] = completed.aggregate(avg=Avg('satisfaction_score'))['avg']
        else:
            context['avg_satisfaction'] = None
        
        return context


class SurveyUpdateView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, UpdateView):
    """Update survey information."""
    model = FeedbackSurvey
    form_class = SurveyForm
    template_name = 'feedback/survey_form.html'
    audit_action = 'UPDATE'
    
    def get_queryset(self):
        center = self.request.user.center_head_profile.center
        return FeedbackSurvey.objects.filter(
            Q(center__isnull=True) | Q(center=center),
            deleted_at__isnull=True
        )
    
    def get_success_url(self):
        return reverse_lazy('feedback:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Survey "{form.instance.title}" updated successfully!')
        return super().form_valid(form)


class SendSurveyView(LoginRequiredMixin, CenterHeadRequiredMixin, View):
    """
    Send survey emails to selected students.
    T170: Create SendSurveyView
    """
    
    def get(self, request, pk):
        """Display send survey form."""
        survey = get_object_or_404(FeedbackSurvey, pk=pk, deleted_at__isnull=True)
        
        # Get center
        center = request.user.center_head_profile.center
        
        # Get students from the center
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        ).order_by('first_name', 'last_name')
        
        # Get existing responses
        existing_responses = FeedbackResponse.objects.filter(
            survey=survey
        ).values_list('student_id', flat=True)
        
        context = {
            'survey': survey,
            'students': students,
            'existing_responses': list(existing_responses),
        }
        
        return render(request, 'feedback/send_survey.html', context)
    
    def post(self, request, pk):
        """Send survey to selected students."""
        survey = get_object_or_404(FeedbackSurvey, pk=pk, deleted_at__isnull=True)
        
        # Get selected student IDs
        student_ids = request.POST.getlist('students')
        
        if not student_ids:
            messages.error(request, 'Please select at least one student.')
            return redirect('feedback:send', pk=pk)
        
        # Validate survey is published and active
        if not survey.is_published or not survey.is_active:
            messages.error(request, 'Survey must be published and active to send.')
            return redirect('feedback:detail', pk=pk)
        
        # Send emails asynchronously
        try:
            send_bulk_survey_emails.delay(survey.id, [int(sid) for sid in student_ids])
            messages.success(
                request,
                f'Survey emails are being sent to {len(student_ids)} student(s). '
                'This may take a few minutes.'
            )
        except Exception as e:
            messages.error(request, f'Error sending surveys: {str(e)}')
        
        return redirect('feedback:detail', pk=pk)


class SubmitSurveyView(TemplateView):
    """
    Public view for students to submit survey responses.
    T174: Create SubmitSurveyView (public)
    T176: Add validation (expiry, token)
    T177: Save responses
    T178: Update student satisfaction_score
    """
    template_name = 'feedback/survey_public.html'
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, token):
        """Display survey form to student."""
        # Get response by token (T176)
        response = get_object_or_404(
            FeedbackResponse,
            token=token,
            deleted_at__isnull=True
        )
        
        # Check if already completed
        if response.is_completed:
            return render(request, 'feedback/survey_completed.html', {
                'response': response,
                'message': 'You have already completed this survey. Thank you!'
            })
        
        # Check if survey is valid (T176)
        if not response.survey.is_valid():
            return render(request, 'feedback/survey_expired.html', {
                'response': response,
                'message': 'This survey has expired.'
            })
        
        # Track email opened
        if not response.email_opened_at:
            response.email_opened_at = timezone.now()
            response.save(update_fields=['email_opened_at'])
        
        context = {
            'response': response,
            'survey': response.survey,
            'student': response.student,
            'questions': response.survey.questions,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, token):
        """Save survey responses (T177)."""
        # Get response by token
        response = get_object_or_404(
            FeedbackResponse,
            token=token,
            deleted_at__isnull=True
        )
        
        # Validate survey is still valid
        if not response.survey.is_valid():
            return JsonResponse({
                'status': 'error',
                'message': 'This survey has expired.'
            }, status=400)
        
        # Check if already completed
        if response.is_completed:
            return JsonResponse({
                'status': 'error',
                'message': 'You have already completed this survey.'
            }, status=400)
        
        # Collect answers
        answers = {}
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.replace('question_', '')
                answers[question_id] = value
        
        # Get overall satisfaction score
        satisfaction_score = request.POST.get('satisfaction_score')
        
        # Save response (T177)
        response.answers = answers
        if satisfaction_score:
            response.satisfaction_score = int(satisfaction_score)
        response.mark_completed()
        
        # Update student satisfaction score (T178)
        from .tasks import update_student_satisfaction_scores
        update_student_satisfaction_scores.delay()
        
        messages.success(request, 'Thank you for completing the survey!')
        
        return render(request, 'feedback/survey_completed.html', {
            'response': response,
            'message': 'Your feedback has been submitted successfully. Thank you!'
        })


class SurveyResponsesView(LoginRequiredMixin, CenterHeadRequiredMixin, DetailView):
    """
    View survey responses and analytics.
    T179: Create SurveyResponsesView
    T181: Add rating distribution chart
    T182: Add faculty-wise breakdown
    """
    model = FeedbackSurvey
    template_name = 'feedback/responses.html'
    context_object_name = 'survey'
    
    def get_queryset(self):
        center = self.request.user.center_head_profile.center
        return FeedbackSurvey.objects.filter(
            Q(center__isnull=True) | Q(center=center),
            deleted_at__isnull=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all responses
        responses = FeedbackResponse.objects.filter(
            survey=self.object,
            deleted_at__isnull=True
        ).select_related('student', 'student__center')
        
        # Basic statistics
        context['total_responses'] = responses.count()
        context['completed_responses'] = responses.filter(is_completed=True).count()
        context['pending_responses'] = responses.filter(is_completed=False).count()
        context['completion_rate'] = (
            (context['completed_responses'] / context['total_responses'] * 100)
            if context['total_responses'] > 0 else 0
        )
        
        # Average satisfaction score
        completed = responses.filter(is_completed=True, satisfaction_score__isnull=False)
        context['avg_satisfaction'] = completed.aggregate(avg=Avg('satisfaction_score'))['avg']
        
        # Rating distribution (T181)
        rating_distribution = {}
        for i in range(1, 6):
            count = completed.filter(satisfaction_score=i).count()
            rating_distribution[i] = count
        context['rating_distribution'] = rating_distribution
        
        # Faculty-wise breakdown (T182)
        from apps.faculty.models import Faculty
        faculty_breakdown = []
        
        for faculty in Faculty.objects.filter(
            center=self.request.user.center_head_profile.center,
            deleted_at__isnull=True
        ):
            # Get students taught by this faculty
            student_ids = faculty.assignments.values_list('student_id', flat=True)
            faculty_responses = completed.filter(student_id__in=student_ids)
            
            if faculty_responses.exists():
                faculty_breakdown.append({
                    'faculty': faculty,
                    'response_count': faculty_responses.count(),
                    'avg_satisfaction': faculty_responses.aggregate(
                        avg=Avg('satisfaction_score')
                    )['avg']
                })
        
        context['faculty_breakdown'] = sorted(
            faculty_breakdown,
            key=lambda x: x['avg_satisfaction'] or 0,
            reverse=True
        )
        
        # Recent responses
        context['recent_responses'] = responses.filter(
            is_completed=True
        ).order_by('-submitted_at')[:10]
        
        # Prepare chart data (T181)
        context['rating_chart_data'] = [
            ['Rating', 'Count'],
            ['1 Star', rating_distribution.get(1, 0)],
            ['2 Stars', rating_distribution.get(2, 0)],
            ['3 Stars', rating_distribution.get(3, 0)],
            ['4 Stars', rating_distribution.get(4, 0)],
            ['5 Stars', rating_distribution.get(5, 0)],
        ]
        
        return context
