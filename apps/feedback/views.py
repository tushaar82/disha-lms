"""
Views for feedback and survey management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count

from apps.core.mixins import CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin
from .models import FeedbackSurvey, FeedbackResponse
from .forms import SurveyForm


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
