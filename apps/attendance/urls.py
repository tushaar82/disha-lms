"""
URL configuration for attendance app.
"""

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('today/', views.TodayAttendanceView.as_view(), name='today'),
    path('mark/', views.MarkAttendanceView.as_view(), name='mark'),
    path('history/', views.AttendanceHistoryView.as_view(), name='history'),
    
    # AJAX endpoints
    path('api/topics/<int:assignment_id>/', views.GetTopicsBySubjectView.as_view(), name='get_topics'),
    path('api/students/available/', views.GetStudentsWithoutTodayAttendanceView.as_view(), name='get_available_students'),
    path('api/student-subjects/<int:student_id>/', views.GetStudentSubjectsView.as_view(), name='get_student_subjects'),
]
