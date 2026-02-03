"""
项目同步功能 - API实现
文件: routers/project_sync_router.py
说明: 处理项目缓存、同步、访问控制等功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import jwt
import httpx
from app.database import get_db, AsyncSession
from app.models import (
    ProjectCache, ProjectSyncHistory, ProjectSyncConfig, 
    ProjectAccessTokens, ProjectStatusNotifications
)
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["project_sync"])

# ============================================================================
# 请求/响应模型
# ============================================================================

class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    project: Optional[Dict[str, Any]] = None
    from_cache: bool = False
    cache_time: Optional[str] = None
    last_sync: Optional[str] = None
    message: str = "success"

class ProjectStatusResponse(BaseModel):
    """项目轻量级状态查询响应（用于AI机器人）"""
    success: bool = True
    project_id: str
    title: str
    type: str  # presale, aftersales, sales, status
    status: str  # 当前状态
    progress: int = 0  # 完成度百分比 0-100
    updated_at: str  # 最后更新时间
    customer_name: Optional[str] = None
    engineer_name: Optional[str] = None
    salesman_name: Optional[str] = None
    from_cache: bool = False
    cache_ttl: Optional[int] = None
    message: str = "success"

class VerifyAccessResponse(BaseModel):
    """访问权限验证响应"""
    has_access: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    access_type: Optional[str] = None

class ProjectSyncConfigModel(BaseModel):
    """项目同步配置"""
    auto_sync_enabled: bool = True
    sync_frequency: str = "*/15 * * * *"
    cron_expression: str = ""
    cache_ttl: int = 30
    sync_types: List[str] = ["presale", "aftersales", "sales"]
    notify_on_change: bool = True
    notify_channels: List[str] = ["wechat", "sms"]

class SyncProjectsRequest(BaseModel):
    """手动同步请求"""
    sync_type: str = "manual"  # auto | manual
    force: bool = False
    project_types: Optional[List[str]] = None

class SyncProjectsResponse(BaseModel):
    """手动同步响应"""
    success: bool
    total: int
    updated: int
    unchanged: int
    failed: int
    sync_time: str
    duration: float
    changes: Optional[List[Dict]] = None
    message: str = ""

class TimeDisplayConfigModel(BaseModel):
    """时间显示配置"""
    aftersales_time_format: str = "YYYY-MM-DD HH:mm"
    sales_time_format: str = "YYYY-MM-DD HH:mm"
    show_payment_time: bool = True
    timezone: str = "Asia/Shanghai"

# ============================================================================
# 工具函数
# ============================================================================

async def get_db_session():
    """获取数据库会话"""
    async with AsyncSession() as session:
        yield session

async def verify_access_token(token: str, project_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    验证访问令牌
    
    Returns:
        {
            'has_access': bool,
            'user_id': str,
            'user_type': str,
            'user_name': str
        }
    """
    try:
        # 解析JWT令牌
        SECRET_KEY = "your-secret-key-here"  # 从配置文件读取
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # 验证项目ID和令牌
        stmt = select(ProjectAccessTokens).where(
            and_(
                ProjectAccessTokens.token == token,
                ProjectAccessTokens.project_id == project_id,
                ProjectAccessTokens.expires_at > datetime.utcnow(),
                ProjectAccessTokens.revoked == False
            )
        )
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            return {
                'has_access': False,
                'user_id': None,
                'user_type': None,
                'user_name': None
            }
        
        # 更新上次访问时间和访问计数
        token_record.last_accessed_at = datetime.utcnow()
        token_record.access_count += 1
        await db.commit()
        
        return {
            'has_access': True,
            'user_id': token_record.user_id,
            'user_type': token_record.user_type,
            'user_name': token_record.user_name
        }
    
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return {
            'has_access': False,
            'user_id': None,
            'user_type': None,
            'user_name': None
        }

