from django.contrib import admin
from .models import Center, CenterHead


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['name', 'code', 'city', 'email']
    filter_horizontal = ['center_heads']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Management', {
            'fields': ('center_heads',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CenterHead)
class CenterHeadAdmin(admin.ModelAdmin):
    list_display = ['user', 'center', 'employee_id', 'joining_date', 'is_active']
    list_filter = ['is_active', 'center', 'joining_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id']
    readonly_fields = ['created_at', 'created_by', 'modified_at', 'modified_by']
    date_hierarchy = 'joining_date'
    
    fieldsets = (
        ('User & Center', {
            'fields': ('user', 'center', 'employee_id', 'is_active')
        }),
        ('Employment', {
            'fields': ('joining_date',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'),
            'classes': ('collapse',)
        }),
    )
