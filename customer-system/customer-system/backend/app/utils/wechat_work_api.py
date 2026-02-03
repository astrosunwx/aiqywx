"""企业微信API集成服务 - 完整实现"""
import httpx
import hashlib
import time
from typing import Optional
from fastapi import HTTPException


class WeChatWorkAPI:
    """企业微信API客户端"""
    
    def __init__(self, corp_id: str, secret: str, agent_id: int):
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        self._access_token = None
        self._token_expires_at = 0
    
    async def get_access_token(self) -> str:
        """获取访问令牌（带缓存）"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        url = f"{self.base_url}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("errcode") != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"获取access_token失败: {data.get('errmsg')}"
                )
            
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + 7000  # 提前200秒过期
            return self._access_token
    
    async def send_text_message(self, user_id: str, content: str) -> dict:
        """发送文本消息"""
        access_token = await self.get_access_token()
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": content
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()
    
    async def send_card_message(
        self,
        user_id: str,
        title: str,
        description: str,
        url: str,
        btn_text: str = "查看详情"
    ) -> dict:
        """发送卡片消息"""
        access_token = await self.get_access_token()
        api_url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": user_id,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btn_text
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=data)
            return response.json()
    
    async def send_markdown_message(self, user_id: str, content: str) -> dict:
        """发送Markdown消息"""
        access_token = await self.get_access_token()
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": user_id,
            "msgtype": "markdown",
            "agentid": self.agent_id,
            "markdown": {
                "content": content
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()
    
    async def get_user_info(self, user_id: str) -> dict:
        """获取成员详情"""
        access_token = await self.get_access_token()
        url = f"{self.base_url}/user/get"
        params = {
            "access_token": access_token,
            "userid": user_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()
    
    async def get_external_contact(self, external_userid: str) -> dict:
        """获取外部联系人详情"""
        access_token = await self.get_access_token()
        url = f"{self.base_url}/externalcontact/get"
        params = {
            "access_token": access_token,
            "external_userid": external_userid
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()


class GroupBotAPI:
    """企业微信群机器人API"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_text(self, content: str, mentioned_list: list = None) -> dict:
        """发送文本消息"""
        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or []
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=data)
            return response.json()
    
    async def send_markdown(self, content: str) -> dict:
        """发送Markdown消息"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=data)
            return response.json()
    
    async def send_news(self, articles: list) -> dict:
        """发送图文消息"""
        data = {
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=data)
            return response.json()


def verify_signature(token: str, timestamp: str, nonce: str, signature: str) -> bool:
    """验证企业微信消息签名"""
    params = sorted([token, timestamp, nonce])
    params_str = ''.join(params)
    hash_obj = hashlib.sha1(params_str.encode('utf-8'))
    return hash_obj.hexdigest() == signature


# 使用示例
"""
# 初始化API客户端
import os

wechat_api = WeChatWorkAPI(
    corp_id=os.getenv("WECHAT_WORK_CORP_ID"),
    secret=os.getenv("WECHAT_WORK_SECRET"),
    agent_id=int(os.getenv("WECHAT_WORK_AGENT_ID"))
)

# 发送消息
await wechat_api.send_text_message(
    user_id="zhangsan",
    content="您好，您的工单已处理完成"
)

# 发送卡片
await wechat_api.send_card_message(
    user_id="zhangsan",
    title="新工单提醒",
    description="客户张三提交了售后工单，请及时处理",
    url="https://your-domain.com/order/123"
)

# 群机器人
bot = GroupBotAPI(webhook_url=os.getenv("GROUP_WEBHOOK_URL"))
await bot.send_text(
    content="项目ID 123 需要技术支持",
    mentioned_list=["@all"]
)
"""
