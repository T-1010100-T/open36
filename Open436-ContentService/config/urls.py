"""
URL configuration for Open436 ContentService.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.posts.urls')),
    path('internal/', include('apps.posts.urls_internal')),
    path('', include('apps.core.urls')),
]
