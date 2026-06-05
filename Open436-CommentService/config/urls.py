"""
URL configuration for Open436 CommentService.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/comments/', include('apps.comments.urls')),
    path('api/', include('apps.comments.urls')),
    path('internal/', include('apps.comments.urls_internal')),
    path('', include('apps.core.urls')),
]