async def get_project_from_cache(project_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """从缓存获取项目数据"""
    stmt = select(ProjectCache).where(
        ProjectCache.project_id == project_id
    )
    result = await db.execute(stmt)
    cache = result.scalar_one_or_none()
    
    if not cache:
        return None
    
    # 检查是否过期
    if cache.expires_at and cache.expires_at < datetime.utcnow():
        return None
    
    # 返回缓存数据
    data = json.loads(cache.data)
    data['from_cache'] = True
    data['cache_time'] = _format_relative_time(cache.cached_at)
    data['last_sync'] = cache.cached_at.isoformat()
    
    return data

async def fetch_from_remote_api(project_id: str, project_type: str) -> Optional[Dict[str, Any]]:
    """从远程API获取项目数据"""
    try:
        # 这里需要配置实际的远程API地址和密钥
        REMOTE_API_BASE = "https://remote-api.example.com"
        REMOTE_API_KEY = "your-api-key"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{REMOTE_API_BASE}/projects/{project_id}",
                headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Remote API error: {response.status_code}")
                return None
    
    except Exception as e:
        logger.error(f"Failed to fetch from remote API: {e}")
        return None

async def update_cache(project_id: str, project_data: Dict[str, Any], 
                      cache_ttl: int, db: AsyncSession) -> ProjectCache:
    """更新项目缓存"""
    stmt = select(ProjectCache).where(ProjectCache.project_id == project_id)
    result = await db.execute(stmt)
    cache = result.scalar_one_or_none()
    
    expires_at = datetime.utcnow() + timedelta(minutes=cache_ttl)
    
    if not cache:
        cache = ProjectCache(
            project_id=project_id,
            project_type=project_data.get('type', 'unknown'),
            title=project_data.get('title'),
            status=project_data.get('status'),
            data=json.dumps(project_data, default=str),
            remote_updated_at=datetime.utcnow(),
            expires_at=expires_at
        )
        db.add(cache)
    else:
        cache.title = project_data.get('title')
        cache.status = project_data.get('status')
        cache.data = json.dumps(project_data, default=str)
        cache.remote_updated_at = datetime.utcnow()
        cache.expires_at = expires_at
    
    await db.commit()
    return cache

def _format_relative_time(dt: datetime) -> str:
    """格式化相对时间"""
    now = datetime.utcnow()
    diff = (now - dt).total_seconds()
    
    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes}分钟前"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours}小时前"
    else:
        days = int(diff / 86400)
        return f"{days}天前"

# ============================================================================
# API 接口
# ============================================================================

