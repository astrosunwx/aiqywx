"""
群机器人发送器
Group Bot Sender

功能：
- 发送消息到企业微信群机器人
- 支持文本、Markdown、图文消息
"""

import aiohttp
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GroupBotSender:
    """群机器人发送器"""
    
    def __init__(self, db_pool):
        """
        初始化
        
        Args:
            db_pool: 数据库连接池
        """
        self.db = db_pool
    
    async def send(
        self,
        config: Dict[str, Any],
        recipient: str,
        content: str,
        subject: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送消息到群机器人
        
        Args:
            config: 渠道配置
                {
                    "bots": [
                        {
                            "bot_id": "bot_001",
                            "bot_name": "售后服务群",
                            "group_id": "wrXXXXXXXXXXXX",
                            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx"
                        }
                    ]
                }
            recipient: 群ID
            content: 消息内容
            subject: 主题（可选）
            metadata: 元数据（可选）
        
        Returns:
            发送结果
        """
        try:
            # 查找对应的群机器人配置
            bot_config = None
            for bot in config.get("bots", []):
                if bot["group_id"] == recipient:
                    bot_config = bot
                    break
            
            if not bot_config:
                raise ValueError(f"未找到群ID对应的机器人配置: {recipient}")
            
            webhook_url = bot_config["webhook_url"]
            
            # 构建消息体
            message_body = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
            # 发送HTTP请求
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message_body) as response:
                    result = await response.json()
                    
                    if result.get("errcode") != 0:
                        raise Exception(f"群机器人返回错误: {result.get('errmsg')}")
                    
                    logger.info(f"群机器人消息发送成功: group_id={recipient}")
                    
                    return {
                        "success": True,
                        "response": result
                    }
        
        except Exception as e:
            logger.error(f"群机器人消息发送失败: {e}")
            raise
