"""
统一消息发送服务
Unified Message Sender Service

功能：
- 统一的消息发送接口，支持6大渠道（SMS/EMAIL/GROUP_BOT/AI/WORK_WECHAT/WECHAT）
- 消息模板渲染
- 失败重试机制
- 发送记录追踪
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import json
import re

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """渠道类型"""
    SMS = "SMS"  # 短信
    EMAIL = "EMAIL"  # 邮件
    GROUP_BOT = "GROUP_BOT"  # 群机器人
    AI = "AI"  # @智能助手
    WORK_WECHAT = "WORK_WECHAT"  # 企业微信客服
    WECHAT = "WECHAT"  # 微信公众号


class MessageStatus(str, Enum):
    """消息状态"""
    PENDING = "pending"  # 待发送
    SENDING = "sending"  # 发送中
    SENT = "sent"  # 已发送
    FAILED = "failed"  # 失败


class SendMode(str, Enum):
    """发送模式"""
    REALTIME = "realtime"  # 实时发送
    SCHEDULED = "scheduled"  # 定时发送


# 每个渠道需要的接收者标识符类型
CHANNEL_RECIPIENT_TYPE = {
    "SMS": "phone",  # 手机号
    "EMAIL": "email",  # 邮箱
    "GROUP_BOT": "group_id",  # 群ID
    "AI": "group_id",  # 群ID
    "WORK_WECHAT": "external_user_id",  # 企业微信外部联系人ID
    "WECHAT": "openid"  # 微信公众号OpenID
}


class TemplateRenderer:
    """模板渲染引擎"""
    
    @staticmethod
    def render(template_content: str, variables: Dict[str, Any]) -> str:
        """
        渲染模板内容
        
        Args:
            template_content: 模板内容，如 "您好，{customer_name}！"
            variables: 变量字典，如 {"customer_name": "张三"}
        
        Returns:
            渲染后的内容
        """
        result = template_content
        
        for key, value in variables.items():
            # 支持 {key} 和 ${key} 两种格式
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"${{{key}}}", str(value))
        
        return result
    
    @staticmethod
    def extract_variables(template_content: str) -> List[str]:
        """
        提取模板中的变量
        
        Args:
            template_content: 模板内容
        
        Returns:
            变量列表，如 ["customer_name", "project_name"]
        """
        # 匹配 {key} 和 ${key} 格式
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        variables = re.findall(pattern, template_content)
        
        pattern2 = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        variables2 = re.findall(pattern2, template_content)
        
        return list(set(variables + variables2))


class UnifiedMessageSender:
    """统一消息发送服务"""
    
    def __init__(self, db_pool):
        """
        初始化
        
        Args:
            db_pool: 数据库连接池
        """
        self.db = db_pool
        self.renderer = TemplateRenderer()
        
        # 延迟导入各渠道的发送器（避免循环导入）
        self._senders = {}
    
    def _get_sender(self, channel_type: str):
        """获取指定渠道的发送器"""
        if channel_type not in self._senders:
            if channel_type == ChannelType.SMS:
                from .senders.sms_sender import SMSSender
                self._senders[channel_type] = SMSSender(self.db)
            elif channel_type == ChannelType.EMAIL:
                from .senders.email_sender import EmailSender
                self._senders[channel_type] = EmailSender(self.db)
            elif channel_type == ChannelType.GROUP_BOT:
                from .senders.group_bot_sender import GroupBotSender
                self._senders[channel_type] = GroupBotSender(self.db)
            elif channel_type == ChannelType.AI:
                from .senders.ai_bot_sender import AIBotSender
                self._senders[channel_type] = AIBotSender(self.db)
            elif channel_type == ChannelType.WORK_WECHAT:
                from .senders.work_wechat_sender import WorkWechatSender
                self._senders[channel_type] = WorkWechatSender(self.db)
            elif channel_type == ChannelType.WECHAT:
                from .senders.wechat_sender import WechatSender
                self._senders[channel_type] = WechatSender(self.db)
            else:
                raise ValueError(f"不支持的渠道类型: {channel_type}")
        
        return self._senders[channel_type]
    
    async def get_channel_config(self, channel_type: str) -> Dict[str, Any]:
        """
        获取渠道配置
        
        Args:
            channel_type: 渠道类型
        
        Returns:
            配置数据
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT config_data, is_enabled
                FROM channel_configs
                WHERE channel_type = $1
            """, channel_type)
            
            if not row:
                raise ValueError(f"渠道配置不存在: {channel_type}")
            
            if not row['is_enabled']:
                raise ValueError(f"渠道已禁用: {channel_type}")
            
            return row['config_data']
    
    async def validate_recipient(self, channel_type: str, recipient_value: str) -> bool:
        """
        验证接收者标识符
        
        Args:
            channel_type: 渠道类型
            recipient_value: 接收者标识符
        
        Returns:
            是否有效
        """
        recipient_type = CHANNEL_RECIPIENT_TYPE.get(channel_type)
        
        if recipient_type == "phone":
            # 验证手机号格式
            return bool(re.match(r'^1[3-9]\d{9}$', recipient_value))
        elif recipient_type == "email":
            # 验证邮箱格式
            return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', recipient_value))
        elif recipient_type in ["openid", "external_user_id", "group_id"]:
            # 微信相关ID，基本验证非空
            return bool(recipient_value and len(recipient_value) > 0)
        
        return True
    
    async def create_message_record(
        self,
        template_id: Optional[int],
        channel_type: str,
        recipient_value: str,
        customer_id: Optional[int],
        content: str,
        subject: Optional[str] = None,
        send_mode: str = SendMode.REALTIME,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建消息记录
        
        Args:
            template_id: 模板ID
            channel_type: 渠道类型
            recipient_value: 接收者标识符
            customer_id: 客户ID
            content: 消息内容
            subject: 主题（邮件）
            send_mode: 发送模式
            scheduled_time: 定时发送时间
            metadata: 元数据
        
        Returns:
            消息记录
        """
        # 生成消息编号
        message_no = f"MSG{datetime.now().strftime('%Y%m%d%H%M%S')}{customer_id or 0:06d}"
        
        recipient_type = CHANNEL_RECIPIENT_TYPE.get(channel_type)
        
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO messages (
                    message_no,
                    template_id,
                    channel_type,
                    sender_type,
                    sender_id,
                    recipient_type,
                    recipient_value,
                    customer_id,
                    subject,
                    content,
                    content_type,
                    status,
                    send_mode,
                    scheduled_time,
                    metadata,
                    created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW()
                )
                RETURNING *
            """,
                message_no,
                template_id,
                channel_type,
                "system",  # sender_type
                None,  # sender_id
                recipient_type,
                recipient_value,
                customer_id,
                subject,
                content,
                "text",  # content_type
                MessageStatus.PENDING,
                send_mode,
                scheduled_time,
                json.dumps(metadata) if metadata else None
            )
            
            return dict(row)
    
    async def update_message_status(
        self,
        message_id: int,
        status: str,
        sent_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        """
        更新消息状态
        
        Args:
            message_id: 消息ID
            status: 状态
            sent_at: 发送时间
            error_message: 错误消息
        """
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE messages
                SET status = $1,
                    sent_at = $2,
                    error_message = $3,
                    updated_at = NOW()
                WHERE id = $4
            """, status, sent_at, error_message, message_id)
    
    async def send_message(self, message_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息
        
        Args:
            message_record: 消息记录
        
        Returns:
            发送结果
            {
                "success": True/False,
                "message_id": "MSG20240203001",
                "sent_at": "2024-02-03T10:30:00",
                "error": None
            }
        """
        channel_type = message_record["channel_type"]
        
        try:
            # 1. 获取渠道配置
            config = await self.get_channel_config(channel_type)
            
            # 2. 验证接收者
            is_valid = await self.validate_recipient(
                channel_type,
                message_record["recipient_value"]
            )
            if not is_valid:
                raise ValueError(f"无效的接收者标识符: {message_record['recipient_value']}")
            
            # 3. 更新状态为发送中
            await self.update_message_status(
                message_record["id"],
                MessageStatus.SENDING
            )
            
            # 4. 获取对应渠道的发送器
            sender = self._get_sender(channel_type)
            
            # 5. 发送消息
            result = await sender.send(
                config=config,
                recipient=message_record["recipient_value"],
                content=message_record["content"],
                subject=message_record.get("subject"),
                metadata=message_record.get("metadata")
            )
            
            # 6. 更新状态为已发送
            await self.update_message_status(
                message_record["id"],
                MessageStatus.SENT,
                sent_at=datetime.now()
            )
            
            logger.info(f"消息发送成功: {message_record['message_no']}")
            
            return {
                "success": True,
                "message_id": message_record["message_no"],
                "sent_at": datetime.now().isoformat(),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"消息发送失败: {message_record['message_no']}, 错误: {e}")
            
            # 更新状态为失败
            await self.update_message_status(
                message_record["id"],
                MessageStatus.FAILED,
                error_message=str(e)
            )
            
            # 判断是否需要重试
            if message_record["retry_count"] < message_record["max_retries"]:
                await self.schedule_retry(message_record["id"])
            
            return {
                "success": False,
                "message_id": message_record["message_no"],
                "error": str(e)
            }
    
    async def schedule_retry(self, message_id: int):
        """
        安排重试
        
        Args:
            message_id: 消息ID
        """
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE messages
                SET retry_count = retry_count + 1,
                    status = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, MessageStatus.PENDING, message_id)
        
        logger.info(f"已安排重试: message_id={message_id}")
    
    async def send_from_template(
        self,
        template_id: int,
        recipients: List[Dict[str, Any]],
        variables: Dict[str, Any],
        send_mode: str = SendMode.REALTIME,
        scheduled_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        使用模板批量发送
        
        Args:
            template_id: 模板ID
            recipients: 接收者列表
                [
                    {"customer_id": 123, "identifier": "13800138000"},
                    {"customer_id": 124, "identifier": "openid_xxx"}
                ]
            variables: 变量字典
                {"customer_name": "张三", "project_id": "123"}
            send_mode: 发送模式
            scheduled_time: 定时发送时间
        
        Returns:
            发送结果列表
            [
                {"customer_id": 123, "message_id": "MSG001", "success": True},
                {"customer_id": 124, "message_id": "MSG002", "success": False, "error": "xxx"}
            ]
        """
        # 1. 加载模板
        async with self.db.acquire() as conn:
            template = await conn.fetchrow("""
                SELECT * FROM message_templates WHERE id = $1
            """, template_id)
            
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
        
        # 2. 渲染内容
        rendered_content = self.renderer.render(template["content"], variables)
        
        # 3. 批量创建消息记录
        messages = []
        for recipient in recipients:
            message_record = await self.create_message_record(
                template_id=template_id,
                channel_type=template["module_type"],
                recipient_value=recipient["identifier"],
                customer_id=recipient.get("customer_id"),
                content=rendered_content,
                subject=template.get("name"),
                send_mode=send_mode,
                scheduled_time=scheduled_time,
                metadata=recipient.get("metadata")
            )
            messages.append(message_record)
        
        # 4. 发送消息
        results = []
        for message in messages:
            if send_mode == SendMode.REALTIME:
                # 立即发送
                result = await self.send_message(message)
            else:
                # 加入定时任务队列
                result = {
                    "success": True,
                    "message_id": message["message_no"],
                    "scheduled": True,
                    "scheduled_time": scheduled_time.isoformat() if scheduled_time else None
                }
            
            results.append({
                "customer_id": message["customer_id"],
                **result
            })
        
        return results
    
    async def get_message_by_no(self, message_no: str) -> Optional[Dict[str, Any]]:
        """
        根据消息编号查询消息
        
        Args:
            message_no: 消息编号
        
        Returns:
            消息记录
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM messages WHERE message_no = $1
            """, message_no)
            
            return dict(row) if row else None
    
    async def get_customer_messages(
        self,
        customer_id: int,
        channel_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查询客户的消息记录
        
        Args:
            customer_id: 客户ID
            channel_type: 渠道类型（可选）
            limit: 返回数量
        
        Returns:
            消息记录列表
        """
        async with self.db.acquire() as conn:
            if channel_type:
                rows = await conn.fetch("""
                    SELECT * FROM messages
                    WHERE customer_id = $1 AND channel_type = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """, customer_id, channel_type, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM messages
                    WHERE customer_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, customer_id, limit)
            
            return [dict(row) for row in rows]
