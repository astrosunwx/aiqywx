"""
维护提醒服务
负责设备维护提醒、保修到期提醒等定时任务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.equipment_service import EquipmentService
from app.services.parts_service import PartsService
from app.models import Equipment, PartsInventory
from typing import List, Dict, Optional
from datetime import datetime
import os


class MaintenanceReminderService:
    """维护提醒服务"""
    
    @staticmethod
    async def check_and_send_maintenance_reminders(
        db: AsyncSession,
        days_ahead: int = 7
    ) -> List[Dict]:
        """
        检查并发送维护提醒
        
        Args:
            db: 数据库会话
            days_ahead: 提前提醒天数
        
        Returns:
            提醒列表
        """
        # 获取需要维护的设备
        equipment_list = await EquipmentService.get_equipment_needing_maintenance(db, days_ahead)
        
        reminders = []
        
        for equipment in equipment_list:
            # 计算距离维护日期的天数
            days_until = (equipment.next_maintenance_date - datetime.now().date()).days
            
            # 构建提醒消息
            reminder = {
                'equipment_id': equipment.id,
                'equipment_no': equipment.equipment_no,
                'equipment_type': equipment.equipment_type,
                'customer_name': equipment.customer_name,
                'customer_phone': equipment.customer_phone,
                'install_location': equipment.install_location,
                'next_maintenance_date': equipment.next_maintenance_date.isoformat(),
                'days_until': days_until,
                'message': f"【维护提醒】\n"
                          f"客户：{equipment.customer_name}\n"
                          f"设备：{equipment.equipment_type} ({equipment.equipment_no})\n"
                          f"位置：{equipment.install_location}\n"
                          f"计划维护日期：{equipment.next_maintenance_date}\n"
                          f"距今还有 {days_until} 天\n"
                          f"建议安排定期保养"
            }
            
            reminders.append(reminder)
            
            # 发送企业微信群通知
            await MaintenanceReminderService._send_group_notification(
                reminder['message'],
                equipment_id=equipment.id
            )
        
        return reminders
    
    @staticmethod
    async def check_and_send_warranty_reminders(
        db: AsyncSession,
        days_ahead: int = 30
    ) -> List[Dict]:
        """
        检查并发送保修到期提醒
        
        Args:
            db: 数据库会话
            days_ahead: 提前提醒天数
        
        Returns:
            提醒列表
        """
        # 获取保修即将到期的设备
        equipment_list = await EquipmentService.get_equipment_warranty_expiring(db, days_ahead)
        
        reminders = []
        
        for equipment in equipment_list:
            # 计算距离保修到期的天数
            days_until = (equipment.warranty_end_date - datetime.now().date()).days
            
            # 构建提醒消息
            reminder = {
                'equipment_id': equipment.id,
                'equipment_no': equipment.equipment_no,
                'equipment_type': equipment.equipment_type,
                'customer_name': equipment.customer_name,
                'customer_phone': equipment.customer_phone,
                'warranty_end_date': equipment.warranty_end_date.isoformat(),
                'days_until': days_until,
                'message': f"【保修到期提醒】\n"
                          f"客户：{equipment.customer_name}\n"
                          f"设备：{equipment.equipment_type} ({equipment.equipment_no})\n"
                          f"保修截止日期：{equipment.warranty_end_date}\n"
                          f"距今还有 {days_until} 天\n"
                          f"建议联系客户推荐延保服务"
            }
            
            reminders.append(reminder)
            
            # 发送企业微信群通知
            await MaintenanceReminderService._send_group_notification(
                reminder['message'],
                equipment_id=equipment.id
            )
        
        return reminders
    
    @staticmethod
    async def check_and_send_low_stock_alerts(
        db: AsyncSession
    ) -> List[Dict]:
        """
        检查并发送库存预警
        
        Args:
            db: 数据库会话
        
        Returns:
            预警列表
        """
        # 获取库存不足的配件
        low_stock_parts = await PartsService.get_low_stock_parts(db)
        
        alerts = []
        
        for part in low_stock_parts:
            # 构建预警消息
            alert = {
                'part_id': part.id,
                'part_code': part.part_code,
                'part_name': part.part_name,
                'stock_quantity': part.stock_quantity,
                'min_stock_alert': part.min_stock_alert,
                'supplier': part.supplier,
                'supplier_contact': part.supplier_contact,
                'message': f"【库存预警】⚠️\n"
                          f"配件：{part.part_name} ({part.part_code})\n"
                          f"当前库存：{part.stock_quantity}\n"
                          f"预警值：{part.min_stock_alert}\n"
                          f"供应商：{part.supplier}\n"
                          f"联系方式：{part.supplier_contact}\n"
                          f"建议尽快补充库存"
            }
            
            alerts.append(alert)
            
            # 发送企业微信群通知
            await MaintenanceReminderService._send_group_notification(
                alert['message'],
                alert_type='low_stock'
            )
        
        return alerts
    
    @staticmethod
    async def _send_group_notification(
        message: str,
        equipment_id: Optional[int] = None,
        alert_type: str = 'maintenance'
    ):
        """
        发送企业微信群通知
        
        Args:
            message: 消息内容
            equipment_id: 设备ID
            alert_type: 提醒类型
        """
        # TODO: 集成企业微信API发送群消息
        # 这里需要调用企业微信的群机器人API
        
        webhook_url = os.getenv("WECHAT_GROUP_WEBHOOK_URL")
        
        if not webhook_url:
            print(f"未配置企业微信群机器人Webhook URL，消息: {message}")
            return
        
        # 构建富文本卡片消息
        card_message = {
            "msgtype": "template_card",
            "template_card": {
                "card_type": "text_notice",
                "source": {
                    "icon_url": "https://...",
                    "desc": "设备维护提醒" if alert_type == 'maintenance' else "库存预警"
                },
                "main_title": {
                    "title": message.split('\n')[0]  # 第一行作为标题
                },
                "sub_title_text": "\n".join(message.split('\n')[1:]),  # 其余作为副标题
                "button_list": [
                    {
                        "text": "生成维护工单",
                        "key": f"create_maintenance_ticket_{equipment_id}" if equipment_id else "view_inventory"
                    },
                    {
                        "text": "查看详情",
                        "key": f"view_equipment_{equipment_id}" if equipment_id else "view_parts"
                    }
                ]
            }
        }
        
        # 发送HTTP请求到企业微信
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(webhook_url, json=card_message) as response:
        #         result = await response.json()
        #         print(f"发送结果: {result}")
        
        print(f"[模拟发送群通知] {message}")
