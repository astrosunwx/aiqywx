"""
AI模型配置管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import func
from app.database import get_db
from app.models_ai import AIModelConfig, AIModelUsageLog
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/admin/ai-models", tags=["AI模型配置"])


# ============================================================================
# Pydantic 模型
# ============================================================================

class AIModelConfigCreate(BaseModel):
    """创建AI模型配置"""
    model_code: str = Field(..., description="模型代码（唯一标识，如：wework-official）")
    model_name: str = Field(..., description="模型显示名称（如：企业微信官方API）")
    provider: str = Field(..., description="提供商：wework/zhipu/tencent/doubao/deepseek/custom")
    provider_display_name: Optional[str] = Field(None, description="提供商显示名称")
    model_version: Optional[str] = Field(None, description="模型版本")
    api_endpoint: Optional[str] = Field(None, description="API端点URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    extra_config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    description: Optional[str] = Field(None, description="模型描述")
    is_official: bool = Field(False, description="是否官方企业微信API")
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否默认模型")
    priority: int = Field(0, description="优先级")


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置"""
    model_name: Optional[str] = None
    provider_display_name: Optional[str] = None
    model_version: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_official: Optional[bool] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应"""
    id: int
    model_code: str
    model_name: str
    provider: str
    provider_display_name: Optional[str]
    model_version: Optional[str]
    api_endpoint: Optional[str]
    api_key_masked: Optional[str] = Field(None, description="脱敏后的API密钥")
    extra_config: Optional[Dict[str, Any]]
    description: Optional[str]
    is_official: bool
    is_active: bool
    is_default: bool
    priority: int
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIModelUsageStats(BaseModel):
    """AI模型使用统计"""
    model_code: str
    model_name: str
    total_calls: int
    success_calls: int
    failed_calls: int
    avg_response_time_ms: Optional[float]
    last_used_at: Optional[datetime]


# ============================================================================
# API 路由
# ============================================================================

@router.get("/list", response_model=List[AIModelConfigResponse])
async def list_ai_models(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    获取AI模型列表
    
    - **include_inactive**: 是否包含未启用的模型（默认只返回启用的）
    """
    query = select(AIModelConfig)
    
    if not include_inactive:
        query = query.where(AIModelConfig.is_active == True)
    
    query = query.order_by(AIModelConfig.priority.desc(), AIModelConfig.created_at.desc())
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 构造响应，脱敏API密钥
    response_list = []
    for model in models:
        model_dict = {
            "id": model.id,
            "model_code": model.model_code,
            "model_name": model.model_name,
            "provider": model.provider,
            "provider_display_name": model.provider_display_name,
            "model_version": model.model_version,
            "api_endpoint": model.api_endpoint,
            "api_key_masked": _mask_api_key(model.api_key) if model.api_key else None,
            "extra_config": model.extra_config,
            "description": model.description,
            "is_official": model.is_official,
            "is_active": model.is_active,
            "is_default": model.is_default,
            "priority": model.priority,
            "usage_count": model.usage_count,
            "last_used_at": model.last_used_at,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }
        response_list.append(AIModelConfigResponse(**model_dict))
    
    return response_list


@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_models(db: AsyncSession = Depends(get_db)):
    """
    获取所有启用的AI模型（简化版，用于下拉选择）
    """
    result = await db.execute(
        select(AIModelConfig)
        .where(AIModelConfig.is_active == True)
        .order_by(AIModelConfig.priority.desc())
    )
    models = result.scalars().all()
    
    return [
        {
            "value": model.model_code,
            "label": model.model_name,
            "provider": model.provider,
            "is_official": model.is_official,
            "is_default": model.is_default,
        }
        for model in models
    ]


