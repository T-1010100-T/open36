"""
Comment app public API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'replies', views.ReplyViewSet, basename='reply')

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<int:post_id>/like/', views.InteractionViewSet.as_view({'post': 'toggle_like'}), name='toggle-like'),
    path('posts/<int:post_id>/favorite/', views.InteractionViewSet.as_view({'post': 'toggle_favorite'}), name='toggle-favorite'),
    path('favorites/', views.InteractionViewSet.as_view({'get': 'my_favorites'}), name='my-favorites'),
]
