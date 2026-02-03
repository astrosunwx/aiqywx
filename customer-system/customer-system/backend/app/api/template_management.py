# -*- coding: utf-8 -*-
"""
消息模板管理 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import sqlite3

from app.database import get_db

router = APIRouter(prefix="/api/template", tags=["消息模板"])


# ========== Models ==========

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    channel_type: str
    send_mode: str
    content: str
    schedule_time: Optional[str] = None
    schedule_frequency: Optional[str] = None
    trigger_keywords: Optional[List[str]] = None
    target_groups: Optional[List[str]] = None
    is_active: bool

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int

# ========== API Endpoints ==========

@router.get("/list", response_model=TemplateListResponse)
async def list_templates(
    page: int = 1,
    page_size: int = 20
):
    """查询模板列表"""
    try:
        conn = sqlite3.connect('./customer_system.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询总数
        cursor.execute("SELECT COUNT(*) as count FROM message_templates")
        total = cursor.fetchone()['count']
        
        # 查询列表
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT * FROM message_templates
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        templates = []
        for row in cursor.fetchall():
            import json
            templates.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'channel_type': row['channel_type'],
                'send_mode': row['send_mode'],
                'content': row['content'],
                'schedule_time': row['schedule_time'],
                'schedule_frequency': row['schedule_frequency'],
                'trigger_keywords': json.loads(row['trigger_keywords']) if row['trigger_keywords'] else [],
                'target_groups': json.loads(row['target_groups']) if row['target_groups'] else [],
                'is_active': bool(row['is_active'])
            })
        
        conn.close()
        return {"templates": templates, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(template_id: int):
    """获取模板详情"""
    try:
        conn = sqlite3.connect('./customer_system.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM message_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        import json
        template = {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'channel_type': row['channel_type'],
            'send_mode': row['send_mode'],
            'content': row['content'],
            'schedule_time': row['schedule_time'],
            'schedule_frequency': row['schedule_frequency'],
            'trigger_keywords': json.loads(row['trigger_keywords']) if row['trigger_keywords'] else [],
            'target_groups': json.loads(row['target_groups']) if row['target_groups'] else [],
            'is_active': bool(row['is_active'])
        }
        
        conn.close()
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{template_id}")
async def preview_template(template_id: int):
    """预览模板"""
    try:
        conn = sqlite3.connect('./customer_system.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT content FROM message_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 简单的变量替换预览
        from datetime import datetime
        content = row['content']
        content = content.replace('{current_date}', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('{pending_count}', '5')
        content = content.replace('{project_name}', '示例项目')
        
        conn.close()
        return {"preview_content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-send")
async def test_send(
    template_id: int,
    variables: Dict[str, Any] = {},
    test_recipients: List[str] = []
):
    """测试发送"""
    return {
        "success": True,
        "message": "测试发送功能需要后续实现",
        "template_id": template_id
    }