@router.get("/projects/{project_id}/status")
async def get_project_status(
    project_id: str,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
) -> ProjectStatusResponse:
    """
    获取项目轻量级状态查询 - 为AI机器人优化
    
    说明:
        - 只返回必要字段，避免传输大量数据
        - 使用激进的缓存策略，最小化数据库查询
        - 不调用远程API，仅使用本地缓存/数据库
        - 专为AI机器人设计，快速响应（<100ms）
    
    Args:
        project_id: 项目ID
        token: 访问令牌（可选）
    
    Returns:
        项目状态信息（9个关键字段）
    """
    try:
        # 验证访问权限（如果提供了token）
        if token:
            try:
                access = await verify_access_token(token, project_id, db)
                if not access['has_access']:
                    raise HTTPException(status_code=403, detail="无访问权限")
            except Exception as e:
                logger.warning(f"Token verification failed for project {project_id}: {str(e)}")
                # 继续执行，可能是匿名访问
        
        # 第一步：尝试从Redis缓存获取（如果可用）
        cache_key = f"project_status:{project_id}"
        try:
            import redis
            from app.services.cache_service import redis_client
            if redis_client:
                cached_status = redis_client.get(cache_key)
                if cached_status:
                    import json
                    status_data = json.loads(cached_status)
                    status_data['from_cache'] = True
                    status_data['cache_ttl'] = redis_client.ttl(cache_key)
                    return ProjectStatusResponse(**status_data)
        except Exception as e:
            logger.debug(f"Redis cache check failed: {str(e)}")
            # 继续使用数据库
        
        # 第二步：从数据库缓存获取
        stmt = select(ProjectCache).where(ProjectCache.project_id == project_id)
        result = await db.execute(stmt)
        cache_record = result.scalars().first()
        
        if cache_record and cache_record.cached_data:
            import json
            project_data = json.loads(cache_record.cached_data)
            
            # 提取必要字段
            status_response = ProjectStatusResponse(
                project_id=project_id,
                title=project_data.get('title', f'项目{project_id}'),
                type=project_data.get('type', 'presale'),
                status=project_data.get('status', 'unknown'),
                progress=project_data.get('progress', 0),
                updated_at=project_data.get('updated_at', cache_record.cached_at.isoformat()),
                customer_name=project_data.get('customer_name'),
                engineer_name=project_data.get('engineer_name'),
                salesman_name=project_data.get('salesman_name'),
                from_cache=True,
                cache_ttl=300  # 5分钟缓存
            )
            
            # 异步更新Redis缓存（不阻塞响应）
            try:
                import json
                redis_client.setex(
                    cache_key,
                    300,
                    json.dumps(status_response.dict(exclude={'from_cache', 'cache_ttl', 'message'}))
                )
            except:
                pass
            
            return status_response
        
        # 第三步：项目不存在
        raise HTTPException(
            status_code=404,
            detail=f"项目 {project_id} 不存在或未同步"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project status for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.get("/projects/{project_id}/verify-access")
async def verify_access(
    project_id: str,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
) -> VerifyAccessResponse:
    """
    验证对项目的访问权限
    
    Args:
        project_id: 项目ID
        token: 访问令牌
    
    Returns:
        访问权限验证结果
    """
    if not token:
        return VerifyAccessResponse(has_access=False)
    
    access = await verify_access_token(token, project_id, db)
    return VerifyAccessResponse(**access)

@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: str,
    token: Optional[str] = Query(None),
    use_cache: bool = Query(True),
    force_sync: bool = Query(False),
    db: AsyncSession = Depends(get_db_session)
) -> ProjectDetailResponse:
    """
    获取项目详情（带缓存支持）
    
    Args:
        project_id: 项目ID
        token: 访问令牌
        use_cache: 是否使用缓存
        force_sync: 是否强制同步
    
    Returns:
        项目详情和缓存状态
    """
    # 验证访问权限
    if token:
        access = await verify_access_token(token, project_id, db)
        if not access['has_access']:
            raise HTTPException(status_code=403, detail="无访问权限")
    
    # 获取缓存数据
    if use_cache and not force_sync:
        cached_data = await get_project_from_cache(project_id, db)
        if cached_data:
            return ProjectDetailResponse(
                project=cached_data,
                from_cache=True,
                cache_time=cached_data.get('cache_time')
            )
    
    # 从远程API获取数据
    remote_data = await fetch_from_remote_api(project_id, "unknown")
    
    if remote_data:
        # 更新缓存
        config = await get_config_value("cache_ttl", 30, db)
        cache = await update_cache(project_id, remote_data, config, db)
        
        return ProjectDetailResponse(
            project=remote_data,
            from_cache=False,
            last_sync=cache.cached_at.isoformat()
        )
    else:
        # 远程获取失败，返回过期缓存或错误
        cached_data = await get_project_from_cache(project_id, db)
        if cached_data:
            return ProjectDetailResponse(
                project=cached_data,
                from_cache=True,
                message="使用过期缓存数据（远程API不可用）"
            )
        else:
            raise HTTPException(status_code=404, detail="项目不存在")

