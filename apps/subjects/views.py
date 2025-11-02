"""
Views for subject and topic management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count

from apps.core.mixins import SetCreatedByMixin, AuditLogMixin, CenterHeadRequiredMixin
from .models import Subject, Topic
from .forms import SubjectForm, TopicForm


class AddTopicView(LoginRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """
    View to add a new topic.
    """
    model = Topic
    form_class = TopicForm
    template_name = 'subjects/add_topic.html'
    success_url = reverse_lazy('subjects:topic_list')
    audit_action = 'CREATE'
    
    def get_initial(self):
        """Pre-populate subject if provided in URL."""
        initial = super().get_initial()
        subject_id = self.request.GET.get('subject')
        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id, deleted_at__isnull=True)
                initial['subject'] = subject
                # Auto-calculate next sequence number
                last_topic = Topic.objects.filter(subject=subject).order_by('-sequence_number').first()
                if last_topic:
                    initial['sequence_number'] = last_topic.sequence_number + 1
                else:
                    initial['sequence_number'] = 1
            except Subject.DoesNotExist:
                pass
        return initial
    
    def get_success_url(self):
        """Redirect back to subject detail if subject was provided."""
        subject_id = self.request.GET.get('subject')
        if subject_id:
            return reverse_lazy('subjects:detail', kwargs={'pk': subject_id})
        return self.success_url
    
    def form_valid(self, form):
        messages.success(self.request, f'Topic "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class TopicListView(LoginRequiredMixin, ListView):
    """
    View to list all topics.
    """
    model = Topic
    template_name = 'subjects/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 20
    
    def get_queryset(self):
        return Topic.objects.filter(
            is_active=True
        ).select_related('subject').order_by('subject', 'sequence_number')


# Subject CRUD Views for Center Heads

class SubjectListView(LoginRequiredMixin, CenterHeadRequiredMixin, ListView):
    """List all subjects (common across all centers)."""
    model = Subject
    template_name = 'subjects/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 20
    
    def get_queryset(self):
        # Subjects are common across all centers
        queryset = Subject.objects.filter(
            deleted_at__isnull=True
        ).annotate(
            topic_count=Count('topics', distinct=True),
            assignment_count=Count('assignments', distinct=True)
        )
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by active status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class SubjectCreateView(LoginRequiredMixin, CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Create a new subject (common across all centers)."""
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_form.html'
    success_url = reverse_lazy('subjects:list')
    audit_action = 'CREATE'
    
    def form_valid(self, form):
        messages.success(self.request, f'Subject "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class SubjectDetailView(LoginRequiredMixin, CenterHeadRequiredMixin, DetailView):
    """View subject details."""
    model = Subject
    template_name = 'subjects/subject_detail.html'
    context_object_name = 'subject'
    
    def get_queryset(self):
        return Subject.objects.filter(
            deleted_at__isnull=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get topics for this subject
        context['topics'] = Topic.objects.filter(
            subject=self.object,
            is_active=True
        ).order_by('sequence_number')
        
        # Get assignments
        from apps.subjects.models import Assignment
        context['assignments'] = Assignment.objects.filter(
            subject=self.object,
            is_active=True
        ).select_related('student', 'faculty__user')
        
        return context


class SubjectUpdateView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, UpdateView):
    """Update subject information."""
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_form.html'
    audit_action = 'UPDATE'
    
    def get_queryset(self):
        return Subject.objects.filter(
            deleted_at__isnull=True
        )
    
    def get_success_url(self):
        return reverse_lazy('subjects:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Subject "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
