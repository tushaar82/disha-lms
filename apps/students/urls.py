"""
URL configuration for students app.
"""

from django.urls import path
from . import views
from . import backdate_views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('create/', views.StudentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
    path('<int:student_pk>/assign-subject/', views.AssignSubjectView.as_view(), name='assign_subject'),
    path('assignment/<int:pk>/assign-faculty/', views.AssignFacultyView.as_view(), name='assign_faculty'),
    path('ready-for-transfer/', views.ReadyForTransferView.as_view(), name='ready_for_transfer'),
    
    # Admin-only backdating URLs
    path('<int:pk>/backdate-admission/', backdate_views.BackdateAdmissionView.as_view(), name='backdate-admission'),
    path('backdate-attendance/', backdate_views.BackdateAttendanceView.as_view(), name='backdate-attendance'),
]
