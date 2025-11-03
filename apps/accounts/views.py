"""
Views for authentication and user management.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView, ListView, DetailView
from django.contrib import messages

from .forms import LoginForm, ProfileUpdateForm
from .models import User


class LoginView(View):
    """View for user login."""
    
    template_name = 'accounts/login.html'
    form_class = LoginForm
    
    def get(self, request):
        if request.user.is_authenticated:
            # Redirect authenticated users based on role
            if request.user.is_faculty_member:
                return redirect('attendance:today')
            elif request.user.is_center_head:
                return redirect('centers:dashboard')
            elif request.user.is_master_account:
                return redirect('centers:list')
            else:
                return redirect('accounts:profile')
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # Set session expiry based on remember_me
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expires when browser closes
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # Redirect based on role
            if user.is_faculty_member:
                return redirect('attendance:today')
            elif user.is_center_head:
                return redirect('centers:dashboard')
            elif user.is_master_account:
                return redirect('centers:list')
            
            return redirect('accounts:profile')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """View for user logout."""
    
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')
    
    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """View for user profile management."""
    
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


# User Management Views

class UserManagementMixin(LoginRequiredMixin):
    """Mixin to ensure only master accounts and center heads can manage users."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not (request.user.role == User.MASTER_ACCOUNT or request.user.role == User.CENTER_HEAD):
            messages.error(request, 'You do not have permission to manage users.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


class UserListView(UserManagementMixin, ListView):
    """List all users with search and filters."""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().select_related('faculty_profile', 'center_head_profile')
        
        # Center heads can only see users in their center
        if self.request.user.role == User.CENTER_HEAD:
            if hasattr(self.request.user, 'center_head_profile'):
                center = self.request.user.center_head_profile.center
                # Get faculty and center heads in this center
                from apps.faculty.models import Faculty
                from apps.centers.models import CenterHead
                faculty_user_ids = Faculty.objects.filter(
                    center=center,
                    deleted_at__isnull=True
                ).values_list('user_id', flat=True)
                center_head_user_ids = CenterHead.objects.filter(
                    center=center,
                    deleted_at__isnull=True
                ).values_list('user_id', flat=True)
                queryset = queryset.filter(
                    id__in=list(faculty_user_ids) + list(center_head_user_ids)
                )
        
        # Search
        search = self.request.GET.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by role
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['role_choices'] = User.ROLE_CHOICES
        return context


class UserDetailView(UserManagementMixin, DetailView):
    """Show user details and activity."""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Get activity summary
        if user.role == User.FACULTY:
            if hasattr(user, 'faculty_profile'):
                from apps.attendance.models import AttendanceRecord
                from apps.subjects.models import Assignment
                from django.db.models import Count, Sum
                
                records = AttendanceRecord.objects.filter(marked_by=user)
                context['total_sessions'] = records.count()
                context['total_students'] = records.values('student').distinct().count()
                context['total_hours'] = (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60
                context['assignments'] = Assignment.objects.filter(
                    faculty=user.faculty_profile,
                    deleted_at__isnull=True
                ).count()
        
        elif user.role == User.CENTER_HEAD:
            if hasattr(user, 'center_head_profile'):
                from apps.students.models import Student
                from apps.faculty.models import Faculty
                
                center = user.center_head_profile.center
                context['center'] = center
                context['total_students'] = Student.objects.filter(
                    center=center,
                    deleted_at__isnull=True
                ).count()
                context['total_faculty'] = Faculty.objects.filter(
                    center=center,
                    deleted_at__isnull=True
                ).count()
        
        return context


class UserUpdateView(UserManagementMixin, UpdateView):
    """Update user details."""
    model = User
    fields = ['first_name', 'last_name', 'email', 'phone', 'is_active']
    template_name = 'accounts/user_form.html'
    
    def get_success_url(self):
        return reverse_lazy('accounts:user_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'User {form.instance.get_full_name()} updated successfully!')
        return super().form_valid(form)


class UserDeleteView(UserManagementMixin, View):
    """Soft delete user (deactivate)."""
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        # Cannot delete self
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('accounts:user_list')
        
        # Deactivate user
        user.is_active = False
        user.save()
        
        # Deactivate associated profile
        if hasattr(user, 'faculty_profile'):
            user.faculty_profile.is_active = False
            user.faculty_profile.save()
        
        messages.success(request, f'User {user.get_full_name()} has been deactivated.')
        return redirect('accounts:user_list')
