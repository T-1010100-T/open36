"""
User model tests
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.users.models import UserProfile, UserStatistics


class UserProfileModelTest(TestCase):
    """用户资料模型测试"""

    def setUp(self):
        self.profile = UserProfile.objects.create(
            user_id=1,
            nickname='TestUser',
            bio='A test user'
        )

    def test_create_profile(self):
        """测试创建用户资料"""
        self.assertEqual(self.profile.user_id, 1)
        self.assertEqual(self.profile.nickname, 'TestUser')
        self.assertEqual(self.profile.bio, 'A test user')
        self.assertIsNone(self.profile.avatar_url)
        self.assertIsNone(self.profile.nickname_updated_at)

    def test_can_update_nickname_first_time(self):
        """首次修改昵称应允许"""
        self.assertTrue(self.profile.can_update_nickname())

    def test_can_update_nickname_within_30_days(self):
        """30天内修改应拒绝"""
        self.profile.nickname_updated_at = timezone.now() - timedelta(days=5)
        self.profile.save()
        self.assertFalse(self.profile.can_update_nickname())

    def test_can_update_nickname_after_30_days(self):
        """30天后修改应允许"""
        self.profile.nickname_updated_at = timezone.now() - timedelta(days=31)
        self.profile.save()
        self.assertTrue(self.profile.can_update_nickname())

    def test_update_nickname(self):
        """测试更新昵称"""
        self.profile.update_nickname('NewNickname')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.nickname, 'NewNickname')
        self.assertIsNotNone(self.profile.nickname_updated_at)


class UserStatisticsModelTest(TestCase):
    """用户统计模型测试"""

    def setUp(self):
        self.profile = UserProfile.objects.create(
            user_id=2,
            nickname='StatsUser'
        )
        self.stats = UserStatistics.objects.create(user_id=2)

    def test_default_values(self):
        """测试默认值"""
        self.assertEqual(self.stats.posts_count, 0)
        self.assertEqual(self.stats.replies_count, 0)
        self.assertEqual(self.stats.likes_received, 0)
        self.assertEqual(self.stats.favorites_received, 0)

    def test_increment_field(self):
        """测试原子性更新"""
        result = UserStatistics.increment_field(2, 'posts_count', 1)
        self.assertEqual(result.posts_count, 1)

        result = UserStatistics.increment_field(2, 'posts_count', 3)
        self.assertEqual(result.posts_count, 4)

    def test_increment_field_negative(self):
        """测试减量更新"""
        UserStatistics.increment_field(2, 'posts_count', 5)
        result = UserStatistics.increment_field(2, 'posts_count', -2)
        self.assertEqual(result.posts_count, 3)

    def test_increment_field_invalid(self):
        """测试无效字段"""
        with self.assertRaises(ValueError):
            UserStatistics.increment_field(2, 'invalid_field', 1)

    def test_increment_field_new_user(self):
        """测试为新用户创建统计记录"""
        result = UserStatistics.increment_field(999, 'posts_count', 1)
        self.assertEqual(result.posts_count, 1)
