"""
API permission classes for Disha LMS.
"""

from apps.accounts.permissions import (
    IsMasterAccount,
    IsCenterHead,
    IsFaculty,
    IsMasterAccountOrCenterHead,
    IsOwnerOrReadOnly
)

# Re-export permissions for API use
__all__ = [
    'IsMasterAccount',
    'IsCenterHead',
    'IsFaculty',
    'IsMasterAccountOrCenterHead',
    'IsOwnerOrReadOnly',
]
