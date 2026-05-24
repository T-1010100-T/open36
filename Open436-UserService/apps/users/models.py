"""
User models
"""
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class UserProfile(models.Model):
    """
    用户资料模型

    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    user_id 关联 M1 认证服务的 users_auth.id
    """

    user_id = models.IntegerField(primary_key=True)

    nickname = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$',
                message='昵称只能包含中文、英文、数字、下划线和连字符'
            )
        ],
        help_text='昵称（2-20字符）'
    )

    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='头像URL（M7文件服务）'
    )

    bio = models.TextField(
        blank=True,
        null=True,
        help_text='个人简介（最大200字符）'
    )

    nickname_updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='昵称最后修改时间（30天限制）'
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
        db_table = 'users_profile'
        managed = False
        ordering = ['-created_at']
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f'{self.nickname} (ID: {self.user_id})'

    def __repr__(self):
        return f'<UserProfile: {self.user_id}>'

    def can_update_nickname(self):
        """
        检查是否可以修改昵称（30天限制）

        Returns:
            bool: 是否可以修改
        """
        if not self.nickname_updated_at:
            return True
        days_since = (timezone.now() - self.nickname_updated_at).days
        return days_since >= 30

    def update_nickname(self, new_nickname):
        """
        更新昵称并记录时间

        Args:
            new_nickname: 新昵称
        """
        self.nickname = new_nickname
        self.nickname_updated_at = timezone.now()
        self.save(update_fields=['nickname', 'nickname_updated_at'])


class UserStatistics(models.Model):
    """
    用户统计模型

    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='user_id',
        related_name='statistics'
    )

    posts_count = models.IntegerField(
        default=0,
        help_text='发帖数'
    )

    replies_count = models.IntegerField(
        default=0,
        help_text='回复数'
    )

    likes_received = models.IntegerField(
        default=0,
        help_text='获赞总数'
    )

    favorites_received = models.IntegerField(
        default=0,
        help_text='获收藏总数'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='更新时间'
    )

    class Meta:
        db_table = 'user_statistics'
        managed = False
        verbose_name = '用户统计'
        verbose_name_plural = '用户统计'

    def __str__(self):
        return f'Stats for User {self.user_id}'

    def __repr__(self):
        return f'<UserStatistics: {self.user_id}>'

    @classmethod
    def increment_field(cls, user_id, field, value=1):
        """
        原子性更新统计字段

        Args:
            user_id: 用户ID
            field: 字段名 (posts_count, replies_count, likes_received, favorites_received)
            value: 增量值（可为负数）

        Returns:
            UserStatistics: 更新后的统计对象
        """
        from django.db.models import F

        allowed_fields = ['posts_count', 'replies_count', 'likes_received', 'favorites_received']
        if field not in allowed_fields:
            raise ValueError(f'无效的统计字段: {field}')

        obj, created = cls.objects.get_or_create(
            user_id=user_id,
            defaults={field: max(0, value)}
        )

        if not created:
            cls.objects.filter(user_id=user_id).update(
                **{field: F(field) + value}
            )
            obj.refresh_from_db()

        return obj
