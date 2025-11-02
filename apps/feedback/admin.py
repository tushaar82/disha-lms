"""
Admin interface for feedback app.
"""

from django.contrib import admin
from .models import FeedbackSurvey, FeedbackResponse


@admin.register(FeedbackSurvey)
class FeedbackSurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'center', 'valid_from', 'valid_until', 'is_published', 'is_active']
    list_filter = ['is_active', 'is_published', 'center']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'center')
        }),
        ('Questions', {
            'fields': ('questions',)
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Status', {
            'fields': ('is_active', 'is_published')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ['student', 'survey', 'satisfaction_score', 'is_completed', 'submitted_at']
    list_filter = ['is_completed', 'survey', 'satisfaction_score']
    search_fields = ['student__first_name', 'student__last_name', 'survey__title', 'token']
    readonly_fields = ['token', 'created_at', 'created_by', 'modified_at', 'modified_by', 'submitted_at']
    
    fieldsets = (
        ('Survey Information', {
            'fields': ('survey', 'student', 'token')
        }),
        ('Response', {
            'fields': ('answers', 'satisfaction_score', 'is_completed', 'submitted_at')
        }),
        ('Email Tracking', {
            'fields': ('email_sent_at', 'email_opened_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
