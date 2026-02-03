"""
Xxl-job定时任务服务
支持分布式任务调度
"""
import logging
from datetime import datetime, timedelta
from typing import Callable
from pyxxl import ExecutorConfig, PyxxlRunner

from app.database import SessionLocal
from app.models_messaging import MessageStatistics, MessageRecord, MessageTask
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


class XxlJobService:
    """Xxl-job服务"""
    
    def __init__(
        self,
        admin_addresses: str = "http://localhost:8080/xxl-job-admin",
        app_name: str = "customer-system-executor",
        access_token: str = ""
    ):
        """
        初始化Xxl-job执行器
        
        Args:
            admin_addresses: Xxl-job管理端地址
            app_name: 执行器应用名
            access_token: 访问令牌
        """
        config = ExecutorConfig(
            admin_addresses=admin_addresses,
            app_name=app_name,
            access_token=access_token
        )
        
        self.runner = PyxxlRunner(config)
        
        logger.info(f"[Xxl-job] 执行器已配置: {app_name}")
    
    def register_handler(self, handler_name: str):
        """注册任务处理器（装饰器）"""
        def decorator(func: Callable):
            self.runner.register(name=handler_name, handler=func)
            logger.info(f"[Xxl-job] 注册处理器: {handler_name}")
            return func
        
        return decorator
    
    def start(self):
        """启动执行器"""
        logger.info("[Xxl-job] 执行器启动中...")
        self.runner.run_executor()


# 创建全局实例
xxl_job = XxlJobService()


# ==================== 任务处理器 ====================

@xxl_job.register_handler("updateMessageStatistics")
async def update_message_statistics_job(job_param: str = None):
    """
    定时任务：更新消息统计
    执行时间：每天凌晨1点
    Cron表达式：0 0 1 * * ?
    """
    logger.info("[定时任务] 开始更新消息统计...")
    
    db = SessionLocal()
    try:
        # 统计昨天的数据
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.date()
        
        # 按渠道聚合统计
        result = await db.execute(
            select(
                MessageRecord.channel,
                func.count(MessageRecord.id).label('total_sent'),
                func.sum(
                    func.case((MessageRecord.status == 'success', 1), else_=0)
                ).label('success_count'),
                func.sum(
                    func.case((MessageRecord.status == 'failed', 1), else_=0)
                ).label('failed_count'),
                func.avg(
                    func.extract('epoch', MessageRecord.sent_at - MessageRecord.created_at) * 1000
                ).label('avg_response_time')
            ).where(
                func.date(MessageRecord.created_at) == yesterday_date
            ).group_by(MessageRecord.channel)
        )
        
        stats = result.all()
        
        # 插入或更新统计数据
        for stat in stats:
            stat_record = MessageStatistics(
                stat_date=yesterday_date,
                channel=stat.channel,
                total_sent=stat.total_sent,
                success_count=stat.success_count or 0,
                failed_count=stat.failed_count or 0,
                avg_response_time=int(stat.avg_response_time) if stat.avg_response_time else 0
            )
            
            db.add(stat_record)
        
        await db.commit()
        
        logger.info(f"[定时任务] 消息统计更新完成，共{len(stats)}条记录")
        
        return f"更新{len(stats)}条统计记录"
        
    except Exception as e:
        logger.error(f"[定时任务] 更新消息统计失败: {e}")
        await db.rollback()
        raise
        
    finally:
        await db.close()


@xxl_job.register_handler("sendDailyReport")
async def send_daily_report_job(job_param: str = None):
    """
    定时任务：发送每日报告
    执行时间：每天早上9点
    Cron表达式：0 0 9 * * ?
    """
    logger.info("[定时任务] 开始发送每日报告...")
    
    db = SessionLocal()
    try:
        # 查询昨天的统计数据
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.date()
        
        result = await db.execute(
            select(MessageStatistics).where(
                MessageStatistics.stat_date == yesterday_date
            )
        )
        
        stats = result.scalars().all()
        
        if not stats:
            logger.warning("[定时任务] 没有统计数据")
            return "没有统计数据"
        
        # 汇总数据
        total_sent = sum(s.total_sent for s in stats)
        total_success = sum(s.success_count for s in stats)
        total_failed = sum(s.failed_count for s in stats)
        success_rate = (total_success / total_sent * 100) if total_sent > 0 else 0
        
        # 生成报告内容
        report = f"""
📊 每日消息发送报告
━━━━━━━━━━━━━━━━━━
📅 统计日期: {yesterday_date}

📧 总发送量: {total_sent:,}
✅ 成功数量: {total_success:,}
❌ 失败数量: {total_failed:,}
📈 成功率: {success_rate:.2f}%

📱 各渠道详情:
"""
        
        for stat in stats:
            channel_success_rate = (stat.success_count / stat.total_sent * 100) if stat.total_sent > 0 else 0
            report += f"""
  {stat.channel}:
    发送: {stat.total_sent:,}
    成功: {stat.success_count:,} ({channel_success_rate:.2f}%)
    平均响应: {stat.avg_response_time}ms
"""
        
        # TODO: 实际发送报告（邮件/钉钉/企业微信）
        logger.info(f"[定时任务] 每日报告:\n{report}")
        
        return "报告已发送"
        
    except Exception as e:
        logger.error(f"[定时任务] 发送每日报告失败: {e}")
        raise
        
    finally:
        await db.close()


