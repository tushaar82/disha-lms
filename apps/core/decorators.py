"""
Utility decorators for Disha LMS.
Provides decorators for error handling, caching, validation, and rate limiting.
"""

import functools
import logging
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings

logger = logging.getLogger(__name__)


def require_gemini_configured(view_func):
    """
    Decorator to check if Gemini API is configured before executing view.
    Redirects to configuration page if not configured.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.core.models import SystemConfiguration
        
        api_key = SystemConfiguration.get_config('GEMINI_API_KEY')
        
        if not api_key:
            messages.warning(
                request,
                'Gemini API is not configured. Please configure it to use AI features.'
            )
            return redirect('core:gemini_config')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def cache_ai_response(ttl=3600, key_prefix='ai'):
    """
    Decorator to cache AI responses in Redis.
    
    Args:
        ttl: Time to live in seconds (default 3600 = 1 hour)
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key} with TTL {ttl}s")
            
            return result
        
        return wrapper
    return decorator


def log_errors(view_func):
    """
    Decorator for comprehensive error logging.
    Logs errors with full context and continues execution.
    """
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Exception as e:
            # Log the error with context
            logger.error(
                f"Error in {view_func.__name__}: {str(e)}",
                exc_info=True,
                extra={
                    'function': view_func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200],
                }
            )
            # Re-raise the exception
            raise
    
    return wrapper


def validate_request_data(schema):
    """
    Decorator for request data validation.
    
    Args:
        schema: Dictionary defining required fields and their types
                Example: {'field_name': str, 'count': int}
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get data based on request method
            if request.method == 'POST':
                data = request.POST
            elif request.method == 'GET':
                data = request.GET
            else:
                data = {}
            
            # Validate required fields
            errors = []
            for field, field_type in schema.items():
                if field not in data:
                    errors.append(f"Missing required field: {field}")
                else:
                    # Try to convert to expected type
                    try:
                        if field_type == int:
                            int(data[field])
                        elif field_type == float:
                            float(data[field])
                        elif field_type == bool:
                            data[field].lower() in ['true', '1', 'yes']
                    except (ValueError, AttributeError):
                        errors.append(f"Invalid type for field {field}: expected {field_type.__name__}")
            
            if errors:
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({'errors': errors}, status=400)
                else:
                    for error in errors:
                        messages.error(request, error)
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(max_calls=10, period=60, key_func=None):
    """
    Decorator for rate limiting critical operations.
    
    Args:
        max_calls: Maximum number of calls allowed
        period: Time period in seconds
        key_func: Optional function to generate rate limit key (default: uses user ID)
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate rate limit key
            if key_func:
                rate_key = key_func(request, *args, **kwargs)
            else:
                # Default: use user ID or IP address
                if request.user.is_authenticated:
                    rate_key = f"rate_limit:{view_func.__name__}:user:{request.user.id}"
                else:
                    from apps.core.utils import get_client_ip
                    ip = get_client_ip(request)
                    rate_key = f"rate_limit:{view_func.__name__}:ip:{ip}"
            
            # Get current count from cache
            current_count = cache.get(rate_key, 0)
            
            if current_count >= max_calls:
                logger.warning(f"Rate limit exceeded for {rate_key}")
                
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Rate limit exceeded. Please try again later.'
                    }, status=429)
                else:
                    messages.error(
                        request,
                        'Too many requests. Please try again later.'
                    )
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Increment counter
            cache.set(rate_key, current_count + 1, period)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_failure(max_retries=3, delay=1, exceptions=(Exception,)):
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}"
                        )
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def require_ai_enabled(view_func):
    """
    Decorator to check if AI features are enabled.
    Returns error if AI is disabled.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(settings, 'ENABLE_AI_FEATURES', False):
            if request.is_ajax() or request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'AI features are currently disabled.'
                }, status=503)
            else:
                messages.error(request, 'AI features are currently disabled.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def measure_performance(func):
    """
    Decorator to measure and log function execution time.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        logger.info(
            f"Function {func.__name__} executed in {execution_time:.4f} seconds"
        )
        
        # Log slow functions (>5 seconds)
        if execution_time > 5:
            logger.warning(
                f"Slow function detected: {func.__name__} took {execution_time:.4f} seconds"
            )
        
        return result
    
    return wrapper
