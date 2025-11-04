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


# ============================================================================
# ENCRYPTION UTILITIES
# ============================================================================

def get_encryption_key():
    """
    Retrieve or generate encryption key for sensitive data.
    
    Returns:
        bytes: Encryption key
    """
    from django.conf import settings
    from cryptography.fernet import Fernet
    import os
    
    # Try to get key from settings
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if not key:
        # Try to get from environment
        key = os.environ.get('ENCRYPTION_KEY')
    
    if not key:
        # Generate a new key (should be stored securely)
        key = Fernet.generate_key().decode()
        import warnings
        warnings.warn(
            "No ENCRYPTION_KEY found. Generated a new one. "
            "Please add it to your .env file for persistence."
        )
    
    if isinstance(key, str):
        key = key.encode()
    
    return key


def encrypt_value(value, key=None):
    """
    Encrypt a value using Fernet symmetric encryption.
    
    Args:
        value: Value to encrypt (string)
        key: Optional encryption key (uses default if not provided)
        
    Returns:
        str: Encrypted value (base64 encoded)
    """
    from cryptography.fernet import Fernet
    
    if not value:
        return value
    
    if key is None:
        key = get_encryption_key()
    
    fernet = Fernet(key)
    
    if isinstance(value, str):
        value = value.encode()
    
    encrypted = fernet.encrypt(value)
    return encrypted.decode()


def decrypt_value(encrypted_value, key=None):
    """
    Decrypt a value encrypted with encrypt_value.
    
    Args:
        encrypted_value: Encrypted value (base64 encoded string)
        key: Optional encryption key (uses default if not provided)
        
    Returns:
        str: Decrypted value
    """
    from cryptography.fernet import Fernet
    
    if not encrypted_value:
        return encrypted_value
    
    if key is None:
        key = get_encryption_key()
    
    fernet = Fernet(key)
    
    if isinstance(encrypted_value, str):
        encrypted_value = encrypted_value.encode()
    
    decrypted = fernet.decrypt(encrypted_value)
    return decrypted.decode()


# ============================================================================
# AI UTILITIES
# ============================================================================

def validate_gemini_api_key(api_key):
    """
    Test if a Gemini API key is valid by making a test request.
    
    Args:
        api_key: Gemini API key to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not api_key:
        return False, "API key is required"
    
    try:
        import google.generativeai as genai
        
        # Configure with the API key
        genai.configure(api_key=api_key)
        
        # Try to list models as a test
        models = genai.list_models()
        model_list = list(models)
        
        if model_list:
            return True, f"API key is valid. Found {len(model_list)} available models."
        else:
            return False, "API key appears invalid. No models available."
            
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"


def format_ai_response(response):
    """
    Format Gemini API response for display.
    
    Args:
        response: Raw response from Gemini API
        
    Returns:
        dict: Formatted response with text, metadata, etc.
    """
    try:
        if hasattr(response, 'text'):
            return {
                'text': response.text,
                'success': True,
                'error': None
            }
        elif isinstance(response, dict):
            return response
        else:
            return {
                'text': str(response),
                'success': True,
                'error': None
            }
    except Exception as e:
        return {
            'text': '',
            'success': False,
            'error': str(e)
        }


def sanitize_data_for_ai(data):
    """
    Remove sensitive information before sending data to AI.
    
    Args:
        data: Data dictionary to sanitize
        
    Returns:
        dict: Sanitized data
    """
    if not isinstance(data, dict):
        return data
    
    # Fields to remove or mask
    sensitive_fields = [
        'password', 'api_key', 'secret', 'token', 
        'ssn', 'credit_card', 'phone', 'email',
        'address', 'guardian_phone'
    ]
    
    sanitized = data.copy()
    
    for key in list(sanitized.keys()):
        # Check if key contains sensitive field names
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = '[REDACTED]'
        # Recursively sanitize nested dicts
        elif isinstance(sanitized[key], dict):
            sanitized[key] = sanitize_data_for_ai(sanitized[key])
        # Sanitize lists of dicts
        elif isinstance(sanitized[key], list):
            sanitized[key] = [
                sanitize_data_for_ai(item) if isinstance(item, dict) else item
                for item in sanitized[key]
            ]
    
    return sanitized
