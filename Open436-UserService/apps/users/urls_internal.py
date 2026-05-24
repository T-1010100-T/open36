"""
User app internal API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_internal

router = DefaultRouter()
router.register(r'users', views_internal.InternalUserViewSet, basename='internal-user')

urlpatterns = [
    path('', include(router.urls)),
]
