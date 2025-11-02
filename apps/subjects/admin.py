from django.contrib import admin
from .models import Subject, Topic, Assignment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'sequence_number', 'estimated_duration', 'is_active']
    list_filter = ['is_active', 'subject']
    search_fields = ['name', 'description', 'subject__name']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('subject', 'name', 'sequence_number', 'is_active')
        }),
        ('Details', {
            'fields': ('description', 'estimated_duration')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'faculty', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'subject', 'start_date']
    search_fields = ['student__first_name', 'student__last_name', 'subject__name', 'faculty__user__first_name']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('student', 'subject', 'faculty', 'is_active')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
