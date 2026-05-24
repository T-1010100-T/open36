"""
Comment model tests
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.comments.models import Reply, PostLike, PostFavorite


class ReplyModelTest(TestCase):
    """回复模型测试"""

    def setUp(self):
        self.reply = Reply.objects.create(
            post_id=1,
            author_id=1,
            content='Test reply content',
            floor_number=1,
        )

    def test_create_reply(self):
        """测试创建回复"""
        self.assertEqual(self.reply.post_id, 1)
        self.assertEqual(self.reply.author_id, 1)
        self.assertEqual(self.reply.content, 'Test reply content')
        self.assertEqual(self.reply.floor_number, 1)
        self.assertFalse(self.reply.is_deleted)

    def test_soft_delete(self):
        """测试软删除"""
        self.reply.soft_delete()
        self.assertTrue(self.reply.is_deleted)

    def test_can_edit_within_5m(self):
        """5分钟内可以编辑"""
        self.assertTrue(self.reply.can_edit(1))

    def test_can_edit_after_5m(self):
        """5分钟后不能编辑"""
        self.reply.created_at = timezone.now() - timedelta(minutes=6)
        self.reply.save()
        self.assertFalse(self.reply.can_edit(1))

    def test_can_edit_admin(self):
        """管理员总是可以编辑"""
        self.reply.created_at = timezone.now() - timedelta(days=1)
        self.reply.save()
        self.assertTrue(self.reply.can_edit(999, is_admin=True))

    def test_can_edit_other_user(self):
        """其他用户不能编辑"""
        self.assertFalse(self.reply.can_edit(2))

    def test_record_edit(self):
        """测试记录编辑"""
        self.reply.record_edit()
        self.assertEqual(self.reply.edit_count, 1)
        self.assertIsNotNone(self.reply.last_edited_at)


class PostLikeModelTest(TestCase):
    """点赞模型测试"""

    def test_create_like(self):
        """测试创建点赞"""
        like = PostLike.objects.create(post_id=1, user_id=1)
        self.assertEqual(like.post_id, 1)
        self.assertEqual(like.user_id, 1)

    def test_unique_like(self):
        """测试同一用户不能重复点赞"""
        PostLike.objects.create(post_id=1, user_id=1)
        with self.assertRaises(Exception):
            PostLike.objects.create(post_id=1, user_id=1)


class PostFavoriteModelTest(TestCase):
    """收藏模型测试"""

    def test_create_favorite(self):
        """测试创建收藏"""
        fav = PostFavorite.objects.create(post_id=1, user_id=1)
        self.assertEqual(fav.post_id, 1)
        self.assertEqual(fav.user_id, 1)

    def test_unique_favorite(self):
        """测试同一用户不能重复收藏"""
        PostFavorite.objects.create(post_id=1, user_id=1)
        with self.assertRaises(Exception):
            PostFavorite.objects.create(post_id=1, user_id=1)
