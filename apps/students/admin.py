from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'enrollment_number', 'center', 'status', 'enrollment_date']
    list_filter = ['status', 'center', 'enrollment_date']
    search_fields = ['first_name', 'last_name', 'enrollment_number', 'email', 'phone']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'email', 'phone')
        }),
        ('Enrollment', {
            'fields': ('center', 'enrollment_number', 'enrollment_date', 'status')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_email')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