@router.get("/config/project-sync")
async def get_project_sync_config(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """获取项目同步配置"""
    config_keys = [
        'auto_sync_enabled',
        'sync_frequency',
        'cron_expression',
        'cache_ttl',
        'sync_types',
        'notify_on_change',
        'notify_channels'
    ]
    
    config = {}
    for key in config_keys:
        value = await get_config_value(key, None, db)
        if value is not None:
            config[key] = value
    
    # 获取上次同步时间
    stmt = select(ProjectSyncHistory).order_by(
        ProjectSyncHistory.sync_time.desc()
    ).limit(1)
    result = await db.execute(stmt)
    last_sync = result.scalar_one_or_none()
    
    return {
        "config": config,
        "last_sync_time": last_sync.sync_time.isoformat() if last_sync else None
    }

@router.post("/config/project-sync")
async def save_project_sync_config(
    config: ProjectSyncConfigModel,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """保存项目同步配置"""
    config_dict = config.dict()
    
    for key, value in config_dict.items():
        await save_config_value(key, value, db)
    
    logger.info(f"Project sync config updated: {config_dict}")
    
    return {"success": True, "message": "配置已保存"}

@router.post("/projects/sync")
async def sync_projects(
    request: SyncProjectsRequest,
    db: AsyncSession = Depends(get_db_session)
) -> SyncProjectsResponse:
    """
    手动触发项目同步
    
    Args:
        sync_type: 同步类型 (auto/manual)
        force: 是否强制同步
        project_types: 要同步的项目类型
    
    Returns:
        同步结果
    """
    start_time = datetime.utcnow()
    
    try:
        # 获取配置
        config = await get_project_sync_config(db)
        if request.project_types is None:
            project_types = config.get('config', {}).get('sync_types', ['presale', 'aftersales', 'sales'])
        else:
            project_types = request.project_types
        
        # 获取所有项目（这里需要实现从远程API批量获取）
        all_projects = await fetch_all_remote_projects(project_types)
        
        total = len(all_projects)
        updated = 0
        unchanged = 0
        failed = 0
        changes = []
        
        cache_ttl = config.get('config', {}).get('cache_ttl', 30)
        
        # 同步每个项目
        for project in all_projects:
            try:
                project_id = project.get('id')
                old_cache = await get_project_from_cache(project_id, db)
                
                await update_cache(project_id, project, cache_ttl, db)
                
                # 检测变更
                if old_cache:
                    if old_cache.get('status') != project.get('status'):
                        updated += 1
                        changes.append({
                            'project_id': project_id,
                            'old_status': old_cache.get('status'),
                            'new_status': project.get('status'),
                            'notified': False
                        })
                        
                        # 发送通知
                        notify_on_change = config.get('config', {}).get('notify_on_change', True)
                        if notify_on_change:
                            await notify_status_change(
                                project_id,
                                old_cache.get('status'),
                                project.get('status'),
                                db
                            )
                    else:
                        unchanged += 1
                else:
                    updated += 1
            
            except Exception as e:
                logger.error(f"Failed to sync project {project.get('id')}: {e}")
                failed += 1
        
        # 记录同步历史
        duration = (datetime.utcnow() - start_time).total_seconds()
        sync_status = "success" if failed == 0 else "partial"
        
        sync_record = ProjectSyncHistory(
            sync_time=datetime.utcnow(),
            sync_type=request.sync_type,
            total_projects=total,
            updated_count=updated,
            unchanged_count=unchanged,
            failed_count=failed,
            duration=duration,
            status=sync_status,
            message=f"同步完成：更新{updated}个，未变更{unchanged}个，失败{failed}个",
            changes=json.dumps(changes, default=str),
            triggered_by="system" if request.sync_type == "auto" else "manual"
        )
        db.add(sync_record)
        await db.commit()
        
        return SyncProjectsResponse(
            success=True,
            total=total,
            updated=updated,
            unchanged=unchanged,
            failed=failed,
            sync_time=datetime.utcnow().isoformat(),
            duration=duration,
            changes=changes,
            message="同步完成"
        )
    
    except Exception as e:
        logger.error(f"Project sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@router.get("/projects/sync-history")
async def get_sync_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """获取项目同步历史"""
    stmt = select(ProjectSyncHistory).order_by(
        ProjectSyncHistory.sync_time.desc()
    ).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    # 获取总数
    count_stmt = select(func.count(ProjectSyncHistory.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    return {
        "history": [
            {
                "sync_time": h.sync_time.isoformat(),
                "sync_type": h.sync_type,
                "total_projects": h.total_projects,
                "updated_count": h.updated_count,
                "duration": f"{h.duration:.1f}秒",
                "status": h.status,
                "message": h.message
            }
            for h in history
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }

@router.post("/config/time-display")
async def save_time_display_config(
    config: TimeDisplayConfigModel,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """保存时间显示配置"""
    config_dict = config.dict()
    
    for key, value in config_dict.items():
        await save_config_value(key, value, db)
    
    return {"success": True, "message": "时间配置已保存"}

# ============================================================================
# 辅助函数
# ============================================================================

async def get_config_value(key: str, default: Any, db: AsyncSession) -> Any:
    """获取配置值"""
    stmt = select(ProjectSyncConfig).where(ProjectSyncConfig.config_key == key)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if config:
        value = json.loads(config.config_value)
        return value.get('value', default)
    return default

async def save_config_value(key: str, value: Any, db: AsyncSession):
    """保存配置值"""
    stmt = select(ProjectSyncConfig).where(ProjectSyncConfig.config_key == key)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = ProjectSyncConfig(
            config_key=key,
            config_value=json.dumps({"value": value})
        )
        db.add(config)
    else:
        config.config_value = json.dumps({"value": value})
        config.updated_at = datetime.utcnow()
    
    await db.commit()

async def fetch_all_remote_projects(project_types: List[str]) -> List[Dict[str, Any]]:
    """从远程API批量获取所有项目"""
    try:
        REMOTE_API_BASE = "https://remote-api.example.com"
        REMOTE_API_KEY = "your-api-key"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{REMOTE_API_BASE}/projects",
                params={"types": ",".join(project_types)},
                headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json().get('projects', [])
            else:
                logger.error(f"Remote API error: {response.status_code}")
                return []
    
    except Exception as e:
        logger.error(f"Failed to fetch projects from remote API: {e}")
        return []

async def notify_status_change(
    project_id: str,
    old_status: str,
    new_status: str,
    db: AsyncSession
):
    """
    项目状态变更时发送通知
    
    Args:
        project_id: 项目ID
        old_status: 原状态
        new_status: 新状态
        db: 数据库会话
    """
    try:
        # 获取项目信息
        cache = await get_project_from_remote(project_id)
        if not cache:
            return
        
        # 获取通知配置
        config = await get_project_sync_config(db)
        notify_channels = config.get('config', {}).get('notify_channels', [])
        
        # 获取需要通知的人员
        notify_recipients = await get_project_stakeholders(project_id)
        
        # 生成通知内容
        message = f"您的{cache.get('type')}项目【{cache.get('title')}】状态已更新：{old_status} → {new_status}"
        
        # 发送通知
        for channel in notify_channels:
            for recipient in notify_recipients:
                notification = ProjectStatusNotifications(
                    project_id=project_id,
                    old_status=old_status,
                    new_status=new_status,
                    notify_to=recipient.get('user_id'),
                    notify_type=channel,
                    notify_content=message,
                    send_status='pending'
                )
                db.add(notification)
        
        await db.commit()
        logger.info(f"Notifications created for project {project_id}")
    
    except Exception as e:
        logger.error(f"Failed to notify status change: {e}")

async def get_project_from_remote(project_id: str) -> Optional[Dict[str, Any]]:
    """从远程获取单个项目信息"""
    try:
        REMOTE_API_BASE = "https://remote-api.example.com"
        REMOTE_API_KEY = "your-api-key"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{REMOTE_API_BASE}/projects/{project_id}",
                headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
    
    except Exception as e:
        logger.error(f"Failed to fetch project from remote: {e}")
    
    return None

async def get_project_stakeholders(project_id: str) -> List[Dict[str, str]]:
    """获取项目相关人员（需要从CRM系统获取）"""
    # 这需要根据实际业务逻辑实现
    # 从CRM系统获取客户、工程师、销售等相关人员
    return [
        # {'user_id': 'user123', 'phone': '138****8888', 'type': 'customer'},
        # {'user_id': 'user456', 'phone': '139****9999', 'type': 'engineer'},
    ]
