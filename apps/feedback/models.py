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


class FacultyFeedback(TimeStampedModel, SoftDeleteModel):
    """
    Faculty-specific feedback model.
    Stores student feedback about faculty teaching quality with 5 learning-based questions.
    """
    
    # Core relationships
    faculty = models.ForeignKey(
        'faculty.Faculty',
        on_delete=models.PROTECT,
        related_name='feedbacks'
    )
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='faculty_feedbacks'
    )
    
    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.PROTECT,
        related_name='faculty_feedbacks'
    )
    
    # Unique token for feedback access (WhatsApp link)
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique token for accessing the feedback form"
    )
    
    # 5 Learning-based questions (1-5 rating scale)
    # Q1: Teaching Quality
    teaching_quality = models.IntegerField(
        null=True,
        blank=True,
        help_text="How would you rate the faculty's teaching quality? (1-5)"
    )
    
    # Q2: Subject Knowledge
    subject_knowledge = models.IntegerField(
        null=True,
        blank=True,
        help_text="How knowledgeable is the faculty about the subject? (1-5)"
    )
    
    # Q3: Explanation Clarity
    explanation_clarity = models.IntegerField(
        null=True,
        blank=True,
        help_text="How clear are the faculty's explanations? (1-5)"
    )
    
    # Q4: Student Engagement
    student_engagement = models.IntegerField(
        null=True,
        blank=True,
        help_text="How well does the faculty engage and motivate you? (1-5)"
    )
    
    # Q5: Doubt Resolution
    doubt_resolution = models.IntegerField(
        null=True,
        blank=True,
        help_text="How effectively does the faculty resolve your doubts? (1-5)"
    )
    
    # Overall score (average of 5 questions)
    overall_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overall feedback score (1-5)"
    )
    
    # Additional feedback
    comments = models.TextField(
        blank=True,
        help_text="Additional comments or suggestions"
    )
    
    # Submission tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # WhatsApp tracking
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True)
    link_opened_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'faculty_feedbacks'
        verbose_name = 'Faculty Feedback'
        verbose_name_plural = 'Faculty Feedbacks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['faculty', 'is_completed']),
            models.Index(fields=['student', 'faculty']),
            models.Index(fields=['center', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} → {self.faculty.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Generate unique token and calculate overall score on save."""
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        
        # Calculate overall score if all questions are answered
        if all([
            self.teaching_quality,
            self.subject_knowledge,
            self.explanation_clarity,
            self.student_engagement,
            self.doubt_resolution
        ]):
            total = (
                self.teaching_quality +
                self.subject_knowledge +
                self.explanation_clarity +
                self.student_engagement +
                self.doubt_resolution
            )
            self.overall_score = round(total / 5, 2)
        
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """Mark feedback as completed."""
        if not self.is_completed:
            self.is_completed = True
            self.submitted_at = timezone.now()
            self.save()
    
    def get_whatsapp_link(self, request=None):
        """Generate WhatsApp link for sending feedback request."""
        if request:
            base_url = request.build_absolute_uri('/')[:-1]
        else:
            from django.conf import settings
            base_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
        
        feedback_url = f"{base_url}/feedback/faculty/{self.token}/"
        
        message = (
            f"Hello {self.student.first_name}! 👋\n\n"
            f"We value your feedback! Please share your experience with "
            f"{self.faculty.user.get_full_name()} by filling out this quick feedback form:\n\n"
            f"{feedback_url}\n\n"
            f"It will only take 2 minutes. Thank you! 🙏"
        )
        
        # URL encode the message
        from urllib.parse import quote
        encoded_message = quote(message)
        
        # WhatsApp link format
        whatsapp_link = f"https://wa.me/{self.student.phone}?text={encoded_message}"
        
        return whatsapp_link
