"""
定时任务调度器
Scheduled Task Scheduler

功能：
- 定时发送消息（daily/weekly/monthly）
- 失败重试机制
- 任务监控和日志
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import logging
import asyncio

from app.services.unified_message_sender import UnifiedMessageSender, SendMode, MessageStatus

logger = logging.getLogger(__name__)


class MessageScheduler:
    """消息调度器"""
    
    def __init__(self, db_pool):
        """
        初始化调度器
        
        Args:
            db_pool: 数据库连接池
        """
        self.db = db_pool
        self.scheduler = AsyncIOScheduler()
        self.sender = UnifiedMessageSender(db_pool)
        self._initialized = False
    
    async def initialize(self):
        """初始化调度器，加载所有定时任务"""
        if self._initialized:
            return
        
        logger.info("开始初始化消息调度器...")
        
        try:
            # 加载所有定时推送的模板
            async with self.db.acquire() as conn:
                templates = await conn.fetch("""
                    SELECT * FROM message_templates
                    WHERE push_mode = 'scheduled'
                    AND is_enabled = TRUE
                    AND schedule_time IS NOT NULL
                """)
            
            logger.info(f"找到 {len(templates)} 个定时推送模板")
            
            # 为每个模板创建定时任务
            for template in templates:
                await self._add_template_job(dict(template))
            
            # 添加失败重试任务（每5分钟检查一次）
            self.scheduler.add_job(
                self._retry_failed_messages,
                CronTrigger(minute='*/5'),
                id='retry_failed_messages',
                name='失败消息重试'
            )
            
            # 添加清理过期消息任务（每天凌晨3点）
            self.scheduler.add_job(
                self._cleanup_old_messages,
                CronTrigger(hour=3, minute=0),
                id='cleanup_old_messages',
                name='清理过期消息'
            )
            
            self._initialized = True
            logger.info("✅ 消息调度器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 消息调度器初始化失败: {e}")
            raise
    
    async def _add_template_job(self, template: dict):
        """
        为模板添加定时任务
        
        Args:
            template: 模板记录
        """
        template_id = template["id"]
        template_name = template["name"]
        schedule_time = template["schedule_time"]
        repeat_type = template["repeat_type"]
        
        # 解析时间
        if isinstance(schedule_time, str):
            hour, minute = map(int, schedule_time.split(':'))
        else:
            hour = schedule_time.hour
            minute = schedule_time.minute
        
        # 根据重复类型创建触发器
        if repeat_type == "daily":
            trigger = CronTrigger(hour=hour, minute=minute)
        elif repeat_type == "weekly":
            # 每周一执行
            trigger = CronTrigger(day_of_week='mon', hour=hour, minute=minute)
        elif repeat_type == "monthly":
            # 每月1号执行
            trigger = CronTrigger(day=1, hour=hour, minute=minute)
        else:
            # 仅一次（立即执行）
            trigger = CronTrigger(hour=hour, minute=minute)
        
        # 添加任务
        self.scheduler.add_job(
            self._execute_template_job,
            trigger,
            args=[template_id],
            id=f'template_{template_id}',
            name=f'定时推送: {template_name}',
            replace_existing=True
        )
        
        logger.info(f"已添加定时任务: {template_name} ({repeat_type} at {hour:02d}:{minute:02d})")
    
    async def _execute_template_job(self, template_id: int):
        """
        执行模板定时任务
        
        Args:
            template_id: 模板ID
        """
        logger.info(f"开始执行定时任务: template_id={template_id}")
        
        try:
            # 加载模板
            async with self.db.acquire() as conn:
                template = await conn.fetchrow("""
                    SELECT * FROM message_templates WHERE id = $1
                """, template_id)
                
                if not template:
                    logger.error(f"模板不存在: {template_id}")
                    return
                
                template = dict(template)
            
            # 获取目标接收者
            recipients = await self._get_template_recipients(template)
            
            if not recipients:
                logger.warning(f"模板 {template['name']} 没有接收者")
                return
            
            logger.info(f"找到 {len(recipients)} 个接收者")
            
            # 获取变量（这里使用实时数据）
            variables = await self._get_template_variables(template)
            
            # 批量发送
            results = await self.sender.send_from_template(
                template_id=template_id,
                recipients=recipients,
                variables=variables,
                send_mode=SendMode.REALTIME  # 定时任务到时间后立即发送
            )
            
            # 统计结果
            success_count = sum(1 for r in results if r["success"])
            failed_count = len(results) - success_count
            
            logger.info(
                f"定时任务执行完成: template_id={template_id}, "
                f"成功={success_count}, 失败={failed_count}"
            )
            
        except Exception as e:
            logger.error(f"定时任务执行失败: template_id={template_id}, 错误: {e}")
    
    async def _get_template_recipients(self, template: dict) -> list:
        """
        获取模板的接收者列表
        
        Args:
            template: 模板记录
        
        Returns:
            接收者列表
            [
                {"customer_id": 123, "identifier": "13800138000"},
                ...
            ]
        """
        module_type = template["module_type"]
        targets = template.get("targets") or []
        target_config = template.get("target_config") or {}
        
        recipients = []
        
        if module_type == "GROUP_BOT":
            # 群机器人：从target_config获取bot_id，然后查询group_id
            bot_id = target_config.get("bot_id")
            if bot_id:
                async with self.db.acquire() as conn:
                    config = await conn.fetchval("""
                        SELECT config_data FROM channel_configs
                        WHERE channel_type = 'GROUP_BOT'
                    """)
                    
                    if config:
                        bots = config.get("bots", [])
                        for bot in bots:
                            if bot["bot_id"] == bot_id:
                                recipients.append({
                                    "customer_id": None,
                                    "identifier": bot["group_id"]
                                })
        
        elif module_type == "AI":
            # @智能助手：从target_config获取目标群列表
            target_groups = target_config.get("target_groups", [])
            for group_id in target_groups:
                recipients.append({
                    "customer_id": None,
                    "identifier": group_id
                })
        
        elif module_type == "WORK_WECHAT":
            # 企业微信：查询客户的external_user_id
            async with self.db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT customer_id, identifier_value
                    FROM customer_channel_identifiers
                    WHERE channel_type = 'WORK_WECHAT'
                    AND is_verified = TRUE
                """)
                
                recipients = [
                    {
                        "customer_id": row["customer_id"],
                        "identifier": row["identifier_value"]
                    }
                    for row in rows
                ]
        
        elif module_type == "WECHAT":
            # 微信公众号：查询粉丝的openid
            async with self.db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT customer_id, identifier_value
                    FROM customer_channel_identifiers
                    WHERE channel_type = 'WECHAT'
                    AND is_verified = TRUE
                """)
                
                recipients = [
                    {
                        "customer_id": row["customer_id"],
                        "identifier": row["identifier_value"]
                    }
                    for row in rows
                ]
        
        elif module_type == "SMS":
            # 短信：查询客户手机号
            async with self.db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT customer_id, identifier_value
                    FROM customer_channel_identifiers
                    WHERE channel_type = 'SMS'
                    AND is_verified = TRUE
                """)
                
                recipients = [
                    {
                        "customer_id": row["customer_id"],
                        "identifier": row["identifier_value"]
                    }
                    for row in rows
                ]
        
        elif module_type == "EMAIL":
            # 邮件：查询客户邮箱
            async with self.db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT customer_id, identifier_value
                    FROM customer_channel_identifiers
                    WHERE channel_type = 'EMAIL'
                    AND is_verified = TRUE
                """)
                
                recipients = [
                    {
                        "customer_id": row["customer_id"],
                        "identifier": row["identifier_value"]
                    }
                    for row in rows
                ]
        
        return recipients
    
    async def _get_template_variables(self, template: dict) -> dict:
        """
        获取模板变量的实时值
        
        Args:
            template: 模板记录
        
        Returns:
            变量字典
        """
        # 这里根据模板内容动态查询数据
        # 示例：如果是"每日工作提醒"，则查询工单统计
        
        variables = {
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "current_time": datetime.now().strftime("%H:%M:%S"),
        }
        
        # 如果模板包含工单相关变量
        if "pending_count" in template["content"]:
            async with self.db.acquire() as conn:
                pending_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM service_tickets
                    WHERE status = 'pending'
                """) or 0
                variables["pending_count"] = pending_count
        
        if "processing_count" in template["content"]:
            async with self.db.acquire() as conn:
                processing_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM service_tickets
                    WHERE status = 'processing'
                """) or 0
                variables["processing_count"] = processing_count
        
        if "completed_count" in template["content"]:
            async with self.db.acquire() as conn:
                completed_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM service_tickets
                    WHERE status = 'completed'
                """) or 0
                variables["completed_count"] = completed_count
        
        return variables
    
    async def _retry_failed_messages(self):
        """重试失败的消息"""
        logger.info("开始检查失败消息...")
        
        try:
            async with self.db.acquire() as conn:
                # 查询待重试的消息
                messages = await conn.fetch("""
                    SELECT * FROM messages
                    WHERE status = $1
                    AND retry_count < max_retries
                    ORDER BY created_at ASC
                    LIMIT 100
                """, MessageStatus.PENDING)
            
            if not messages:
                logger.info("没有需要重试的消息")
                return
            
            logger.info(f"找到 {len(messages)} 条待重试消息")
            
            # 逐条重试
            success_count = 0
            for msg in messages:
                message = dict(msg)
                result = await self.sender.send_message(message)
                if result["success"]:
                    success_count += 1
            
            logger.info(f"重试完成: 成功={success_count}, 失败={len(messages) - success_count}")
            
        except Exception as e:
            logger.error(f"重试失败消息时出错: {e}")
    
    async def _cleanup_old_messages(self):
        """清理过期消息（保留最近30天）"""
        logger.info("开始清理过期消息...")
        
        try:
            async with self.db.acquire() as conn:
                deleted = await conn.fetchval("""
                    DELETE FROM messages
                    WHERE created_at < NOW() - INTERVAL '30 days'
                    AND status IN ('sent', 'failed')
                    RETURNING COUNT(*)
                """) or 0
            
            logger.info(f"清理完成: 删除 {deleted} 条过期消息")
            
        except Exception as e:
            logger.error(f"清理过期消息时出错: {e}")
    
    async def reload_template_job(self, template_id: int):
        """
        重新加载模板任务（模板更新时调用）
        
        Args:
            template_id: 模板ID
        """
        logger.info(f"重新加载模板任务: template_id={template_id}")
        
        try:
            # 移除旧任务
            job_id = f'template_{template_id}'
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 加载新任务
            async with self.db.acquire() as conn:
                template = await conn.fetchrow("""
                    SELECT * FROM message_templates
                    WHERE id = $1
                    AND push_mode = 'scheduled'
                    AND is_enabled = TRUE
                """, template_id)
                
                if template:
                    await self._add_template_job(dict(template))
                    logger.info(f"✅ 模板任务重新加载成功: {template['name']}")
                else:
                    logger.info(f"模板已禁用或删除: template_id={template_id}")
        
        except Exception as e:
            logger.error(f"重新加载模板任务失败: {e}")
    
    def start(self):
        """启动调度器"""
        if not self._initialized:
            raise RuntimeError("请先调用 initialize() 初始化调度器")
        
        self.scheduler.start()
        logger.info("🚀 消息调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("⏹️ 消息调度器已关闭")
    
    def get_jobs(self) -> list:
        """获取所有任务"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]


# 全局调度器实例
_scheduler_instance = None


async def get_scheduler(db_pool) -> MessageScheduler:
    """获取调度器单例"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = MessageScheduler(db_pool)
        await _scheduler_instance.initialize()
    
    return _scheduler_instance
