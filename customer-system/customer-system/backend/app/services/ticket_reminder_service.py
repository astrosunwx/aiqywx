"""
工单超时提醒服务
实现24小时超时自动提醒，类似腾讯客服的催促机制
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from ..models import Project, Customer
from ..utils.wechat_work_api import GroupBotAPI
import os
import asyncio


class TicketReminderService:
    """工单超时提醒服务"""
    
    @staticmethod
    async def check_overdue_tickets(db: AsyncSession) -> List[Project]:
        """
        检查超时工单
        
        Returns:
            超时工单列表
        """
        now = datetime.now()
        
        # 查询超时且未解决的工单
        stmt = select(Project).where(
            and_(
                Project.project_type == 'aftersale',
                Project.status.in_(['pending', 'assigned', 'processing']),  # 未完成状态
                Project.deadline < now,  # 已超期
                or_(
                    Project.last_reminder_at.is_(None),  # 从未提醒过
                    Project.last_reminder_at < now - timedelta(hours=2)  # 距上次提醒超过2小时
                )
            )
        ).order_by(Project.deadline.asc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def send_overdue_reminder(
        db: AsyncSession,
        ticket: Project,
        customer: Customer = None
    ) -> bool:
        """
        发送超时提醒到内部群
        
        Args:
            db: 数据库会话
            ticket: 工单对象
            customer: 客户对象（可选）
        
        Returns:
            是否发送成功
        """
        webhook_url = os.getenv("GROUP_WEBHOOK_URL")
        if not webhook_url:
            print("⚠️  未配置GROUP_WEBHOOK_URL，无法发送提醒")
            return False
        
        bot = GroupBotAPI(webhook_url)
        
        # 如果没有传入customer，查询数据库
        if not customer and ticket.customer_id:
            stmt = select(Customer).where(Customer.id == ticket.customer_id)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
        
        # 计算超时时长
        overdue_hours = int((datetime.now() - ticket.deadline).total_seconds() / 3600)
        
        # 提醒次数
        ticket.reminder_count = (ticket.reminder_count or 0) + 1
        
        # 构建提醒消息
        urgency_icon = "⚠️"
        if overdue_hours > 48:
            urgency_icon = "🚨🚨🚨"
        elif overdue_hours > 24:
            urgency_icon = "🚨🚨"
        elif overdue_hours > 12:
            urgency_icon = "🚨"
        
        content = f"""{urgency_icon} 【工单超时提醒】

工单编号：#{ticket.id}
客户：{customer.name if customer else '未知'} ({ticket.customer_phone})
问题：{ticket.description[:50]}{'...' if len(ticket.description) > 50 else ''}

当前状态：{ticket.status}
负责人：{ticket.assigned_to_name or '未分配 ⚠️'}
处理进度：{ticket.progress}%

⏰ 处理期限：{ticket.deadline.strftime('%Y-%m-%d %H:%M')}
⏱️  已超时：{overdue_hours} 小时
🔔 催促次数：第 {ticket.reminder_count} 次

{'@' + ticket.assigned_to_name if ticket.assigned_to_name else '@all'} 请尽快处理！

---
💡 回复 "#{ticket.id} 已解决" 可关闭工单
💡 回复 "#{ticket.id} 升级处理" 可升级工单"""
        
        try:
            # 发送提醒
            mentioned_list = []
            if ticket.assigned_to_name:
                mentioned_list = [ticket.assigned_to_name]
            else:
                mentioned_list = ["@all"]
            
            await bot.send_text(
                content=content,
                mentioned_list=mentioned_list
            )
            
            # 更新提醒时间
            ticket.last_reminder_at = datetime.now()
            await db.commit()
            
            print(f"✅ 工单 #{ticket.id} 超时提醒已发送（超时{overdue_hours}小时）")
            return True
        
        except Exception as e:
            print(f"❌ 发送超时提醒失败: {e}")
            return False
    
    @staticmethod
    async def run_reminder_task(db: AsyncSession):
        """
        运行提醒任务（定时任务入口）
        
        建议配置：
        1. APScheduler：每小时运行一次
        2. Celery Beat：定时任务
        3. 系统cron：0 */1 * * *
        """
        print("🔍 开始检查超时工单...")
        
        try:
            # 查询超时工单
            overdue_tickets = await TicketReminderService.check_overdue_tickets(db)
            
            if not overdue_tickets:
                print("✅ 没有超时工单")
                return
            
            print(f"📋 发现 {len(overdue_tickets)} 个超时工单")
            
            # 逐个发送提醒
            for ticket in overdue_tickets:
                # 查询客户信息
                stmt = select(Customer).where(Customer.id == ticket.customer_id)
                result = await db.execute(stmt)
                customer = result.scalar_one_or_none()
                
                # 发送提醒
                await TicketReminderService.send_overdue_reminder(db, ticket, customer)
                
                # 避免频繁发送，间隔1秒
                await asyncio.sleep(1)
            
            print(f"✅ 超时提醒任务完成，共处理 {len(overdue_tickets)} 个工单")
        
        except Exception as e:
            print(f"❌ 超时提醒任务执行失败: {e}")
            import traceback
            traceback.print_exc()


# 可选：使用APScheduler实现定时任务
class ReminderScheduler:
    """提醒任务调度器（可选）"""
    
    def __init__(self, db_session_factory):
        """
        初始化调度器
        
        Args:
            db_session_factory: 数据库会话工厂函数
        """
        self.db_session_factory = db_session_factory
        self.scheduler = None
    
    def start(self):
        """启动定时任务"""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            self.scheduler = AsyncIOScheduler()
            
            # 每小时检查一次超时工单
            self.scheduler.add_job(
                self._run_task,
                CronTrigger(minute=0),  # 每小时的0分
                id='ticket_reminder',
                name='工单超时提醒',
                replace_existing=True
            )
            
            self.scheduler.start()
            print("✅ 工单超时提醒任务已启动（每小时运行）")
        
        except ImportError:
            print("⚠️  APScheduler未安装，定时提醒功能不可用")
            print("   安装命令：pip install apscheduler")
    
    async def _run_task(self):
        """执行任务"""
        async with self.db_session_factory() as db:
            await TicketReminderService.run_reminder_task(db)
    
    def stop(self):
        """停止定时任务"""
        if self.scheduler:
            self.scheduler.shutdown()
            print("⏹️  工单超时提醒任务已停止")
