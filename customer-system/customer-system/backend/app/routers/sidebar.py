"""
聊天工具栏侧边栏路由
员工在客户聊天界面点击侧边栏，一键发送项目进度
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Project, Customer, WeChatSession
from ..services.customer_contact_service import CustomerContactService
from ..services.secure_link_service import SecureLinkService
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/sidebar", tags=["聊天工具栏侧边栏"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/project-selector", response_class=HTMLResponse)
async def show_project_selector(
    request: Request,
    userid: str = Query(..., description="员工UserID"),
    external_userid: str = Query(..., description="客户external_userid"),
    db: AsyncSession = Depends(get_db)
):
    """
    展示项目选择器侧边栏页面
    
    员工在与客户聊天时，点击工具栏，显示该客户关联的所有项目
    员工选择项目后，点击"发送进度"按钮
    
    企业微信会自动传入：
    - userid: 当前员工的UserID
    - external_userid: 当前客户的external_userid
    """
    
    # 1. 查询该客户关联的所有项目
    stmt = select(Customer).where(Customer.wechat_openid == external_userid)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    
    projects = []
    customer_name = "客户"
    
    if customer:
        customer_name = customer.name
        # 查询客户的所有项目
        stmt = select(Project).where(Project.customer_id == customer.id)
        result = await db.execute(stmt)
        projects = result.scalars().all()
    
    # 2. 渲染侧边栏页面
    return templates.TemplateResponse(
        "sidebar_project_selector.html",
        {
            "request": request,
            "userid": userid,
            "external_userid": external_userid,
            "customer_name": customer_name,
            "projects": projects
        }
    )


@router.post("/send-progress")
async def send_project_progress(
    project_id: int,
    userid: str,
    external_userid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    发送项目进度给客户
    
    由侧边栏页面的"发送进度"按钮触发
    
    Args:
        project_id: 选中的项目ID
        userid: 员工UserID
        external_userid: 客户external_userid
    
    Returns:
        发送结果
    """
    
    try:
        result = await CustomerContactService.send_progress_to_customer(
            db=db,
            project_id=project_id,
            customer_external_userid=external_userid,
            sender_userid=userid
        )
        
        return {
            "success": True,
            "message": "项目进度已发送给客户",
            "secure_link": result.get('secure_link')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送失败：{str(e)}")


@router.get("/preview-message")
async def preview_progress_message(
    project_id: int,
    external_userid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    预览将要发送给客户的消息内容
    
    在员工点击"发送"前，先预览消息效果
    """
    
    # 查询项目
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 查询客户
    customer = None
    if project.customer_id:
        stmt = select(Customer).where(Customer.id == project.customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
    
    # 生成预览链接
    secure_link = SecureLinkService.generate_project_detail_link(
        user_id=external_userid,
        project_id=project_id,
        wechat_user_id=external_userid,
        expiry_hours=1
    )
    
    # 构建消息内容
    message_content = await CustomerContactService._build_progress_message(
        project=project,
        customer=customer,
        secure_link=secure_link
    )
    
    return {
        "project_id": project_id,
        "project_title": project.title,
        "progress": project.progress,
        "message_preview": message_content.get('link', {}).get('desc'),
        "secure_link": secure_link
    }
