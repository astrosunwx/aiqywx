from fastapi import HTTPException
import httpx

class GroupBotService:
    """内部群机器人服务"""
    
    @staticmethod
    async def send_group_notification(group_webhook_url: str, message: str, mentioned_list: list = None) -> dict:
        """
        通过群机器人向指定内部群推送结构化消息
        支持@成员和操作按钮
        """
        if not group_webhook_url or not message:
            raise HTTPException(status_code=400, detail="群webhook URL和消息内容不能为空")
        
        # 构建企业微信群机器人消息格式
        payload = {
            "msgtype": "text",
            "text": {
                "content": message,
                "mentioned_list": mentioned_list or []
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(group_webhook_url, json=payload)
                response.raise_for_status()
                return {"status": "success", "message": "消息已发送"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"发送群消息失败: {str(e)}")
    
    @staticmethod
    async def send_interactive_card(group_webhook_url: str, title: str, description: str, buttons: list) -> dict:
        """
        发送带操作按钮的卡片消息
        """
        payload = {
            "msgtype": "template_card",
            "template_card": {
                "card_type": "text_notice",
                "source": {
                    "desc": "智能售前售后系统"
                },
                "main_title": {
                    "title": title
                },
                "sub_title_text": description,
                "horizontal_content_list": buttons
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(group_webhook_url, json=payload)
                response.raise_for_status()
                return {"status": "success", "message": "卡片消息已发送"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"发送卡片消息失败: {str(e)}")
