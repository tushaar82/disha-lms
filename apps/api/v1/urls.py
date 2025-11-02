"""
API URL configuration for version 1.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api_v1'

# Create router for ViewSets
router = DefaultRouter()

# Register US2 ViewSets (T106)
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'faculty', views.FacultyViewSet, basename='faculty')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'assignments', views.AssignmentViewSet, basename='assignment')

# Register US3 ViewSets (T131)
router.register(r'centers', views.CenterViewSet, basename='center')
router.register(r'center-heads', views.CenterHeadViewSet, basename='centerhead')

# URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginAPIView.as_view(), name='login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('auth/me/', views.MeAPIView.as_view(), name='me'),
    
    # Attendance endpoints
    path('attendance/', views.AttendanceViewSet.as_view(), name='attendance'),
    path('attendance/today/', views.TodayAttendanceAPIView.as_view(), name='attendance-today'),
    path('attendance/bulk/', views.BulkAttendanceAPIView.as_view(), name='attendance-bulk'),
    
    # Report endpoints (T154 - US4)
    path('reports/center/<int:center_id>/', views.CenterReportAPIView.as_view(), name='report-center'),
    path('reports/student/<int:student_id>/', views.StudentReportAPIView.as_view(), name='report-student'),
    path('reports/faculty/<int:faculty_id>/', views.FacultyReportAPIView.as_view(), name='report-faculty'),
    path('reports/insights/', views.InsightsAPIView.as_view(), name='report-insights'),
    path('reports/insights/<int:center_id>/', views.InsightsAPIView.as_view(), name='report-insights-center'),
    
    # Router URLs (includes all registered ViewSets)
    path('', include(router.urls)),
]
