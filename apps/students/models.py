"""
Student models for Disha LMS.
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Student(TimeStampedModel, SoftDeleteModel):
    """
    Student model.
    Represents a student enrolled in a center.
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),  # Transferred or finished
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Enrollment Information
    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.PROTECT,
        related_name='students'
    )
    enrollment_number = models.CharField(max_length=50, unique=True)
    enrollment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Guardian Information
    guardian_name = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Internal notes about the student")
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['center', 'status']),
            models.Index(fields=['enrollment_number']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.enrollment_number})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
