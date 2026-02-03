"""
配置管理后台路由 - 极简配置界面
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models_config import (
    EnhancedSystemConfig, ConfigGroup, WorkflowTemplate, 
    RobotWebhook, AdminUser, Role, Permission, OperationLog
)
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets
from passlib.context import CryptContext

router = APIRouter(prefix="/api/admin/config-center", tags=["配置中心"])

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Pydantic 模型
# ============================================================================

class ConfigItem(BaseModel):
    """配置项"""
    id: Optional[int] = None
    config_key: str
    config_value: Optional[str] = None
    config_type: str = 'string'
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_required: bool = False
    is_sensitive: bool = False
    sort_order: int = 0


class ConfigGroupResponse(BaseModel):
    """配置分组响应"""
    id: int
    group_code: str
    group_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    configs: List[Dict[str, Any]] = []


class WebhookConfig(BaseModel):
    """Webhook配置"""
    id: Optional[int] = None
    webhook_name: str
    webhook_url: str
    webhook_type: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class WorkflowTemplateResponse(BaseModel):
    """业务流程模板响应"""
    id: int
    template_code: str
    template_name: str
    template_type: str
    description: Optional[str] = None
    is_default: bool
    is_active: bool


class BatchConfigUpdate(BaseModel):
    """批量配置更新"""
    configs: List[Dict[str, Any]]


class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    role_name: str
    role_display_name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_system: bool


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """创建用户"""
    username: str
    password: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    wework_userid: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户"""
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# ============================================================================
# 配置中心 - 极简配置界面
# ============================================================================

@router.get("/overview")
async def get_config_overview(db: AsyncSession = Depends(get_db)):
    """
    获取配置中心概览 - 所有配置按分组展示
    """
    # 获取所有配置分组
    groups_result = await db.execute(
        select(ConfigGroup).where(ConfigGroup.is_active == True).order_by(ConfigGroup.sort_order)
    )
    groups = groups_result.scalars().all()
    
    overview = []
    for group in groups:
        # 获取该分组下的所有配置
        configs_result = await db.execute(
            select(EnhancedSystemConfig)
            .where(EnhancedSystemConfig.group_id == group.id)
            .order_by(EnhancedSystemConfig.sort_order)
        )
        configs = configs_result.scalars().all()
        
        config_list = []
        for config in configs:
            config_data = {
                "id": config.id,
                "config_key": config.config_key,
                "config_value": config.config_value if not config.is_sensitive else "******",
                "config_type": config.config_type,
                "display_name": config.display_name,
                "description": config.description,
                "is_required": config.is_required,
                "is_sensitive": config.is_sensitive,
                "sort_order": config.sort_order
            }
            config_list.append(config_data)
        
        overview.append({
            "id": group.id,
            "group_code": group.group_code,
            "group_name": group.group_name,
            "description": group.description,
            "icon": group.icon,
            "configs": config_list
        })
    
    return {"groups": overview}


@router.post("/batch-update")
async def batch_update_configs(
    request: BatchConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    批量更新配置（极简配置的核心功能）
    """
    updated_count = 0
    errors = []
    
    for config_data in request.configs:
        try:
            config_key = config_data.get("config_key")
            config_value = config_data.get("config_value")
            
            if not config_key:
                continue
            
            # 查找配置项
            result = await db.execute(
                select(EnhancedSystemConfig).where(EnhancedSystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.config_value = str(config_value) if config_value is not None else None
                config.updated_at = func.now()
                updated_count += 1
            else:
                # 如果配置不存在，创建新配置
                new_config = EnhancedSystemConfig(
                    config_key=config_key,
                    config_value=str(config_value) if config_value is not None else None,
                    config_type=config_data.get("config_type", "string"),
                    display_name=config_data.get("display_name"),
                    description=config_data.get("description")
                )
                db.add(new_config)
                updated_count += 1
        
        except Exception as e:
            errors.append(f"配置 {config_key} 更新失败: {str(e)}")
    
    await db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "errors": errors if errors else None
    }


@router.get("/callback-url")
async def get_callback_url(request: Request):
    """
    自动生成回调URL（根据当前请求域名）
    """
    base_url = str(request.base_url).rstrip('/')
    callback_url = f"{base_url}/api/wechat/callback"
    
    return {
        "callback_url": callback_url,
        "description": "将此URL配置到企业微信应用的接收消息服务器URL"
    }


# ============================================================================
# 群机器人配置
# ============================================================================

@router.get("/webhooks")
async def get_webhooks(db: AsyncSession = Depends(get_db)):
    """
    获取所有群机器人配置
    """
    result = await db.execute(
        select(RobotWebhook).order_by(RobotWebhook.created_at.desc())
    )
    webhooks = result.scalars().all()
    
    return {
        "webhooks": [
            {
                "id": w.id,
                "webhook_name": w.webhook_name,
                "webhook_url": w.webhook_url,
                "webhook_type": w.webhook_type,
                "description": w.description,
                "is_active": w.is_active,
                "send_count": w.send_count,
                "last_send_at": w.last_send_at
            }
            for w in webhooks
        ]
    }


@router.post("/webhooks")
async def create_webhook(
    webhook: WebhookConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    创建群机器人Webhook配置
    """
    new_webhook = RobotWebhook(
        webhook_name=webhook.webhook_name,
        webhook_url=webhook.webhook_url,
        webhook_type=webhook.webhook_type,
        description=webhook.description,
        is_active=webhook.is_active
    )
    
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)
    
    return {
        "success": True,
        "webhook_id": new_webhook.id,
        "message": "Webhook配置创建成功"
    }


