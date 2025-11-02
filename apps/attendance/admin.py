from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'in_time', 'out_time', 'duration_minutes', 'marked_by', 'is_backdated']
    list_filter = ['date', 'is_backdated', 'marked_by']
    search_fields = ['student__first_name', 'student__last_name', 'assignment__subject__name']
    filter_horizontal = ['topics_covered']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by', 'duration_minutes']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('student', 'assignment', 'date', 'marked_by')
        }),
        ('Time', {
            'fields': ('in_time', 'out_time', 'duration_minutes')
        }),
        ('Topics & Notes', {
            'fields': ('topics_covered', 'notes')
        }),
        ('Backdating', {
            'fields': ('is_backdated', 'backdated_reason')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Attendance records should not be deleted (event-sourced)
        return False
