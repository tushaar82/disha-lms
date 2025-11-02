"""
URL configuration for centers app.
"""

from django.urls import path
from . import views

app_name = 'centers'

urlpatterns = [
    # Center Head Dashboard
    path('dashboard/', views.CenterDashboardView.as_view(), name='dashboard'),
    
    # Master Account - Center Switching (T116)
    path('access/<int:center_id>/', views.AccessCenterDashboardView.as_view(), name='access'),
    
    # Master Account - Center Management
    path('', views.CenterListView.as_view(), name='list'),
    path('create/', views.CenterCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CenterDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CenterUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.CenterDeleteView.as_view(), name='delete'),
]
