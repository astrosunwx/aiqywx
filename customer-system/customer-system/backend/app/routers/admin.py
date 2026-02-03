from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SystemConfig, Project
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    config_key: str
    config_value: str

@router.get("/api/admin/config")
async def get_system_config(db: AsyncSession = Depends(get_db)):
    """
    获取系统配置
    """
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    return {
        "configs": [
            {
                "key": config.config_key,
                "value": config.config_value,
                "description": config.description
            }
            for config in configs
        ]
    }


@router.post("/api/admin/config")
async def update_system_config(request: ConfigUpdateRequest, db: AsyncSession = Depends(get_db)):
    """
    更新系统配置
    """
    if not request.config_key or not request.config_value:
        raise HTTPException(status_code=400, detail="配置键值不能为空")

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == request.config_key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.config_value = request.config_value
    else:
        config = SystemConfig(
            config_key=request.config_key,
            config_value=request.config_value
        )
        db.add(config)
    
    await db.commit()
    await db.refresh(config)
    
    return {
        "status": "success",
        "config_key": config.config_key,
        "config_value": config.config_value
    }


@router.get("/api/admin/reports/sales")
async def get_sales_report(db: AsyncSession = Depends(get_db)):
    """
    获取销售报表
    包含两个入口的客户来源分析
    """
    # TODO: 实现真实的报表查询逻辑
    # 示例数据
    return {
        "total_projects": 150,
        "by_source": {
            "wechat_official": 80,  # 公众号来源
            "wechat_work": 70       # 企业微信来源
        },
        "by_type": {
            "presale": 60,
            "installation": 50,
            "aftersale": 40
        },
        "by_status": {
            "pending": 20,
            "contacted": 30,
            "processing": 40,
            "completed": 50,
            "cancelled": 10
        }
    }


@router.get("/api/projects")
async def get_projects(
    phone: str = None,
    employee_id: int = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    根据条件查询项目
    权限控制：仅本人和绑定员工可见
    """
    query = select(Project)
    
    if phone:
        query = query.where(Project.customer_phone == phone)
    
    if employee_id:
        query = query.where(
            (Project.sales_id == employee_id) | (Project.engineer_id == employee_id)
        )
    
    if status:
        query = query.where(Project.status == status)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return {
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "type": p.project_type,
                "status": p.status,
                "customer_phone": p.customer_phone,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in projects
        ]
    }


@router.get("/api/daily-report")
async def get_daily_report(db: AsyncSession = Depends(get_db)):
    """
    获取每日售后简报
    """
    from app.services.daily_report import DailyReportService
    
    report = await DailyReportService.generate_daily_report(db)
    return report


@router.post("/api/daily-report/send")
async def send_daily_report(db: AsyncSession = Depends(get_db)):
    """
    发送每日简报到企业微信群
    """
    from app.services.daily_report import DailyReportService
    
    result = await DailyReportService.send_daily_report_to_group(db)
    return result


@router.get("/api/sync/tickets")
async def get_tickets_for_sync(
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    外部CRM系统拉取工单数据（Pull模式）
    供客户关怀系统定时调用
    """
    from app.services.sync_service import SyncService
    from datetime import datetime
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    tickets = await SyncService.get_tickets_for_external_pull(db, start, end)
    return {"tickets": tickets, "count": len(tickets)}
