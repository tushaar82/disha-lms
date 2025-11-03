"""
Core views for Disha LMS.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.views import View as BaseView
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Notification, Task
from .services import create_notification


def home_view(request):
    """Home page view."""
    return render(request, 'home.html')


class NotificationListView(LoginRequiredMixin, ListView):
    """
    List all notifications for the current user.
    """
    model = Notification
    template_name = 'core/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by type
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by read status
        status = self.request.GET.get('status')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'read':
            queryset = queryset.filter(is_read=True)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_filter'] = self.request.GET.get('type', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).count()
        return context


class MarkNotificationReadView(LoginRequiredMixin, BaseView):
    """
    AJAX endpoint to mark notification as read.
    """
    
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification marked as read'
        })


class MarkAllNotificationsReadView(LoginRequiredMixin, BaseView):
    """
    Mark all notifications as read for current user.
    """
    
    def post(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        messages.success(request, 'All notifications marked as read')
        return redirect('core:notification_list')


class TaskListView(LoginRequiredMixin, ListView):
    """
    List all tasks for the current user.
    """
    model = Task
    template_name = 'core/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Task.objects.filter(assigned_to=self.request.user)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by type
        task_type = self.request.GET.get('type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # Sort
        sort = self.request.GET.get('sort', 'priority')
        if sort == 'due_date':
            queryset = queryset.order_by('due_date', 'priority')
        elif sort == 'created':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('priority', 'due_date')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['priority_filter'] = self.request.GET.get('priority', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['sort'] = self.request.GET.get('sort', 'priority')
        
        # Count by status
        context['pending_count'] = Task.objects.filter(
            assigned_to=self.request.user,
            status='pending'
        ).count()
        context['in_progress_count'] = Task.objects.filter(
            assigned_to=self.request.user,
            status='in_progress'
        ).count()
        context['completed_count'] = Task.objects.filter(
            assigned_to=self.request.user,
            status='completed'
        ).count()
        
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """
    Show task details.
    """
    model = Task
    template_name = 'core/task_detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        # Users can only view their own tasks
        return Task.objects.filter(assigned_to=self.request.user)


class MarkTaskCompletedView(LoginRequiredMixin, BaseView):
    """
    Mark task as completed.
    """
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
        task.mark_completed()
        task.modified_by = request.user
        task.save()
        
        # Create notification for task creator
        if task.created_by and task.created_by != request.user:
            create_notification(
                user=task.created_by,
                title=f"Task Completed: {task.title}",
                message=f"{request.user.get_full_name()} has completed the task.",
                notification_type='success',
                action_url=f'/core/tasks/{task.id}/'
            )
        
        messages.success(request, 'Task marked as completed')
        return redirect('core:task_detail', pk=task.pk)


class UpdateTaskStatusView(LoginRequiredMixin, BaseView):
    """
    Update task status.
    """
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.modified_by = request.user
            
            if new_status == 'completed':
                task.mark_completed()
            else:
                task.save()
            
            messages.success(request, f'Task status updated to {task.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
        
        return redirect('core:task_detail', pk=task.pk)
