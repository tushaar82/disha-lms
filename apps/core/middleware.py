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


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive error handling and logging.
    Catches unhandled exceptions and provides user-friendly error pages.
    """
    
    def process_exception(self, request, exception):
        """Handle unhandled exceptions."""
        import logging
        import traceback
        from django.http import JsonResponse
        from django.shortcuts import render
        
        logger = logging.getLogger('apps.core.middleware')
        
        # Log the error with full context
        logger.error(
            f"Unhandled exception: {str(exception)}",
            exc_info=True,
            extra={
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                'path': request.path,
                'method': request.method,
                'GET': dict(request.GET),
                'POST': dict(request.POST) if request.method == 'POST' else {},
                'ip_address': AuditLog.get_client_ip(request),
            }
        )
        
        # Send to Sentry if configured
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exception)
        except ImportError:
            pass
        
        # Return appropriate response based on request type
        if request.is_ajax() or request.content_type == 'application/json':
            return JsonResponse({
                'error': 'An unexpected error occurred. Please try again later.',
                'detail': str(exception) if request.user.is_staff else None
            }, status=500)
        
        # For regular requests, render error page
        context = {
            'error_message': 'An unexpected error occurred.',
            'error_detail': str(exception) if request.user.is_staff else None,
            'traceback': traceback.format_exc() if request.user.is_staff else None,
        }
        
        return render(request, 'errors/500.html', context, status=500)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging all requests with timing information.
    Tracks slow queries and user actions for audit trail.
    """
    
    def process_request(self, request):
        """Log incoming request."""
        import time
        import logging
        
        logger = logging.getLogger('apps.core.middleware')
        
        # Store start time
        request._start_time = time.time()
        
        # Log request details (only for authenticated users to reduce noise)
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(
                f"Request: {request.method} {request.path}",
                extra={
                    'user': str(request.user),
                    'method': request.method,
                    'path': request.path,
                    'ip_address': AuditLog.get_client_ip(request),
                }
            )
        
        return None
    
    def process_response(self, request, response):
        """Log response with timing."""
        import time
        import logging
        
        logger = logging.getLogger('apps.core.middleware')
        
        # Calculate request duration
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests (>1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} took {duration:.2f}s",
                    extra={
                        'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': response.status_code,
                    }
                )
            
            # Add timing header for debugging
            response['X-Request-Duration'] = f"{duration:.4f}s"
        
        return response


class AIFeatureMiddleware(MiddlewareMixin):
    """
    Middleware to inject AI feature status into request context.
    Makes AI configuration available throughout the application.
    """
    
    def process_request(self, request):
        """Add AI feature status to request."""
        from django.conf import settings
        from apps.core.models import SystemConfiguration
        
        # Check if AI features are enabled
        request.ai_enabled = getattr(settings, 'ENABLE_AI_FEATURES', False)
        
        # Check if Gemini is configured
        if request.ai_enabled:
            api_key = SystemConfiguration.get_config('GEMINI_API_KEY')
            request.gemini_configured = bool(api_key)
        else:
            request.gemini_configured = False
        
        return None
    
    def process_template_response(self, request, response):
        """Add AI context to template context."""
        if hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            
            response.context_data['ai_enabled'] = getattr(request, 'ai_enabled', False)
            response.context_data['gemini_configured'] = getattr(request, 'gemini_configured', False)
        
        return response
