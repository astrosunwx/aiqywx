# -*- coding: utf-8 -*-
"""Message Channel Configuration API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import os
import json

router = APIRouter(prefix="/api/channel-config", tags=["Channel Configuration"])

# Database path
DB_PATH = r'G:\aiqywx\customer-system\customer-system\backend\customer_system.db'

# Models
class ChannelConfigResponse(BaseModel):
    id: int
    channel_type: str
    channel_name: str
    is_enabled: bool
    config_data: Optional[Dict[str, Any]] = None

class ChannelConfigListResponse(BaseModel):
    channels: List[ChannelConfigResponse]
    total: int

class ChannelConfigUpdate(BaseModel):
    channel_name: Optional[str] = None
    is_enabled: Optional[bool] = None
    config_data: Optional[Dict[str, Any]] = None

# API Endpoints
@router.get("/list", response_model=ChannelConfigListResponse)
async def list_channels():
    """List all channel configurations"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM channel_configs")
        total = cursor.fetchone()['count']
        
        cursor.execute("SELECT * FROM channel_configs ORDER BY id ASC")
        
        channels = []
        for row in cursor.fetchall():
            config_data = json.loads(row['config_data']) if row['config_data'] else {}
            channels.append({
                'id': row['id'],
                'channel_type': row['channel_type'],
                'channel_name': row['channel_name'],
                'is_enabled': bool(row['is_enabled']),
                'config_data': config_data
            })
        
        conn.close()
        return {"channels": channels, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{channel_id}")
async def get_channel(channel_id: int):
    """Get channel config by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channel_configs WHERE id = ?", (channel_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        config_data = json.loads(row['config_data']) if row['config_data'] else {}
        channel = {
            'id': row['id'],
            'channel_type': row['channel_type'],
            'channel_name': row['channel_name'],
            'is_enabled': bool(row['is_enabled']),
            'config_data': config_data
        }
        
        conn.close()
        return channel
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{channel_id}")
async def update_channel(channel_id: int, update: ChannelConfigUpdate):
    """Update channel configuration"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM channel_configs WHERE id = ?", (channel_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Build update query
        updates = []
        params = []
        
        if update.channel_name is not None:
            updates.append("channel_name = ?")
            params.append(update.channel_name)
        
        if update.is_enabled is not None:
            updates.append("is_enabled = ?")
            params.append(1 if update.is_enabled else 0)
        
        if update.config_data is not None:
            updates.append("config_data = ?")
            params.append(json.dumps(update.config_data))
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(channel_id)
        query = f"UPDATE channel_configs SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Channel updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_channel_stats():
    """Get channel statistics summary"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get channel counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled,
                SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled
            FROM channel_configs
        """)
        stats = cursor.fetchone()
        
        # Get template usage by channel
        cursor.execute("""
            SELECT 
                cc.channel_name,
                COUNT(mt.id) as template_count
            FROM channel_configs cc
            LEFT JOIN message_templates mt ON mt.channel_config_id = cc.id
            GROUP BY cc.id, cc.channel_name
            ORDER BY template_count DESC
        """)
        usage = [{'channel': row['channel_name'], 'templates': row['template_count']} 
                 for row in cursor.fetchall()]
        
        conn.close()
        return {
            "total_channels": stats['total'],
            "enabled_channels": stats['enabled'],
            "disabled_channels": stats['disabled'],
            "channel_usage": usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
