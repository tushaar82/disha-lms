"""
Custom permission classes for Disha LMS.
Implements role-based access control (RBAC).
"""

from rest_framework import permissions


class IsMasterAccount(permissions.BasePermission):
    """
    Permission class to check if user is a Master Account.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_master_account
        )


class IsCenterHead(permissions.BasePermission):
    """
    Permission class to check if user is a Center Head.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_center_head
        )


class IsFaculty(permissions.BasePermission):
    """
    Permission class to check if user is a Faculty member.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_faculty_member
        )


class IsMasterAccountOrCenterHead(permissions.BasePermission):
    """
    Permission class to check if user is either Master Account or Center Head.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_master_account or request.user.is_center_head)
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.created_by == request.user
