# Data Model: Multi-Center LMS

**Feature**: Multi-Center Student Learning & Satisfaction Management System  
**Branch**: 001-multi-center-lms  
**Date**: 2025-11-01

## Overview

This document defines the Django data models for the multi-center LMS. All models follow event-sourcing principles with immutable audit trails, soft-delete capabilities, and timestamp tracking.

---

## Base Models

### TimeStampedModel (Abstract)
Provides automatic timestamp tracking for all models.

```python
from django.db import models
from django.conf import settings

class TimeStampedModel(models.Model):
    """
    Abstract base model providing created/modified timestamps and user tracking.
    All models should inherit from this for audit trail compliance.
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
```

### SoftDeleteModel (Abstract)
Provides soft-delete functionality to preserve audit trails.

```python
class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted records by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteModel(models.Model):
    """
    Abstract base model providing soft-delete functionality.
    Records are never hard-deleted to maintain audit trail.
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
        """Soft delete this record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
```

---

## Core Models

### 1. User (Custom User Model)

```python
from django.contrib.auth.models.AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.MASTER_ACCOUNT)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with role-based access control.
    Supports three primary roles: Master Account, Center Head, Faculty.
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
    
    # Fields
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
    
    # MFA fields (future)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_master_account(self):
        return self.role == self.MASTER_ACCOUNT
    
    @property
    def is_center_head(self):
        return self.role == self.CENTER_HEAD
    
    @property
    def is_faculty_member(self):
        return self.role == self.FACULTY
```

### 2. Center

```python
class Center(TimeStampedModel, SoftDeleteModel):
    """
    Represents a physical or logical learning center.
    Each center operates independently with its own students, faculty, and center head.
    """
    name = models.CharField(max_length=200, db_index=True)
    location = models.CharField(max_length=300)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Center heads (many-to-many: one center can have multiple heads)
    center_heads = models.ManyToManyField(
        User,
        limit_choices_to={'role': User.CENTER_HEAD},
        related_name='managed_centers'
    )
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    class Meta:
        db_table = 'centers'
        verbose_name = 'Center'
        verbose_name_plural = 'Centers'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.city})"
```

### 3. Student

```python
class Student(TimeStampedModel, SoftDeleteModel):
    """
    Represents a student enrolled in a center for individual/personal teaching.
    """
    center = models.ForeignKey(Center, on_delete=models.PROTECT, related_name='students')
    
    # Personal information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Enrollment information
    enrollment_date = models.DateField(db_index=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Satisfaction score (aggregated from feedback)
    satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['first_name', 'last_name']
        unique_together = [['center', 'email']]  # Unique email per center
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.center.name})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```

### 4. Faculty

```python
class Faculty(TimeStampedModel, SoftDeleteModel):
    """
    Represents teaching staff who conduct one-on-one or small group sessions.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    center = models.ForeignKey(Center, on_delete=models.PROTECT, related_name='faculty_members')
    
    # Employment information
    hire_date = models.DateField()
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Bio
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'faculty'
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculty'
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.center.name})"
```

### 5. Subject

```python
class Subject(TimeStampedModel, SoftDeleteModel):
    """
    Represents a course or topic area being taught (e.g., "Mathematics Grade 10").
    """
    center = models.ForeignKey(Center, on_delete=models.PROTECT, related_name='subjects')
    
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    
    # Metadata
    estimated_duration_hours = models.IntegerField(help_text="Estimated hours to complete")
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    
    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
        unique_together = [['center', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.center.name})"
```

### 6. Topic

```python
class Topic(TimeStampedModel, SoftDeleteModel):
    """
    Represents a specific lesson or concept within a subject.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    
    name = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True)
    sequence_number = models.IntegerField(help_text="Order in which topic should be taught")
    
    # Metadata
    estimated_duration_minutes = models.IntegerField(help_text="Estimated minutes to teach")
    
    # Type
    TYPE_CHOICES = [
        ('core', 'Core (Mandatory)'),
        ('supplementary', 'Supplementary (Optional)'),
    ]
    topic_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='core')
    
    # Prerequisites (topics that should be completed first)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_topics')
    
    class Meta:
        db_table = 'topics'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        ordering = ['subject', 'sequence_number']
        unique_together = [['subject', 'sequence_number']]
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"
```

### 7. Assignment

```python
class Assignment(TimeStampedModel, SoftDeleteModel):
    """
    Links a student to subjects and faculty members.
    Defines who teaches what to whom.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='assignments')
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='assignments')
    
    # Assignment period
    start_date = models.DateField(db_index=True)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('transferred', 'Transferred'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Primary faculty flag (for students with multiple faculty)
    is_primary = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'assignments'
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['faculty', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} ({self.faculty.user.get_full_name()})"
```

### 8. AttendanceRecord (Event-Sourced)

```python
class AttendanceRecord(TimeStampedModel):
    """
    Immutable event capturing a student's presence/absence for a specific date.
    This is the core event-sourced model - records are never modified, only appended.
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='attendance_records')
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='attendance_records')
    
    # Attendance details
    date = models.DateField(db_index=True)
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    
    # Time tracking (required for 'present' status)
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    session_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Topics taught (many-to-many)
    topics_taught = models.ManyToManyField(Topic, blank=True, related_name='attendance_records')
    
    # Backdated entry tracking
    is_backdated = models.BooleanField(default=False)
    backdated_reason = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['faculty', 'date']),
            models.Index(fields=['date', 'status']),
        ]
        # Prevent duplicate attendance for same student/date/faculty
        unique_together = [['student', 'faculty', 'date', 'created_at']]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Calculate session duration
        if self.in_time and self.out_time:
            from datetime import datetime, timedelta
            in_dt = datetime.combine(self.date, self.in_time)
            out_dt = datetime.combine(self.date, self.out_time)
            duration = (out_dt - in_dt).total_seconds() / 60
            self.session_duration_minutes = int(duration)
        
        # Check if backdated (more than 24 hours old)
        if self.date < (timezone.now().date() - timedelta(days=1)):
            self.is_backdated = True
        
        super().save(*args, **kwargs)
```

