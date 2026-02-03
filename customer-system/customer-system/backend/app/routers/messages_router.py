"""
消息处理API路由
支持消息模板、批量发送、链路追踪、统计分析
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta
import redis
import uuid

from app.database import get_db, redis_client
from app.models_messaging import (
    MessageTemplate, MessageTask, MessageRecord, MessageTrace,
    MessageStatistics, MessageChannel, MessageStatus
)
from app.services.thread_pool_service import ThreadPoolManager
from app.services.message_trace_service import MessageTracer
from app.services.rabbitmq_service import RabbitMQService, MessageQueue
from app.services.redis_lock_service import distributed_lock
from app.services.sentinel_service import rate_limit

router = APIRouter(prefix="/api/messages", tags=["消息处理"])

# 初始化服务
thread_pool_manager = ThreadPoolManager()

# RabbitMQ 和消息队列（可选，仅在 RabbitMQ 可用时启用）
try:
    rabbitmq_service = RabbitMQService(
        host="localhost",
        port=5672,
        username="guest",
        password="guest"
    )
    message_queue = MessageQueue(rabbitmq_service) if rabbitmq_service.channel else None
except Exception as e:
    print(f"⚠️  RabbitMQ连接失败，消息队列功能不可用: {e}")
    rabbitmq_service = None
    message_queue = None


# ==================== 消息模板管理 ====================

@router.get("/templates", summary="获取消息模板列表")
async def get_templates(
    channel: Optional[str] = None,
    status: Optional[str] = "active",
    db: AsyncSession = Depends(get_db)
):
    """获取消息模板列表"""
    query = select(MessageTemplate)
    
    filters = []
    if channel:
        filters.append(MessageTemplate.channel == channel)
    if status:
        filters.append(MessageTemplate.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    result = await db.execute(query.order_by(MessageTemplate.created_at.desc()))
    templates = result.scalars().all()
    
    return {
        "code": 0,
        "data": [
            {
                "id": t.id,
                "name": t.name,
                "channel": t.channel,
                "subject": t.subject,
                "content": t.content,
                "variables": t.variables,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in templates
        ]
    }


@router.post("/templates", summary="创建消息模板")
async def create_template(
    name: str,
    channel: str,
    subject: str,
    content: str,
    variables: Optional[dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """创建消息模板"""
    template = MessageTemplate(
        name=name,
        channel=channel,
        subject=subject,
        content=content,
        variables=variables or []
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return {
        "code": 0,
        "message": "模板创建成功",
        "data": {"id": template.id}
    }


# ==================== 消息发送 ====================

@router.post("/send", summary="发送单条消息")
@rate_limit(resource="api:/messages/send", max_qps=1000)
async def send_message(
    template_id: int,
    recipient: str,
    variables: Optional[dict] = None,
    priority: int = 5,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """发送单条消息"""
    # 查询模板
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template.status != "active":
        raise HTTPException(status_code=400, detail="模板未激活")
    
    # 创建链路追踪（如果 Redis 可用）
    trace_id = str(uuid.uuid4())
    if redis_client:
        try:
            tracer = MessageTracer(redis_client)
            trace_id = tracer.start_trace({
                "template_id": template_id,
                "recipient": recipient,
                "channel": template.channel
            })
        except Exception as e:
            print(f"Redis追踪失败: {e}")
    
    # 创建消息记录
    record = MessageRecord(
        trace_id=trace_id,
        template_id=template_id,
        recipient=recipient,
        channel=template.channel,
        subject=template.subject,
        content=_render_template(template.content, variables or {}),
        variables=variables,
        priority=priority
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    # 添加追踪节点（如果 Redis 可用）
    if redis_client:
        try:
            tracer.add_node(trace_id, "queue", {"record_id": record.id})
        except Exception:
            pass
    
    # 发送到消息队列
    rabbitmq_service.publish_message(
        queue=message_queue.QUEUE_MESSAGE_SEND,
        message={
            "record_id": record.id,
            "trace_id": trace_id,
            "template_id": template_id,
            "recipient": recipient,
            "channel": template.channel,
            "content": record.content,
            "priority": priority
        },
        priority=priority
    )
    
    tracer.finish_node(trace_id, "queue", {"status": "success"})
    
    return {
        "code": 0,
        "message": "消息已加入发送队列",
        "data": {
            "record_id": record.id,
            "trace_id": trace_id
        }
    }


@router.post("/send-batch", summary="批量发送消息")
@rate_limit(resource="api:/messages/send-batch", max_qps=100)
async def send_batch_messages(
    template_id: int,
    recipients: List[str],
    variables_list: Optional[List[dict]] = None,
    priority: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """批量发送消息"""
    # 查询模板
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 创建批量任务
    task = MessageTask(
        template_id=template_id,
        total_count=len(recipients),
        channel=template.channel
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 批量创建消息记录
    for i, recipient in enumerate(recipients):
        variables = variables_list[i] if variables_list and i < len(variables_list) else {}
        
        # 创建链路追踪（如果 Redis 可用）
        trace_id = str(uuid.uuid4())
        if redis_client:
            try:
                tracer = MessageTracer(redis_client)
                trace_id = tracer.start_trace({
                    "task_id": task.id,
                    "template_id": template_id,
                    "recipient": recipient
                })
            except Exception:
                pass
        
        # 创建记录
        record = MessageRecord(
            trace_id=trace_id,
            task_id=task.id,
            template_id=template_id,
            recipient=recipient,
            channel=template.channel,
            subject=template.subject,
            content=_render_template(template.content, variables),
            variables=variables,
            priority=priority
        )
        
        db.add(record)
        
        # 每100条提交一次
        if (i + 1) % 100 == 0:
            await db.commit()
        
        await db.commit()
    
    # 发送到队列
    rabbitmq_service.publish_message(
        queue=message_queue.QUEUE_MESSAGE_SEND,
        message={
            "type": "batch",
            "task_id": task.id,
            "template_id": template_id,
            "priority": priority
        },
        priority=priority
    )
    
    return {
        "code": 0,
        "message": f"批量任务已创建，共{len(recipients)}条消息",
        "data": {"task_id": task.id}
    }


# ==================== 消息追踪 ====================

@router.get("/traces/{trace_id}", summary="获取消息链路追踪")
async def get_message_trace(trace_id: str):
    """获取消息链路追踪详情"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis服务不可用，链路追踪功能暂时不可用")
    
    try:
        tracer = MessageTracer(redis_client)
        trace_data = tracer.get_trace(trace_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取追踪信息失败: {str(e)}")
    
    if not trace_data:
        raise HTTPException(status_code=404, detail="追踪记录不存在")
    
    # 获取统计信息
    stats = tracer.get_statistics(trace_id)
    
    return {
        "code": 0,
        "data": {
            "trace_id": trace_id,
            "trace_data": trace_data,
            "statistics": stats
        }
    }


@router.get("/tasks/{task_id}", summary="获取批量任务详情")
async def get_task_detail(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取批量任务详情"""
    # 查询任务
    result = await db.execute(
        select(MessageTask).where(MessageTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 查询消息记录统计
    stats_result = await db.execute(
        select(
            MessageRecord.status,
            func.count(MessageRecord.id).label("count")
        ).where(
            MessageRecord.task_id == task_id
        ).group_by(MessageRecord.status)
    )
    
    status_stats = {row.status: row.count for row in stats_result}
    
    return {
        "code": 0,
        "data": {
            "id": task.id,
            "template_id": task.template_id,
            "total_count": task.total_count,
            "success_count": task.success_count,
            "failed_count": task.failed_count,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "status_breakdown": status_stats
        }
    }


# ==================== 统计分析 ====================

@router.get("/statistics/overview", summary="获取消息统计概览")
async def get_statistics_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取消息统计概览"""
    # 默认查询最近7天
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 查询统计数据
    result = await db.execute(
        select(MessageStatistics).where(
            and_(
                MessageStatistics.stat_date >= start_date,
                MessageStatistics.stat_date <= end_date
            )
        ).order_by(MessageStatistics.stat_date)
    )
    
    stats = result.scalars().all()
    
    # 汇总数据
    total_sent = sum(s.total_sent for s in stats)
    total_success = sum(s.success_count for s in stats)
    total_failed = sum(s.failed_count for s in stats)
    
    success_rate = (total_success / total_sent * 100) if total_sent > 0 else 0
    
    # 按渠道统计
    channel_stats = {}
    for stat in stats:
        if stat.channel not in channel_stats:
            channel_stats[stat.channel] = {
                "sent": 0,
                "success": 0,
                "failed": 0
            }
        channel_stats[stat.channel]["sent"] += stat.total_sent
        channel_stats[stat.channel]["success"] += stat.success_count
        channel_stats[stat.channel]["failed"] += stat.failed_count
    
    return {
        "code": 0,
        "data": {
            "overview": {
                "total_sent": total_sent,
                "total_success": total_success,
                "total_failed": total_failed,
                "success_rate": round(success_rate, 2),
                "avg_response_time": sum(s.avg_response_time for s in stats if s.avg_response_time) / len(stats) if stats else 0
            },
            "by_channel": channel_stats,
            "daily_stats": [
                {
                    "date": s.stat_date.isoformat(),
                    "channel": s.channel,
                    "sent": s.total_sent,
                    "success": s.success_count,
                    "failed": s.failed_count,
                    "avg_response_time": s.avg_response_time
                }
                for s in stats
            ]
        }
    }


@router.get("/statistics/realtime", summary="获取实时统计")
async def get_realtime_statistics(db: AsyncSession = Depends(get_db)):
    """获取实时统计（最近1小时）"""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    # 查询最近1小时的记录
    result = await db.execute(
        select(
            MessageRecord.status,
            MessageRecord.channel,
            func.count(MessageRecord.id).label("count"),
            func.avg(
                func.extract('epoch', MessageRecord.sent_at - MessageRecord.created_at)
            ).label("avg_duration")
        ).where(
            MessageRecord.created_at >= one_hour_ago
        ).group_by(
            MessageRecord.status,
            MessageRecord.channel
        )
    )
    
    stats = result.all()
    
    # 获取线程池状态
    pool_stats = thread_pool_manager.get_all_metrics()
    
    return {
        "code": 0,
        "data": {
            "message_stats": [
                {
                    "status": s.status,
                    "channel": s.channel,
                    "count": s.count,
                    "avg_duration_seconds": round(s.avg_duration, 2) if s.avg_duration else 0
                }
                for s in stats
            ],
            "thread_pool_stats": pool_stats,
            "timestamp": datetime.now().isoformat()
        }
    }


# ==================== 工具函数 ====================

def _render_template(template: str, variables: dict) -> str:
    """渲染消息模板"""
    content = template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    return content
