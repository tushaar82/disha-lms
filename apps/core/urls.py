"""
URL configuration for core app.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    
    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/complete/', views.MarkTaskCompletedView.as_view(), name='task_complete'),
    path('tasks/<int:pk>/update-status/', views.UpdateTaskStatusView.as_view(), name='task_update_status'),
    
    # AI Configuration (Master Account Only)
    path('admin/config/', views.SystemConfigurationView.as_view(), name='system_config'),
    path('admin/config/gemini/', views.GeminiAPIKeyConfigView.as_view(), name='gemini_config'),
    path('admin/config/ai-settings/', views.AISettingsView.as_view(), name='ai_settings'),
    path('admin/config/test-gemini/', views.TestGeminiConnectionView.as_view(), name='test_gemini'),
]
