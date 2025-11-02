"""
Attendance models for Disha LMS.
Implements event-sourced attendance tracking with immutable records.
"""

from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class AttendanceRecord(TimeStampedModel):
    """
    Attendance record model.
    Immutable event-sourced record of student attendance.
    
    Implements Constitution Principle II: Evidence-Based & Event-Sourced Architecture
    """
    
    # Who attended
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='attendance_records'
    )
    
    # What subject/assignment
    assignment = models.ForeignKey(
        'subjects.Assignment',
        on_delete=models.PROTECT,
        related_name='attendance_records'
    )
    
    # When
    date = models.DateField(db_index=True)
    in_time = models.TimeField()
    out_time = models.TimeField()
    
    # Session duration in minutes (calculated)
    duration_minutes = models.IntegerField(
        help_text="Session duration in minutes"
    )
    
    # What was taught
    topics_covered = models.ManyToManyField(
        'subjects.Topic',
        related_name='attendance_records',
        blank=True
    )
    
    # Notes about the session
    notes = models.TextField(
        blank=True,
        help_text="Notes about what was covered, student progress, etc."
    )
    
    # Backdating tracking
    is_backdated = models.BooleanField(
        default=False,
        help_text="Was this attendance marked for a past date?"
    )
    backdated_reason = models.TextField(
        blank=True,
        help_text="Reason for backdating (required if backdated)"
    )
    
    # Faculty who marked attendance
    marked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='marked_attendance_records',
        limit_choices_to={'role': 'faculty'}
    )
    
    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-in_time']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['assignment', 'date']),
            models.Index(fields=['marked_by', 'date']),
            models.Index(fields=['date', 'is_backdated']),
        ]
        # Prevent duplicate attendance for same student/assignment/date
        unique_together = [['student', 'assignment', 'date', 'in_time']]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.date} ({self.duration_minutes}min)"
    
    def save(self, *args, **kwargs):
        """Calculate duration before saving."""
        if self.in_time and self.out_time:
            from apps.core.utils import calculate_session_duration
            self.duration_minutes = calculate_session_duration(self.in_time, self.out_time)
        
        # Check if backdated
        if self.date < timezone.now().date():
            from apps.core.utils import is_backdated
            self.is_backdated = is_backdated(self.date)
        
        super().save(*args, **kwargs)
