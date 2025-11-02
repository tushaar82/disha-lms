"""
Views for student management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q

from apps.core.mixins import CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin
from .models import Student
from .forms import StudentForm, AssignmentForm
from apps.subjects.models import Assignment


class StudentListView(LoginRequiredMixin, CenterHeadRequiredMixin, ListView):
    """List all students. Master sees all, Center Head sees their center."""
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def get_queryset(self):
        # Master account can see all students
        if self.request.user.is_master_account:
            queryset = Student.objects.filter(deleted_at__isnull=True).select_related('center')
        else:
            # Get center from user's profile
            if not hasattr(self.request.user, 'center_head_profile'):
                return Student.objects.none()
            
            queryset = Student.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('center')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(enrollment_number__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-enrollment_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class StudentCreateView(LoginRequiredMixin, CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Create a new student."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')
    audit_action = 'CREATE'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit center selection to user's center
        form.fields['center'].initial = self.request.user.center_head_profile.center
        form.fields['center'].widget.attrs['readonly'] = True
        return form
    
    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.get_full_name()} created successfully!')
        return super().form_valid(form)


class StudentDetailView(LoginRequiredMixin, DetailView):
    """View student details. Accessible by Master, Center Head, and Faculty."""
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions based on user role."""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Master account can view all students
        if request.user.is_master_account:
            return super().dispatch(request, *args, **kwargs)
        
        # Center head and faculty must have profiles
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile'):
                from django.contrib import messages
                messages.error(request, "Your center head profile is not set up.")
                return redirect('accounts:profile')
        elif request.user.is_faculty_member:
            if not hasattr(request.user, 'faculty_profile'):
                from django.contrib import messages
                messages.error(request, "Your faculty profile is not set up.")
                return redirect('accounts:profile')
        else:
            # Not authorized
            raise PermissionDenied("You don't have permission to view student details.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter students based on user role."""
        queryset = Student.objects.filter(deleted_at__isnull=True)
        
        # Master account can see all students
        if self.request.user.is_master_account:
            return queryset
        
        # Center head can see students in their center
        if self.request.user.is_center_head:
            return queryset.filter(center=self.request.user.center_head_profile.center)
        
        # Faculty can see students they teach (have assignments with)
        if self.request.user.is_faculty_member:
            return queryset.filter(
                assignments__faculty=self.request.user.faculty_profile,
                assignments__is_active=True
            ).distinct()
        
        return Student.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get student's assignments
        context['assignments'] = Assignment.objects.filter(
            student=self.object,
            is_active=True
        ).select_related('subject', 'faculty__user')
        
        # Get attendance summary
        from apps.attendance.services import get_student_attendance_summary
        context['attendance_summary'] = get_student_attendance_summary(self.object)
        
        return context


class StudentUpdateView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, UpdateView):
    """Update student information."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    audit_action = 'UPDATE'
    
    def get_queryset(self):
        return Student.objects.filter(
            center=self.request.user.center_head_profile.center,
            deleted_at__isnull=True
        )
    
    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.get_full_name()} updated successfully!')
        return super().form_valid(form)


class StudentDeleteView(LoginRequiredMixin, CenterHeadRequiredMixin, AuditLogMixin, DeleteView):
    """Soft delete a student."""
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:list')
    audit_action = 'DELETE'
    
    def get_queryset(self):
        return Student.objects.filter(
            center=self.request.user.center_head_profile.center,
            deleted_at__isnull=True
        )
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete
        self.object.delete()
        messages.success(request, f'Student {self.object.get_full_name()} deleted successfully!')
        return redirect(self.success_url)


class AssignSubjectView(LoginRequiredMixin, CenterHeadRequiredMixin, SetCreatedByMixin, AuditLogMixin, CreateView):
    """Assign a subject to a student."""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'students/assign_subject.html'
    audit_action = 'CREATE'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = get_object_or_404(
            Student,
            pk=self.kwargs['student_pk'],
            center=self.request.user.center_head_profile.center
        )
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        student = get_object_or_404(
            Student,
            pk=self.kwargs['student_pk'],
            center=self.request.user.center_head_profile.center
        )
        form.fields['student'].initial = student
        form.fields['student'].widget.attrs['readonly'] = True
        return form
    
    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.kwargs['student_pk']})
    
    def form_valid(self, form):
        messages.success(self.request, 'Subject assigned successfully!')
        return super().form_valid(form)


class AssignFacultyView(LoginRequiredMixin, CenterHeadRequiredMixin, UpdateView):
    """Update faculty assignment for a student's subject."""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'students/assign_faculty.html'
    
    def get_queryset(self):
        return Assignment.objects.filter(
            student__center=self.request.user.center_head_profile.center
        )
    
    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.object.student.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Faculty assigned successfully!')
        return super().form_valid(form)


class ReadyForTransferView(LoginRequiredMixin, CenterHeadRequiredMixin, ListView):
    """List students ready for transfer (completed status)."""
    model = Student
    template_name = 'students/ready_for_transfer.html'
    context_object_name = 'students'
    
    def get_queryset(self):
        return Student.objects.filter(
            center=self.request.user.center_head_profile.center,
            status='completed',
            deleted_at__isnull=True
        ).order_by('-modified_at')
