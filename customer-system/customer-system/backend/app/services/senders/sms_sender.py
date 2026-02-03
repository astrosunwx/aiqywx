"""短信发送器 - 占位符"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SMSSender:
    def __init__(self, db_pool):
        self.db = db_pool
    
    async def send(self, config: Dict, Any], recipient: str, content: str,
                   subject: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """发送短信"""
        logger.info(f"短信: recipient={recipient}")
        # TODO: 实现短信发送（阿里云/腾讯云/华为云）
        return {"success": True}
