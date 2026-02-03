"""
项目详情查看路由
实现安全链接访问、SSR渲染、增量数据更新
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Project
from ..services.secure_link_service import SecureLinkService
from ..services.cache_service import cache_service
from typing import Optional
import os
from pathlib import Path


router = APIRouter(prefix="/view", tags=["页面视图"])

# 配置模板目录
templates_dir = Path(__file__).parent.parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/project-detail", response_class=HTMLResponse)
async def view_project_detail(
    request: Request,
    token: str = Query(..., description="访问令牌"),
    db: AsyncSession = Depends(get_db)
):
    """
    项目详情页面（服务端渲染）
    
    - 验证JWT令牌
    - 首次加载时直接渲染数据到HTML
    - 页面包含JavaScript定时器，定期请求增量更新
    """
    try:
        # 1. 验证令牌并获取项目数据
        project_data = await SecureLinkService.verify_and_get_project_data(token, db)
        
        # 2. 渲染HTML模板，注入初始数据
        return templates.TemplateResponse(
            "project_detail.html",
            {
                "request": request,
                "project": project_data,
                "token": token  # 传递token用于后续增量更新
            }
        )
    
    except ValueError as e:
        # 令牌验证失败
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>访问失败</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .error-box {{
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 400px;
                    }}
                    .error-icon {{
                        font-size: 60px;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #666;
                        line-height: 1.6;
                    }}
                </style>
            </head>
            <body>
                <div class="error-box">
                    <div class="error-icon">🔒</div>
                    <h1>访问受限</h1>
                    <p>{str(e)}</p>
                    <p style="margin-top: 20px; font-size: 14px; color: #999;">
                        如需查看项目详情，请从企业微信重新获取链接
                    </p>
                </div>
            </body>
            </html>
            """,
            status_code=403
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/api/project/progress")
async def get_project_progress(
    project_id: int = Query(..., description="项目ID"),
    token: str = Query(..., description="访问令牌"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目进度增量更新数据
    
    - 仅返回可能变化的字段（进度、状态等）
    - 使用Redis缓存，减少数据库查询
    - 前端JavaScript定时调用此接口
    """
    try:
        # 1. 验证令牌（确保用户有权限访问）
        payload = SecureLinkService.verify_token(token)
        
        # 验证项目ID是否匹配
        if payload.get('project_id') != project_id:
            raise ValueError("项目ID不匹配")
        
        # 2. 先尝试从缓存获取
        cached_data = cache_service.get_project_progress(project_id)
        if cached_data:
            return JSONResponse(content={
                "success": True,
                "data": cached_data,
                "from_cache": True
            })
        
        # 3. 缓存未命中，查询数据库
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 4. 组装增量数据（只返回可能变化的字段）
        progress_data = {
            'status': project.status,
            'progress': project.progress,
            'updated_at': project.updated_at.isoformat(),
            'team_members': project.team_members,
            # 可以根据需要添加其他可能变化的字段
        }
        
        # 5. 写入缓存（10分钟过期）
        cache_service.set_project_progress(project_id, progress_data, expire_seconds=600)
        
        return JSONResponse(content={
            "success": True,
            "data": progress_data,
            "from_cache": False
        })
    
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/api/project/invalidate-cache")
async def invalidate_project_cache(
    project_id: int = Query(..., description="项目ID")
):
    """
    手动清除项目缓存（用于项目更新后立即刷新）
    
    - 管理员或系统在更新项目数据后调用
    - 确保用户下次访问时获取最新数据
    """
    success = cache_service.invalidate_project_cache(project_id)
    
    return JSONResponse(content={
        "success": success,
        "message": "缓存已清除" if success else "缓存清除失败（Redis不可用）"
    })
