from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.wechat_service import WeChatService
from app.services.project_service import ProjectService
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()

class CommandRequest(BaseModel):
    command: str
    session_id: str
    employee_id: int

class WeChatMessageEvent(BaseModel):
    ToUserName: str
    FromUserName: str
    MsgType: str
    Content: Optional[str] = None
    Event: Optional[str] = None

@router.post("/api/wechat/work/command")
async def handle_work_command(request: CommandRequest, db: AsyncSession = Depends(get_db)):
    """
    处理企业微信员工发送的快捷命令
    支持命令: #记录客户 #查询进度 #转接工程师 #完成处理
    """
    if not request.command:
        raise HTTPException(status_code=400, detail="命令不能为空")

    command = request.command.strip()
    
    # #记录客户 手机号138xxxx 意向产品空调
    if command.startswith("#记录客户"):
        parts = command.split()
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="命令格式错误，应为: #记录客户 手机号 产品名称")
        
        phone = parts[1].replace("手机号", "")
        product = " ".join(parts[2:]).replace("意向产品", "")
        
        # 创建售前项目
        project_data = {
            "customer_phone": phone,
            "project_type": "presale",
            "status": "contacted",
            "title": f"{product} - 售前咨询",
            "sales_id": request.employee_id
        }
        project = await ProjectService.create_project(db, project_data)
        
        return {
            "response": f"已记录客户 {phone}，创建售前项目ID: {project.id}",
            "project_id": project.id
        }
    
    # #查询进度 手机号138xxxx
    elif command.startswith("#查询进度"):
        parts = command.split()
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="命令格式错误，应为: #查询进度 手机号")
        
        phone = parts[1].replace("手机号", "")
        projects = await ProjectService.get_projects_by_phone(db, phone, request.employee_id)
        
        if not projects:
            return {"response": f"未找到手机号 {phone} 的项目记录"}
        
        result = f"手机号 {phone} 的项目进度：\n"
        for p in projects:
            result += f"- 项目ID {p.id}: {p.title} ({p.status})\n"
        
        return {"response": result, "projects": [{"id": p.id, "title": p.title, "status": p.status} for p in projects]}
    
    # #转接工程师 项目ID123 问题描述XXX
    elif command.startswith("#转接工程师"):
        parts = command.split(maxsplit=2)
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="命令格式错误，应为: #转接工程师 项目ID 问题描述")
        
        project_id = int(parts[1].replace("项目ID", ""))
        issue = parts[2].replace("问题描述", "")
        
        # 更新项目状态
        project = await ProjectService.update_project_status(db, project_id, "processing")
        
        return {
            "response": f"项目ID {project_id} 已转接给工程师，问题: {issue}",
            "action": "notify_engineer"
        }
    
    # #问题已解决
    elif command.startswith("#问题已解决"):
        return {
            "response": "问题已标记为已解决",
            "action": "notify_customer"
        }
    
    else:
        raise HTTPException(status_code=400, detail="未知命令，支持的命令: #记录客户、#查询进度、#转接工程师、#问题已解决")


@router.post("/api/wechat/work-message")
async def handle_wechat_message(event_data: WeChatMessageEvent, db: AsyncSession = Depends(get_db)):
    """
    接收企业微信推送的消息事件
    
    支持功能：
    1. 自动工单生成和多轮对话
    2. 内部群@机器人命令（/创建工单、/查询工单、/分配工单）
    3. 工单回复监听（"#123 已解决"）
    """
    from app.services.ticket_service import TicketService
    from app.services.ticket_interaction_service import TicketInteractionService
    from app.utils.wechat_work_api import WeChatWorkAPI
    
    # 如果是文本消息
    if event_data.MsgType == "text" and event_data.Content:
        user_id = event_data.FromUserName
        message = event_data.Content
        
        # 检查是否是内部群消息（包含命令）
        if message.startswith('/'):
            # 内部群命令处理（需要额外的参数：from_user_name, chat_id）
            # 这里简化处理，实际需要从企业微信事件中获取
            from_user_name = event_data.FromUserName  # 实际应该是用户昵称
            chat_id = "internal_group_id"  # 实际应该从事件中获取
            
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
            
            result = await TicketInteractionService.handle_group_message(
                db=db,
                message=message,
                from_user_id=user_id,
                from_user_name=from_user_name,
                chat_id=chat_id,
                wechat_api=wechat_api
            )
            
            if result.get('handled'):
                return {
                    "type": "command_response",
                    "response": result.get("response"),
                    "data": result
                }
        
        # 工单回复监听（包含#工单号）
        if '#' in message and any(kw in message for kw in ['已解决', '已处理', '已修复', '升级']):
            from_user_name = event_data.FromUserName
            chat_id = "internal_group_id"
            
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
            
            result = await TicketInteractionService._handle_ticket_reply(
                db=db,
                message=message,
                from_user_id=user_id,
                from_user_name=from_user_name,
                chat_id=chat_id,
                wechat_api=wechat_api
            )
            
            if result.get('handled'):
                return {
                    "type": "ticket_update",
                    "response": result.get("response"),
                    "data": result
                }
        
        # 默认：自动工单生成（多轮对话）
        result = await TicketService.process_customer_message(
            db=db,
            user_id=user_id,
            message=message
        )
        
        return {
            "type": "auto_response",
            "response": result.get("response"),
            "data": result
        }
    
    # 其他消息类型使用原有逻辑
    response = await WeChatService.process_message_event(event_data.dict())
    return response


@router.get("/api/wechat/sidebar-data")
async def get_sidebar_data(customer_wechat_id: str, employee_id: int, db: AsyncSession = Depends(get_db)):
    """
    根据当前聊天对象（客户）返回相关的项目信息
    提供快速操作按钮（创建项目、查询进度、转接处理）
    """
    if not customer_wechat_id:
        raise HTTPException(status_code=400, detail="客户微信ID不能为空")

    # TODO: 根据customer_wechat_id查询客户信息和项目
    # 这里返回示例数据
    return {
        "customer_name": "张三",
        "customer_phone": "138xxxx1234",
        "projects": [
            {"id": 123, "title": "空调安装", "status": "processing", "type": "installation"},
            {"id": 124, "title": "售后维修", "status": "pending", "type": "aftersale"}
        ],
        "actions": [
            {"label": "创建项目", "action": "create_project", "command": "#记录客户"},
            {"label": "查询进度", "action": "query_progress", "command": "#查询进度"},
            {"label": "转接处理", "action": "transfer", "command": "#转接工程师"}
        ]
    }


@router.post("/api/wechat/group-bot-notify")
async def group_bot_notify(group_webhook_url: str, message: str, mentioned_list: list = None):
    """
    通过群机器人向指定内部群推送结构化消息
    支持操作按钮（如"我来处理"、"转交他人"）
    """
    from app.services.group_bot_service import GroupBotService
    
    result = await GroupBotService.send_group_notification(
        group_webhook_url=group_webhook_url,
        message=message,
        mentioned_list=mentioned_list
    )
    return result
