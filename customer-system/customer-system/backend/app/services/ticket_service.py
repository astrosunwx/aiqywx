"""自动工单服务 - 智能识别并生成工单"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Project, Customer
from app.services.conversation_state import conversation_state
from app.services.secure_link_service import SecureLinkService
from app.utils.wechat_work_api import WeChatWorkAPI, GroupBotAPI
import re
import os


class TicketService:
    """工单自动生成服务"""
    
    @staticmethod
    async def process_customer_message(
        db: AsyncSession,
        user_id: str,
        message: str,
        wechat_api: WeChatWorkAPI = None
    ) -> dict:
        """
        处理客户消息，自动识别意图并生成工单
        支持多轮对话收集信息
        支持多项目自动识别
        """
        from sqlalchemy import select
        
        # 获取当前对话状态
        state = conversation_state.get_state(user_id)
        
        # 1. 识别关键词
        if any(keyword in message for keyword in ['售后', '维修', '坏了', '不工作', '问题']):
            if not state or state['intent'] != 'aftersale':
                # 开始售后流程
                conversation_state.set_state(user_id, 'aftersale', {})
                return {
                    "response": "好的，正在为您创建售后工单。请问具体是什么产品出现了问题？（如：无法安装/页面白屏/报错提示等）",
                    "next_step": "collect_problem"
                }
            
            # 收集问题描述
            if 'problem' not in state['data']:
                conversation_state.update_state(user_id, 'problem', message)
                return {
                    "response": "收到。请提供一下您的手机号，方便我们快速查询您的订单。",
                    "next_step": "collect_phone"
                }
            
            # 收集手机号
            if 'phone' not in state['data']:
                phone = extract_phone(message)
                if phone:
                    conversation_state.update_state(user_id, 'phone', phone)
                    
                    # 自动创建工单
                    ticket = await TicketService.create_auto_ticket(
                        db=db,
                        phone=phone,
                        problem=state['data']['problem'],
                        user_id=user_id
                    )
                    
                    # 清除状态
                    conversation_state.clear_state(user_id)
                    
                    # 推送到内部群（带安全链接）
                    if os.getenv("GROUP_WEBHOOK_URL"):
                        await TicketService.notify_internal_group(ticket, wechat_user_id=user_id)
                    
                    # 生成客户专属查看链接（1小时有效）
                    customer_link = SecureLinkService.generate_project_detail_link(
                        user_id=user_id,
                        project_id=ticket.id,
                        wechat_user_id=user_id,
                        expiry_hours=1
                    )
                    
                    return {
                        "response": f"信息已记录！工单号SV{ticket.id}已创建，技术支持将在30分钟内联系您。\n\n📊 查看详情：{customer_link}",
                        "ticket_id": ticket.id,
                        "detail_link": customer_link,
                        "completed": True
                    }
                else:
                    return {
                        "response": "请提供正确的手机号（11位数字）",
                        "next_step": "collect_phone"
                    }
        
        # 2. 识别售前咨询
        elif any(keyword in message for keyword in ['售前', '咨询', '购买', '价格', '报价']):
            if not state or state['intent'] != 'presale':
                conversation_state.set_state(user_id, 'presale', {})
                return {
                    "response": "好的，请问您对哪个产品感兴趣？",
                    "next_step": "collect_product"
                }
            
            if 'product' not in state['data']:
                conversation_state.update_state(user_id, 'product', message)
                return {
                    "response": "收到。请留下您的手机号，我们的销售顾问会尽快联系您。",
                    "next_step": "collect_phone"
                }
            
            if 'phone' not in state['data']:
                phone = extract_phone(message)
                if phone:
                    # 创建售前项目
                    project = await TicketService.create_presale_project(
                        db=db,
                        phone=phone,
                        product=state['data']['product']
                    )
                    conversation_state.clear_state(user_id)
                    return {
                        "response": f"感谢您的咨询！我们的销售顾问会在1小时内联系您（手机号：{phone}）。",
                        "project_id": project.id,
                        "completed": True
                    }
        
        # 3. 查询进度
        elif any(keyword in message for keyword in ['进度', '状态', '怎么样了', '到哪了']):
            phone = extract_phone(message)
            if phone:
                # 查询项目
                from app.services.project_service import ProjectService
                projects = await ProjectService.get_projects_by_phone(db, phone)
                
                if projects:
                    result = f"您的项目进度：\n"
                    for p in projects:
                        status_map = {
                            'pending': '待处理',
                            'contacted': '已联系',
                            'processing': '处理中',
                            'completed': '已完成'
                        }
                        result += f"• {p.title}: {status_map.get(p.status, p.status)}\n"
                    return {"response": result}
                else:
                    return {"response": f"未找到手机号 {phone} 的相关记录。"}
            else:
                return {"response": "请提供您的手机号以便查询项目进度。"}
        
        # 默认回复
        return {
            "response": "您好！我是智能客服助手。\n您可以咨询：\n• 售前咨询\n• 售后服务\n• 查询进度"
        }
    
    @staticmethod
    async def create_auto_ticket(db: AsyncSession, phone: str, problem: str, user_id: str) -> Project:
        """自动创建售后工单"""
        from sqlalchemy import select
        
        # 检查客户是否存在
        result = await db.execute(select(Customer).where(Customer.phone == phone))
        customer = result.scalar_one_or_none()
        
        if not customer:
            # 创建新客户
            customer = Customer(phone=phone, wechat_openid=user_id)
            db.add(customer)
            await db.flush()
        
        # 创建工单
        ticket = Project(
            customer_phone=phone,
            project_type='aftersale',
            status='pending',
            title=f"售后服务 - {problem[:20]}",
            description=problem
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        return ticket
    
    @staticmethod
    async def create_presale_project(db: AsyncSession, phone: str, product: str) -> Project:
        """创建售前项目"""
        from sqlalchemy import select
        
        result = await db.execute(select(Customer).where(Customer.phone == phone))
        customer = result.scalar_one_or_none()
        
        if not customer:
            customer = Customer(phone=phone)
            db.add(customer)
            await db.flush()
        
        project = Project(
            customer_phone=phone,
            project_type='presale',
            status='contacted',
            title=f"售前咨询 - {product}",
            description=f"客户咨询产品：{product}"
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return project
    
    @staticmethod
    async def notify_internal_group(ticket: Project, wechat_user_id: str = None):
        """
        推送工单到内部群（包含安全详情链接）
        
        Args:
            ticket: 工单项目
            wechat_user_id: 企业微信用户ID（用于生成安全链接）
        """
        webhook_url = os.getenv("GROUP_WEBHOOK_URL")
        if not webhook_url:
            return
        
        bot = GroupBotAPI(webhook_url)
        
        # 生成安全查看链接（24小时有效）
        detail_link = ""
        if wechat_user_id:
            try:
                secure_url = SecureLinkService.generate_project_detail_link(
                    user_id=wechat_user_id,
                    project_id=ticket.id,
                    wechat_user_id=wechat_user_id,
                    expiry_hours=24  # 内部链接24小时有效
                )
                detail_link = f"\n\n📊 查看详情：{secure_url}"
            except Exception as e:
                print(f"⚠️  生成安全链接失败: {e}")
        
        content = f"""【自动创建工单】🔧
工单号：SV{ticket.id}
客户：{ticket.customer_phone}
联系：{ticket.customer_phone}
项目：售后服务
问题：{ticket.description}
处理状态：待分配
创建时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}{detail_link}

请相关人员尽快处理。"""
        
        await bot.send_text(content=content, mentioned_list=["@all"])


def extract_phone(text: str) -> str:
    """从文本中提取手机号"""
    pattern = r'1[3-9]\d{9}'
    match = re.search(pattern, text)
    return match.group(0) if match else None