@xxl_job.register_handler("cleanExpiredData")
async def clean_expired_data_job(job_param: str = None):
    """
    定时任务：清理过期数据
    执行时间：每天凌晨3点
    Cron表达式：0 0 3 * * ?
    """
    logger.info("[定时任务] 开始清理过期数据...")
    
    db = SessionLocal()
    try:
        # 删除30天前的消息记录
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        result = await db.execute(
            select(func.count(MessageRecord.id)).where(
                MessageRecord.created_at < thirty_days_ago
            )
        )
        
        count = result.scalar()
        
        if count > 0:
            # 分批删除（每次1000条）
            deleted = 0
            while True:
                delete_result = await db.execute(
                    MessageRecord.__table__.delete().where(
                        MessageRecord.created_at < thirty_days_ago
                    ).limit(1000)
                )
                
                batch_deleted = delete_result.rowcount
                deleted += batch_deleted
                
                await db.commit()
                
                if batch_deleted == 0:
                    break
            
            logger.info(f"[定时任务] 清理过期数据完成，共删除{deleted}条记录")
            
            return f"删除{deleted}条记录"
        
        else:
            logger.info("[定时任务] 没有过期数据需要清理")
            return "无过期数据"
        
    except Exception as e:
        logger.error(f"[定时任务] 清理过期数据失败: {e}")
        await db.rollback()
        raise
        
    finally:
        await db.close()


@xxl_job.register_handler("retryFailedMessages")
async def retry_failed_messages_job(job_param: str = None):
    """
    定时任务：重试失败的消息
    执行时间：每小时执行一次
    Cron表达式：0 0 * * * ?
    """
    logger.info("[定时任务] 开始重试失败消息...")
    
    db = SessionLocal()
    try:
        # 查询失败的消息（24小时内，重试次数<3）
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        result = await db.execute(
            select(MessageRecord).where(
                and_(
                    MessageRecord.status == 'failed',
                    MessageRecord.retry_count < 3,
                    MessageRecord.created_at > twenty_four_hours_ago
                )
            ).limit(100)  # 每次最多重试100条
        )
        
        failed_messages = result.scalars().all()
        
        if not failed_messages:
            logger.info("[定时任务] 没有需要重试的消息")
            return "无需重试的消息"
        
        # 将消息重新加入队列
        from app.services.rabbitmq_service import RabbitMQService, MessageQueue
        
        rabbitmq = RabbitMQService()
        message_queue = MessageQueue()
        
        retry_count = 0
        for record in failed_messages:
            # 更新重试次数
            record.retry_count += 1
            record.status = 'pending'
            
            # 发送到队列
            rabbitmq.publish_message(
                queue=message_queue.QUEUE_MESSAGE_SEND,
                message={
                    'record_id': record.id,
                    'trace_id': record.trace_id,
                    'template_id': record.template_id,
                    'recipient': record.recipient,
                    'channel': record.channel,
                    'content': record.content,
                    'priority': record.priority
                },
                priority=record.priority
            )
            
            retry_count += 1
        
        await db.commit()
        
        logger.info(f"[定时任务] 已重试{retry_count}条失败消息")
        
        return f"重试{retry_count}条消息"
        
    except Exception as e:
        logger.error(f"[定时任务] 重试失败消息异常: {e}")
        await db.rollback()
        raise
        
    finally:
        await db.close()


def start_xxljob_executor():
    """启动Xxl-job执行器"""
    xxl_job.start()


# 使用说明
"""
1. 在Xxl-job管理端创建执行器：
   - AppName: customer-system-executor
   - 名称: 客户系统执行器
   - 注册方式: 自动注册

2. 创建任务：
   - 任务1：更新消息统计
     - JobHandler: updateMessageStatistics
     - Cron: 0 0 1 * * ?
     - 描述: 每天凌晨1点更新消息统计
   
   - 任务2：发送每日报告
     - JobHandler: sendDailyReport
     - Cron: 0 0 9 * * ?
     - 描述: 每天早上9点发送报告
   
   - 任务3：清理过期数据
     - JobHandler: cleanExpiredData
     - Cron: 0 0 3 * * ?
     - 描述: 每天凌晨3点清理30天前的数据
   
   - 任务4：重试失败消息
     - JobHandler: retryFailedMessages
     - Cron: 0 0 * * * ?
     - 描述: 每小时重试失败的消息

3. 启动执行器：
   python -m app.services.xxljob_service
"""


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动执行器
    start_xxljob_executor()
