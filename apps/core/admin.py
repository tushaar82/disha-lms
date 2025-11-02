from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__email', 'object_repr', 'reason']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 
                       'changes', 'reason', 'timestamp', 'ip_address', 'user_agent', 'request_path']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Audit logs are created automatically, not manually
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should never be deleted
        return False
