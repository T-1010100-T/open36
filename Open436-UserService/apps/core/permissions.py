"""
Custom permission classes
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    仅允许管理员访问
    """
    message = '需要管理员权限'

    def has_permission(self, request, view):
        return getattr(request, 'is_admin', False)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    仅允许本人或管理员访问
    """
    message = '只能操作自己的数据'

    def has_object_permission(self, request, view, obj):
        if getattr(request, 'is_admin', False):
            return True
        return hasattr(obj, 'user_id') and obj.user_id == getattr(request, 'user_id', None)
