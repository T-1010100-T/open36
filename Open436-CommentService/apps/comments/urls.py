"""
Comment app public API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'replies', views.ReplyViewSet, basename='reply')
router.register(r'topics', views.TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<int:post_id>/interaction-status/', views.InteractionViewSet.as_view({'get': 'interaction_status'}), name='interaction-status'),
    path('posts/<int:post_id>/like/', views.InteractionViewSet.as_view({'post': 'toggle_like'}), name='toggle-like'),
    path('posts/<int:post_id>/favorite/', views.InteractionViewSet.as_view({'post': 'toggle_favorite'}), name='toggle-favorite'),
    path('favorites/', views.InteractionViewSet.as_view({'get': 'my_favorites'}), name='my-favorites'),
    # 分享
    path('posts/<int:post_id>/share/', views.ShareViewSet.as_view({'post': 'record_share'}), name='record-share'),
    path('posts/<int:post_id>/share-count/', views.ShareViewSet.as_view({'get': 'share_count'}), name='share-count'),
    # 用户关注
    path('follows/users/<int:target_id>/toggle/', views.FollowViewSet.as_view({'post': 'toggle_follow'}), name='toggle-follow'),
    path('follows/users/<int:target_id>/status/', views.FollowViewSet.as_view({'get': 'follow_status'}), name='follow-status'),
    path('follows/my-following/', views.FollowViewSet.as_view({'get': 'my_following'}), name='my-following'),
    path('follows/my-followers/', views.FollowViewSet.as_view({'get': 'my_followers'}), name='my-followers'),
]
