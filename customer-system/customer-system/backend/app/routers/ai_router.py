from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.ai_service import AIService
from pydantic import BaseModel

router = APIRouter()

class RouterRequest(BaseModel):
    message: str
    source: str  # 'wechat_official' or 'wechat_work'
    user_id: str
    session_id: str = None

@router.post("/api/ai/router")
async def intelligent_router(request_data: RouterRequest, db: AsyncSession = Depends(get_db)):
    """
    统一处理公众号和企业微信入口的消息
    支持多轮对话状态管理
    """
    if not request_data.message:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # 1. AI解析意图
    intent_result = await AIService.parse_intent(request_data.message)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]
    
    # 2. 提取关键信息（如手机号）
    phone = await AIService.extract_phone(request_data.message)
    
    # 3. 根据意图执行相应的业务逻辑
    if intent == "presale":
        return {
            "intent": intent,
            "confidence": confidence,
            "response": "您好！我们的售前团队将尽快与您联系。请问您对哪款产品感兴趣？",
            "next_action": "collect_product_info"
        }
    elif intent == "aftersale":
        return {
            "intent": intent,
            "confidence": confidence,
            "response": "我们将为您安排售后服务。请描述您遇到的具体问题。",
            "next_action": "collect_issue_info"
        }
    elif intent == "query":
        if phone:
            return {
                "intent": intent,
                "confidence": confidence,
                "response": f"正在查询手机号 {phone} 的项目进度...",
                "next_action": "query_projects",
                "phone": phone
            }
        else:
            return {
                "intent": intent,
                "confidence": confidence,
                "response": "请提供您的手机号以便查询项目进度。",
                "next_action": "collect_phone"
            }
    else:
        return {
            "intent": "unknown",
            "confidence": confidence,
            "response": "抱歉，我没有理解您的意图。您可以咨询售前、售后或查询项目进度。",
            "next_action": "clarify_intent"
        }
