"""外部系统同步服务 - 支持Pull和Push模式"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Project, Customer
from typing import List, Dict
import httpx
from datetime import datetime


class SyncService:
    """外部系统同步服务"""
    
    @staticmethod
    async def sync_to_external_crm(ticket_data: dict, crm_api_url: str) -> dict:
        """
        同步工单到外部CRM系统（Push模式）
        当创建工单时主动推送
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    crm_api_url,
                    json=ticket_data,
                    timeout=10.0
                )
                return {
                    "status": "success",
                    "response": response.json()
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
    
    @staticmethod
    async def get_tickets_for_external_pull(
        db: AsyncSession,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict]:
        """
        提供数据给外部系统拉取（Pull模式）
        外部系统定时调用此接口获取工单数据
        """
        query = select(Project)
        
        if start_date:
            query = query.where(Project.created_at >= start_date)
        if end_date:
            query = query.where(Project.created_at <= end_date)
        
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # 转换为标准格式
        return [
            {
                "ticket_id": f"SV{p.id}",
                "customer": p.customer_phone,
                "project_type": p.project_type,
                "title": p.title,
                "description": p.description,
                "status": p.status,
                "amount": float(p.amount) if p.amount else None,
                "sales_id": p.sales_id,
                "engineer_id": p.engineer_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in projects
        ]
    
    @staticmethod
    async def receive_webhook_from_wechat(event_data: dict) -> dict:
        """
        接收企业微信的Webhook推送（Push模式）
        企业微信主动推送消息/事件
        """
        event_type = event_data.get("EventType")
        
        if event_type == "change_external_contact":
            # 外部联系人变更事件
            return {
                "action": "customer_updated",
                "data": event_data
            }
        elif event_type == "change_external_chat":
            # 客户群变更事件
            return {
                "action": "group_updated",
                "data": event_data
            }
        else:
            return {
                "action": "unknown",
                "data": event_data
            }
