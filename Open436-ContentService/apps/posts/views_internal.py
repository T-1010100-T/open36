"""
Internal API views for service-to-service communication
"""
import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.responses import success_response, error_response
from .models import Post
from .serializers import PostListSerializer

logger = logging.getLogger(__name__)


class InternalPostViewSet(viewsets.GenericViewSet):
    """内部服务视图集（仅供其他服务调用）"""

    queryset = Post.objects.filter(status=Post.STATUS_PUBLISHED)
    lookup_field = 'pk'

    @action(detail=True, methods=['post'], url_path='increment-views')
    def increment_views(self, request, pk=None):
        """增加浏览量"""
        try:
            post = self.get_queryset().get(pk=pk)
            post.increment_views()
            return Response(success_response(
                data={'views_count': post.views_count},
                message='浏览量已更新'
            ))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=True, methods=['get'], url_path='validate')
    def validate_post(self, request, pk=None):
        """验证帖子是否存在且有效"""
        try:
            post = self.get_queryset().get(pk=pk)
            return Response(success_response(data={
                'id': post.id,
                'title': post.title,
                'author_id': post.author_id,
                'section_id': post.section_id,
                'status': post.status,
            }))
        except Post.DoesNotExist:
            resp, code = error_response('帖子不存在', code=40401, status_code=404)
            return Response(resp, status=code)

    @action(detail=False, methods=['get'], url_path='batch')
    def batch_info(self, request):
        """批量获取帖子基础信息（供其他服务调用）"""
        ids_param = request.query_params.get('ids', '')
        if not ids_param:
            resp, code = error_response('缺少 ids 参数', code=400, status_code=400)
            return Response(resp, status=code)

        try:
            ids = [int(i.strip()) for i in ids_param.split(',') if i.strip()]
        except (ValueError, TypeError):
            resp, code = error_response('ids 参数格式错误', code=400, status_code=400)
            return Response(resp, status=code)

        if len(ids) > 100:
            resp, code = error_response('单次最多查询100条', code=400, status_code=400)
            return Response(resp, status=code)

        posts = Post.objects.filter(id__in=ids, status=Post.STATUS_PUBLISHED)
        result = {}
        for p in posts:
            result[p.id] = {
                'id': p.id,
                'title': p.title,
                'author_id': p.author_id,
                'section_id': p.section_id,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'views_count': p.views_count,
            }

        return Response(success_response(data={'posts': result}))

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """获取用户帖子列表"""
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            resp, code = error_response('无效的用户ID', code=400, status_code=400)
            return Response(resp, status=code)

        queryset = self.get_queryset().filter(author_id=user_id)

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-views_count']
        if ordering in allowed:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        posts = queryset[start:end]

        serializer = PostListSerializer(posts, many=True)
        return Response(success_response(data={
            'count': total,
            'next': f'/internal/posts/by-user/{user_id}/?page={page + 1}' if end < total else None,
            'previous': f'/internal/posts/by-user/{user_id}/?page={page - 1}' if page > 1 else None,
            'results': serializer.data,
        }))
