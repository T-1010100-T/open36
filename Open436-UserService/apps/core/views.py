"""
Core views (health check)
"""
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check(request):
    """
    健康检查端点

    Returns:
        JsonResponse: 服务状态
    """
    # 检查数据库连接
    db_status = 'ok'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        db_status = f'error: {str(e)}'

    status = 200 if db_status == 'ok' else 503

    return JsonResponse({
        'status': 'healthy' if db_status == 'ok' else 'unhealthy',
        'database': db_status,
        'service': 'user-service',
        'timestamp': timezone.now().isoformat(),
    }, status=status)
