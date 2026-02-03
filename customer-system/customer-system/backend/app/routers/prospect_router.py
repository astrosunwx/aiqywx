"""
商机管理和客户身份管理API路由
处理商机收集、身份转换、权限检查
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.prospect_service import ProspectService, CustomerTypeService
from app.services.multi_contact_permission import MultiContactPermissionService
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class InquiryCreateRequest(BaseModel):
    """创建商机咨询请求"""
    phone: Optional[str] = None
    name: Optional[str] = None
    inquiry_content: str
    product_interest: Optional[str] = None
    source: str = 'wechat'
    source_openid: Optional[str] = None


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    customer_phone: str
    permission_type: str  # 'query_project' 或 'submit_aftersales'


@router.post("/api/prospect/inquiry")
async def create_inquiry(
    request: InquiryCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建商机咨询记录
    
    流程：
    1. API自动询问：请问怎么称呼您？您的电话是多少？
    2. 记录咨询信息
    3. 自动分配销售顾问
    4. 推送通知给销售顾问
    """
    result = await ProspectService.collect_inquiry(
        db,
        phone=request.phone,
        name=request.name,
        inquiry_content=request.inquiry_content,
        source=request.source,
        source_openid=request.source_openid,
        product_interest=request.product_interest
    )
    
    if not result['success']:
        if result.get('need_phone'):
            # 引导用户提供手机号
            return {
                'success': False,
                'message': result['message'],
                'need_input': 'phone',
                'prompt': '请提供您的手机号，方便我们的销售顾问联系您'
            }
        raise HTTPException(status_code=400, detail=result['message'])
    
    # 检查是否需要补充信息
    response = {
        'success': True,
        'message': result['message'],
        'inquiry_no': result['inquiry_no']
    }
    
    if result.get('need_name'):
        response['need_input'] = 'name'
        response['prompt'] = '请问怎么称呼您？'
    
    return response


