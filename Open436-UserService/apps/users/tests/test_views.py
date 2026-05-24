"""
User API tests
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from apps.users.models import UserProfile, UserStatistics
from apps.users.views import UserViewSet, AdminUserViewSet
from apps.users.views_internal import InternalUserViewSet


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class UserViewSetTest(TestCase):
    """用户视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.profile = UserProfile.objects.create(
            user_id=1,
            nickname='Alice',
            bio='A test user'
        )
        UserStatistics.objects.create(user_id=1)

    def _add_auth_headers(self, request, user_id=None, role='user'):
        """模拟 Kong Gateway 注入的 headers"""
        if user_id:
            request.META['HTTP_X_USER_ID'] = str(user_id)
            request.META['HTTP_X_USERNAME'] = 'testuser'
            request.META['HTTP_X_USER_ROLE'] = role
        return request

    def test_retrieve_user(self):
        """测试获取用户信息"""
        request = self.factory.get(f'/api/users/1/')
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nickname'], 'Alice')
        self.assertIn('statistics', response.data['data'])

    def test_retrieve_user_not_found(self):
        """测试获取不存在的用户"""
        request = self.factory.get('/api/users/999/')
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, user_id=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_profile(self):
        """测试更新用户资料"""
        request = self.factory.put(
            '/api/users/1/profile/',
            data={'bio': 'Updated bio'},
            format='json'
        )
        request = self._add_auth_headers(request, user_id=1)
        view = UserViewSet.as_view({'put': 'update_profile'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['bio'], 'Updated bio')

    def test_update_profile_permission_denied(self):
        """测试非本人/管理员无法修改"""
        request = self.factory.put(
            '/api/users/1/profile/',
            data={'bio': 'Hacked'},
            format='json'
        )
        request = self._add_auth_headers(request, user_id=2)
        view = UserViewSet.as_view({'put': 'update_profile'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_statistics(self):
        """测试获取统计数据"""
        request = self.factory.get('/api/users/1/statistics/')
        view = UserViewSet.as_view({'get': 'statistics'})
        response = view(request, user_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['posts_count'], 0)


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class AdminUserViewSetTest(TestCase):
    """管理员视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.profile = UserProfile.objects.create(user_id=1, nickname='Admin')
        UserStatistics.objects.create(user_id=1)

    def _add_auth_headers(self, request, user_id=1, role='admin'):
        request.META['HTTP_X_USER_ID'] = str(user_id)
        request.META['HTTP_X_USERNAME'] = 'admin'
        request.META['HTTP_X_USER_ROLE'] = role
        return request

    def test_list_users(self):
        """测试管理员获取用户列表"""
        request = self.factory.get('/api/admin/users/')
        request = self._add_auth_headers(request, role='admin')
        view = AdminUserViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_list_users_permission_denied(self):
        """测试普通用户无法访问管理员接口"""
        request = self.factory.get('/api/admin/users/')
        request = self._add_auth_headers(request, role='user')
        view = AdminUserViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class InternalUserViewSetTest(TestCase):
    """内部服务视图集测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        UserProfile.objects.create(user_id=1, nickname='Alice')
        UserProfile.objects.create(user_id=2, nickname='Bob')
        UserStatistics.objects.create(user_id=1)
        UserStatistics.objects.create(user_id=2)

    def test_batch_get_users(self):
        """测试批量获取用户信息"""
        request = self.factory.post(
            '/internal/users/batch/',
            data={'user_ids': [1, 2]},
            format='json'
        )
        view = InternalUserViewSet.as_view({'post': 'batch'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_batch_get_users_empty(self):
        """测试空用户列表"""
        request = self.factory.post(
            '/internal/users/batch/',
            data={'user_ids': []},
            format='json'
        )
        view = InternalUserViewSet.as_view({'post': 'batch'})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_increment_statistics(self):
        """测试更新统计数据"""
        request = self.factory.post(
            '/internal/users/1/statistics/increment/',
            data={'field': 'posts_count', 'value': 1},
            format='json'
        )
        view = InternalUserViewSet.as_view({'post': 'increment_statistics'})
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['posts_count'], 1)

    def test_increment_statistics_invalid_field(self):
        """测试无效字段"""
        request = self.factory.post(
            '/internal/users/1/statistics/increment/',
            data={'field': 'invalid', 'value': 1},
            format='json'
        )
        view = InternalUserViewSet.as_view({'post': 'increment_statistics'})
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
