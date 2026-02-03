"""
消息消费者服务
从RabbitMQ队列消费消息并处理
"""
import json
import asyncio
import logging
from typing import Callable, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.services.rabbitmq_service import RabbitMQService, MessageQueue
from app.services.message_trace_service import MessageTracer
from app.services.thread_pool_service import ThreadPoolManager
from app.database import SessionLocal, redis_client
from app.models_messaging import MessageRecord, MessageTask, MessageStatus
from sqlalchemy import update

logger = logging.getLogger(__name__)


class MessageProcessor:
    """消息处理器基类"""
    
    def __init__(self):
        self.thread_pool_manager = ThreadPoolManager()
        self.message_tracer = MessageTracer(redis_client)
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """处理消息（子类实现）"""
        raise NotImplementedError


class SMSProcessor(MessageProcessor):
    """短信处理器"""
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """发送短信"""
        try:
            # 模拟发送短信
            await asyncio.sleep(0.1)
            
            logger.info(f"[短信] 发送成功: {message.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"[短信] 发送失败: {e}")
            return False


class EmailProcessor(MessageProcessor):
    """邮件处理器"""
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """发送邮件"""
        try:
            # 模拟发送邮件
            await asyncio.sleep(0.2)
            
            logger.info(f"[邮件] 发送成功: {message.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"[邮件] 发送失败: {e}")
            return False


class APPProcessor(MessageProcessor):
    """APP推送处理器"""
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """发送APP推送"""
        try:
            # 模拟发送APP推送
            await asyncio.sleep(0.15)
            
            logger.info(f"[APP] 推送成功: {message.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"[APP] 推送失败: {e}")
            return False


class WeChatProcessor(MessageProcessor):
    """微信公众号处理器"""
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """发送微信公众号消息"""
        try:
            # 模拟发送微信消息
            await asyncio.sleep(0.12)
            
            logger.info(f"[微信] 发送成功: {message.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"[微信] 发送失败: {e}")
            return False


class FeishuProcessor(MessageProcessor):
    """飞书机器人处理器"""
    
    async def process(self, message: Dict[str, Any]) -> bool:
        """发送飞书消息"""
        try:
            # 模拟发送飞书消息
            await asyncio.sleep(0.1)
            
            logger.info(f"[飞书] 发送成功: {message.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"[飞书] 发送失败: {e}")
            return False


class MessageConsumer:
    """消息消费者"""
    
    def __init__(self):
        self.rabbitmq = RabbitMQService()
        self.message_queue = MessageQueue()
        self.tracer = MessageTracer(redis_client)
        
        # 注册处理器
        self.processors = {
            'sms': SMSProcessor(),
            'email': EmailProcessor(),
            'app': APPProcessor(),
            'wechat': WeChatProcessor(),
            'feishu': FeishuProcessor()
        }
        
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def start(self):
        """启动消费者"""
        logger.info("[消息消费者] 启动中...")
        
        # 消费消息发送队列
        self.rabbitmq.consume_messages(
            queue=self.message_queue.QUEUE_MESSAGE_SEND,
            callback=self._handle_message_send
        )
    
    def _handle_message_send(self, ch, method, properties, body):
        """处理消息发送"""
        try:
            message = json.loads(body)
            
            # 处理单条消息
            if message.get('type') != 'batch':
                asyncio.run(self._process_single_message(message))
            else:
                # 处理批量任务
                asyncio.run(self._process_batch_task(message))
            
            # 确认消息
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"[消息消费者] 处理失败: {e}")
            # 拒绝消息并重新入队
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    async def _process_single_message(self, message: Dict[str, Any]):
        """处理单条消息"""
        record_id = message.get('record_id')
        trace_id = message.get('trace_id')
        channel = message.get('channel')
        
        # 添加追踪节点
        self.tracer.add_node(trace_id, 'process', {'record_id': record_id})
        
        # 更新消息状态为发送中
        await self._update_record_status(record_id, MessageStatus.SENDING)
        
        # 获取处理器
        processor = self.processors.get(channel)
        if not processor:
            logger.error(f"[消息消费者] 未找到处理器: {channel}")
            await self._update_record_status(
                record_id, 
                MessageStatus.FAILED,
                error_message=f"不支持的渠道: {channel}"
            )
            self.tracer.finish_node(trace_id, 'process', {'status': 'failed'})
            return
        
        # 处理消息
        self.tracer.add_node(trace_id, 'send', {'channel': channel})
        
        success = await processor.process(message)
        
        if success:
            # 发送成功
            await self._update_record_status(
                record_id,
                MessageStatus.SUCCESS,
                sent_at=datetime.now()
            )
            self.tracer.finish_node(trace_id, 'send', {'status': 'success'})
            self.tracer.finish_node(trace_id, 'process', {'status': 'success'})
            self.tracer.finish_trace(trace_id, {'status': 'success'})
            
        else:
            # 发送失败
            await self._update_record_status(
                record_id,
                MessageStatus.FAILED,
                error_message="发送失败"
            )
            self.tracer.finish_node(trace_id, 'send', {'status': 'failed'})
            self.tracer.finish_node(trace_id, 'process', {'status': 'failed'})
            self.tracer.finish_trace(trace_id, {'status': 'failed'})
    
    async def _process_batch_task(self, message: Dict[str, Any]):
        """处理批量任务"""
        task_id = message.get('task_id')
        
        # 查询任务下的所有消息
        db = SessionLocal()
        try:
            from sqlalchemy import select
            from app.models_messaging import MessageRecord
            
            result = await db.execute(
                select(MessageRecord).where(
                    MessageRecord.task_id == task_id,
                    MessageRecord.status == MessageStatus.PENDING
                ).limit(100)  # 每次处理100条
            )
            
            records = result.scalars().all()
            
            # 批量发送
            for record in records:
                msg = {
                    'record_id': record.id,
                    'trace_id': record.trace_id,
                    'channel': record.channel,
                    'recipient': record.recipient,
                    'content': record.content
                }
                
                await self._process_single_message(msg)
            
        finally:
            await db.close()
    
    async def _update_record_status(
        self,
        record_id: int,
        status: str,
        error_message: str = None,
        sent_at: datetime = None
    ):
        """更新消息记录状态"""
        db = SessionLocal()
        try:
            update_data = {'status': status}
            
            if error_message:
                update_data['error_message'] = error_message
            
            if sent_at:
                update_data['sent_at'] = sent_at
            
            await db.execute(
                update(MessageRecord).where(
                    MessageRecord.id == record_id
                ).values(**update_data)
            )
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"[消息消费者] 更新记录状态失败: {e}")
            await db.rollback()
            
        finally:
            await db.close()


# 全局消费者实例
consumer = MessageConsumer()


def start_consumer():
    """启动消费者（在单独的进程中运行）"""
    consumer.start()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动消费者
    start_consumer()
