"""
User app public API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/users/', views.AdminUserViewSet.as_view({'get': 'list', 'post': 'create'}), name='admin-users'),
]
