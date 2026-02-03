"""
客户服务请求路由
统一处理所有客户的服务请求（查询/更改/取消订单、售后）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.customer_service_request import CustomerServiceRequestService
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceRequestCreate(BaseModel):
    """服务请求创建"""
    customer_phone: str
    customer_name: Optional[str] = None
    request_type: str  # query_order, modify_order, cancel_order, aftersales, inquiry
    request_content: str
    source: str = 'wechat'
    source_openid: Optional[str] = None


class WeChatServiceMessage(BaseModel):
    """微信服务消息"""
    message: str
    openid: str
    phone: Optional[str] = None
    name: Optional[str] = None
    request_type: Optional[str] = None


@router.post("/api/service/request/create")
async def create_service_request(
    request: ServiceRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建客户服务请求（不拒绝任何客户）
    
    支持的请求类型：
    - query_order: 查询订单
    - modify_order: 更改订单
    - cancel_order: 取消订单
    - aftersales: 售后服务
    - inquiry: 咨询
    
    不论客户身份如何（商机/正式/取消/不存在），都会记录请求
    如果需要验证，会推送通知给销售顾问："请先搜索手机号添加客户"
    """
    result = await CustomerServiceRequestService.create_service_request(
        db=db,
        customer_phone=request.customer_phone,
        customer_name=request.customer_name,
        request_type=request.request_type,
        request_content=request.request_content,
        source=request.source,
        source_openid=request.source_openid
    )
    
    return result


@router.post("/api/wechat/message/service")
async def handle_wechat_service_message(
    message: WeChatServiceMessage,
    db: AsyncSession = Depends(get_db)
):
    """
    处理微信服务消息（分步收集）
    
    对话流程：
    1. 请问怎么称呼您？
    2. 您的电话是多少？
    3. 您要查询订单？还是更改？取消订单？还是售后？
    4. 请简单描述您的需求
    5. 已记录，将帮您转给该项目对应的专员进行处理，请保持电话畅通
    """
    result = await CustomerServiceRequestService.collect_request_info_step_by_step(
        db=db,
        message=message.message,
        phone=message.phone,
        name=message.name,
        request_type=message.request_type,
        source_openid=message.openid
    )
    
    return result


@router.get("/api/service/request/{request_no}")
async def get_service_request(
    request_no: str,
    db: AsyncSession = Depends(get_db)
):
    """查询服务请求详情"""
    from sqlalchemy import select
    from app.models import CustomerServiceRequest
    
    result = await db.execute(
        select(CustomerServiceRequest).where(
            CustomerServiceRequest.request_no == request_no
        )
    )
    service_request = result.scalar_one_or_null()
    
    if not service_request:
        raise HTTPException(status_code=404, detail='服务请求不存在')
    
    return {
        'request_no': service_request.request_no,
        'customer_phone': service_request.customer_phone,
        'customer_name': service_request.customer_name,
        'customer_type': service_request.customer_type,
        'request_type': service_request.request_type,
        'request_content': service_request.request_content,
        'urgency': service_request.urgency,
        'status': service_request.status,
        'needs_verification': service_request.needs_verification,
        'verification_note': service_request.verification_note,
        'assigned_to_name': service_request.assigned_to_name,
        'created_at': service_request.created_at.isoformat() if service_request.created_at else None
    }


@router.get("/api/service/request/phone/{phone}")
async def get_service_requests_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """查询客户的所有服务请求"""
    from sqlalchemy import select
    from app.models import CustomerServiceRequest
    
    result = await db.execute(
        select(CustomerServiceRequest)
        .where(CustomerServiceRequest.customer_phone == phone)
        .order_by(CustomerServiceRequest.created_at.desc())
        .limit(10)
    )
    requests = result.scalars().all()
    
    return {
        'phone': phone,
        'total': len(requests),
        'requests': [
            {
                'request_no': req.request_no,
                'request_type': req.request_type,
                'urgency': req.urgency,
                'status': req.status,
                'needs_verification': req.needs_verification,
                'created_at': req.created_at.isoformat() if req.created_at else None
            }
            for req in requests
        ]
    }
