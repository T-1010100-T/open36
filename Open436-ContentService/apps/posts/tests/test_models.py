"""
Post model tests
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.posts.models import Post, PostEditHistory


class PostModelTest(TestCase):
    """帖子模型测试"""

    def setUp(self):
        self.post = Post.objects.create(
            title='Test Post Title',
            content='This is a test post content.',
            author_id=1,
            section_id=1,
        )

    def test_create_post(self):
        """测试创建帖子"""
        self.assertEqual(self.post.title, 'Test Post Title')
        self.assertEqual(self.post.author_id, 1)
        self.assertEqual(self.post.status, Post.STATUS_PUBLISHED)
        self.assertEqual(self.post.views_count, 0)
        self.assertFalse(self.post.is_pinned)

    def test_soft_delete(self):
        """测试软删除"""
        self.post.soft_delete()
        self.assertEqual(self.post.status, Post.STATUS_DELETED)

    def test_restore(self):
        """测试恢复"""
        self.post.soft_delete()
        self.post.restore()
        self.assertEqual(self.post.status, Post.STATUS_PUBLISHED)

    def test_pin(self):
        """测试置顶"""
        self.post.pin(Post.PIN_GLOBAL)
        self.assertTrue(self.post.is_pinned)
        self.assertEqual(self.post.pin_type, Post.PIN_GLOBAL)

    def test_unpin(self):
        """测试取消置顶"""
        self.post.pin(Post.PIN_GLOBAL)
        self.post.unpin()
        self.assertFalse(self.post.is_pinned)
        self.assertEqual(self.post.pin_type, Post.PIN_NONE)

    def test_increment_views(self):
        """测试增加浏览量"""
        self.post.increment_views()
        self.assertEqual(self.post.views_count, 1)

    def test_can_edit_within_24h(self):
        """24小时内可以编辑"""
        self.assertTrue(self.post.can_edit(1))

    def test_can_edit_after_24h(self):
        """24小时后有限制"""
        self.post.created_at = timezone.now() - timedelta(hours=25)
        self.post.save()
        self.assertTrue(self.post.can_edit(1))

    def test_can_edit_after_24h_exceed(self):
        """24小时后超过5次不能编辑"""
        self.post.created_at = timezone.now() - timedelta(hours=25)
        self.post.edit_count = 5
        self.post.save()
        self.assertFalse(self.post.can_edit(1))

    def test_can_edit_admin(self):
        """管理员总是可以编辑"""
        self.post.created_at = timezone.now() - timedelta(days=30)
        self.post.edit_count = 100
        self.post.save()
        self.assertTrue(self.post.can_edit(999, is_admin=True))

    def test_record_edit(self):
        """测试记录编辑"""
        self.post.record_edit(1)
        self.assertEqual(self.post.edit_count, 1)
        self.assertIsNotNone(self.post.last_edited_at)
        self.assertEqual(self.post.last_edited_by, 1)


class PostEditHistoryModelTest(TestCase):
    """编辑历史模型测试"""

    def setUp(self):
        self.post = Post.objects.create(
            title='Original Title',
            content='Original content.',
            author_id=1,
            section_id=1,
        )
        self.history = PostEditHistory.objects.create(
            post=self.post,
            title='Edited Title',
            content='Edited content.',
            section_id=1,
            edited_by=1,
        )

    def test_create_history(self):
        """测试创建编辑历史"""
        self.assertEqual(self.history.post_id, self.post.id)
        self.assertEqual(self.history.title, 'Edited Title')
        self.assertEqual(self.history.edited_by, 1)
