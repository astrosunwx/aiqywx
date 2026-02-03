# -*- coding: utf-8 -*-
"""Message Template Management API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import os
import json

router = APIRouter(prefix="/api/template", tags=["Message Templates"])

# Database path - using absolute path
DB_PATH = r'G:\aiqywx\customer-system\customer-system\backend\customer_system.db'

# Models matching actual database schema
class TemplateResponse(BaseModel):
    id: int
    name: str
    module_type: str
    category: Optional[str] = None
    content: str
    content_type: Optional[str] = None
    channel_config_id: Optional[int] = None
    target_config: Optional[str] = None
    push_mode: Optional[str] = None
    keywords: Optional[List[str]] = None
    schedule_time: Optional[str] = None
    repeat_type: Optional[str] = None
    targets: Optional[List[str]] = None
    is_enabled: bool

class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int

# API Endpoints
@router.get("/list", response_model=TemplateListResponse)
async def list_templates(page: int = 1, page_size: int = 20):
    """List all templates"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM message_templates")
        total = cursor.fetchone()['count']
        
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT * FROM message_templates
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        templates = []
        for row in cursor.fetchall():
            # 安全解析JSON字段
            try:
                keywords = json.loads(row['keywords']) if row['keywords'] and row['keywords'] != 'None' else []
            except:
                keywords = []
            
            try:
                targets = json.loads(row['targets']) if row['targets'] and row['targets'] != 'None' else []
            except:
                targets = []
            
            templates.append({
                'id': row['id'],
                'name': row['name'],
                'module_type': row['module_type'],
                'category': row['category'],
                'content': row['content'],
                'content_type': row['content_type'],
                'channel_config_id': row['channel_config_id'],
                'target_config': row['target_config'],
                'push_mode': row['push_mode'],
                'keywords': keywords,
                'schedule_time': row['schedule_time'],
                'repeat_type': row['repeat_type'],
                'targets': targets,
                'is_enabled': bool(row['is_enabled'])
            })
        
        conn.close()
        return {"templates": templates, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_id}")
async def get_template(template_id: int):
    """Get template by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM message_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template = {
            'id': row['id'],
            'name': row['name'],
            'module_type': row['module_type'],
            'category': row['category'],
            'content': row['content'],
            'content_type': row['content_type'],
            'channel_config_id': row['channel_config_id'],
            'target_config': row['target_config'],
            'push_mode': row['push_mode'],
            'keywords': json.loads(row['keywords']) if row['keywords'] else [],
            'schedule_time': row['schedule_time'],
            'repeat_type': row['repeat_type'],
            'targets': json.loads(row['targets']) if row['targets'] else [],
            'is_enabled': bool(row['is_enabled'])
        }
        
        conn.close()
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview/{template_id}")
async def preview_template(template_id: int):
    """Preview template with sample data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT content FROM message_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        
        from datetime import datetime
        content = row['content']
        content = content.replace('{current_date}', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('{pending_count}', '5')
        content = content.replace('{project_name}', 'Sample Project')
        
        conn.close()
        return {"preview_content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-send")
async def test_send(template_id: int, variables: Dict[str, Any] = {}, test_recipients: List[str] = []):
    """Test send message"""
    return {
        "success": True,
        "message": "Test send feature will be implemented",
        "template_id": template_id
    }
