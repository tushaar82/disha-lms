"""
URL configuration for feedback app.
"""

from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    # Survey CRUD
    path('', views.SurveyListView.as_view(), name='list'),
    path('create/', views.SurveyCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SurveyUpdateView.as_view(), name='edit'),
]
