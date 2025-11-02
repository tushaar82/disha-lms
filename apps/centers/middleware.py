"""
Middleware for center context management.
T118: Center context middleware for session-based center switching.
"""

from django.utils.deprecation import MiddlewareMixin
from .models import Center


class CenterContextMiddleware(MiddlewareMixin):
    """
    Middleware to provide center context in request object.
    Supports master accounts viewing any center via session.
    """
    
    def process_request(self, request):
        """Add center context to request."""
        request.active_center = None
        request.active_center_name = None
        
        if not request.user.is_authenticated:
            return
        
        # Master accounts: Get center from session
        if request.user.is_master_account:
            center_id = request.session.get('active_center_id')
            if center_id:
                try:
                    center = Center.objects.get(pk=center_id, deleted_at__isnull=True)
                    request.active_center = center
                    request.active_center_name = center.name
                except Center.DoesNotExist:
                    # Clear invalid center from session
                    request.session.pop('active_center_id', None)
                    request.session.pop('active_center_name', None)
        
        # Center heads: Get their assigned center
        elif request.user.is_center_head:
            if hasattr(request.user, 'center_head_profile'):
                center = request.user.center_head_profile.center
                request.active_center = center
                request.active_center_name = center.name
        
        # Faculty: Get their assigned center
        elif request.user.is_faculty_member:
            if hasattr(request.user, 'faculty_profile'):
                center = request.user.faculty_profile.center
                request.active_center = center
                request.active_center_name = center.name