### 9. AuditLog (Event Store)

```python
class AuditLog(models.Model):
    """
    Immutable audit log for all critical operations.
    Captures complete before/after state for event replay.
    """
    # Who
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # What
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ACCESS', 'Access'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.IntegerField(db_index=True)
    object_repr = models.CharField(max_length=200)
    
    # Changes (JSON field for before/after state)
    changes = models.JSONField(help_text="Before/after state for event replay")
    
    # Why
    reason = models.TextField(blank=True, help_text="Reason for the action")
    
    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Context
    request_path = models.CharField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
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
```

### 10. FeedbackSurvey

```python
class FeedbackSurvey(TimeStampedModel, SoftDeleteModel):
    """
    Questionnaire sent to students to collect satisfaction data.
    """
    center = models.ForeignKey(Center, on_delete=models.PROTECT, related_name='surveys')
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    
    # Survey configuration
    questions = models.JSONField(help_text="List of questions with types (rating, multiple_choice, text)")
    
    # Targeting
    target_students = models.ManyToManyField(Student, related_name='surveys', blank=True)
    target_faculty = models.ManyToManyField(Faculty, related_name='surveys', blank=True)
    
    # Timing
    sent_date = models.DateTimeField(null=True, blank=True)
    response_deadline = models.DateField(null=True, blank=True)
    
    # Settings
    is_anonymous = models.BooleanField(default=False)
    allow_multiple_responses = models.BooleanField(default=False)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    class Meta:
        db_table = 'feedback_surveys'
        verbose_name = 'Feedback Survey'
        verbose_name_plural = 'Feedback Surveys'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.center.name})"
```

### 11. FeedbackResponse

```python
class FeedbackResponse(TimeStampedModel):
    """
    A student's answers to a feedback survey.
    """
    survey = models.ForeignKey(FeedbackSurvey, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='feedback_responses', null=True, blank=True)
    
    # Response data
    responses = models.JSONField(help_text="Question ID -> Answer mapping")
    satisfaction_rating = models.IntegerField(null=True, blank=True, help_text="Overall rating 1-5")
    comments = models.TextField(blank=True)
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Unique token for anonymous surveys
    response_token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        db_table = 'feedback_responses'
        verbose_name = 'Feedback Response'
        verbose_name_plural = 'Feedback Responses'
        ordering = ['-submitted_at']
    
    def __str__(self):
        student_name = self.student.full_name if self.student else "Anonymous"
        return f"{student_name} - {self.survey.title}"
```

---

## Relationships Summary

```
User (1) ←→ (1) Faculty
User (M) ←→ (M) Center (center_heads)

Center (1) ←→ (M) Student
Center (1) ←→ (M) Faculty
Center (1) ←→ (M) Subject

Subject (1) ←→ (M) Topic
Topic (M) ←→ (M) Topic (prerequisites)

Student (1) ←→ (M) Assignment
Subject (1) ←→ (M) Assignment
Faculty (1) ←→ (M) Assignment

Assignment (1) ←→ (M) AttendanceRecord
Student (1) ←→ (M) AttendanceRecord
Faculty (1) ←→ (M) AttendanceRecord
AttendanceRecord (M) ←→ (M) Topic (topics_taught)

Center (1) ←→ (M) FeedbackSurvey
FeedbackSurvey (M) ←→ (M) Student (target_students)
FeedbackSurvey (M) ←→ (M) Faculty (target_faculty)
FeedbackSurvey (1) ←→ (M) FeedbackResponse
Student (1) ←→ (M) FeedbackResponse

User (1) ←→ (M) AuditLog
```

---

## Database Indexes

All models include indexes on:
- Primary keys (automatic)
- Foreign keys (automatic in PostgreSQL, explicit in SQLite)
- `created_at` (for temporal queries)
- `is_deleted` (for soft-delete filtering)
- Frequently queried fields (`status`, `date`, `email`)

---

## Event Sourcing Implementation

### Immutable Records
- `AttendanceRecord`: Never modified after creation
- `AuditLog`: Never modified after creation

### Audit Trail
- All models inherit from `TimeStampedModel` for `created_at`, `created_by`, `modified_at`, `modified_by`
- `AuditLog` captures before/after state in JSON field
- Django signals (`post_save`, `post_delete`) automatically create audit logs

### Soft Delete
- All models inherit from `SoftDeleteModel`
- Records marked as deleted via `is_deleted` flag
- Custom manager excludes deleted records by default
- `all_objects` manager includes deleted records for audit queries

### Temporal Queries
```python
# Get student's attendance on specific date
AttendanceRecord.objects.filter(student=student, date=date)

# Reconstruct student state at point in time
AuditLog.objects.filter(
    model_name='Student',
    object_id=student.id,
    timestamp__lte=target_datetime
).order_by('timestamp')
```

---

## Django Migrations

All models will be created via Django migrations:

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create initial data (superuser, sample center)
python manage.py createsuperuser
python manage.py loaddata initial_data.json
```

---

## Next Steps

1. **Phase 1**: Generate API contracts in `contracts/`
2. **Phase 1**: Create `quickstart.md` for development setup
3. **Phase 2**: Generate `tasks.md` with implementation tasks

This data model supports all 5 user stories (P1-P5) and aligns with the constitution's event-sourcing and audit trail requirements.
