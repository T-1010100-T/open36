"""
Comment views
"""
import logging
import requests
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAuthenticated, IsAuthorOrAdmin, IsAdminUser, IsActiveUser
from apps.core.responses import success_response, error_response
from apps.core.consul_client import consul_client
from django.conf import settings

from .models import Reply, PostLike, PostFavorite
from .serializers import (
    ReplyListSerializer, ReplyCreateSerializer, ReplyUpdateSerializer,
    PostLikeSerializer, PostFavoriteSerializer, FavoriteListSerializer
)

logger = logging.getLogger(__name__)


def _get_service_url(service_name, fallback_env):
    url = consul_client.discover_service(service_name)
    return url or getattr(settings, fallback_env, None)


def _validate_post(post_id):
    """验证帖子是否存在（调用 M3）"""
    try:
        url = _get_service_url('content-service', 'CONTENT_SERVICE_URL')
        if not url:
            return True, None
        resp = requests.get(f'{url}/internal/posts/{post_id}/validate/', timeout=2)
        if resp.status_code == 200:
            return True, None
        return False, '帖子不存在'
    except Exception as e:
        logger.warning(f'Post validation failed: {e}')
        return True, None


def _update_user_stats(user_id, field, value):
    """更新用户统计（调用 M2）"""
    try:
        url = _get_service_url('user-service', 'USER_SERVICE_URL')
        if not url:
            return
        requests.post(
            f'{url}/internal/users/{user_id}/statistics/increment/',
            json={'field': field, 'value': value},
            timeout=2,
            headers={'X-Internal-API-Key': settings.INTERNAL_API_KEY}
        )
    except Exception as e:
        logger.warning(f'Update user stats failed: {e}')


