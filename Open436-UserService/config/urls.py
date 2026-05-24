"""
URL configuration for Open436 UserService.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('internal/', include('apps.users.urls_internal')),
    path('', include('apps.core.urls')),
]
