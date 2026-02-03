from fastapi import HTTPException
import re

class WeChatService:
    """企业微信服务 - 处理企业微信消息和事件"""
    
    @staticmethod
    async def process_message_event(event_data: dict) -> dict:
        """
        处理企业微信推送的消息事件
        支持文本消息和事件通知
        """
        event_type = event_data.get("MsgType", "")
        
        if event_type == "text":
            content = event_data.get("Content", "")
            return {
                "type": "text_message",
                "content": content,
                "response": await WeChatService.process_text_message(content)
            }
        elif event_type == "event":
            event = event_data.get("Event", "")
            return {
                "type": "event_notification",
                "event": event,
                "response": f"已处理事件: {event}"
            }
        else:
            raise HTTPException(status_code=400, detail=f"未知的消息类型: {event_type}")
    
    @staticmethod
    async def process_text_message(content: str) -> str:
        """处理文本消息，识别快捷命令"""
        if content.startswith("#"):
            return await WeChatService.process_command(content)
        else:
            return "收到消息，请使用快捷命令（如 #记录客户、#查询进度）"
    
    @staticmethod
    async def process_command(command: str) -> str:
        """处理快捷命令"""
        if command.startswith("#记录客户"):
            return "已记录客户信息"
        elif command.startswith("#查询进度"):
            return "正在查询项目进度..."
        elif command.startswith("#转接工程师"):
            return "已转接给工程师"
        elif command.startswith("#问题已解决"):
            return "问题已标记为已解决"
        else:
            return "未知命令，请使用正确的格式"
