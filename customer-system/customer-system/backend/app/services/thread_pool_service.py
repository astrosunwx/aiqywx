"""
动态线程池管理器
支持自动扩缩容、监控告警
"""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Callable
from datetime import datetime
import logging
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class ThreadPoolMetrics:
    """线程池指标"""
    pool_name: str
    core_size: int
    max_size: int
    active_count: int
    queue_size: int
    queue_capacity: int
    completed_tasks: int
    rejected_tasks: int
    avg_task_duration_ms: float
    queue_usage_percent: float
    timestamp: datetime


class DynamicThreadPool:
    """动态线程池"""
    
    def __init__(
        self,
        pool_name: str,
        core_pool_size: int = 10,
        max_pool_size: int = 50,
        queue_capacity: int = 1000,
        auto_scale: bool = True,
        scale_up_threshold: int = 80,
        scale_down_threshold: int = 20
    ):
        self.pool_name = pool_name
        self.core_pool_size = core_pool_size
        self.max_pool_size = max_pool_size
        self.queue_capacity = queue_capacity
        self.auto_scale = auto_scale
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(
            max_workers=core_pool_size,
            thread_name_prefix=f"{pool_name}-"
        )
        
        # 任务队列
        self.task_queue = asyncio.Queue(maxsize=queue_capacity)
        
        # 统计信息
        self.completed_tasks = 0
        self.rejected_tasks = 0
        self.task_durations = []
        self.lock = threading.Lock()
        
        # 监控线程
        self.monitor_thread = None
        self.running = False
    
    async def submit_task(self, func: Callable, *args, **kwargs):
        """提交任务"""
        try:
            # 检查队列是否已满
            if self.task_queue.full():
                with self.lock:
                    self.rejected_tasks += 1
                logger.warning(f"[{self.pool_name}] 任务队列已满，拒绝任务")
                raise Exception("任务队列已满")
            
            # 添加到队列
            await self.task_queue.put((func, args, kwargs))
            
            # 异步执行
            start_time = time.time()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                func,
                *args,
                **kwargs
            )
            
            # 记录统计
            duration_ms = (time.time() - start_time) * 1000
            with self.lock:
                self.completed_tasks += 1
                self.task_durations.append(duration_ms)
                if len(self.task_durations) > 1000:
                    self.task_durations = self.task_durations[-1000:]
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.pool_name}] 任务执行失败: {e}")
            raise
    
    def get_metrics(self) -> ThreadPoolMetrics:
        """获取线程池指标"""
        queue_size = self.task_queue.qsize()
        queue_usage = (queue_size / self.queue_capacity * 100) if self.queue_capacity > 0 else 0
        
        avg_duration = 0
        if self.task_durations:
            avg_duration = sum(self.task_durations) / len(self.task_durations)
        
        return ThreadPoolMetrics(
            pool_name=self.pool_name,
            core_size=self.core_pool_size,
            max_size=self.max_pool_size,
            active_count=self.executor._threads.__len__() if hasattr(self.executor, '_threads') else 0,
            queue_size=queue_size,
            queue_capacity=self.queue_capacity,
            completed_tasks=self.completed_tasks,
            rejected_tasks=self.rejected_tasks,
            avg_task_duration_ms=avg_duration,
            queue_usage_percent=queue_usage,
            timestamp=datetime.now()
        )
    
    async def auto_scale_monitor(self):
        """自动扩缩容监控"""
        while self.running:
            try:
                metrics = self.get_metrics()
                
                # 检查是否需要扩容
                if metrics.queue_usage_percent > self.scale_up_threshold:
                    current_workers = self.executor._max_workers
                    if current_workers < self.max_pool_size:
                        new_size = min(current_workers + 10, self.max_pool_size)
                        self.executor._max_workers = new_size
                        logger.info(f"[{self.pool_name}] 自动扩容: {current_workers} → {new_size}")
                
                # 检查是否需要缩容
                elif metrics.queue_usage_percent < self.scale_down_threshold:
                    current_workers = self.executor._max_workers
                    if current_workers > self.core_pool_size:
                        new_size = max(current_workers - 5, self.core_pool_size)
                        self.executor._max_workers = new_size
                        logger.info(f"[{self.pool_name}] 自动缩容: {current_workers} → {new_size}")
                
                # 等待下一次检查
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"[{self.pool_name}] 自动扩缩容监控异常: {e}")
                await asyncio.sleep(10)
    
    def start(self):
        """启动线程池"""
        self.running = True
        if self.auto_scale:
            asyncio.create_task(self.auto_scale_monitor())
        logger.info(f"[{self.pool_name}] 线程池已启动 (core={self.core_pool_size}, max={self.max_pool_size})")
    
    def stop(self):
        """停止线程池"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info(f"[{self.pool_name}] 线程池已停止")


class ThreadPoolManager:
    """线程池管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'pools'):
            self.pools: Dict[str, DynamicThreadPool] = {}
    
    def create_pool(
        self,
        pool_name: str,
        core_pool_size: int = 10,
        max_pool_size: int = 50,
        queue_capacity: int = 1000,
        auto_scale: bool = True
    ) -> DynamicThreadPool:
        """创建线程池"""
        if pool_name in self.pools:
            logger.warning(f"线程池 {pool_name} 已存在")
            return self.pools[pool_name]
        
        pool = DynamicThreadPool(
            pool_name=pool_name,
            core_pool_size=core_pool_size,
            max_pool_size=max_pool_size,
            queue_capacity=queue_capacity,
            auto_scale=auto_scale
        )
        pool.start()
        self.pools[pool_name] = pool
        
        logger.info(f"创建线程池: {pool_name}")
        return pool
    
    def get_pool(self, pool_name: str) -> Optional[DynamicThreadPool]:
        """获取线程池"""
        return self.pools.get(pool_name)
    
    def get_all_metrics(self) -> Dict[str, ThreadPoolMetrics]:
        """获取所有线程池指标"""
        return {
            name: pool.get_metrics()
            for name, pool in self.pools.items()
        }
    
    def shutdown_all(self):
        """关闭所有线程池"""
        for pool in self.pools.values():
            pool.stop()
        self.pools.clear()


# 全局线程池管理器实例
thread_pool_manager = ThreadPoolManager()


# 预定义线程池
def init_default_pools():
    """初始化默认线程池"""
    # 消息发送线程池
    thread_pool_manager.create_pool(
        pool_name="message_sender",
        core_pool_size=20,
        max_pool_size=100,
        queue_capacity=2000,
        auto_scale=True
    )
    
    # AI处理线程池
    thread_pool_manager.create_pool(
        pool_name="ai_processor",
        core_pool_size=10,
        max_pool_size=50,
        queue_capacity=500,
        auto_scale=True
    )
    
    # 通知线程池
    thread_pool_manager.create_pool(
        pool_name="notifier",
        core_pool_size=5,
        max_pool_size=20,
        queue_capacity=200,
        auto_scale=True
    )
    
    logger.info("默认线程池已初始化")
