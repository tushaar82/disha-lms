"""
Faculty models for Disha LMS.
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Faculty(TimeStampedModel, SoftDeleteModel):
    """
    Faculty profile model.
    Links a User with faculty role to a center and subjects.
    """
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='faculty_profile',
        limit_choices_to={'role': 'faculty'}
    )
    
    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.PROTECT,
        related_name='faculty_members'
    )
    
    # Subjects this faculty can teach
    subjects = models.ManyToManyField(
        'subjects.Subject',
        related_name='faculty_members',
        blank=True
    )
    
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Additional Information
    qualification = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    experience_years = models.IntegerField(default=0, help_text="Years of teaching experience")
    
    class Meta:
        db_table = 'faculty'
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculty'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.center.name}"
