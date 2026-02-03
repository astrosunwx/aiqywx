"""
RabbitMQ消息队列服务
实现异步解耦、削峰填谷
"""
import pika
import json
import logging
from typing import Callable, Dict, Optional
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class RabbitMQService:
    """RabbitMQ服务"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5672,
        username: str = 'guest',
        password: str = 'guest',
        virtual_host: str = '/'
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        
        self.connection = None
        self.channel = None
        self.consumers = {}
        self._lock = threading.Lock()
    
    def connect(self):
        """连接RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info(f"[RabbitMQ] 连接成功: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"[RabbitMQ] 连接失败: {e}")
            raise
    
    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        arguments: Optional[Dict] = None
    ):
        """声明队列"""
        try:
            self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                arguments=arguments or {}
            )
            logger.info(f"[RabbitMQ] 声明队列: {queue_name}")
        except Exception as e:
            logger.error(f"[RabbitMQ] 声明队列失败: {e}")
            raise
    
    def publish_message(
        self,
        queue_name: str,
        message: Dict,
        priority: int = 0,
        delay_ms: int = 0
    ):
        """发布消息"""
        try:
            # 添加元数据
            message_data = {
                "data": message,
                "timestamp": datetime.now().isoformat(),
                "priority": priority
            }
            
            # 消息属性
            properties = pika.BasicProperties(
                delivery_mode=2,  # 持久化
                priority=priority,
                content_type='application/json'
            )
            
            # 延迟消息处理
            if delay_ms > 0:
                # 使用延迟队列插件
                properties.headers = {'x-delay': delay_ms}
            
            # 发布消息
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message_data, ensure_ascii=False),
                properties=properties
            )
            
            logger.debug(f"[RabbitMQ] 发布消息: {queue_name} (priority={priority})")
            
        except Exception as e:
            logger.error(f"[RabbitMQ] 发布消息失败: {e}")
            raise
    
    def consume_messages(
        self,
        queue_name: str,
        callback: Callable,
        prefetch_count: int = 1
    ):
        """消费消息"""
        try:
            # 设置QoS
            self.channel.basic_qos(prefetch_count=prefetch_count)
            
            # 定义消费回调
            def on_message(ch, method, properties, body):
                try:
                    message_data = json.loads(body)
                    
                    # 执行回调
                    result = callback(message_data)
                    
                    # 确认消息
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
                    logger.debug(f"[RabbitMQ] 消息处理成功: {queue_name}")
                    
                except Exception as e:
                    logger.error(f"[RabbitMQ] 消息处理失败: {e}")
                    # 拒绝消息并重新入队
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True
                    )
            
            # 开始消费
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message,
                auto_ack=False
            )
            
            self.consumers[queue_name] = True
            logger.info(f"[RabbitMQ] 开始消费: {queue_name}")
            
            # 阻塞消费
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"[RabbitMQ] 消费消息失败: {e}")
            raise
    
    def stop_consuming(self, queue_name: str):
        """停止消费"""
        if queue_name in self.consumers:
            self.channel.stop_consuming()
            del self.consumers[queue_name]
            logger.info(f"[RabbitMQ] 停止消费: {queue_name}")
    
    def close(self):
        """关闭连接"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("[RabbitMQ] 连接已关闭")


class MessageQueue:
    """消息队列管理器"""
    
    # 队列名称常量
    QUEUE_MESSAGE_SEND = "queue.message.send"  # 消息发送队列
    QUEUE_AI_PROCESS = "queue.ai.process"  # AI处理队列
    QUEUE_NOTIFICATION = "queue.notification"  # 通知队列
    QUEUE_DELAYED = "queue.delayed"  # 延迟队列
    
    def __init__(self, rabbitmq_service: RabbitMQService):
        self.mq = rabbitmq_service
        self.init_queues()
    
    def init_queues(self):
        """初始化队列"""
        # 消息发送队列（优先级队列）
        self.mq.declare_queue(
            self.QUEUE_MESSAGE_SEND,
            durable=True,
            arguments={'x-max-priority': 10}
        )
        
        # AI处理队列
        self.mq.declare_queue(
            self.QUEUE_AI_PROCESS,
            durable=True
        )
        
        # 通知队列
        self.mq.declare_queue(
            self.QUEUE_NOTIFICATION,
            durable=True
        )
        
        # 延迟队列（需要rabbitmq-delayed-message-exchange插件）
        self.mq.declare_queue(
            self.QUEUE_DELAYED,
            durable=True,
            arguments={
                'x-delayed-type': 'direct'
            }
        )
        
        logger.info("[MQ] 所有队列已初始化")
    
    async def send_to_queue(
        self,
        queue_name: str,
        data: Dict,
        priority: int = 0,
        delay_ms: int = 0
    ):
        """发送消息到队列"""
        self.mq.publish_message(
            queue_name=queue_name,
            message=data,
            priority=priority,
            delay_ms=delay_ms
        )
    
    async def process_message_send(self, message_data: Dict):
        """处理消息发送（消费者回调）"""
        try:
            # 从消息队列获取数据
            data = message_data.get("data", {})
            trace_id = data.get("trace_id")
            
            # 这里调用实际的消息发送逻辑
            # await send_message(data)
            
            logger.info(f"[MQ] 消息发送完成: trace_id={trace_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MQ] 消息发送失败: {e}")
            return False
    
    async def process_ai_task(self, message_data: Dict):
        """处理AI任务（消费者回调）"""
        try:
            data = message_data.get("data", {})
            trace_id = data.get("trace_id")
            
            # 这里调用AI处理逻辑
            # result = await ai_process(data)
            
            logger.info(f"[MQ] AI处理完成: trace_id={trace_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MQ] AI处理失败: {e}")
            return False
    
    async def process_notification(self, message_data: Dict):
        """处理通知（消费者回调）"""
        try:
            data = message_data.get("data", {})
            
            # 这里调用通知发送逻辑
            # await send_notification(data)
            
            logger.info("[MQ] 通知发送完成")
            return True
            
        except Exception as e:
            logger.error(f"[MQ] 通知发送失败: {e}")
            return False


# 使用示例
"""
# 初始化RabbitMQ服务
mq_service = RabbitMQService(
    host='localhost',
    port=5672,
    username='guest',
    password='guest'
)
mq_service.connect()

# 创建消息队列管理器
message_queue = MessageQueue(mq_service)

# 发送消息到队列
await message_queue.send_to_queue(
    queue_name=MessageQueue.QUEUE_MESSAGE_SEND,
    data={
        "trace_id": "trace_123",
        "phone": "13800138000",
        "content": "测试消息"
    },
    priority=5
)

# 启动消费者（在单独的线程中）
import threading

def start_consumer():
    mq_service.consume_messages(
        queue_name=MessageQueue.QUEUE_MESSAGE_SEND,
        callback=message_queue.process_message_send,
        prefetch_count=10
    )

consumer_thread = threading.Thread(target=start_consumer, daemon=True)
consumer_thread.start()
"""
