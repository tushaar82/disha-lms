"""
URL configuration for faculty app.
"""

from django.urls import path
from . import views

app_name = 'faculty'

urlpatterns = [
    path('', views.FacultyListView.as_view(), name='list'),
    path('dashboard/', views.FacultyDashboardView.as_view(), name='dashboard'),
    path('dashboard/<int:faculty_id>/', views.FacultyDashboardView.as_view(), name='dashboard_detail'),
    path('create/', views.FacultyCreateView.as_view(), name='create'),
    path('<int:pk>/', views.FacultyDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.FacultyUpdateView.as_view(), name='edit'),
]