@router.get("/{model_id}", response_model=AIModelConfigResponse)
async def get_ai_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个AI模型配置详情"""
    result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型配置不存在")
    
    model_dict = {
        "id": model.id,
        "model_code": model.model_code,
        "model_name": model.model_name,
        "provider": model.provider,
        "provider_display_name": model.provider_display_name,
        "model_version": model.model_version,
        "api_endpoint": model.api_endpoint,
        "api_key_masked": _mask_api_key(model.api_key) if model.api_key else None,
        "extra_config": model.extra_config,
        "description": model.description,
        "is_official": model.is_official,
        "is_active": model.is_active,
        "is_default": model.is_default,
        "priority": model.priority,
        "usage_count": model.usage_count,
        "last_used_at": model.last_used_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
    
    return AIModelConfigResponse(**model_dict)


@router.post("/create", response_model=AIModelConfigResponse)
async def create_ai_model(
    config: AIModelConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建AI模型配置
    """
    # 检查model_code是否已存在
    existing = await db.execute(
        select(AIModelConfig).where(AIModelConfig.model_code == config.model_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"模型代码 {config.model_code} 已存在")
    
    # 如果设置为默认模型，取消其他模型的默认状态
    if config.is_default:
        await db.execute(
            update(AIModelConfig).values(is_default=False)
        )
        await db.commit()
    
    # 创建新模型配置
    new_model = AIModelConfig(
        model_code=config.model_code,
        model_name=config.model_name,
        provider=config.provider,
        provider_display_name=config.provider_display_name,
        model_version=config.model_version,
        api_endpoint=config.api_endpoint,
        api_key=config.api_key,
        extra_config=config.extra_config,
        description=config.description,
        is_official=config.is_official,
        is_active=config.is_active,
        is_default=config.is_default,
        priority=config.priority,
    )
    
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    
    model_dict = {
        "id": new_model.id,
        "model_code": new_model.model_code,
        "model_name": new_model.model_name,
        "provider": new_model.provider,
        "provider_display_name": new_model.provider_display_name,
        "model_version": new_model.model_version,
        "api_endpoint": new_model.api_endpoint,
        "api_key_masked": _mask_api_key(new_model.api_key) if new_model.api_key else None,
        "extra_config": new_model.extra_config,
        "description": new_model.description,
        "is_official": new_model.is_official,
        "is_active": new_model.is_active,
        "is_default": new_model.is_default,
        "priority": new_model.priority,
        "usage_count": new_model.usage_count,
        "last_used_at": new_model.last_used_at,
        "created_at": new_model.created_at,
        "updated_at": new_model.updated_at,
    }
    
    return AIModelConfigResponse(**model_dict)


@router.put("/update/{model_id}", response_model=AIModelConfigResponse)
async def update_ai_model(
    model_id: int,
    config: AIModelConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新AI模型配置
    """
    # 查询模型
    result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型配置不存在")
    
    # 如果设置为默认模型，取消其他模型的默认状态
    if config.is_default:
        await db.execute(
            update(AIModelConfig)
            .where(AIModelConfig.id != model_id)
            .values(is_default=False)
        )
    
    # 更新字段
    update_data = config.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
    
    await db.commit()
    await db.refresh(model)
    
    model_dict = {
        "id": model.id,
        "model_code": model.model_code,
        "model_name": model.model_name,
        "provider": model.provider,
        "provider_display_name": model.provider_display_name,
        "model_version": model.model_version,
        "api_endpoint": model.api_endpoint,
        "api_key_masked": _mask_api_key(model.api_key) if model.api_key else None,
        "extra_config": model.extra_config,
        "description": model.description,
        "is_official": model.is_official,
        "is_active": model.is_active,
        "is_default": model.is_default,
        "priority": model.priority,
        "usage_count": model.usage_count,
        "last_used_at": model.last_used_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
    
    return AIModelConfigResponse(**model_dict)


@router.delete("/delete/{model_id}")
async def delete_ai_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除AI模型配置
    """
    result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型配置不存在")
    
    # 检查是否是默认模型
    if model.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认模型，请先设置其他模型为默认")
    
    await db.execute(
        delete(AIModelConfig).where(AIModelConfig.id == model_id)
    )
    await db.commit()
    
    return {"message": f"AI模型配置 {model.model_name} 已删除", "success": True}


@router.post("/set-default/{model_id}")
async def set_default_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """
    设置默认AI模型
    """
    result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型配置不存在")
    
    if not model.is_active:
        raise HTTPException(status_code=400, detail="不能设置未启用的模型为默认")
    
    # 取消其他模型的默认状态
    await db.execute(
        update(AIModelConfig).values(is_default=False)
    )
    
    # 设置当前模型为默认
    model.is_default = True
    await db.commit()
    
    return {"message": f"{model.model_name} 已设置为默认AI模型", "success": True}


@router.get("/stats/usage", response_model=List[AIModelUsageStats])
async def get_usage_stats(db: AsyncSession = Depends(get_db)):
    """
    获取AI模型使用统计
    """
    # 获取所有模型的基础信息
    models_result = await db.execute(select(AIModelConfig))
    models = {m.model_code: m for m in models_result.scalars().all()}
    
    # 统计每个模型的使用情况
    stats_query = select(
        AIModelUsageLog.model_code,
        func.count(AIModelUsageLog.id).label('total_calls'),
        func.sum(func.cast(AIModelUsageLog.success, Integer)).label('success_calls'),
        func.avg(AIModelUsageLog.response_time_ms).label('avg_response_time'),
        func.max(AIModelUsageLog.created_at).label('last_used')
    ).group_by(AIModelUsageLog.model_code)
    
    stats_result = await db.execute(stats_query)
    stats_data = stats_result.all()
    
    usage_stats = []
    for row in stats_data:
        model = models.get(row.model_code)
        if model:
            usage_stats.append(AIModelUsageStats(
                model_code=row.model_code,
                model_name=model.model_name,
                total_calls=row.total_calls,
                success_calls=row.success_calls or 0,
                failed_calls=row.total_calls - (row.success_calls or 0),
                avg_response_time_ms=float(row.avg_response_time) if row.avg_response_time else None,
                last_used_at=row.last_used
            ))
    
    return usage_stats


# ============================================================================
# 辅助函数
# ============================================================================

def _mask_api_key(api_key: str) -> str:
    """脱敏API密钥，只显示前6位和后4位"""
    if not api_key or len(api_key) < 10:
        return "***"
    return f"{api_key[:6]}...{api_key[-4:]}"
