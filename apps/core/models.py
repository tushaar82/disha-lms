"""
Core models for Disha LMS.
Provides base models for event sourcing and audit trail.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model providing created/modified timestamps and user tracking.
    All models should inherit from this for audit trail compliance.
    
    Implements Constitution Principle II: Evidence-Based & Event-Sourced Architecture
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        help_text="User who created this record"
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_modified',
        help_text="User who last modified this record"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Override save to ensure created_by is set on creation."""
        # Note: created_by and modified_by should be set in views/forms
        super().save(*args, **kwargs)


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted records by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """
    Abstract base model providing soft-delete functionality.
    Records are never hard-deleted to maintain audit trail.
    
    Implements Constitution Principle II: Evidence-Based & Event-Sourced Architecture
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted'
    )
    
    objects = SoftDeleteManager()  # Default manager excludes deleted
    all_objects = models.Manager()  # Includes deleted records
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user):
        """
        Soft delete this record.
        
        Args:
            user: The user performing the deletion
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()


class AuditLog(models.Model):
    """
    Immutable audit log for all critical operations.
    Captures complete before/after state for event replay.
    
    Implements Constitution Principle II: Evidence-Based & Event-Sourced Architecture
    Implements Constitution Principle III: Explainability & Transparency
    """
    
    # Who performed the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # What action was performed
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ACCESS', 'Access'),
        ('EXPORT', 'Export'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.IntegerField(db_index=True)
    object_repr = models.CharField(max_length=200)
    
    # Changes (JSON field for before/after state)
    changes = models.JSONField(
        help_text="Before/after state for event replay",
        default=dict
    )
    
    # Why (reason for the action)
    reason = models.TextField(blank=True, help_text="Reason for the action")
    
    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Context
    request_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} {self.model_name} #{self.object_id} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, obj, changes=None, reason='', request=None):
        """
        Create an audit log entry.
        
        Args:
            user: User performing the action
            action: Action type (CREATE, UPDATE, DELETE, etc.)
            obj: The object being acted upon
            changes: Dict with 'before' and 'after' states
            reason: Reason for the action
            request: HTTP request object (optional)
        """
        ip_address = None
        user_agent = ''
        request_path = ''
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            request_path = request.path
        
        return cls.objects.create(
            user=user,
            action=action,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj)[:200],
            changes=changes or {},
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
        )
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class Notification(models.Model):
    """
    Notification model for user notifications.
    Supports different notification types and action URLs.
    """
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )
    is_read = models.BooleanField(default=False, db_index=True)
    action_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class Task(models.Model):
    """
    Task model for tracking action items and follow-ups.
    Supports different task types, priorities, and statuses.
    """
    
    TASK_TYPES = [
        ('follow_up', 'Follow Up'),
        ('approval', 'Approval'),
        ('review', 'Review'),
        ('action', 'Action Required'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPES,
        default='action'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    related_center = models.ForeignKey(
        'centers.Center',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    due_date = models.DateField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modified_tasks'
    )
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['priority', 'due_date']
        indexes = [
            models.Index(fields=['assigned_to', 'status', 'priority']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.email}"
    
    def mark_completed(self):
        """Mark task as completed."""
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False
