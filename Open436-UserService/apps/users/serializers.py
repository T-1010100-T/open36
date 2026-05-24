"""
User serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import UserProfile, UserStatistics


class UserStatisticsSerializer(serializers.ModelSerializer):
    """用户统计序列化器"""

    class Meta:
        model = UserStatistics
        fields = ['user_id', 'posts_count', 'replies_count', 'likes_received', 'favorites_received', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """用户基础资料序列化器"""

    class Meta:
        model = UserProfile
        fields = ['user_id', 'nickname', 'avatar_url', 'bio', 'created_at', 'updated_at']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器（含统计数据）"""

    statistics = UserStatisticsSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'nickname', 'avatar_url', 'bio', 'created_at', 'updated_at', 'statistics']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """更新用户资料序列化器"""

    nickname = serializers.CharField(required=False, max_length=20)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=200)
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = ['nickname', 'bio', 'avatar_url']

    def validate_nickname(self, value):
        """验证昵称格式"""
        import re
        if len(value) < 2 or len(value) > 20:
            raise serializers.ValidationError('昵称长度必须为2-20个字符')
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError('昵称只能包含中文、英文、数字、下划线和连字符')
        return value

    def validate_bio(self, value):
        """验证简介长度"""
        if value and len(value) > 200:
            raise serializers.ValidationError('个人简介不能超过200个字符')
        return value


class AdminUserCreateSerializer(serializers.Serializer):
    """管理员创建用户序列化器"""

    username = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, min_length=6, max_length=32, write_only=True)
    role = serializers.ChoiceField(choices=['user', 'admin'], default='user')
    nickname = serializers.CharField(required=True, max_length=20)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate_nickname(self, value):
        import re
        if len(value) < 2 or len(value) > 20:
            raise serializers.ValidationError('昵称长度必须为2-20个字符')
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError('昵称只能包含中文、英文、数字、下划线和连字符')
        return value


class AdminUserListSerializer(serializers.Serializer):
    """管理员用户列表项序列化器"""

    user_id = serializers.IntegerField()
    username = serializers.CharField()
    nickname = serializers.CharField()
    avatar_url = serializers.URLField(allow_blank=True, allow_null=True)
    status = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
    posts_count = serializers.IntegerField(default=0)
    replies_count = serializers.IntegerField(default=0)


class BatchUserSerializer(serializers.ModelSerializer):
    """批量获取用户信息序列化器（精简版）"""

    class Meta:
        model = UserProfile
        fields = ['user_id', 'nickname', 'avatar_url']


class UserActivityPostSerializer(serializers.Serializer):
    """用户发帖历史项序列化器"""

    post_id = serializers.IntegerField()
    title = serializers.CharField()
    content_preview = serializers.CharField()
    section_name = serializers.CharField()
    created_at = serializers.DateTimeField()
    views_count = serializers.IntegerField()
    replies_count = serializers.IntegerField()
    likes_count = serializers.IntegerField()


class UserActivityReplySerializer(serializers.Serializer):
    """用户回复历史项序列化器"""

    reply_id = serializers.IntegerField()
    content = serializers.CharField()
    post_id = serializers.IntegerField()
    post_title = serializers.CharField()
    created_at = serializers.DateTimeField()
    likes_count = serializers.IntegerField()
