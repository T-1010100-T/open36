"""
Comment API tests
"""
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.comments.models import Reply, PostLike, PostFavorite
from apps.comments.views import ReplyViewSet, InteractionViewSet
from apps.comments.views_internal import InternalReplyViewSet, InternalInteractionViewSet


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class ReplyViewSetTest(TestCase):
    """回复视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.reply = Reply.objects.create(
            post_id=1,
            author_id=1,
            content='Test reply',
            floor_number=1,
        )

    def _add_auth_headers(self, request, user_id=None, role='user', user_status='active'):
        if user_id is not None:
            request.META['HTTP_X_USER_ID'] = str(user_id)
            request.META['HTTP_X_USERNAME'] = 'testuser'
            request.META['HTTP_X_USER_ROLE'] = role
            request.META['HTTP_X_USER_STATUS'] = user_status
        return request

    def test_list_replies(self):
        """测试获取回复列表"""
        request = self.factory.get('/api/replies/', {'post_id': 1})
        view = ReplyViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_list_replies_missing_post_id(self):
        """测试缺少 post_id"""
        request = self.factory.get('/api/replies/')
        view = ReplyViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reply(self):
        """测试发布回复"""
        request = self.factory.post('/api/replies/', {
            'post_id': 1,
            'content': 'New reply',
        }, format='json')
        request = self._add_auth_headers(request, user_id=2)
        view = ReplyViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['floor_number'], 2)

    def test_create_reply_pending_user_forbidden(self):
        """测试pending用户无法发布回复"""
        request = self.factory.post('/api/replies/', {
            'post_id': 1,
            'content': 'New reply',
        }, format='json')
        request = self._add_auth_headers(request, user_id=2, user_status='pending')
        view = ReplyViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reply_unauthenticated(self):
        """测试未登录无法发布"""
        request = self.factory.post('/api/replies/', {
            'post_id': 1,
            'content': 'New reply',
        }, format='json')
        view = ReplyViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_reply(self):
        """测试编辑回复"""
        request = self.factory.put(f'/api/replies/{self.reply.id}/', {
            'content': 'Updated reply',
        }, format='json')
        request = self._add_auth_headers(request, user_id=1)
        view = ReplyViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.reply.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['content'], 'Updated reply')

    def test_delete_reply(self):
        """测试删除回复"""
        request = self.factory.delete(f'/api/replies/{self.reply.id}/')
        request = self._add_auth_headers(request, user_id=1)
        view = ReplyViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.reply.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reply.refresh_from_db()
        self.assertTrue(self.reply.is_deleted)


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class InteractionViewSetTest(TestCase):
    """互动视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _add_auth_headers(self, request, user_id=1, role='user', user_status='active'):
        request.META['HTTP_X_USER_ID'] = str(user_id)
        request.META['HTTP_X_USERNAME'] = 'testuser'
        request.META['HTTP_X_USER_ROLE'] = role
        request.META['HTTP_X_USER_STATUS'] = user_status
        return request

    def test_toggle_like(self):
        """测试点赞"""
        request = self.factory.post('/api/posts/1/like/')
        request = self._add_auth_headers(request, user_id=1)
        view = InteractionViewSet.as_view({'post': 'toggle_like'})
        response = view(request, post_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '点赞成功')

    def test_toggle_like_pending_user_forbidden(self):
        """测试pending用户无法点赞"""
        request = self.factory.post('/api/posts/1/like/')
        request = self._add_auth_headers(request, user_id=1, user_status='pending')
        view = InteractionViewSet.as_view({'post': 'toggle_like'})
        response = view(request, post_id=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_like_cancel(self):
        """测试取消点赞"""
        PostLike.objects.create(post_id=1, user_id=1)
        request = self.factory.post('/api/posts/1/like/')
        request = self._add_auth_headers(request, user_id=1)
        view = InteractionViewSet.as_view({'post': 'toggle_like'})
        response = view(request, post_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '已取消点赞')

    def test_toggle_favorite(self):
        """测试收藏"""
        request = self.factory.post('/api/posts/1/favorite/')
        request = self._add_auth_headers(request, user_id=1)
        view = InteractionViewSet.as_view({'post': 'toggle_favorite'})
        response = view(request, post_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '收藏成功')

    def test_my_favorites(self):
        """测试我的收藏"""
        PostFavorite.objects.create(post_id=1, user_id=1)
        PostFavorite.objects.create(post_id=2, user_id=1)
        request = self.factory.get('/api/favorites/')
        request = self._add_auth_headers(request, user_id=1)
        view = InteractionViewSet.as_view({'get': 'my_favorites'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class InternalViewSetTest(TestCase):
    """内部接口测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        Reply.objects.create(post_id=1, author_id=1, content='Reply 1', floor_number=1)
        Reply.objects.create(post_id=1, author_id=1, content='Reply 2', floor_number=2)
        PostLike.objects.create(post_id=1, user_id=1)
        PostFavorite.objects.create(post_id=1, user_id=1)

    def test_replies_count(self):
        """测试回复数"""
        request = self.factory.get('/internal/posts/1/replies/count/')
        view = InternalReplyViewSet.as_view({'get': 'count'})
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['replies_count'], 2)

    def test_likes_count(self):
        """测试点赞数"""
        request = self.factory.get('/internal/posts/1/likes/count/')
        view = InternalInteractionViewSet.as_view({'get': 'likes_count'})
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['likes_count'], 1)

    def test_favorites_count(self):
        """测试收藏数"""
        request = self.factory.get('/internal/posts/1/favorites/count/')
        view = InternalInteractionViewSet.as_view({'get': 'favorites_count'})
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['favorites_count'], 1)

    def test_by_user(self):
        """测试用户回复历史"""
        request = self.factory.get('/internal/users/1/replies/')
        view = InternalReplyViewSet.as_view({'get': 'by_user'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)
