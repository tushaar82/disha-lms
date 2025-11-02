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
]
