"""
Service functions for notifications and tasks.
"""

from django.utils import timezone
from datetime import timedelta
from .models import Notification, Task


def create_notification(user, title, message, notification_type='info', action_url=None):
    """
    Create a notification for a user.
    
    Args:
        user: User to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info/warning/error/success)
        action_url: Optional URL for action
    
    Returns:
        Notification instance
    """
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        action_url=action_url
    )
    return notification


def get_unread_notifications(user, limit=None):
    """
    Get unread notifications for a user.
    
    Args:
        user: User instance
        limit: Optional limit on number of notifications
    
    Returns:
        QuerySet of unread notifications
    """
    notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-created_at')
    
    if limit:
        notifications = notifications[:limit]
    
    return notifications


def create_task(assigned_to, title, description, task_type='action', 
                priority='medium', related_center=None, due_date=None, created_by=None):
    """
    Create a task and notify the assigned user.
    
    Args:
        assigned_to: User to assign task to
        title: Task title
        description: Task description
        task_type: Type of task (follow_up/approval/review/action)
        priority: Priority level (low/medium/high/critical)
        related_center: Optional related center
        due_date: Optional due date
        created_by: User creating the task
    
    Returns:
        Task instance
    """
    task = Task.objects.create(
        assigned_to=assigned_to,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        related_center=related_center,
        due_date=due_date,
        created_by=created_by
    )
    
    # Create notification for assigned user
    priority_emoji = {
        'low': '📋',
        'medium': '📌',
        'high': '⚠️',
        'critical': '🚨'
    }
    
    create_notification(
        user=assigned_to,
        title=f"{priority_emoji.get(priority, '📋')} New Task: {title}",
        message=f"You have been assigned a new {priority} priority task.",
        notification_type='info' if priority in ['low', 'medium'] else 'warning',
        action_url=f'/core/tasks/{task.id}/'
    )
    
    return task


def get_pending_tasks(user, limit=None):
    """
    Get pending tasks for a user.
    
    Args:
        user: User instance
        limit: Optional limit on number of tasks
    
    Returns:
        QuerySet of pending tasks
    """
    tasks = Task.objects.filter(
        assigned_to=user,
        status='pending'
    ).order_by('priority', 'due_date')
    
    if limit:
        tasks = tasks[:limit]
    
    return tasks


def auto_create_tasks_for_at_risk_centers():
    """
    Automatically create tasks for centers with low performance.
    Should be run periodically (e.g., daily cron job).
    """
    from apps.reports.services import get_low_performing_centers
    from apps.accounts.models import User
    
    # Get master account users
    master_users = User.objects.filter(is_master_account=True, is_active=True)
    
    if not master_users.exists():
        return
    
    # Get low performing centers
    low_performing = get_low_performing_centers()
    
    for center_data in low_performing:
        center = center_data['center']
        
        # Check if task already exists for this center in last 7 days
        week_ago = timezone.now().date() - timedelta(days=7)
        existing_task = Task.objects.filter(
            related_center=center,
            task_type='review',
            created_at__gte=week_ago
        ).exists()
        
        if not existing_task:
            # Create task for each master user
            for master_user in master_users:
                create_task(
                    assigned_to=master_user,
                    title=f"Review Low-Performing Center: {center.name}",
                    description=f"Center {center.name} requires attention:\n"
                                f"- Attendance Rate: {center_data['attendance_rate']}%\n"
                                f"- Satisfaction Score: {center_data['satisfaction_score']}\n"
                                f"- At-Risk Students: {center_data['at_risk_count']} ({center_data['at_risk_percentage']}%)",
                    task_type='review',
                    priority='high' if center_data['performance_score'] < 40 else 'medium',
                    related_center=center,
                    due_date=timezone.now().date() + timedelta(days=3)
                )


def auto_create_tasks_for_at_risk_students():
    """
    Automatically create tasks for at-risk students.
    Should be run periodically (e.g., daily cron job).
    """
    from apps.reports.services import get_at_risk_students
    from apps.centers.models import Center
    from apps.accounts.models import User
    
    centers = Center.objects.filter(deleted_at__isnull=True, is_active=True)
    
    for center in centers:
        # Get center head
        try:
            center_head = center.center_heads.first()
            if not center_head or not center_head.user.is_active:
                continue
        except:
            continue
        
        # Get at-risk students for this center
        at_risk = get_at_risk_students(center, days_threshold=7)
        
        if at_risk.count() > 0:
            # Check if task already exists in last 3 days
            three_days_ago = timezone.now().date() - timedelta(days=3)
            existing_task = Task.objects.filter(
                assigned_to=center_head.user,
                related_center=center,
                task_type='follow_up',
                created_at__gte=three_days_ago
            ).exists()
            
            if not existing_task:
                create_task(
                    assigned_to=center_head.user,
                    title=f"Follow Up with At-Risk Students",
                    description=f"There are {at_risk.count()} students who haven't attended in the last 7 days. "
                                f"Please reach out to them and their guardians.",
                    task_type='follow_up',
                    priority='high',
                    related_center=center,
                    due_date=timezone.now().date() + timedelta(days=2)
                )
