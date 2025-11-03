"""
URL configuration for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # User Management (General)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # Master Account - Center Manager Management
    path('center-managers/', views.CenterManagerListView.as_view(), name='center_manager_list'),
    path('center-managers/create/', views.CreateCenterManagerView.as_view(), name='create_center_manager'),
    
    # Center Head - Faculty Management
    path('faculty/', views.FacultyListView.as_view(), name='faculty_list'),
    path('faculty/create/', views.CreateFacultyView.as_view(), name='create_faculty'),
    path('faculty/<int:pk>/edit-credentials/', views.EditFacultyCredentialsView.as_view(), name='edit_faculty_credentials'),
]
