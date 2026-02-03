"""
Redis缓存服务
用于缓存项目数据，减少数据库查询压力
"""
import json
import redis
import os
from typing import Optional, Dict, Any
from datetime import timedelta


class CacheService:
    """Redis缓存管理服务"""
    
    def __init__(self):
        """初始化Redis连接"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            self.available = True
        except Exception as e:
            print(f"⚠️  Redis连接失败，缓存功能不可用: {e}")
            self.redis_client = None
            self.available = False
    
    def get_project_progress(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取项目进度缓存数据
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目进度数据，未命中缓存返回None
        """
        if not self.available:
            return None
        
        try:
            cache_key = f"project_progress:{project_id}"
            data = self.redis_client.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"⚠️  Redis读取失败: {e}")
            return None
    
    def set_project_progress(
        self,
        project_id: int,
        data: Dict[str, Any],
        expire_seconds: int = 600
    ) -> bool:
        """
        设置项目进度缓存
        
        Args:
            project_id: 项目ID
            data: 要缓存的数据
            expire_seconds: 过期时间（秒），默认10分钟
            
        Returns:
            是否设置成功
        """
        if not self.available:
            return False
        
        try:
            cache_key = f"project_progress:{project_id}"
            self.redis_client.setex(
                cache_key,
                expire_seconds,
                json.dumps(data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"⚠️  Redis写入失败: {e}")
            return False
    
    def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取项目完整详情缓存
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目详情数据，未命中缓存返回None
        """
        if not self.available:
            return None
        
        try:
            cache_key = f"project_detail:{project_id}"
            data = self.redis_client.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"⚠️  Redis读取失败: {e}")
            return None
    
    def set_project_detail(
        self,
        project_id: int,
        data: Dict[str, Any],
        expire_seconds: int = 600
    ) -> bool:
        """
        设置项目详情缓存
        
        Args:
            project_id: 项目ID
            data: 要缓存的数据
            expire_seconds: 过期时间（秒），默认10分钟
            
        Returns:
            是否设置成功
        """
        if not self.available:
            return False
        
        try:
            cache_key = f"project_detail:{project_id}"
            self.redis_client.setex(
                cache_key,
                expire_seconds,
                json.dumps(data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"⚠️  Redis写入失败: {e}")
            return False
    
    def invalidate_project_cache(self, project_id: int) -> bool:
        """
        清除项目相关的所有缓存
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否清除成功
        """
        if not self.available:
            return False
        
        try:
            keys = [
                f"project_progress:{project_id}",
                f"project_detail:{project_id}"
            ]
            self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"⚠️  Redis删除失败: {e}")
            return False


# 全局缓存服务实例
cache_service = CacheService()
