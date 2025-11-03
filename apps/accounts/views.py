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

from .forms import LoginForm, ProfileUpdateForm, CenterManagerCreationForm, FacultyCreationForm
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


class UserUpdateView(UserManagementMixin, View):
    """Update user details and optionally change password."""
    template_name = 'accounts/user_form.html'
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, self.template_name, {'object': user})
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        # Update basic fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.is_active = 'is_active' in request.POST
        
        # Handle password change if provided
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if new_password or confirm_password:
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, self.template_name, {'object': user})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, self.template_name, {'object': user})
            
            # Set the new password
            user.set_password(new_password)
            messages.success(request, f'Password updated for {user.get_full_name()}!')
        
        try:
            user.save()
            messages.success(request, f'User {user.get_full_name()} updated successfully!')
            return redirect('accounts:user_detail', pk=user.pk)
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            return render(request, self.template_name, {'object': user})


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


# Master Account - Center Manager Management

class MasterAccountRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only master accounts can access."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_master_account:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


class CenterHeadRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only center heads can access."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_center_head:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)


class CreateCenterManagerView(MasterAccountRequiredMixin, View):
    """Master account creates center managers (center heads)."""
    
    template_name = 'accounts/create_center_manager.html'
    form_class = CenterManagerCreationForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            from django.db import transaction
            from apps.centers.models import CenterHead
            
            try:
                with transaction.atomic():
                    # Create user
                    user = User.objects.create_user(
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role=User.CENTER_HEAD
                    )
                    
                    # Create center head profile
                    center_head = CenterHead.objects.create(
                        user=user,
                        center=form.cleaned_data['center'],
                        employee_id=form.cleaned_data.get('employee_id', ''),
                        joining_date=form.cleaned_data['joining_date'],
                        created_by=request.user,
                        modified_by=request.user
                    )
                    
                    messages.success(
                        request,
                        f'Center Manager {user.get_full_name()} created successfully! '
                        f'Username: {user.email}'
                    )
                    return redirect('accounts:center_manager_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating center manager: {str(e)}')
        
        return render(request, self.template_name, {'form': form})


class CenterManagerListView(MasterAccountRequiredMixin, ListView):
    """List all center managers."""
    
    model = User
    template_name = 'accounts/center_manager_list.html'
    context_object_name = 'managers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.CENTER_HEAD
        ).select_related('center_head_profile__center')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(center_head_profile__center__name__icontains=search)
            )
        
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
        context['status_filter'] = self.request.GET.get('status', '')
        return context


# Center Head - Faculty Management

class CreateFacultyView(CenterHeadRequiredMixin, View):
    """Center head creates faculty members."""
    
    template_name = 'accounts/create_faculty.html'
    form_class = FacultyCreationForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            from django.db import transaction
            from apps.faculty.models import Faculty
            
            try:
                with transaction.atomic():
                    # Get center head's center
                    if not hasattr(request.user, 'center_head_profile'):
                        messages.error(request, 'You are not associated with any center.')
                        return redirect('accounts:profile')
                    
                    center = request.user.center_head_profile.center
                    
                    # Create user
                    user = User.objects.create_user(
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role=User.FACULTY
                    )
                    
                    # Create faculty profile
                    faculty = Faculty.objects.create(
                        user=user,
                        center=center,
                        employee_id=form.cleaned_data.get('employee_id', ''),
                        joining_date=form.cleaned_data['joining_date'],
                        qualification=form.cleaned_data.get('qualification', ''),
                        specialization=form.cleaned_data.get('specialization', ''),
                        experience_years=form.cleaned_data.get('experience_years', 0),
                        created_by=request.user,
                        modified_by=request.user
                    )
                    
                    messages.success(
                        request,
                        f'Faculty {user.get_full_name()} created successfully! '
                        f'Username: {user.email}'
                    )
                    return redirect('accounts:faculty_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating faculty: {str(e)}')
        
        return render(request, self.template_name, {'form': form})


class FacultyListView(CenterHeadRequiredMixin, ListView):
    """List all faculty in center head's center."""
    
    model = User
    template_name = 'accounts/faculty_list.html'
    context_object_name = 'faculty_members'
    paginate_by = 20
    
    def get_queryset(self):
        # Get center head's center
        if not hasattr(self.request.user, 'center_head_profile'):
            return User.objects.none()
        
        center = self.request.user.center_head_profile.center
        
        queryset = User.objects.filter(
            role=User.FACULTY,
            faculty_profile__center=center,
            faculty_profile__deleted_at__isnull=True
        ).select_related('faculty_profile')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(faculty_profile__specialization__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True, faculty_profile__is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(
                Q(is_active=False) | Q(faculty_profile__is_active=False)
            )
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        if hasattr(self.request.user, 'center_head_profile'):
            context['center'] = self.request.user.center_head_profile.center
        return context


class EditFacultyCredentialsView(CenterHeadRequiredMixin, View):
    """Center head edits faculty username and password."""
    
    template_name = 'accounts/edit_faculty_credentials.html'
    
    def get(self, request, pk):
        # Verify faculty belongs to center head's center
        if not hasattr(request.user, 'center_head_profile'):
            messages.error(request, 'You are not associated with any center.')
            return redirect('accounts:profile')
        
        center = request.user.center_head_profile.center
        user = get_object_or_404(
            User,
            pk=pk,
            role=User.FACULTY,
            faculty_profile__center=center,
            faculty_profile__deleted_at__isnull=True
        )
        
        return render(request, self.template_name, {'faculty_user': user})
    
    def post(self, request, pk):
        # Verify faculty belongs to center head's center
        if not hasattr(request.user, 'center_head_profile'):
            messages.error(request, 'You are not associated with any center.')
            return redirect('accounts:profile')
        
        center = request.user.center_head_profile.center
        user = get_object_or_404(
            User,
            pk=pk,
            role=User.FACULTY,
            faculty_profile__center=center,
            faculty_profile__deleted_at__isnull=True
        )
        
        # Update basic info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        
        # Update email/username
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != user.email:
            # Check if email already exists
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                messages.error(request, f'Email {new_email} is already in use.')
                return render(request, self.template_name, {'faculty_user': user})
            user.email = new_email
            messages.success(request, f'Username/Email updated to {new_email}')
        
        # Handle password change
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if new_password or confirm_password:
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, self.template_name, {'faculty_user': user})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, self.template_name, {'faculty_user': user})
            
            user.set_password(new_password)
            messages.success(request, f'Password updated for {user.get_full_name()}!')
        
        # Update faculty profile
        if hasattr(user, 'faculty_profile'):
            faculty = user.faculty_profile
            faculty.employee_id = request.POST.get('employee_id', faculty.employee_id)
            faculty.specialization = request.POST.get('specialization', faculty.specialization)
            faculty.qualification = request.POST.get('qualification', faculty.qualification)
            faculty.is_active = 'is_active' in request.POST
            faculty.modified_by = request.user
            faculty.save()
        
        try:
            user.save()
            messages.success(request, f'Faculty {user.get_full_name()} updated successfully!')
            return redirect('accounts:faculty_list')
        except Exception as e:
            messages.error(request, f'Error updating faculty: {str(e)}')
            return render(request, self.template_name, {'faculty_user': user})
