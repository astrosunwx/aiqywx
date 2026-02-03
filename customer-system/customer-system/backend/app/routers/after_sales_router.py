"""
售后服务API路由
支持客户提交售后工单、订单修改请求，并自动推送给员工
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.after_sales_service import AfterSalesService, OrderModificationService
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class TicketCreateRequest(BaseModel):
    """创建工单请求"""
    customer_phone: str
    ticket_type: str  # maintenance/repair/complaint/consultation/return/refund
    subject: str
    description: str
    source: str = 'wechat'
    source_openid: Optional[str] = None
    attachments: Optional[List[str]] = None


class TicketUpdateRequest(BaseModel):
    """更新工单请求"""
    status: str  # processing/resolved/closed
    operator_userid: str
    response_content: Optional[str] = None
    resolution: Optional[str] = None


class ModificationCreateRequest(BaseModel):
    """创建订单修改请求"""
    customer_phone: str
    project_id: int
    modification_type: str  # modify/cancel/refund
    modification_content: Dict
    reason: str
    source: str = 'wechat'


@router.post("/api/after-sales/ticket")
async def create_ticket(
    request: TicketCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建售后工单
    
    客户在公众号或企业微信提交售后请求
    系统自动：
    1. 验证客户身份（is_verified=True）
    2. 匹配客户项目
    3. 分配给负责人
    4. 推送通知到企业微信
    """
    result = await AfterSalesService.create_ticket(
        db,
        customer_phone=request.customer_phone,
        ticket_type=request.ticket_type,
        subject=request.subject,
        description=request.description,
        source=request.source,
        source_openid=request.source_openid,
        attachments=request.attachments
    )
    
    if not result['success']:
        if result.get('need_verification'):
            raise HTTPException(
                status_code=403,
                detail=result['message']
            )
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.get("/api/after-sales/tickets/{phone}")
async def get_customer_tickets(
    phone: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    查询客户的售后工单
    
    Args:
        phone: 客户手机号
        status: 状态筛选（可选）
    """
    tickets = await AfterSalesService.get_customer_tickets(
        db, phone, status
    )
    
    return {
        'success': True,
        'tickets': tickets,
        'count': len(tickets)
    }


@router.put("/api/after-sales/ticket/{ticket_no}")
async def update_ticket(
    ticket_no: str,
    request: TicketUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新工单状态
    
    员工处理工单后调用此接口
    """
    result = await AfterSalesService.update_ticket_status(
        db,
        ticket_no=ticket_no,
        status=request.status,
        operator_userid=request.operator_userid,
        response_content=request.response_content,
        resolution=request.resolution
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/api/order/modification")
async def create_modification(
    request: ModificationCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建订单修改/退订请求
    
    客户提交订单修改、取消或退款申请
    系统自动：
    1. 验证客户身份和项目归属
    2. 创建变更记录
    3. 推送审核通知给负责人
    """
    result = await OrderModificationService.create_modification(
        db,
        customer_phone=request.customer_phone,
        project_id=request.project_id,
        modification_type=request.modification_type,
        modification_content=request.modification_content,
        reason=request.reason,
        source=request.source
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/api/wechat/message/aftersales")
async def handle_wechat_aftersales_message(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    处理公众号售后消息
    
    当客户在公众号发送特定关键词时，引导创建工单
    """
    data = await request.json()
    
    msg_type = data.get('MsgType')
    content = data.get('Content', '')
    from_user = data.get('FromUserName')  # OpenID
    
    # 检测售后关键词
    after_sales_keywords = ['售后', '维修', '保养', '投诉', '退货', '退款']
    
    if msg_type == 'text' and any(keyword in content for keyword in after_sales_keywords):
        # 引导客户创建工单
        return {
            'success': True,
            'reply_type': 'text',
            'reply_content': """
您好！请选择您需要的售后服务：

1️⃣ 设备保养
2️⃣ 维修服务
3️⃣ 投诉建议
4️⃣ 退货申请
5️⃣ 退款申请
6️⃣ 咨询服务

请回复数字选择服务类型
            """.strip()
        }
    
    # 处理数字选择
    if msg_type == 'text' and content in ['1', '2', '3', '4', '5', '6']:
        type_map = {
            '1': 'maintenance',
            '2': 'repair',
            '3': 'complaint',
            '4': 'return',
            '5': 'refund',
            '6': 'consultation'
        }
        
        # 这里可以保存用户选择的类型到会话状态
        # 然后引导用户输入详细描述
        
        return {
            'success': True,
            'reply_type': 'text',
            'reply_content': '请详细描述您的问题，我们会尽快为您处理'
        }
    
    return {
        'success': True,
        'reply_type': 'text',
        'reply_content': '如需售后服务，请发送"售后"'
    }


@router.get("/api/project/{token}")
async def get_project_by_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    通过token获取项目详情
    
    员工点击企业微信消息中的项目链接时访问此接口
    无需登录，直接通过token查看
    
    Args:
        token: 项目链接token (project_link_token)
    
    Returns:
        项目详细信息
    """
    from sqlalchemy import select
    from app.models import Project, Customer, AfterSalesTicket
    
    # 查找项目
    result = await db.execute(
        select(Project).where(Project.project_link_token == token)
    )
    project = result.scalar_one_or_null()
    
    if not project:
        raise HTTPException(status_code=404, detail='项目不存在或链接已失效')
    
    # 查找客户信息
    result = await db.execute(
        select(Customer).where(Customer.id == project.customer_id)
    )
    customer = result.scalar_one_or_null()
    
    # 查找相关售后工单
    result = await db.execute(
        select(AfterSalesTicket)
        .where(AfterSalesTicket.project_id == project.id)
        .order_by(AfterSalesTicket.created_at.desc())
    )
    tickets = result.scalars().all()
    
    return {
        'success': True,
        'project': {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'status': project.status,
            'amount': str(project.amount) if project.amount else None,
            'progress': project.progress,
            'assigned_to_name': project.assigned_to_name,
            'created_at': project.created_at.isoformat() if project.created_at else None
        },
        'customer': {
            'name': customer.name if customer else None,
            'phone': customer.phone if customer else None,
            'company': customer.company if customer else None
        },
        'tickets': [
            {
                'ticket_no': t.ticket_no,
                'ticket_type': t.ticket_type,
                'subject': t.subject,
                'status': t.status,
                'priority': t.priority,
                'created_at': t.created_at.isoformat() if t.created_at else None
            }
            for t in tickets
        ]
    }
