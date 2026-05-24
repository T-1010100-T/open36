"""
Custom exceptions and exception handler
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.utils import timezone


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，统一错误响应格式
    """
    # 先调用DRF默认的异常处理
    response = exception_handler(exc, context)

    if response is not None:
        # 统一响应格式
        data = {
            'code': response.status_code,
            'message': response.data.get('detail', '请求处理失败'),
            'timestamp': int(timezone.now().timestamp() * 1000),
        }

        # 如果有详细错误信息，保留
        if 'detail' in response.data:
            del response.data['detail']
        if response.data:
            data['errors'] = response.data

        response.data = data

    return response


class ServiceError(Exception):
    """服务调用异常"""
    pass


class ValidationError(Exception):
    """业务验证异常"""
    pass
