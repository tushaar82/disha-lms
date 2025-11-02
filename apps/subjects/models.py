"""
Subject, Topic, and Assignment models for Disha LMS.
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Subject(TimeStampedModel, SoftDeleteModel):
    """
    Subject model.
    Represents a subject that is common across all centers.
    """
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Topic(TimeStampedModel, SoftDeleteModel):
    """
    Topic model.
    Represents a topic within a subject.
    """
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sequence_number = models.IntegerField(
        default=0,
        help_text="Order in which topics should be taught"
    )
    
    # Estimated duration in minutes
    estimated_duration = models.IntegerField(
        default=60,
        help_text="Estimated time to cover this topic (in minutes)"
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'topics'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        ordering = ['subject', 'sequence_number', 'name']
        indexes = [
            models.Index(fields=['subject', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class Assignment(TimeStampedModel, SoftDeleteModel):
    """
    Assignment model.
    Links a student to a subject with a faculty member.
    """
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    
    faculty = models.ForeignKey(
        'faculty.Faculty',
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'assignments'
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['faculty', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
        ]
        unique_together = [['student', 'subject', 'faculty', 'start_date']]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name} ({self.faculty.user.get_full_name()})"
