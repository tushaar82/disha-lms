"""
User models for Disha LMS.
Implements custom User model with role-based access control.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.MASTER_ACCOUNT)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with role-based access control.
    
    Supports three primary roles:
    - Master Account: Can manage multiple centers
    - Center Head: Can manage one center
    - Faculty: Can mark attendance for assigned students
    
    Implements Constitution Principle VIII: Security & Least Privilege
    """
    
    # Role choices
    MASTER_ACCOUNT = 'master'
    CENTER_HEAD = 'center_head'
    FACULTY = 'faculty'
    
    ROLE_CHOICES = [
        (MASTER_ACCOUNT, 'Master Account'),
        (CENTER_HEAD, 'Center Head'),
        (FACULTY, 'Faculty'),
    ]
    
    # Core fields
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # MFA fields (future implementation)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name
    
    @property
    def is_master_account(self):
        """Check if user is a master account."""
        return self.role == self.MASTER_ACCOUNT
    
    @property
    def is_center_head(self):
        """Check if user is a center head."""
        return self.role == self.CENTER_HEAD
    
    @property
    def is_faculty_member(self):
        """Check if user is a faculty member."""
        return self.role == self.FACULTY
