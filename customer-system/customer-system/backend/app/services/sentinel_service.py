"""
Sentinel限流服务
实现QPS限流、并发线程数限流
"""
import time
import redis
from typing import Optional
import logging
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """限流器基类"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, resource: str, **kwargs) -> bool:
        """检查是否允许通过"""
        raise NotImplementedError


class QPSRateLimiter(RateLimiter):
    """QPS限流器（每秒请求数）"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_qps: int = 100,
        window_size: int = 1
    ):
        super().__init__(redis_client)
        self.max_qps = max_qps
        self.window_size = window_size  # 窗口大小（秒）
    
    def is_allowed(self, resource: str, user_id: Optional[str] = None) -> bool:
        """检查QPS是否超限"""
        # 构建key
        if user_id:
            key = f"rate_limit:qps:{resource}:{user_id}"
        else:
            key = f"rate_limit:qps:{resource}:global"
        
        current_second = int(time.time())
        
        try:
            # 使用Lua脚本实现原子性操作
            lua_script = """
            local key = KEYS[1]
            local max_qps = tonumber(ARGV[1])
            local current_second = tonumber(ARGV[2])
            local window_size = tonumber(ARGV[3])
            
            -- 清理过期数据
            redis.call('ZREMRANGEBYSCORE', key, 0, current_second - window_size)
            
            -- 获取当前窗口内的请求数
            local current_qps = redis.call('ZCARD', key)
            
            if current_qps < max_qps then
                -- 允许通过，记录请求
                redis.call('ZADD', key, current_second, current_second .. ':' .. math.random())
                redis.call('EXPIRE', key, window_size + 1)
                return 1
            else
                -- 拒绝请求
                return 0
            end
            """
            
            result = self.redis.eval(
                lua_script,
                1,
                key,
                self.max_qps,
                current_second,
                self.window_size
            )
            
            if result == 0:
                logger.warning(f"[限流] QPS超限: {resource} (max={self.max_qps})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[限流] QPS检查异常: {e}")
            # 异常时默认允许通过（降级策略）
            return True


class ConcurrentLimiter(RateLimiter):
    """并发线程数限流器"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_concurrent: int = 50
    ):
        super().__init__(redis_client)
        self.max_concurrent = max_concurrent
    
    def is_allowed(self, resource: str, request_id: str) -> bool:
        """检查并发数是否超限"""
        key = f"rate_limit:concurrent:{resource}"
        
        try:
            # 使用Lua脚本
            lua_script = """
            local key = KEYS[1]
            local max_concurrent = tonumber(ARGV[1])
            local request_id = ARGV[2]
            local current_time = tonumber(ARGV[3])
            
            -- 清理过期请求（超过60秒）
            redis.call('ZREMRANGEBYSCORE', key, 0, current_time - 60)
            
            -- 获取当前并发数
            local current_concurrent = redis.call('ZCARD', key)
            
            if current_concurrent < max_concurrent then
                -- 允许通过，记录请求
                redis.call('ZADD', key, current_time, request_id)
                redis.call('EXPIRE', key, 61)
                return 1
            else
                -- 拒绝请求
                return 0
            end
            """
            
            result = self.redis.eval(
                lua_script,
                1,
                key,
                self.max_concurrent,
                request_id,
                int(time.time())
            )
            
            if result == 0:
                logger.warning(f"[限流] 并发数超限: {resource} (max={self.max_concurrent})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[限流] 并发检查异常: {e}")
            return True
    
    def release(self, resource: str, request_id: str):
        """释放并发资源"""
        key = f"rate_limit:concurrent:{resource}"
        try:
            self.redis.zrem(key, request_id)
            logger.debug(f"[限流] 释放并发资源: {resource} ({request_id})")
        except Exception as e:
            logger.error(f"[限流] 释放并发资源失败: {e}")


class SlidingWindowLimiter(RateLimiter):
    """滑动窗口限流器"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        super().__init__(redis_client)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, resource: str, user_id: Optional[str] = None) -> bool:
        """滑动窗口限流"""
        if user_id:
            key = f"rate_limit:sliding:{resource}:{user_id}"
        else:
            key = f"rate_limit:sliding:{resource}:global"
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            # Lua脚本
            lua_script = """
            local key = KEYS[1]
            local max_requests = tonumber(ARGV[1])
            local window_start = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            
            -- 清理窗口外的数据
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
            
            -- 获取窗口内的请求数
            local request_count = redis.call('ZCARD', key)
            
            if request_count < max_requests then
                -- 允许通过
                redis.call('ZADD', key, current_time, current_time)
                redis.call('EXPIRE', key, ARGV[4])
                return 1
            else
                -- 拒绝
                return 0
            end
            """
            
            result = self.redis.eval(
                lua_script,
                1,
                key,
                self.max_requests,
                window_start,
                current_time,
                self.window_seconds + 1
            )
            
            if result == 0:
                logger.warning(
                    f"[限流] 滑动窗口超限: {resource} "
                    f"(max={self.max_requests}/{self.window_seconds}s)"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[限流] 滑动窗口检查异常: {e}")
            return True


def rate_limit(
    resource: str,
    max_qps: int = 100,
    redis_client: Optional[redis.Redis] = None
):
    """限流装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取Redis客户端
            if redis_client is None:
                # 从全局获取
                from app.database import redis_client as rc
                client = rc
            else:
                client = redis_client
            
            # 创建限流器
            limiter = QPSRateLimiter(client, max_qps)
            
            # 检查限流
            if not limiter.is_allowed(resource):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请稍后再试 (限制: {max_qps} QPS)"
                )
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 使用示例
"""
# 方式1：直接使用
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# QPS限流
qps_limiter = QPSRateLimiter(redis_client, max_qps=100)
if qps_limiter.is_allowed("api:/send_message"):
    send_message()
else:
    print("请求过于频繁")

# 并发限流
concurrent_limiter = ConcurrentLimiter(redis_client, max_concurrent=50)
request_id = "req_123"
if concurrent_limiter.is_allowed("process_task", request_id):
    try:
        process_task()
    finally:
        concurrent_limiter.release("process_task", request_id)

# 滑动窗口限流
sliding_limiter = SlidingWindowLimiter(redis_client, max_requests=1000, window_seconds=60)
if sliding_limiter.is_allowed("api:/query", user_id="user_123"):
    query_data()

# 方式2：装饰器
from app.database import redis_client

@router.post("/api/send-message")
@rate_limit(resource="api:/send_message", max_qps=100, redis_client=redis_client)
async def send_message():
    # 业务逻辑
    pass
"""


class SentinelManager:
    """Sentinel管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.limiters = {}
    
    def create_qps_limiter(
        self,
        resource: str,
        max_qps: int = 100
    ) -> QPSRateLimiter:
        """创建QPS限流器"""
        key = f"qps:{resource}"
        if key not in self.limiters:
            self.limiters[key] = QPSRateLimiter(self.redis, max_qps)
        return self.limiters[key]
    
    def create_concurrent_limiter(
        self,
        resource: str,
        max_concurrent: int = 50
    ) -> ConcurrentLimiter:
        """创建并发限流器"""
        key = f"concurrent:{resource}"
        if key not in self.limiters:
            self.limiters[key] = ConcurrentLimiter(self.redis, max_concurrent)
        return self.limiters[key]
    
    def get_statistics(self) -> dict:
        """获取限流统计"""
        stats = {}
        for key, limiter in self.limiters.items():
            # 这里可以添加统计逻辑
            stats[key] = {
                "type": type(limiter).__name__,
                "config": getattr(limiter, 'max_qps', None) or getattr(limiter, 'max_concurrent', None)
            }
        return stats
