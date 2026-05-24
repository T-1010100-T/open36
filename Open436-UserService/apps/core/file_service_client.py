"""
File service client for avatar upload
"""
import logging
import requests
from django.conf import settings
from django.core.cache import cache

from .consul_client import consul_client

logger = logging.getLogger(__name__)


class FileServiceClient:
    """
    M7 文件存储服务客户端
    """

    def __init__(self):
        self.service_name = 'file-service'
        self.fallback_url = settings.FILE_SERVICE_URL

    def _get_base_url(self):
        """获取文件服务地址"""
        url = consul_client.discover_service(self.service_name)
        return url or self.fallback_url

    def upload_avatar(self, file_obj, user_id):
        """
        上传用户头像

        Args:
            file_obj: 文件对象
            user_id: 用户ID

        Returns:
            dict: 上传结果，包含 file_url
        """
        base_url = self._get_base_url()
        if not base_url:
            raise Exception("File service not available")

        url = f"{base_url}/api/files/upload"
        files = {'file': (file_obj.name, file_obj, file_obj.content_type)}
        data = {'file_type': 'avatar', 'user_id': user_id}

        try:
            response = requests.post(url, files=files, data=data, timeout=10)
            response.raise_for_status()
            return response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload avatar: {e}")
            raise Exception(f"文件上传失败: {e}")


# 全局实例
file_service_client = FileServiceClient()
