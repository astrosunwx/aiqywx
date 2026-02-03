"""
智能工单交互服务
实现类似腾讯客服的双向交互工单系统：
1. @机器人创建工单
2. 富文本卡片推送
3. 消息回复监听
4. 状态自动更新
5. 超时提醒
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from datetime import datetime, timedelta
from ..models import Project, Customer
from ..utils.wechat_work_api import WeChatWorkAPI
from ..services.secure_link_service import SecureLinkService
from ..services.customer_transfer_service import CustomerTransferService
import re
import os


class TicketInteractionService:
    """工单交互服务 - 实现类似腾讯客服的双向交互"""
    
    @staticmethod
    async def handle_group_message(
        db: AsyncSession,
        message: str,
        from_user_id: str,
        from_user_name: str,
        chat_id: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        处理内部群消息
        
        支持命令：
        1. /创建工单 @客户张三 问题：服务器无法连接
        2. /查询工单 客户张三
        3. /分配工单 #123 @李四
        4. 直接回复工单消息：已解决，问题已修复
        """
        
        # 1. 识别命令类型
        if message.startswith('/创建工单'):
            return await TicketInteractionService._create_ticket_from_command(
                db, message, from_user_id, from_user_name, chat_id, wechat_api
            )
        
        elif message.startswith('/查询工单'):
            return await TicketInteractionService._query_tickets(
                db, message, from_user_id, wechat_api
            )
        
        elif message.startswith('/分配工单'):
            return await TicketInteractionService._assign_ticket(
                db, message, from_user_id, from_user_name, wechat_api
            )
        
        elif '已解决' in message or '已处理' in message or '已修复' in message:
            # 这是对工单的回复，尝试解析并更新状态
            return await TicketInteractionService._handle_ticket_reply(
                db, message, from_user_id, from_user_name, chat_id, wechat_api
            )
        
        else:
            return {
                "handled": False,
                "response": None
            }
    
    @staticmethod
    async def _create_ticket_from_command(
        db: AsyncSession,
        message: str,
        from_user_id: str,
        from_user_name: str,
        chat_id: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        从命令创建工单
        
        格式：/创建工单 @客户张三 手机:13800138000 问题：服务器无法连接
        """
        
        # 解析命令参数
        try:
            # 提取客户名称
            customer_match = re.search(r'@客户([^\s]+)', message)
            if not customer_match:
                return {
                    "handled": True,
                    "response": "❌ 格式错误，请使用：/创建工单 @客户张三 手机:13800138000 问题：无法登录"
                }
            
            customer_name = customer_match.group(1)
            
            # 提取手机号
            phone_match = re.search(r'手机[:：](\d{11})', message)
            if not phone_match:
                return {
                    "handled": True,
                    "response": f"❌ 请提供客户手机号，格式：手机:13800138000"
                }
            
            customer_phone = phone_match.group(1)
            
            # 提取问题描述
            problem_match = re.search(r'问题[:：](.+)', message)
            if not problem_match:
                return {
                    "handled": True,
                    "response": "❌ 请描述问题，格式：问题：无法登录系统"
                }
            
            problem = problem_match.group(1).strip()
            
            # 提取优先级（可选）
            priority = 'normal'
            if '紧急' in message or '严重' in message:
                priority = 'urgent'
            elif '高优先级' in message:
                priority = 'high'
            
            # 查询或创建客户
            stmt = select(Customer).where(Customer.phone == customer_phone)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
            
            if not customer:
                customer = Customer(
                    phone=customer_phone,
                    name=customer_name
                )
                db.add(customer)
                await db.flush()
            
            # 创建工单
            ticket = Project(
                customer_id=customer.id,
                customer_phone=customer_phone,
                project_type='aftersale',
                status='pending',
                priority=priority,
                title=f"售后工单 - {problem[:30]}",
                description=problem,
                assigned_to=None,  # 待分配
                progress=0,
                deadline=datetime.now() + timedelta(hours=24)  # 默认24小时期限
            )
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
            
            # 推送富文本工单通知到群
            if wechat_api:
                message_result = await TicketInteractionService._send_ticket_card(
                    ticket, customer, wechat_api, chat_id, created_by=from_user_name
                )
                
                # 保存消息ID用于后续回复监听
                if message_result.get('msg_id'):
                    ticket.group_message_id = message_result['msg_id']
                    await db.commit()
            
            return {
                "handled": True,
                "response": f"✅ 工单 #{ticket.id} 创建成功！已推送到群聊。",
                "ticket_id": ticket.id
            }
        
        except Exception as e:
            return {
                "handled": True,
                "response": f"❌ 创建工单失败：{str(e)}"
            }
    
    @staticmethod
    async def _send_ticket_card(
        ticket: Project,
        customer: Customer,
        wechat_api: WeChatWorkAPI,
        chat_id: str,
        created_by: str = None
    ) -> Dict[str, Any]:
        """
        发送工单卡片消息（仿腾讯客服样式）
        """
        
        # 状态颜色映射
        status_color = {
            'pending': '🟡',
            'assigned': '🔵',
            'processing': '🟢',
            'escalated': '🔴',
            'resolved': '✅',
            'closed': '⚫'
        }
        
        status_text = {
            'pending': '待分配',
            'assigned': '已分配',
            'processing': '处理中',
            'escalated': '已升级',
            'resolved': '已解决',
            'closed': '已关闭'
        }
        
        priority_icon = {
            'low': '⬇️',
            'normal': '➡️',
            'high': '⬆️',
            'urgent': '🚨'
        }
        
        # 生成安全查看链接
        detail_link = ""
        try:
            secure_url = SecureLinkService.generate_project_detail_link(
                user_id=created_by or 'system',
                project_id=ticket.id,
                wechat_user_id=created_by or 'system',
                expiry_hours=24
            )
            detail_link = f"\n\n📊 [查看详情]({secure_url})"
        except:
            pass
        
        # 构建Markdown消息
        content = f"""### {status_color.get(ticket.status, '⚪')} 【新工单提醒】#ID{ticket.id}

**客户信息**
> 客户：{customer.name or '未知'}
> 公司：{customer.company or '未填写'}
> 联系：{customer.phone}

**工单详情**
> 产品/项目：{ticket.title}
> 问题描述：{ticket.description}
> 优先级：{priority_icon.get(ticket.priority, '➡️')} {ticket.priority.upper()}
> 提交时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}

