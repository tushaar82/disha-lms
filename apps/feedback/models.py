"""
Feedback and satisfaction survey models for Disha LMS.
"""

from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel
import secrets


class FeedbackSurvey(TimeStampedModel, SoftDeleteModel):
    """
    Feedback survey model.
    Represents a satisfaction survey that can be sent to students.
    """
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Survey questions (stored as JSON)
    questions = models.JSONField(
        default=list,
        help_text="List of survey questions with type and options"
    )
    
    # Center association (optional - can be global or center-specific)
    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.PROTECT,
        related_name='surveys',
        null=True,
        blank=True,
        help_text="Leave blank for global surveys"
    )
    
    # Survey validity
    valid_from = models.DateField()
    valid_until = models.DateField()
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(
        default=False,
        help_text="Published surveys can be sent to students"
    )
    
    class Meta:
        db_table = 'feedback_surveys'
        verbose_name = 'Feedback Survey'
        verbose_name_plural = 'Feedback Surveys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_published']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        """Check if survey is currently valid."""
        today = timezone.now().date()
        return self.valid_from <= today <= self.valid_until


class FeedbackResponse(TimeStampedModel, SoftDeleteModel):
    """
    Feedback response model.
    Stores student responses to surveys.
    """
    
    survey = models.ForeignKey(
        FeedbackSurvey,
        on_delete=models.PROTECT,
        related_name='responses'
    )
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='feedback_responses'
    )
    
    # Unique token for survey access
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique token for accessing the survey"
    )
    
    # Response data (stored as JSON)
    answers = models.JSONField(
        default=dict,
        help_text="Student's answers to survey questions"
    )
    
    # Overall satisfaction score (1-5)
    satisfaction_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Overall satisfaction score (1-5)"
    )
    
    # Response metadata
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Email tracking
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_opened_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'feedback_responses'
        verbose_name = 'Feedback Response'
        verbose_name_plural = 'Feedback Responses'
        ordering = ['-created_at']
        unique_together = [['survey', 'student']]
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.survey.title}"
    
    def save(self, *args, **kwargs):
        """Generate unique token on creation."""
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """Mark response as completed."""
        if not self.is_completed:
            self.is_completed = True
            self.submitted_at = timezone.now()
            self.save()
