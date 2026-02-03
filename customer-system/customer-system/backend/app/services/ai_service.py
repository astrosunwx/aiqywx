from fastapi import HTTPException
import re

class AIService:
    """AI智能服务 - 处理意图识别和智能问答"""
    
    @staticmethod
    async def parse_intent(message: str) -> dict:
        """
        解析用户消息的意图
        支持的意图：售前咨询、售后服务、进度查询
        """
        message_lower = message.lower()
        
        # 售前咨询关键词
        presale_keywords = ['售前', '咨询', '购买', '价格', '报价', '产品', '空调', '冰箱']
        # 售后服务关键词
        aftersale_keywords = ['售后', '维修', '故障', '问题', '坏了', '不工作']
        # 查询进度关键词
        query_keywords = ['查询', '进度', '状态', '怎么样', '到哪了']
        
        if any(keyword in message_lower for keyword in presale_keywords):
            return {"intent": "presale", "confidence": 0.9}
        elif any(keyword in message_lower for keyword in aftersale_keywords):
            return {"intent": "aftersale", "confidence": 0.9}
        elif any(keyword in message_lower for keyword in query_keywords):
            return {"intent": "query", "confidence": 0.85}
        else:
            return {"intent": "unknown", "confidence": 0.5}
    
    @staticmethod
    async def extract_phone(message: str) -> str:
        """从消息中提取手机号"""
        phone_pattern = r'1[3-9]\d{9}'
        match = re.search(phone_pattern, message)
        return match.group(0) if match else None
