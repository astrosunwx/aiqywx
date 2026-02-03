"""
自动进度通知路由
用于定时或事件触发的自动通知
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Project, Customer
from ..services.customer_contact_service import CustomerContactService
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/auto-notify", tags=["自动通知"])


class MilestoneNotification(BaseModel):
    """里程碑通知请求"""
    project_id: int
    milestone: str
    customer_external_userid: str
    sender_userid: str


class BatchNotification(BaseModel):
    """批量通知请求"""
    project_ids: List[int]
    sender_userid: str


@router.post("/milestone")
async def notify_milestone(
    notification: MilestoneNotification,
    db: AsyncSession = Depends(get_db)
):
    """
    发送里程碑通知
    
    当项目到达重要节点时自动触发
    例如：需求确认、开发完成、测试通过、上线部署等
    
    使用场景：
    - 在项目管理系统中，当进度更新到特定阶段时调用此API
    - 由定时任务监测进度变化，自动通知客户
    """
    
    try:
        result = await CustomerContactService.auto_notify_on_milestone(
            db=db,
            project_id=notification.project_id,
            milestone=notification.milestone,
            customer_external_userid=notification.customer_external_userid,
            sender_userid=notification.sender_userid
        )
        
        return {
            "success": True,
            "message": f"里程碑通知已发送：{notification.milestone}",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"通知发送失败：{str(e)}")


@router.post("/batch-weekly")
async def batch_weekly_notification(
    notification: BatchNotification,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    批量发送周报
    
    用于每周五定时向所有进行中的项目客户发送进度更新
    
    使用场景：
    - 定时任务（cron）每周五17:00执行
    - 选择所有status='processing'的项目
    - 批量发送进度通知，减少客户咨询
    
    示例：
    ```bash
    # 每周五17:00执行
    curl -X POST http://localhost:8000/auto-notify/batch-weekly \
      -H "Content-Type: application/json" \
      -d '{"project_ids": [1,2,3], "sender_userid": "zhangsan"}'
    ```
    """
    
    # 添加到后台任务，避免阻塞
    background_tasks.add_task(
        _batch_send_task,
        db=db,
        project_ids=notification.project_ids,
        sender_userid=notification.sender_userid
    )
    
    return {
        "success": True,
        "message": f"已开始批量发送通知，共 {len(notification.project_ids)} 个项目",
        "project_count": len(notification.project_ids)
    }


async def _batch_send_task(
    db: AsyncSession,
    project_ids: List[int],
    sender_userid: str
):
    """后台任务：批量发送通知"""
    
    results = await CustomerContactService.batch_send_progress_updates(
        db=db,
        project_ids=project_ids,
        sender_userid=sender_userid
    )
    
    # 记录发送结果
    success_count = sum(1 for r in results if r.get('success'))
    print(f"✅ 批量通知完成：成功 {success_count}/{len(results)}")
    
    return results


@router.post("/progress-threshold")
async def notify_on_progress_threshold(
    project_id: int,
    threshold: int,
    sender_userid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    进度达到阈值时通知
    
    当项目进度达到特定百分比时自动通知客户
    
    Args:
        project_id: 项目ID
        threshold: 进度阈值（如：50, 80, 100）
        sender_userid: 发送者UserID
    
    使用场景：
    - 进度达到50%：通知客户"项目已完成一半"
    - 进度达到80%：通知客户"项目即将完成"
    - 进度达到100%：通知客户"项目已完成，请验收"
    """
    
    # 查询项目
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否达到阈值
    if project.progress < threshold:
        return {
            "success": False,
            "message": f"项目进度（{project.progress}%）尚未达到阈值（{threshold}%）"
        }
    
    # 查询客户
    if not project.customer_id:
        raise HTTPException(status_code=400, detail="项目未关联客户")
    
    stmt = select(Customer).where(Customer.id == project.customer_id)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    
    if not customer or not customer.wechat_openid:
        raise HTTPException(status_code=400, detail="客户无企业微信联系方式")
    
    # 根据阈值确定里程碑
    milestone_map = {
        25: "需求确认",
        50: "开发完成50%",
        75: "测试阶段",
        90: "即将完成",
        100: "验收通过"
    }
    
    milestone = milestone_map.get(threshold, f"进度达到{threshold}%")
    
    # 发送通知
    result = await CustomerContactService.auto_notify_on_milestone(
        db=db,
        project_id=project_id,
        milestone=milestone,
        customer_external_userid=customer.wechat_openid,
        sender_userid=sender_userid
    )
    
    return {
        "success": True,
        "message": f"已通知客户：{milestone}",
        "threshold": threshold,
        "current_progress": project.progress
    }


@router.get("/active-projects")
async def get_active_projects_for_notification(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有需要发送周报的活跃项目
    
    筛选条件：
    - status in ['processing', 'assigned']
    - customer_id 不为空
    - 客户有企业微信联系方式
    
    返回项目列表供批量通知使用
    """
    
    # 查询活跃项目
    stmt = select(Project).where(
        Project.status.in_(['processing', 'assigned']),
        Project.customer_id.isnot(None)
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()
    
    # 过滤出有企业微信联系方式的客户项目
    valid_projects = []
    
    for project in projects:
        stmt = select(Customer).where(Customer.id == project.customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if customer and customer.wechat_openid:
            valid_projects.append({
                "project_id": project.id,
                "project_title": project.title,
                "progress": project.progress,
                "customer_name": customer.name,
                "customer_external_userid": customer.wechat_openid
            })
    
    return {
        "total_count": len(valid_projects),
        "projects": valid_projects
    }
