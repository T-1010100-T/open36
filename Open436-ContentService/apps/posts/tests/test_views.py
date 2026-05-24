"""
Post API tests
"""
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.posts.models import Post, PostEditHistory
from apps.posts.views import PostViewSet
from apps.posts.views_internal import InternalPostViewSet


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class PostViewSetTest(TestCase):
    """帖子视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author_id=1,
            section_id=1,
        )

    def _add_auth_headers(self, request, user_id=None, role='user', user_status='active'):
        if user_id is not None:
            request.META['HTTP_X_USER_ID'] = str(user_id)
            request.META['HTTP_X_USERNAME'] = 'testuser'
            request.META['HTTP_X_USER_ROLE'] = role
            request.META['HTTP_X_USER_STATUS'] = user_status
        return request

    def test_list_posts(self):
        """测试获取帖子列表"""
        request = self.factory.get('/api/posts/')
        view = PostViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_list_posts_filter_section(self):
        """测试按板块筛选"""
        Post.objects.create(title='Another Post', content='Content.', author_id=2, section_id=2)
        request = self.factory.get('/api/posts/', {'section_id': 1})
        view = PostViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_create_post(self):
        """测试发布帖子"""
        request = self.factory.post('/api/posts/', {
            'title': 'New Post Title',
            'content': 'New post content here.',
            'section_id': 1,
        }, format='json')
        request = self._add_auth_headers(request, user_id=1)
        view = PostViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'New Post Title')

    def test_create_post_unauthenticated(self):
        """测试未登录无法发布"""
        request = self.factory.post('/api/posts/', {
            'title': 'New Post',
            'content': 'Content.',
            'section_id': 1,
        }, format='json')
        view = PostViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_post_pending_user_forbidden(self):
        """测试pending用户无法发布帖子"""
        request = self.factory.post('/api/posts/', {
            'title': 'New Post',
            'content': 'Content.',
            'section_id': 1,
        }, format='json')
        request = self._add_auth_headers(request, user_id=1, user_status='pending')
        view = PostViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_post_invalid_title(self):
        """测试标题过短"""
        request = self.factory.post('/api/posts/', {
            'title': 'Hi',
            'content': 'Content.',
            'section_id': 1,
        }, format='json')
        request = self._add_auth_headers(request, user_id=1)
        view = PostViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_post(self):
        """测试获取帖子详情"""
        request = self.factory.get(f'/api/posts/{self.post.id}/')
        view = PostViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Test Post')

    def test_retrieve_deleted_post(self):
        """测试已删除帖子不可见"""
        self.post.soft_delete()
        request = self.factory.get(f'/api/posts/{self.post.id}/')
        view = PostViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post(self):
        """测试编辑帖子"""
        request = self.factory.put(f'/api/posts/{self.post.id}/', {
            'title': 'Updated Title',
            'content': 'Updated content here.',
        }, format='json')
        request = self._add_auth_headers(request, user_id=1)
        view = PostViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Updated Title')

    def test_delete_post(self):
        """测试删除帖子"""
        request = self.factory.delete(f'/api/posts/{self.post.id}/')
        request = self._add_auth_headers(request, user_id=1)
        view = PostViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_DELETED)

    def test_pin_post_admin(self):
        """测试管理员置顶"""
        request = self.factory.post(f'/api/posts/{self.post.id}/pin/', {
            'pin_type': 'global',
        }, format='json')
        request = self._add_auth_headers(request, user_id=1, role='admin')
        view = PostViewSet.as_view({'post': 'pin'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_pinned)

    def test_pin_post_user_forbidden(self):
        """测试普通用户无法置顶"""
        request = self.factory.post(f'/api/posts/{self.post.id}/pin/', {
            'pin_type': 'global',
        }, format='json')
        request = self._add_auth_headers(request, user_id=1, role='user')
        view = PostViewSet.as_view({'post': 'pin'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class InternalPostViewSetTest(TestCase):
    """内部接口测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.post = Post.objects.create(
            title='Internal Test',
            content='Content.',
            author_id=1,
            section_id=1,
        )

    def test_increment_views(self):
        """测试增加浏览量"""
        request = self.factory.post(f'/internal/posts/{self.post.id}/increment-views/')
        view = InternalPostViewSet.as_view({'post': 'increment_views'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['views_count'], 1)

    def test_validate_post(self):
        """测试验证帖子"""
        request = self.factory.get(f'/internal/posts/{self.post.id}/validate/')
        view = InternalPostViewSet.as_view({'get': 'validate_post'})
        response = view(request, pk=self.post.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], self.post.id)

    def test_by_user(self):
        """测试获取用户帖子"""
        request = self.factory.get('/internal/posts/by-user/1/')
        view = InternalPostViewSet.as_view({'get': 'by_user'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
