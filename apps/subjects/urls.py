"""
URL configuration for subjects app.
"""

from django.urls import path
from . import views

app_name = 'subjects'

urlpatterns = [
    # Subject CRUD
    path('', views.SubjectListView.as_view(), name='list'),
    path('create/', views.SubjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SubjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='edit'),
    
    # Topics
    path('topics/', views.TopicListView.as_view(), name='topic_list'),
    path('topics/add/', views.AddTopicView.as_view(), name='add_topic'),
]
