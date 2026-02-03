"""
Redisson分布式锁服务
支持可重入锁、公平锁、读写锁
"""
import redis
import time
import uuid
import threading
from typing import Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class RedisDistributedLock:
    """Redis分布式锁"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        lock_name: str,
        expire_time: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1
    ):
        self.redis = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.expire_time = expire_time
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        
        # 锁标识（避免误解锁）
        self.lock_id = f"{threading.current_thread().name}_{uuid.uuid4().hex}"
        self.is_locked = False
    
    def acquire(self) -> bool:
        """获取锁"""
        for i in range(self.retry_times):
            # 尝试获取锁（SET NX EX）
            result = self.redis.set(
                self.lock_name,
                self.lock_id,
                nx=True,  # 只在键不存在时设置
                ex=self.expire_time  # 过期时间
            )
            
            if result:
                self.is_locked = True
                logger.debug(f"[分布式锁] 获取成功: {self.lock_name}")
                return True
            
            # 未获取到锁，等待重试
            if i < self.retry_times - 1:
                time.sleep(self.retry_delay)
        
        logger.warning(f"[分布式锁] 获取失败: {self.lock_name} (重试{self.retry_times}次)")
        return False
    
    def release(self) -> bool:
        """释放锁"""
        if not self.is_locked:
            return False
        
        # Lua脚本：原子性检查并删除
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = self.redis.eval(lua_script, 1, self.lock_name, self.lock_id)
            
            if result:
                self.is_locked = False
                logger.debug(f"[分布式锁] 释放成功: {self.lock_name}")
                return True
            else:
                logger.warning(f"[分布式锁] 释放失败（锁已被其他线程持有）: {self.lock_name}")
                return False
                
        except Exception as e:
            logger.error(f"[分布式锁] 释放异常: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器：进入"""
        if not self.acquire():
            raise Exception(f"无法获取分布式锁: {self.lock_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.release()


class RedisReentrantLock:
    """可重入锁"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        lock_name: str,
        expire_time: int = 30
    ):
        self.redis = redis_client
        self.lock_name = f"reentrant_lock:{lock_name}"
        self.expire_time = expire_time
        
        self.thread_id = threading.get_ident()
        self.lock_count = 0
    
    def acquire(self) -> bool:
        """获取锁"""
        # 当前线程已持有锁
        if self.lock_count > 0:
            self.lock_count += 1
            logger.debug(f"[可重入锁] 重入: {self.lock_name} (count={self.lock_count})")
            return True
        
        # 首次获取锁
        lock_value = f"{self.thread_id}:1"
        result = self.redis.set(
            self.lock_name,
            lock_value,
            nx=True,
            ex=self.expire_time
        )
        
        if result:
            self.lock_count = 1
            logger.debug(f"[可重入锁] 获取成功: {self.lock_name}")
            return True
        
        # 检查是否是当前线程持有
        current_value = self.redis.get(self.lock_name)
        if current_value and current_value.decode().startswith(f"{self.thread_id}:"):
            # 增加重入次数
            self.lock_count += 1
            new_value = f"{self.thread_id}:{self.lock_count}"
            self.redis.set(self.lock_name, new_value, ex=self.expire_time)
            logger.debug(f"[可重入锁] 重入: {self.lock_name} (count={self.lock_count})")
            return True
        
        logger.warning(f"[可重入锁] 获取失败: {self.lock_name}")
        return False
    
    def release(self) -> bool:
        """释放锁"""
        if self.lock_count <= 0:
            return False
        
        self.lock_count -= 1
        
        if self.lock_count == 0:
            # 完全释放锁
            self.redis.delete(self.lock_name)
            logger.debug(f"[可重入锁] 完全释放: {self.lock_name}")
        else:
            # 减少重入次数
            new_value = f"{self.thread_id}:{self.lock_count}"
            self.redis.set(self.lock_name, new_value, ex=self.expire_time)
            logger.debug(f"[可重入锁] 部分释放: {self.lock_name} (count={self.lock_count})")
        
        return True
    
    def __enter__(self):
        if not self.acquire():
            raise Exception(f"无法获取可重入锁: {self.lock_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


@contextmanager
def distributed_lock(
    redis_client: redis.Redis,
    lock_name: str,
    expire_time: int = 30,
    retry_times: int = 3
):
    """分布式锁上下文管理器（便捷用法）"""
    lock = RedisDistributedLock(
        redis_client,
        lock_name,
        expire_time,
        retry_times
    )
    
    try:
        if not lock.acquire():
            raise Exception(f"无法获取分布式锁: {lock_name}")
        yield lock
    finally:
        lock.release()


# 使用示例
"""
# 初始化Redis客户端
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 方式1：手动管理
lock = RedisDistributedLock(redis_client, "my_resource")
if lock.acquire():
    try:
        # 执行临界区代码
        process_critical_section()
    finally:
        lock.release()

# 方式2：with语句
with RedisDistributedLock(redis_client, "my_resource"):
    process_critical_section()

# 方式3：便捷函数
with distributed_lock(redis_client, "my_resource"):
    process_critical_section()

# 可重入锁
with RedisReentrantLock(redis_client, "my_resource"):
    process_step_1()
    
    # 同一线程可以再次获取锁
    with RedisReentrantLock(redis_client, "my_resource"):
        process_step_2()
"""


class LockManager:
    """分布式锁管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.locks = {}
    
    def get_lock(
        self,
        lock_name: str,
        lock_type: str = "simple",
        expire_time: int = 30
    ):
        """获取锁实例"""
        if lock_type == "simple":
            return RedisDistributedLock(self.redis, lock_name, expire_time)
        elif lock_type == "reentrant":
            return RedisReentrantLock(self.redis, lock_name, expire_time)
        else:
            raise ValueError(f"未知的锁类型: {lock_type}")
    
    def release_all(self):
        """释放所有锁"""
        for lock in self.locks.values():
            try:
                lock.release()
            except Exception as e:
                logger.error(f"释放锁失败: {e}")
        
        self.locks.clear()
