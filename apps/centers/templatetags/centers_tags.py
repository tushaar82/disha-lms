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