@router.post("/api/customer/permission/check")
async def check_permission(
    request: PermissionCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    检查客户权限
    
    Args:
        customer_phone: 客户手机号
        permission_type: 权限类型
            - query_project: 查询项目权限
            - submit_aftersales: 提交售后权限
    
    Returns:
        权限检查结果
    """
    result = await CustomerTypeService.check_customer_permission(
        db,
        customer_phone=request.customer_phone,
        permission_type=request.permission_type
    )
    
    return result


@router.get("/api/customer/{phone}/type")
async def get_customer_type(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询客户类型和状态
    
    Returns:
        客户类型信息：
        - prospect: 商机用户（只询价，未成交）
        - customer: 正式客户（有订单）
        - cancelled: 取消客户（订单已取消）
    """
    from sqlalchemy import select
    from app.models import Customer
    
    result = await db.execute(
        select(Customer).where(Customer.phone == phone)
    )
    customer = result.scalar_one_or_null()
    
    if not customer:
        return {
            'exists': False,
            'message': '客户不存在'
        }
    
    return {
        'exists': True,
        'customer_type': customer.customer_type,
        'is_verified': customer.is_verified,
        'has_active_order': customer.has_active_order,
        'binding_status': customer.binding_status,
        'permissions': {
            'can_query_projects': customer.customer_type == 'customer' and customer.has_active_order,
            'can_submit_aftersales': (
                customer.customer_type == 'customer' 
                and customer.has_active_order 
                and customer.is_verified
            )
        },
        'created_at': customer.created_at.isoformat() if customer.created_at else None,
        'first_order_at': customer.first_order_at.isoformat() if customer.first_order_at else None
    }


@router.get("/api/customer/{phone}/projects")
async def get_customer_projects(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询客户的项目列表（支持多联系人）
    
    权限规则：
    1. 主客户（customer_id匹配）→ 返回所有自己的项目
    2. 额外联系人（在项目additional_contacts中）→ 返回有权限的项目
    3. 商机/取消客户 → 不直接拒绝，走服务请求流程
    
    使用MultiContactPermissionService.get_accessible_projects()
    自动查询：主客户项目 + 额外联系人项目
    """
    # 检查基础权限
    permission_check = await CustomerTypeService.check_customer_permission(
        db, phone, 'query_project'
    )
    
    if not permission_check['has_permission']:
        # 不是正式客户或无订单 → 不直接拒绝
        # 返回提示：请通过服务请求联系销售
        return {
            'success': False,
            'can_query_directly': False,
            'reason': permission_check['reason'],
            'message': permission_check['message'],
            'suggestion': '您可以提交服务请求，我们的销售顾问会帮您查询项目信息',
            'action': 'create_service_request'
        }
    
    # 有权限，获取可访问的所有项目（主客户 + 额外联系人）
    projects = await MultiContactPermissionService.get_accessible_projects(
        db, phone
    )
    
    return {
        'success': True,
        'customer_type': permission_check['customer_type'],
        'total_projects': len(projects),
        'projects': [
            {
                'id': p.id,
                'title': p.title,
                'status': p.status,
                'amount': str(p.amount) if p.amount else None,
                'progress': p.progress,
                'assigned_to_name': p.assigned_to_name,
                'created_at': p.created_at.isoformat() if p.created_at else None
            }
            for p in projects
        ],
        'count': len(projects)
    }


@router.post("/api/wechat/message/inquiry")
async def handle_inquiry_message(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    处理公众号商机咨询消息
    
    自动对话流程：
    1. 客户：我想了解XX产品
    2. 系统：请问怎么称呼您？
    3. 客户：张三
    4. 系统：您的电话是多少？
    5. 客户：13800138000
    6. 系统：已记录，我们的销售顾问会联系您
    """
    msg_type = request.get('MsgType')


# ============================================================================
# 多联系人项目权限管理API
# ============================================================================

class AddContactRequest(BaseModel):
    """添加项目联系人请求"""
    project_id: int
    phone: str
    name: str
    role: str = '联系人'


class RemoveContactRequest(BaseModel):
    """移除项目联系人请求"""
    project_id: int
    phone: str


class CheckProjectAccessRequest(BaseModel):
    """检查项目访问权限请求"""
    customer_phone: str
    project_id: int


@router.post("/api/project/contact/add")
async def add_project_contact(
    request: AddContactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    为项目添加额外联系人
    
    场景：
    - 企业项目有多个对接人（技术负责人、采购负责人等）
    - 添加后，该联系人可以查询和提交该项目的售后
    
    示例：
    {
      "project_id": 123,
      "phone": "13900139000",
      "name": "李四",
      "role": "技术负责人"
    }
    """
    result = await MultiContactPermissionService.add_project_contact(
        db=db,
        project_id=request.project_id,
        phone=request.phone,
        name=request.name,
        role=request.role
    )
    
    return result


@router.post("/api/project/contact/remove")
async def remove_project_contact(
    request: RemoveContactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    移除项目额外联系人
    
    移除后，该联系人将无法查询此项目
    """
    result = await MultiContactPermissionService.remove_project_contact(
        db=db,
        project_id=request.project_id,
        phone=request.phone
    )
    
    return result


@router.post("/api/project/access/check")
async def check_project_access(
    request: CheckProjectAccessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    检查客户是否有权限访问指定项目
    
    返回：
    - has_access: true/false
    - access_type: primary_customer（主客户）/ additional_contact（额外联系人）
    - reason: 无权限原因
    - message: 友好提示
    
    用于：
    - 微信公众号/企业微信查询项目前的权限验证
    - 售后工单提交前的权限验证
    """
    result = await MultiContactPermissionService.check_project_access(
        db=db,
        customer_phone=request.customer_phone,
        project_id=request.project_id
    )
    
    if not result['has_access']:
        # 无权限，但不直接拒绝，返回建议
        result['suggestion'] = '您可以提交服务请求，我们的销售顾问会帮您处理'
        result['action'] = 'create_service_request'
    
    return result


@router.get("/api/project/{project_id}/contacts")
async def get_project_contacts(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目的所有联系人
    
    返回：
    - 主客户信息
    - 额外联系人列表
    """
    from sqlalchemy import select
    from app.models import Project, Customer
    
    # 查询项目
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_null()
    
    if not project:
        raise HTTPException(status_code=404, detail='项目不存在')
    
    # 查询主客户
    primary_customer = None
    if project.customer_id:
        result = await db.execute(
            select(Customer).where(Customer.id == project.customer_id)
        )
        customer = result.scalar_one_or_null()
        if customer:
            primary_customer = {
                'phone': customer.phone,
                'name': customer.name,
                'role': '主客户',
                'type': 'primary'
            }
    
    # 额外联系人
    additional_contacts = project.additional_contacts or []
    
    return {
        'project_id': project_id,
        'project_title': project.title,
        'primary_customer': primary_customer,
        'additional_contacts': [
            {
                'phone': contact.get('phone'),
                'name': contact.get('name'),
                'role': contact.get('role'),
                'type': 'additional'
            }
            for contact in additional_contacts
        ],
        'total_contacts': 1 + len(additional_contacts) if primary_customer else len(additional_contacts)
    }


# 保留原有的消息处理
@router.post("/api/wechat/message/inquiry/original")
async def handle_inquiry_message_original(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    处理公众号商机咨询消息（原有实现）
    """
    msg_type = request.get('MsgType')
    content = request.get('Content', '')
    from_user = request.get('FromUserName')  # OpenID
    
    # 检测商机关键词
    inquiry_keywords = ['了解', '咨询', '询价', '价格', '多少钱', '购买', '产品']
    
    if msg_type == 'text' and any(kw in content for kw in inquiry_keywords):
        # 检查用户是否已经是客户
        from sqlalchemy import select
        from app.models import Customer
        
        result = await db.execute(
            select(Customer).where(Customer.wechat_openid == from_user)
        )
        customer = result.scalar_one_or_null()
        
        if customer and customer.customer_type == 'customer':
            # 已经是正式客户，直接提供服务
            return {
                'success': True,
                'reply_type': 'text',
                'reply_content': '欢迎回来！请问有什么可以帮您？\n发送"项目"查询订单，发送"售后"提交工单'
            }
        
        # 商机用户，引导收集信息
        return {
            'success': True,
            'reply_type': 'text',
            'reply_content': '您好！感谢您的咨询。\n为了更好地为您服务，请问怎么称呼您？'
        }
    
    return {
        'success': True,
        'reply_type': 'text',
        'reply_content': '如需咨询产品，请直接描述您的需求'
    }