class ReplyViewSet(viewsets.GenericViewSet):
    """回复视图集"""

    queryset = Reply.objects.all()
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsActiveUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsActiveUser(), IsAuthorOrAdmin()]
        return []

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        try:
            return self.get_queryset().get(pk=pk)
        except Reply.DoesNotExist:
            return None

    def list(self, request):
        """获取帖子的回复列表（管理员支持全量查询）"""
        is_admin = getattr(request, 'is_admin', False)
        post_id = request.query_params.get('post_id')

        queryset = self.get_queryset()

        if post_id:
            try:
                post_id = int(post_id)
            except (ValueError, TypeError):
                resp, code = error_response('无效的 post_id', code=400, status_code=400)
                return Response(resp, status=code)
            queryset = queryset.filter(post_id=post_id)
        elif not is_admin:
            resp, code = error_response('缺少 post_id 参数', code=400, status_code=400)
            return Response(resp, status=code)

        if not is_admin:
            # 普通用户只能看到未删除的回复，但作者可以看到自己的已删除回复
            user_id = getattr(request, 'user_id', None)
            if user_id:
                queryset = queryset.filter(
                    Q(is_deleted=False) | Q(author_id=user_id)
                )
            else:
                queryset = queryset.filter(is_deleted=False)
        else:
            # 管理员可按状态筛选
            status_filter = request.query_params.get('status')
            if status_filter == 'deleted':
                queryset = queryset.filter(is_deleted=True)
            elif status_filter == 'normal':
                queryset = queryset.filter(is_deleted=False)
            # 管理员搜索内容
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(content__icontains=search)

        queryset = queryset.order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 50)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        replies = queryset[start:end]

        serializer = ReplyListSerializer(replies, many=True, context={'request': request})
        next_url = None
        prev_url = None
        if end < total:
            next_parts = [f'page={page + 1}']
            if post_id:
                next_parts.insert(0, f'post_id={post_id}')
            next_url = f'/api/replies/?{"&".join(next_parts)}'
        if page > 1:
            prev_parts = [f'page={page - 1}']
            if post_id:
                prev_parts.insert(0, f'post_id={post_id}')
            prev_url = f'/api/replies/?{"&".join(prev_parts)}'
        return Response(success_response(data={
            'count': total,
            'next': next_url,
            'previous': prev_url,
            'results': serializer.data,
        }))

    @transaction.atomic
    def create(self, request):
        """发布回复"""
        post_id = request.data.get('post_id')
        if not post_id:
            resp, code = error_response('缺少 post_id', code=400, status_code=400)
            return Response(resp, status=code)

        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的 post_id', code=400, status_code=400)
            return Response(resp, status=code)

        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        serializer = ReplyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        author_id = getattr(request, 'user_id', None)
        if not author_id:
            resp, code = error_response('未获取到用户信息', code=401, status_code=401)
            return Response(resp, status=code)

        # 计算楼层号
        last_floor = Reply.objects.filter(post_id=post_id).order_by('-floor_number').first()
        floor_number = (last_floor.floor_number + 1) if last_floor else 1

        reply = Reply.objects.create(
            post_id=post_id,
            author_id=author_id,
            content=serializer.validated_data['content'],
            floor_number=floor_number,
        )

        _update_user_stats(author_id, 'replies_count', 1)
        return Response(success_response(
            data=ReplyListSerializer(reply, context={'request': request}).data,
            message='回复成功'
        ), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """编辑回复"""
        reply = self.get_object()
        if not reply:
            resp, code = error_response('回复不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        if reply.is_deleted:
            resp, code = error_response('回复已删除', code=400, status_code=400)
            return Response(resp, status=code)

        is_admin = getattr(request, 'is_admin', False)
        user_id = getattr(request, 'user_id', None)

        if not reply.can_edit(user_id, is_admin):
            resp, code = error_response('超过编辑时限（5分钟）', code=400, status_code=400)
            return Response(resp, status=code)

        serializer = ReplyUpdateSerializer(reply, data=request.data, partial=True)
        if not serializer.is_valid():
            resp, code = error_response('参数错误', code=400, errors=serializer.errors, status_code=400)
            return Response(resp, status=code)

        serializer.save()
        reply.record_edit()

        return Response(success_response(
            data=ReplyListSerializer(reply, context={'request': request}).data,
            message='回复已更新'
        ))

    def destroy(self, request, pk=None):
        """删除回复（软删除）"""
        reply = self.get_object()
        if not reply:
            resp, code = error_response('回复不存在', code=40401, status_code=404)
            return Response(resp, status=code)

        reply.soft_delete()
        _update_user_stats(reply.author_id, 'replies_count', -1)
        return Response(success_response(message='回复已删除'))


class InteractionViewSet(viewsets.GenericViewSet):
    """互动视图集（点赞/收藏）"""

    def get_permissions(self):
        if self.action in ['toggle_like', 'toggle_favorite', 'my_favorites']:
            return [IsAuthenticated(), IsActiveUser()]
        return []

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/like')
    def toggle_like(self, request, post_id=None):
        """点赞/取消点赞"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)

        # 验证帖子
        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        like, created = PostLike.objects.get_or_create(post_id=post_id, user_id=user_id)

        if not created:
            # 已点赞，取消点赞
            like.delete()
            _update_user_stats(user_id, 'likes_received', -1)
            return Response(success_response(message='已取消点赞'))

        # 新增点赞
        _update_user_stats(user_id, 'likes_received', 1)
        return Response(success_response(message='点赞成功'))

    @action(detail=False, methods=['post'], url_path='posts/(?P<post_id>[^/.]+)/favorite')
    def toggle_favorite(self, request, post_id=None):
        """收藏/取消收藏"""
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的帖子ID', code=400, status_code=400)
            return Response(resp, status=code)

        user_id = getattr(request, 'user_id', None)

        valid, err = _validate_post(post_id)
        if not valid:
            resp, code = error_response(err, code=400, status_code=400)
            return Response(resp, status=code)

        fav, created = PostFavorite.objects.get_or_create(post_id=post_id, user_id=user_id)

        if not created:
            fav.delete()
            _update_user_stats(user_id, 'favorites_received', -1)
            return Response(success_response(message='已取消收藏'))

        _update_user_stats(user_id, 'favorites_received', 1)
        return Response(success_response(message='收藏成功'))

    @action(detail=False, methods=['get'], url_path='favorites')
    def my_favorites(self, request):
        """我的收藏列表"""
        user_id = getattr(request, 'user_id', None)

        queryset = PostFavorite.objects.filter(user_id=user_id).order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        favorites = queryset[start:end]

        serializer = FavoriteListSerializer(favorites, many=True)
        return Response(success_response(data={
            'count': total,
            'next': f'/api/favorites/?page={page + 1}' if end < total else None,
            'previous': f'/api/favorites/?page={page - 1}' if page > 1 else None,
            'results': serializer.data,
        }))
