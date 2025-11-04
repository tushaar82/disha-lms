"""
URL configuration for feedback app.
"""

from django.urls import path
from . import views
from .analysis_views import FacultyFeedbackAnalysisView

app_name = 'feedback'

urlpatterns = [
    # Survey CRUD
    path('', views.SurveyListView.as_view(), name='list'),
    path('create/', views.SurveyCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SurveyUpdateView.as_view(), name='edit'),
    
    # Send survey (T170)
    path('<int:pk>/send/', views.SendSurveyView.as_view(), name='send'),
    
    # Public survey submission (T174, T172 - unique token)
    path('survey/<str:token>/', views.SubmitSurveyView.as_view(), name='submit'),
    
    # Survey responses and analytics (T179)
    path('<int:pk>/responses/', views.SurveyResponsesView.as_view(), name='responses'),
    
    # Faculty Feedback Management
    path('faculty-feedback/', views.FacultyFeedbackListView.as_view(), name='faculty_list'),
    path('faculty-feedback/create/', views.CreateFeedbackRequestView.as_view(), name='create_request'),
    path('faculty-feedback/<int:pk>/whatsapp/', views.SendFeedbackWhatsAppView.as_view(), name='send_whatsapp'),
    path('faculty-feedback/<int:pk>/delete/', views.DeleteFeedbackRequestView.as_view(), name='delete_request'),
    
    # Faculty Feedback Analysis Report
    path('faculty-feedback/analysis/<int:faculty_id>/', FacultyFeedbackAnalysisView.as_view(), name='faculty_analysis'),
    
    # Public faculty feedback submission
    path('faculty/<str:token>/', views.SubmitFacultyFeedbackView.as_view(), name='submit_faculty_feedback'),
]
