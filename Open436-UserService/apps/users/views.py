"""
User views
"""
import logging
import requests
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.core.responses import success_response, error_response
from apps.core.file_service_client import file_service_client
from apps.core.consul_client import consul_client
from django.conf import settings

from .models import UserProfile, UserStatistics
from .serializers import (
    UserProfileSerializer, UserProfileDetailSerializer, UserProfileUpdateSerializer,
    UserStatisticsSerializer, AdminUserCreateSerializer, AdminUserListSerializer,
    UserActivityPostSerializer, UserActivityReplySerializer
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.GenericViewSet):
    """用户资料视图集"""
    queryset = UserProfile.objects.select_related('statistics').all()
    lookup_field = 'user_id'

    def get_permissions(self):
        if self.action in ['update_profile', 'upload_avatar']:
            return [IsOwnerOrAdmin()]
        return []

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_field)
        try:
            return self.get_queryset().get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    def retrieve(self, request, user_id=None):
        """获取用户信息"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)
        serializer = UserProfileDetailSerializer(user)
        return Response(success_response(data=serializer.data))

    @action(detail=True, methods=['put'], url_path='profile')
    def update_profile(self, request, user_id=None):
        """更新用户资料"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        # 昵称修改频率限制（管理员除外）
        if 'nickname' in request.data and not getattr(request, 'is_admin', False):
            if not user.can_update_nickname():
                resp, code = error_response('昵称每30天只能修改一次', code=40002, status_code=400)
                return Response(resp, status=code)

        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        # 如果修改了昵称，更新时间戳
        if 'nickname' in serializer.validated_data:
            user.nickname = serializer.validated_data['nickname']
            user.nickname_updated_at = timezone.now()
            user.save(update_fields=['nickname', 'nickname_updated_at'])
            serializer.validated_data.pop('nickname', None)

        serializer.save()
        return Response(success_response(data=UserProfileSerializer(user).data, message='用户资料已更新'))

    @action(detail=True, methods=['post'], url_path='avatar')
    def upload_avatar(self, request, user_id=None):
        """上传用户头像"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            resp, code = error_response('请上传头像文件', code=400, status_code=400)
            return Response(resp, status=code)

        # 文件大小检查 (2MB)
        if avatar_file.size > 2 * 1024 * 1024:
            resp, code = error_response('文件过大，请上传小于2MB的图片', code=40005, status_code=400)
            return Response(resp, status=code)

        try:
            result = file_service_client.upload_avatar(avatar_file, user_id)
            user.avatar_url = result.get('file_url')
            user.save(update_fields=['avatar_url'])
            return Response(success_response(
                data={'avatar_url': user.avatar_url},
                message='头像上传成功'
            ))
        except Exception as e:
            logger.error(f'Avatar upload failed: {e}')
            resp, code = error_response('头像上传失败', code=500, status_code=500)
            return Response(resp, status=code)

    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, user_id=None):
        """获取用户统计数据"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        stats, created = UserStatistics.objects.get_or_create(user_id=user_id)
        serializer = UserStatisticsSerializer(stats)
        return Response(success_response(data=serializer.data))

    @action(detail=True, methods=['get'], url_path='posts')
    def posts(self, request, user_id=None):
        """获取用户发帖历史（预留M3集成）"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        # TODO: 调用 M3 内容服务获取帖子列表
        # 当前返回空列表，等 M3 完成后集成
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        ordering = request.query_params.get('ordering', '-created_at')

        return Response(success_response(data={
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }))

    @action(detail=True, methods=['get'], url_path='replies')
    def replies(self, request, user_id=None):
        """获取用户回复历史（预留M4集成）"""
        user = self.get_object()
        if not user:
            resp, code = error_response('用户不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        # TODO: 调用 M4 评论服务获取回复列表
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)

        return Response(success_response(data={
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }))


class AdminUserViewSet(viewsets.GenericViewSet):
    """管理员用户管理视图集"""
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return UserProfile.objects.select_related('statistics').all().order_by('-created_at')

    def list(self, request):
        """获取用户列表"""
        queryset = self.get_queryset()

        # 搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(nickname__icontains=search)

        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        users = queryset[start:end]

        # 组装响应数据（管理员视图需要包含用户名和状态，这些信息来自M1）
        results = []
        for u in users:
            results.append({
                'user_id': u.user_id,
                'username': None,  # 从M1获取，暂留空
                'nickname': u.nickname,
                'avatar_url': u.avatar_url,
                'status': 'active',  # 从M1获取
                'role': 'user',  # 从M1获取
                'created_at': u.created_at,
                'posts_count': getattr(u.statistics, 'posts_count', 0),
                'replies_count': getattr(u.statistics, 'replies_count', 0),
            })

        return Response(success_response(data={
            'count': total,
            'next': f'/api/admin/users?page={page + 1}' if end < total else None,
            'previous': f'/api/admin/users?page={page - 1}' if page > 1 else None,
            'results': results
        }))

    @transaction.atomic
    def create(self, request):
        """创建用户（调用M1创建认证账号后创建资料）"""
        serializer = AdminUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        data = serializer.validated_data

        # 1. 调用 M1 创建认证账号
        auth_service_url = consul_client.discover_service('auth-service') or settings.AUTH_SERVICE_URL
        try:
            resp = requests.post(
                f'{auth_service_url}/api/auth/users',
                json={
                    'username': data['username'],
                    'password': data['password'],
                    'role': data.get('role', 'user')
                },
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            if resp.status_code not in [200, 201]:
                resp_err, code = error_response(
                    f'创建认证账号失败: {resp.text}',
                    code=400, status_code=400
                )
                return Response(resp_err, status=code)
            user_id = resp.json().get('data', {}).get('user_id')
            if not user_id:
                resp_err, code = error_response('M1返回数据异常', code=500, status_code=500)
                return Response(resp_err, status=code)
        except requests.exceptions.RequestException as e:
            logger.error(f'Auth service request failed: {e}')
            resp_err, code = error_response('认证服务不可用', code=500, status_code=500)
            return Response(resp_err, status=code)

        # 2. 创建用户资料
        profile = UserProfile.objects.create(
            user_id=user_id,
            nickname=data['nickname'],
            avatar_url=data.get('avatar_url', ''),
            bio=data.get('bio', '')
        )

        # 3. 创建统计记录
        UserStatistics.objects.create(user_id=user_id)

        return Response(success_response(
            data=UserProfileSerializer(profile).data,
            message='用户创建成功'
        ), status=status.HTTP_201_CREATED)
