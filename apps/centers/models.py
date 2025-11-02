"""
Center models for Disha LMS.
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Center(TimeStampedModel, SoftDeleteModel):
    """
    Learning center model.
    Represents a physical location where teaching happens.
    """
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, help_text="Unique center code")
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Center head (can be multiple, but we'll use the first one)
    center_heads = models.ManyToManyField(
        'accounts.User',
        related_name='managed_centers',
        limit_choices_to={'role': 'center_head'}
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'centers'
        verbose_name = 'Center'
        verbose_name_plural = 'Centers'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class CenterHead(TimeStampedModel, SoftDeleteModel):
    """
    Center Head profile model.
    Links a User with center_head role to a center.
    """
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='center_head_profile',
        limit_choices_to={'role': 'center_head'}
    )
    
    center = models.ForeignKey(
        Center,
        on_delete=models.PROTECT,
        related_name='center_head_profiles'
    )
    
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'center_heads'
        verbose_name = 'Center Head'
        verbose_name_plural = 'Center Heads'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.center.name}"
