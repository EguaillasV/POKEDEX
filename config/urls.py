"""
URL Configuration for Animal Recognition Project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from src.interfaces.api.views import StartDetectionView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Detection (root level for simplicity)
    path('start-detection/', StartDetectionView.as_view(), name='start-detection-root'),
    
    # API endpoints (Interface Layer)
    path('api/', include('src.interfaces.api.urls')),
    
    # Web views (Interface Layer)
    path('', include('src.interfaces.web.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
