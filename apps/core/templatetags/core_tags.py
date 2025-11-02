"""
Custom template tags for Disha LMS.
"""

from django import template
from django.utils.safestring import mark_safe
from apps.core.utils import format_duration, truncate_text

register = template.Library()


@register.filter
def duration(minutes):
    """Format duration in minutes to human-readable format."""
    return format_duration(minutes)


@register.filter
def truncate(text, length=100):
    """Truncate text to specified length."""
    return truncate_text(text, length)


@register.filter
def percentage(value, total):
    """Calculate percentage."""
    if not total or total == 0:
        return 0
    return round((value / total) * 100, 1)


@register.simple_tag
def badge_class(status):
    """Return badge class based on status."""
    status_classes = {
        'active': 'badge-success',
        'inactive': 'badge-error',
        'pending': 'badge-warning',
        'completed': 'badge-info',
        'present': 'badge-success',
        'absent': 'badge-error',
        'leave': 'badge-warning',
        'holiday': 'badge-info',
    }
    return status_classes.get(status.lower(), 'badge-neutral')


@register.simple_tag
def status_icon(status):
    """Return icon SVG based on status."""
    icons = {
        'success': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        'error': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        'warning': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        'info': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
    }
    return mark_safe(icons.get(status, ''))


@register.inclusion_tag('components/card.html')
def card(title='', content='', badge='', badge_type='primary', image='', hover=False):
    """Render a card component."""
    return {
        'title': title,
        'content': content,
        'badge': badge,
        'badge_type': badge_type,
        'image': image,
        'hover': hover,
    }


@register.filter
def add_class(field, css_class):
    """Add CSS class to form field."""
    return field.as_widget(attrs={'class': css_class})


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary."""
    return dictionary.get(key)
