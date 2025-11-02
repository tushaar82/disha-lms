"""
Template tags for centers app.
"""

from django import template
from apps.centers.models import Center

register = template.Library()


@register.simple_tag
def get_active_centers():
    """Get all active centers for the switch center dropdown."""
    return Center.objects.filter(
        deleted_at__isnull=True,
        is_active=True
    ).order_by('name')


@register.simple_tag(takes_context=True)
def get_user_center(context):
    """Get the center for the current user."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    
    user = request.user
    
    # For master accounts, get from session
    if user.is_master_account:
        center_id = request.session.get('active_center_id')
        if center_id:
            try:
                return Center.objects.get(pk=center_id, deleted_at__isnull=True)
            except Center.DoesNotExist:
                return None
        return None
    
    # For center heads, get from their profile
    if user.is_center_head and hasattr(user, 'center_head_profile'):
        return user.center_head_profile.center
    
    return None
