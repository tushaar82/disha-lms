"""
URL configuration for Disha LMS project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.core.views import home_view

urlpatterns = [
    # Home page
    path('', home_view, name='home'),
    
    # Django admin
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/v1/', include('apps.api.v1.urls')),
    
    # App URLs
    path('accounts/', include('apps.accounts.urls')),
    path('subjects/', include('apps.subjects.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('students/', include('apps.students.urls')),
    path('faculty/', include('apps.faculty.urls')),
    path('centers/', include('apps.centers.urls')),
    path('reports/', include('apps.reports.urls')),  # T122: Reports URLs
    path('feedback/', include('apps.feedback.urls')),  # T164: Feedback URLs
    path('core/', include('apps.core.urls')),  # Core: Notifications & Tasks
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Customize admin site
admin.site.site_header = "Disha LMS Administration"
admin.site.site_title = "Disha LMS Admin Portal"
admin.site.index_title = "Welcome to Disha LMS Administration"
