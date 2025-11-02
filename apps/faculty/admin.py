from django.contrib import admin
from .models import Faculty


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['user', 'center', 'employee_id', 'joining_date', 'is_active']
    list_filter = ['is_active', 'center', 'joining_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id']
    filter_horizontal = ['subjects']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    date_hierarchy = 'joining_date'
    
    fieldsets = (
        ('User & Center', {
            'fields': ('user', 'center', 'employee_id', 'is_active')
        }),
        ('Employment', {
            'fields': ('joining_date', 'subjects')
        }),
        ('Qualifications', {
            'fields': ('qualification', 'specialization', 'experience_years')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