**处理状态**
> 当前状态：{status_text.get(ticket.status, '未知')}
> 负责人：{ticket.assigned_to_name or '待分配'}
> 处理进度：{ticket.progress}%
> 处理期限：⏰ {ticket.deadline.strftime('%Y-%m-%d %H:%M') if ticket.deadline else '24小时'}

---
💬 请负责人在本消息下回复处理进度
✅ 回复"已解决"可自动关闭工单
📋 回复"分配给@某人"可转交工单{detail_link}

🆘 <font color="warning">请在{ticket.deadline.strftime('%m月%d日 %H:%M') if ticket.deadline else '24小时'}前处理</font>
"""
        
        # 发送Markdown消息
        try:
            result = await wechat_api.send_markdown(
                content=content,
                mentioned_list=["@all"] if ticket.priority == 'urgent' else []
            )
            return result
        except Exception as e:
            print(f"⚠️  发送工单卡片失败: {e}")
            # 降级为普通文本消息
            return await wechat_api.send_text(
                content=content,
                mentioned_list=["@all"] if ticket.priority == 'urgent' else []
            )
    
    @staticmethod
    async def _query_tickets(
        db: AsyncSession,
        message: str,
        from_user_id: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        查询工单
        
        格式：
        - /查询工单 客户张三
        - /查询工单 手机13800138000
        - /查询工单 #123
        """
        
        try:
            # 提取查询参数
            if '#' in message:
                # 按工单ID查询
                ticket_id_match = re.search(r'#(\d+)', message)
                if ticket_id_match:
                    ticket_id = int(ticket_id_match.group(1))
                    stmt = select(Project).where(Project.id == ticket_id)
                    result = await db.execute(stmt)
                    tickets = [result.scalar_one_or_none()]
            
            elif re.search(r'\d{11}', message):
                # 按手机号查询
                phone = re.search(r'(\d{11})', message).group(1)
                stmt = select(Project).where(
                    and_(
                        Project.customer_phone == phone,
                        Project.project_type == 'aftersale'
                    )
                ).order_by(desc(Project.created_at)).limit(5)
                result = await db.execute(stmt)
                tickets = list(result.scalars().all())
            
            else:
                # 按客户名称查询
                customer_name_match = re.search(r'客户([^\s]+)', message)
                if customer_name_match:
                    customer_name = customer_name_match.group(1)
                    # 先查客户
                    stmt = select(Customer).where(Customer.name.like(f'%{customer_name}%'))
                    result = await db.execute(stmt)
                    customers = list(result.scalars().all())
                    
                    if not customers:
                        return {
                            "handled": True,
                            "response": f"❌ 未找到客户：{customer_name}"
                        }
                    
                    # 查询这些客户的工单
                    customer_ids = [c.id for c in customers]
                    stmt = select(Project).where(
                        and_(
                            Project.customer_id.in_(customer_ids),
                            Project.project_type == 'aftersale'
                        )
                    ).order_by(desc(Project.created_at)).limit(5)
                    result = await db.execute(stmt)
                    tickets = list(result.scalars().all())
                else:
                    return {
                        "handled": True,
                        "response": "❌ 请指定客户或工单号，例如：/查询工单 客户张三"
                    }
            
            # 过滤掉None
            tickets = [t for t in tickets if t is not None]
            
            if not tickets:
                return {
                    "handled": True,
                    "response": "未找到相关工单"
                }
            
            # 构建工单列表
            response = f"📋 查询到 {len(tickets)} 个工单：\n\n"
            
            for ticket in tickets:
                status_text = {
                    'pending': '待分配',
                    'assigned': '已分配',
                    'processing': '处理中',
                    'escalated': '已升级',
                    'resolved': '已解决',
                    'closed': '已关闭'
                }
                
                response += f"""**工单 #{ticket.id}**
状态：{status_text.get(ticket.status, '未知')} | 进度：{ticket.progress}%
问题：{ticket.description[:50]}...
负责人：{ticket.assigned_to_name or '待分配'}
创建时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}

"""
            
            return {
                "handled": True,
                "response": response,
                "tickets": tickets
            }
        
        except Exception as e:
            return {
                "handled": True,
                "response": f"❌ 查询失败：{str(e)}"
            }
    
    @staticmethod
    async def _assign_ticket(
        db: AsyncSession,
        message: str,
        from_user_id: str,
        from_user_name: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        分配工单
        
        格式：/分配工单 #123 @李四
        """
        
        try:
            # 提取工单ID
            ticket_id_match = re.search(r'#(\d+)', message)
            if not ticket_id_match:
                return {
                    "handled": True,
                    "response": "❌ 请指定工单ID，例如：/分配工单 #123 @李四"
                }
            
            ticket_id = int(ticket_id_match.group(1))
            
            # 提取负责人
            assignee_match = re.search(r'@([^\s]+)', message)
            if not assignee_match:
                return {
                    "handled": True,
                    "response": "❌ 请指定负责人，例如：/分配工单 #123 @李四"
                }
            
            assignee_name = assignee_match.group(1)
            
            # 提取assignee_userid（假设格式为 @李四(lisi) 或 @李四）
            assignee_userid_match = re.search(r'@[^\s]+\(([^\)]+)\)', message)
            assignee_userid = assignee_userid_match.group(1) if assignee_userid_match else assignee_name
            
            # 查询工单
            stmt = select(Project).where(Project.id == ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return {
                    "handled": True,
                    "response": f"❌ 工单 #{ticket_id} 不存在"
                }
            
            # ⭐ 关键：分配工单时，自动转接客户关系
            transfer_result = None
            if ticket.customer_id:
                try:
                    transfer_result = await CustomerTransferService.transfer_customer_to_engineer(
                        db=db,
                        project_id=ticket_id,
                        engineer_userid=assignee_userid,
                        engineer_name=assignee_name,
                        wechat_api=wechat_api
                    )
                except Exception as e:
                    # 转接失败不影响工单分配
                    print(f"⚠️ 客户转接失败，但工单已分配：{str(e)}")
            
            # 更新负责人
            ticket.assigned_to = assignee_userid
            ticket.assigned_to_name = assignee_name
            ticket.status = 'assigned'
            ticket.updated_at = datetime.now()
            ticket.transfer_reason = f"工单分配给 {assignee_name}"
            
            await db.commit()
            
            response_msg = f"✅ 工单 #{ticket_id} 已分配给 @{assignee_name}"
            if transfer_result and transfer_result.get('success'):
                response_msg += f"\n🔄 客户关系已自动转接给 @{assignee_name}（对客户无感知）"
            
            return {
                "handled": True,
                "response": response_msg,
                "ticket_id": ticket_id,
                "transfer_result": transfer_result
            }
        
        except Exception as e:
            return {
                "handled": True,
                "response": f"❌ 分配失败：{str(e)}"
            }
    
    @staticmethod
    async def _handle_ticket_reply(
        db: AsyncSession,
        message: str,
        from_user_id: str,
        from_user_name: str,
        chat_id: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        处理工单回复（自动更新状态）
        
        当员工回复"已解决"、"已处理"等关键词时，自动更新工单状态
        """
        
        # 这里需要根据消息ID关联到具体工单
        # 简化处理：尝试从消息中提取工单ID
        ticket_id_match = re.search(r'#(\d+)', message)
        
        if not ticket_id_match:
            # 如果消息中没有工单ID，返回提示
            return {
                "handled": False,
                "response": "💡 提示：请在回复中包含工单号，例如：#123 已解决"
            }
        
        ticket_id = int(ticket_id_match.group(1))
        
        try:
            stmt = select(Project).where(Project.id == ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                return {
                    "handled": True,
                    "response": f"❌ 工单 #{ticket_id} 不存在"
                }
            
            # 更新状态
            if '已解决' in message or '已修复' in message:
                ticket.status = 'resolved'
                ticket.progress = 100
                status_text = "已解决"
                
                # ⭐ 关键：工单解决后，自动将客户关系转回原销售
                transfer_back_result = None
                if ticket.customer_id and ticket.original_sales_userid:
                    try:
                        transfer_back_result = await CustomerTransferService.transfer_customer_back_to_sales(
                            db=db,
                            project_id=ticket_id,
                            wechat_api=wechat_api
                        )
                    except Exception as e:
                        print(f"⚠️ 客户转回失败：{str(e)}")
                
            elif '已处理' in message:
                ticket.status = 'processing'
                ticket.progress = 80
                status_text = "处理中"
                transfer_back_result = None
            elif '升级' in message:
                ticket.status = 'escalated'
                status_text = "已升级"
                transfer_back_result = None
            else:
                return {"handled": False}
            
            ticket.updated_at = datetime.now()
            await db.commit()
            
            response_msg = f"✅ 工单 #{ticket_id} 状态已更新为：{status_text}"
            if transfer_back_result and transfer_back_result.get('success'):
                response_msg += f"\n🔄 客户关系已自动转回原销售（对客户无感知）"
            
            return {
                "handled": True,
                "response": response_msg,
                "ticket_id": ticket_id,
                "new_status": ticket.status,
                "transfer_back_result": transfer_back_result
            }
        
        except Exception as e:
            return {
                "handled": True,
                "response": f"❌ 更新失败：{str(e)}"
            }
