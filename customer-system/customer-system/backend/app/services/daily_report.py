"""定时任务服务 - 每日售后简报"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Project
from app.utils.wechat_work_api import GroupBotAPI
import os


class DailyReportService:
    """每日报表服务"""
    
    @staticmethod
    async def generate_daily_report(db: AsyncSession) -> dict:
        """生成每日售后简报"""
        from sqlalchemy import and_
        
        # 统计各状态的工单数量
        pending_count = await db.scalar(
            select(func.count(Project.id)).where(Project.status == 'pending')
        )
        
        processing_count = await db.scalar(
            select(func.count(Project.id)).where(Project.status == 'processing')
        )
        
        # 统计即将超时的工单（创建超过24小时且未完成）
        overdue_threshold = datetime.now() - timedelta(hours=24)
        overdue_count = await db.scalar(
            select(func.count(Project.id)).where(
                and_(
                    Project.created_at < overdue_threshold,
                    Project.status.in_(['pending', 'processing'])
                )
            )
        )
        
        # 今日新增工单
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await db.scalar(
            select(func.count(Project.id)).where(Project.created_at >= today_start)
        )
        
        return {
            "pending": pending_count or 0,
            "processing": processing_count or 0,
            "overdue": overdue_count or 0,
            "today_new": today_count or 0
        }
    
    @staticmethod
    async def send_daily_report_to_group(db: AsyncSession):
        """发送每日简报到群"""
        webhook_url = os.getenv("GROUP_WEBHOOK_URL")
        if not webhook_url:
            return {"status": "error", "message": "未配置群机器人Webhook"}
        
        # 生成报表
        report = await DailyReportService.generate_daily_report(db)
        
        # 构建消息
        content = f"""【今日售后简报】📊
━━━━━━━━━━━━━━━━━━━━
📌 待处理：{report['pending']}件
⚙️ 处理中：{report['processing']}件
⚠️ 即将超时：{report['overdue']}件
🆕 今日新增：{report['today_new']}件
━━━━━━━━━━━━━━━━━━━━
详情查看：http://localhost:8000/docs

请相关同事及时跟进处理！"""
        
        # 发送到群
        bot = GroupBotAPI(webhook_url)
        result = await bot.send_text(content=content)
        
        return {"status": "success", "report": report, "result": result}
    
    @staticmethod
    async def get_overdue_tickets(db: AsyncSession) -> list:
        """获取超时工单详情"""
        overdue_threshold = datetime.now() - timedelta(hours=24)
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.created_at < overdue_threshold,
                    Project.status.in_(['pending', 'processing'])
                )
            ).limit(10)
        )
        return result.scalars().all()
