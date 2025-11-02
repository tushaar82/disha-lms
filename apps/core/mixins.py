"""
View mixins for Disha LMS.
Provides reusable functionality for views.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin to require specific user roles.
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            required_role = 'master'  # or 'center_head' or 'faculty'
    """
    required_role = None
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        if self.required_role is None:
            return True
        
        return self.request.user.role == self.required_role


class MasterAccountRequiredMixin(RoleRequiredMixin):
    """Require Master Account role."""
    required_role = 'master'


class CenterHeadRequiredMixin:
    """
    Mixin to restrict access to center head users (or master account).
    Master accounts have full access to everything.
    Checks both role and profile existence for center heads.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Master account has access to everything
        if request.user.is_master_account:
            return super().dispatch(request, *args, **kwargs)
        
        if not request.user.is_center_head:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a center head or master account to access this page.")
        
        # Check if center head profile exists
        if not hasattr(request.user, 'center_head_profile'):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Your center head profile is not set up. Please contact the administrator.")
            return redirect('accounts:profile')
        
        return super().dispatch(request, *args, **kwargs)


class FacultyRequiredMixin:
    """
    Mixin to restrict access to faculty users (or master account).
    Master accounts have full access to everything.
    Checks both role and profile existence for faculty.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Master account has access to everything
        if request.user.is_master_account:
            return super().dispatch(request, *args, **kwargs)
        
        if not request.user.is_faculty_member:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a faculty member or master account to access this page.")
        
        # Check if faculty profile exists
        if not hasattr(request.user, 'faculty_profile'):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Your faculty profile is not set up. Please contact the administrator.")
            return redirect('accounts:profile')
        
        return super().dispatch(request, *args, **kwargs)


class AdminOrMasterRequiredMixin:
    """
    Mixin to restrict access to Master Account or Center Head (Admin) only.
    Used for faculty performance dashboards.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Allow master account or center head
        if not (request.user.is_master_account or request.user.is_center_head):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account or Center Head to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class AdminOrFacultyRequiredMixin:
    """
    Mixin to restrict access to Master Account, Center Head (Admin), or Faculty.
    Used for student progress dashboards.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Allow master account, center head, or faculty
        if not (request.user.is_master_account or request.user.is_center_head or request.user.is_faculty_member):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You must be a Master Account, Center Head, or Faculty member to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class CenterContextMixin:
    """
    Mixin to provide center context to views.
    Useful for multi-center operations.
    """
    
    def get_center(self):
        """Get the current center from session or user profile."""
        # Try to get from session first (for master account switching)
        center_id = self.request.session.get('current_center_id')
        if center_id:
            from apps.centers.models import Center
            return Center.objects.filter(id=center_id).first()
        
        # Otherwise, get from user's profile
        user = self.request.user
        if hasattr(user, 'center_head_profile'):
            return user.center_head_profile.center
        elif hasattr(user, 'faculty_profile'):
            return user.faculty_profile.center
        
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_center'] = self.get_center()
        return context


class AuditLogMixin:
    """
    Mixin to automatically create audit logs for create/update/delete actions.
    
    Usage:
        class MyView(AuditLogMixin, CreateView):
            audit_action = 'CREATE'
    """
    audit_action = None
    
    def form_valid(self, form):
        """Log the action after successful form submission."""
        response = super().form_valid(form)
        
        if self.audit_action:
            from apps.core.models import AuditLog
            
            changes = {}
            if self.audit_action == 'UPDATE' and hasattr(self, 'get_object'):
                # For updates, capture before/after state
                old_obj = self.get_object()
                changes = {
                    'before': self.serialize_object(old_obj),
                    'after': self.serialize_object(form.instance),
                }
            
            AuditLog.log_action(
                user=self.request.user,
                action=self.audit_action,
                obj=form.instance,
                changes=changes,
                request=self.request,
            )
        
        return response
    
    def serialize_object(self, obj):
        """Serialize object to dict for audit log."""
        data = {}
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            data[field.name] = str(value)
        return data


class SetCreatedByMixin:
    """
    Mixin to automatically set created_by and modified_by fields.
    
    Usage:
        class MyView(SetCreatedByMixin, CreateView):
            pass
    """
    
    def form_valid(self, form):
        """Set created_by and modified_by before saving."""
        if not form.instance.pk:
            # New object - set created_by
            form.instance.created_by = self.request.user
        
        # Always set modified_by
        form.instance.modified_by = self.request.user
        
        return super().form_valid(form)