@router.put("/webhooks/{webhook_id}")
async def update_webhook(
    webhook_id: int,
    webhook: WebhookConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新群机器人Webhook配置
    """
    result = await db.execute(
        select(RobotWebhook).where(RobotWebhook.id == webhook_id)
    )
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")
    
    existing.webhook_name = webhook.webhook_name
    existing.webhook_url = webhook.webhook_url
    existing.webhook_type = webhook.webhook_type
    existing.description = webhook.description
    existing.is_active = webhook.is_active
    existing.updated_at = func.now()
    
    await db.commit()
    
    return {"success": True, "message": "Webhook配置更新成功"}


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除群机器人Webhook配置
    """
    result = await db.execute(
        select(RobotWebhook).where(RobotWebhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")
    
    await db.delete(webhook)
    await db.commit()
    
    return {"success": True, "message": "Webhook配置删除成功"}


# ============================================================================
# 业务流程模板管理
# ============================================================================

@router.get("/workflows")
async def get_workflow_templates(db: AsyncSession = Depends(get_db)):
    """
    获取所有业务流程模板
    """
    result = await db.execute(
        select(WorkflowTemplate).order_by(WorkflowTemplate.is_default.desc(), WorkflowTemplate.created_at)
    )
    templates = result.scalars().all()
    
    return {
        "templates": [
            {
                "id": t.id,
                "template_code": t.template_code,
                "template_name": t.template_name,
                "template_type": t.template_type,
                "description": t.description,
                "workflow_steps": t.workflow_steps,
                "auto_rules": t.auto_rules,
                "notification_config": t.notification_config,
                "is_default": t.is_default,
                "is_active": t.is_active
            }
            for t in templates
        ]
    }


@router.post("/workflows/activate/{template_code}")
async def activate_workflow_template(
    template_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    激活业务流程模板（设置为当前使用的模板）
    """
    # 检查模板是否存在
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.template_code == template_code)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="业务流程模板不存在")
    
    # 更新配置
    config_result = await db.execute(
        select(EnhancedSystemConfig).where(EnhancedSystemConfig.config_key == 'active_workflow_template')
    )
    config = config_result.scalar_one_or_none()
    
    if config:
        config.config_value = template_code
        config.updated_at = func.now()
    else:
        new_config = EnhancedSystemConfig(
            config_key='active_workflow_template',
            config_value=template_code,
            config_type='string',
            display_name='当前业务流程'
        )
        db.add(new_config)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已激活业务流程模板：{template.template_name}"
    }


# ============================================================================
# 权限管理 API
# ============================================================================

@router.get("/roles")
async def get_roles(db: AsyncSession = Depends(get_db)):
    """
    获取所有角色
    """
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    
    return {
        "roles": [
            {
                "id": r.id,
                "role_name": r.role_name,
                "role_display_name": r.role_display_name,
                "description": r.description,
                "permissions": r.permissions,
                "is_system": r.is_system
            }
            for r in roles
        ]
    }


@router.get("/permissions")
async def get_permissions(db: AsyncSession = Depends(get_db)):
    """
    获取所有权限（按模块分组）
    """
    result = await db.execute(
        select(Permission).order_by(Permission.module, Permission.sort_order)
    )
    permissions = result.scalars().all()
    
    # 按模块分组
    modules = {}
    for perm in permissions:
        if perm.module not in modules:
            modules[perm.module] = []
        modules[perm.module].append({
            "id": perm.id,
            "permission_code": perm.permission_code,
            "permission_name": perm.permission_name,
            "description": perm.description,
            "action": perm.action
        })
    
    return {"modules": modules}


@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    """
    获取所有管理员用户
    """
    result = await db.execute(
        select(AdminUser, Role)
        .outerjoin(Role, AdminUser.role_id == Role.id)
        .order_by(AdminUser.created_at.desc())
    )
    users_with_roles = result.all()
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "email": user.email,
                "phone": user.phone,
                "role_id": user.role_id,
                "role_name": role.role_display_name if role else None,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at
            }
            for user, role in users_with_roles
        ]
    }


@router.post("/users")
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建管理员用户
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == user.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 密码加密
    hashed_password = pwd_context.hash(user.password)
    
    new_user = AdminUser(
        username=user.username,
        password_hash=hashed_password,
        real_name=user.real_name,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
        wework_userid=user.wework_userid
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "success": True,
        "user_id": new_user.id,
        "message": "用户创建成功"
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新管理员用户
    """
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    if user_update.real_name is not None:
        user.real_name = user_update.real_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.role_id is not None:
        user.role_id = user_update.role_id
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.password is not None:
        user.password_hash = pwd_context.hash(user_update.password)
    
    user.updated_at = func.now()
    await db.commit()
    
    return {"success": True, "message": "用户更新成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除管理员用户
    """
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    await db.delete(user)
    await db.commit()
    
    return {"success": True, "message": "用户删除成功"}


# ============================================================================
# 操作日志
# ============================================================================

@router.get("/logs")
async def get_operation_logs(
    page: int = 1,
    page_size: int = 50,
    module: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取操作日志（分页）
    """
    query = select(OperationLog).order_by(OperationLog.created_at.desc())
    
    if module:
        query = query.where(OperationLog.module == module)
    
    # 计算总数
    count_query = select(func.count()).select_from(OperationLog)
    if module:
        count_query = count_query.where(OperationLog.module == module)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.limit(page_size).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "username": log.username,
                "operation_type": log.operation_type,
                "module": log.module,
                "description": log.description,
                "request_path": log.request_path,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
