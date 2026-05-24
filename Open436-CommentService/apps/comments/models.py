"""
Comment models
"""
from django.db import models
from django.utils import timezone


class Reply(models.Model):
    """
    回复模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID（关联M3 posts.id）'
    )

    author_id = models.IntegerField(
        db_index=True,
        help_text='作者ID（关联M1 users_auth.id）'
    )

    content = models.TextField(
        help_text='回复内容（2-10000字符）'
    )

    floor_number = models.IntegerField(
        help_text='楼层号'
    )

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='是否已删除'
    )

    edit_count = models.IntegerField(
        default=0,
        help_text='编辑次数'
    )

    last_edited_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='最后编辑时间'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='更新时间'
    )

    class Meta:
        db_table = 'replies'
        managed = False
        ordering = ['post_id', 'floor_number']
        verbose_name = '回复'
        verbose_name_plural = '回复'

    def __str__(self):
        return f'Reply #{self.floor_number} on Post {self.post_id}'

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def can_edit(self, user_id, is_admin=False):
        """
        检查是否可以编辑
        5分钟内可以编辑，管理员无限制
        """
        if is_admin:
            return True
        if self.author_id != user_id:
            return False
        minutes_since = (timezone.now() - self.created_at).total_seconds() / 60
        return minutes_since <= 5

    def record_edit(self):
        """记录编辑"""
        self.edit_count += 1
        self.last_edited_at = timezone.now()
        self.save(update_fields=['edit_count', 'last_edited_at'])


class PostLike(models.Model):
    """
    帖子点赞模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID'
    )

    user_id = models.IntegerField(
        db_index=True,
        help_text='用户ID'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='点赞时间'
    )

    class Meta:
        db_table = 'post_likes'
        managed = False
        ordering = ['-created_at']
        verbose_name = '帖子点赞'
        verbose_name_plural = '帖子点赞'
        unique_together = [['post_id', 'user_id']]

    def __str__(self):
        return f'Like: User {self.user_id} -> Post {self.post_id}'


class PostFavorite(models.Model):
    """
    帖子收藏模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID'
    )

    user_id = models.IntegerField(
        db_index=True,
        help_text='用户ID'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='收藏时间'
    )

    class Meta:
        db_table = 'post_favorites'
        managed = False
        ordering = ['-created_at']
        verbose_name = '帖子收藏'
        verbose_name_plural = '帖子收藏'
        unique_together = [['post_id', 'user_id']]

    def __str__(self):
        return f'Favorite: User {self.user_id} -> Post {self.post_id}'
