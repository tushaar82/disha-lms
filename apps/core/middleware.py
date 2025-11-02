"""
Custom middleware for Disha LMS.
"""

from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log certain actions.
    
    Logs:
    - Login/Logout events
    - Access to sensitive pages
    """
    
    def process_request(self, request):
        """Process incoming request."""
        # Store request start time for performance monitoring
        import time
        request._start_time = time.time()
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response."""
        # Log login/logout events
        if hasattr(request, 'user') and request.user.is_authenticated:
            path = request.path
            
            # Log login
            if 'login' in path and request.method == 'POST' and response.status_code == 302:
                AuditLog.objects.create(
                    user=request.user,
                    action='LOGIN',
                    model_name='User',
                    object_id=request.user.pk,
                    object_repr=str(request.user),
                    ip_address=AuditLog.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    request_path=path,
                )
            
            # Log logout
            elif 'logout' in path and request.method in ['POST', 'GET']:
                AuditLog.objects.create(
                    user=request.user,
                    action='LOGOUT',
                    model_name='User',
                    object_id=request.user.pk,
                    object_repr=str(request.user),
                    ip_address=AuditLog.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    request_path=path,
                )
        
        return response


class CenterContextMiddleware(MiddlewareMixin):
    """
    Middleware to inject center context into requests.
    
    For Master Account: Checks session for center_id
    For Center Head/Faculty: Automatically sets their center
    """
    
    def process_request(self, request):
        """Add center context to request."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            center = None
            
            if request.user.is_master_account:
                # Master account uses session-stored center
                center_id = request.session.get('center_id')
                if center_id:
                    from apps.centers.models import Center
                    try:
                        center = Center.objects.get(id=center_id)
                    except Center.DoesNotExist:
                        pass
            
            elif request.user.is_center_head:
                # Center head's first managed center
                center = request.user.managed_centers.first()
            
            elif request.user.is_faculty_member:
                # Faculty's center
                if hasattr(request.user, 'faculty_profile'):
                    center = request.user.faculty_profile.center
            
            request.current_center = center
        
        return None
