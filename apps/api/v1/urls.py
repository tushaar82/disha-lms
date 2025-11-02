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

# Register US5 ViewSets (T189 - Feedback/Surveys)
router.register(r'surveys', views.SurveyViewSet, basename='survey')

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
    
    # Feedback/Survey endpoints (T189 - US5)
    path('surveys/<int:pk>/send/', views.SendSurveyAPIView.as_view(), name='survey-send'),
    path('surveys/submit/<str:token>/', views.SubmitSurveyAPIView.as_view(), name='survey-submit'),
    path('surveys/<int:pk>/responses/', views.SurveyResponsesAPIView.as_view(), name='survey-responses'),
    
    # Feedback analytics endpoints
    path('feedback/trends/', views.SatisfactionTrendsAPIView.as_view(), name='feedback-trends'),
    path('feedback/faculty-breakdown/', views.FacultyBreakdownAPIView.as_view(), name='feedback-faculty-breakdown'),
    
    # Router URLs (includes all registered ViewSets)
    path('', include(router.urls)),
]
