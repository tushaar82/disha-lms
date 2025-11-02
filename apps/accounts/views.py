"""
Views for authentication and user management.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView
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
