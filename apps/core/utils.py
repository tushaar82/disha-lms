"""
Utility functions for Disha LMS.
"""

import secrets
import string
import datetime
from datetime import timedelta, time
from django.utils import timezone


def get_client_ip(request):
    """
    Extract client IP address from request.
    
    Args:
        request: HTTP request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_token(length=32):
    """
    Generate a secure random token.
    
    Args:
        length: Length of the token
        
    Returns:
        str: Random token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def calculate_session_duration(in_time, out_time):
    """
    Calculate session duration in minutes.
    
    Args:
        in_time: Session start time
        out_time: Session end time
        
    Returns:
        int: Duration in minutes
    """
    if not in_time or not out_time:
        return 0
    
    # Convert to datetime if they're time objects
    if isinstance(in_time, time):
        today = timezone.now().date()
        in_dt = datetime.datetime.combine(today, in_time)
        out_dt = datetime.datetime.combine(today, out_time)
    else:
        in_dt = in_time
        out_dt = out_time
    
    duration = (out_dt - in_dt).total_seconds() / 60
    return int(duration)


def is_backdated(date, threshold_hours=24):
    """
    Check if a date is backdated (older than threshold).
    
    Args:
        date: Date to check
        threshold_hours: Hours threshold (default 24)
        
    Returns:
        bool: True if backdated
    """
    if not date:
        return False
    
    threshold = timezone.now() - timedelta(hours=threshold_hours)
    
    if isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())
        date = timezone.make_aware(date)
    
    return date < threshold


def format_duration(minutes):
    """
    Format duration in minutes to human-readable format.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        str: Formatted duration (e.g., "1h 30m")
    """
    if not minutes:
        return "0m"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def calculate_attendance_rate(present_count, total_count):
    """
    Calculate attendance rate as a percentage.
    
    Args:
        present_count: Number of present days
        total_count: Total number of days
        
    Returns:
        float: Attendance rate (0.0 to 1.0)
    """
    if total_count == 0:
        return 0.0
    
    return round(present_count / total_count, 2)


def get_date_range(start_date, end_date):
    """
    Generate a list of dates between start and end date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        list: List of dates
    """
    dates = []
    current = start_date
    
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def truncate_text(text, length=100, suffix='...'):
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix


def sanitize_filename(filename):
    """
    Sanitize filename to remove unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove unsafe characters
    safe_chars = string.ascii_letters + string.digits + '.-_'
    sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # Remove multiple underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    return sanitized


def chunk_list(lst, chunk_size):
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        list: List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
