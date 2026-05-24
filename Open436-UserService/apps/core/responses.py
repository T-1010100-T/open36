"""
Unified response utilities
"""
from django.utils import timezone


def success_response(data=None, message='success', code=200):
    """
    统一的成功响应格式

    Args:
        data: 响应数据
        message: 消息
        code: 业务状态码

    Returns:
        dict: 标准响应格式
    """
    response = {
        'code': code,
        'message': message,
        'timestamp': int(timezone.now().timestamp() * 1000),
    }
    if data is not None:
        response['data'] = data
    return response


def error_response(message, code=400, errors=None, status_code=400):
    """
    统一的错误响应格式

    Args:
        message: 错误消息
        code: 业务错误码
        errors: 详细错误信息
        status_code: HTTP状态码

    Returns:
        tuple: (dict, HTTP状态码)
    """
    response = {
        'code': code,
        'message': message,
        'timestamp': int(timezone.now().timestamp() * 1000),
    }
    if errors is not None:
        response['errors'] = errors
    return response, status_code
