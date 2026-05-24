"""
Internal API views for service-to-service communication
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.responses import success_response, error_response
from .models import UserProfile, UserStatistics
from .serializers import BatchUserSerializer, UserStatisticsSerializer

logger = logging.getLogger(__name__)


class InternalUserViewSet(viewsets.GenericViewSet):
    """内部服务视图集（仅供其他服务调用）"""

    @action(detail=False, methods=['post'], url_path='batch')
    def batch(self, request):
        """批量获取用户信息"""
        user_ids = request.data.get('user_ids', [])

        if not isinstance(user_ids, list) or len(user_ids) == 0:
            resp, code = error_response('user_ids 必须为非空数组', code=400, status_code=400)
            return Response(resp, status=code)

        if len(user_ids) > 100:
            resp, code = error_response('每次最多查询100个用户', code=400, status_code=400)
            return Response(resp, status=code)

        # 去重并过滤无效值
        user_ids = list(set(int(uid) for uid in user_ids if isinstance(uid, int) or str(uid).isdigit()))

        profiles = UserProfile.objects.filter(user_id__in=user_ids)
        serializer = BatchUserSerializer(profiles, many=True)

        return Response(success_response(data=serializer.data))

    @action(detail=True, methods=['post'], url_path='statistics/increment')
    def increment_statistics(self, request, pk=None):
        """更新用户统计数据"""
        user_id = pk
        field = request.data.get('field')
        value = request.data.get('value', 0)

        allowed_fields = ['posts_count', 'replies_count', 'likes_received', 'favorites_received']
        if field not in allowed_fields:
            resp, code = error_response(
                f'无效的字段名，可选: {", ".join(allowed_fields)}',
                code=400, status_code=400
            )
            return Response(resp, status=code)

        try:
            value = int(value)
        except (ValueError, TypeError):
            resp, code = error_response('value 必须是整数', code=400, status_code=400)
            return Response(resp, status=code)

        try:
            stats = UserStatistics.increment_field(user_id, field, value)
            serializer = UserStatisticsSerializer(stats)
            return Response(success_response(
                data=serializer.data,
                message='统计数据已更新'
            ))
        except ValueError as e:
            resp, code = error_response(str(e), code=400, status_code=400)
            return Response(resp, status=code)
        except Exception as e:
            logger.error(f'Increment statistics failed: {e}')
            resp, code = error_response('更新统计数据失败', code=500, status_code=500)
            return Response(resp, status=code)
