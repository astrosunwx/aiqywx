"""
售后服务处理模块
支持客户在公众号或企业微信提交售后请求，自动匹配项目并推送给员工
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from app.models import AfterSalesTicket, Customer, Project, OrderModification
from app.services.wechat_service import WeChatService
from typing import Dict, List, Optional
from datetime import datetime
import logging
import secrets

logger = logging.getLogger(__name__)


class AfterSalesService:
    """售后服务处理服务"""
    
    @staticmethod
    async def create_ticket(
        db: AsyncSession,
        customer_phone: str,
        ticket_type: str,
        subject: str,
        description: str,
        source: str = 'wechat',
        source_openid: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict:
        """
        创建售后工单
        
        流程：
        1. 验证客户是否为可信用户（is_verified=True）
        2. 自动匹配客户的项目（优先最近的项目）
        3. 生成工单编号
        4. 自动分配给项目负责人
        5. 推送通知到企业微信
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            ticket_type: 工单类型（maintenance/repair/complaint/consultation/return/refund）
            subject: 工单主题
            description: 详细描述
            source: 来源（wechat/wework/web）
            source_openid: 公众号OpenID或企业微信ExternalUserID
            attachments: 附件列表
        
        Returns:
            Dict: 创建结果
        """
        try:
            # 1. 验证客户身份和权限
            from app.services.prospect_service import CustomerTypeService
            
            permission_check = await CustomerTypeService.check_customer_permission(
                db, customer_phone, 'submit_aftersales'
            )
            
            if not permission_check['has_permission']:
                return {
                    'success': False,
                    'message': permission_check['message'],
                    'reason': permission_check['reason'],
                    'need_verification': permission_check.get('need_verification', False)
                }
            
            customer_id = permission_check['customer_id']
            
            # 查找客户详细信息
            result = await db.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_null()
            
            if not customer:
                return {
                    'success': False,
                    'message': '客户信息不存在'
                }
            
            # 2. 自动匹配项目（只匹配客户自己的项目）
            project = await AfterSalesService._match_project(db, customer.id)
            
            if not project:
                return {
                    'success': False,
                    'message': '未找到关联的项目，请联系客服'
                }
            
            # 3. 生成工单编号
            ticket_no = f"AS{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"
            
            # 4. 创建工单
            ticket = AfterSalesTicket(
                ticket_no=ticket_no,
                customer_id=customer.id,
                customer_phone=customer_phone,
                customer_name=customer.name,
                project_id=project.id,
                project_title=project.title,
                ticket_type=ticket_type,
                subject=subject,
                description=description,
                attachments=attachments or [],
                status='pending',
                priority=AfterSalesService._calculate_priority(ticket_type),
                assigned_to=project.assigned_to or customer.sales_representative,
                assigned_to_name=project.assigned_to_name or customer.sales_representative_name,
                assigned_at=datetime.now(),
                source=source,
                source_openid=source_openid,
                created_at=datetime.now()
            )
            
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
            
            logger.info(f"售后工单创建成功: {ticket_no}, 客户: {customer_phone}")
            
            # 5. 推送通知到企业微信
            await AfterSalesService._send_notification(db, ticket, project)
            
            return {
                'success': True,
                'message': '工单已提交，我们会尽快处理',
                'ticket_no': ticket_no,
                'ticket_id': ticket.id,
                'assigned_to': ticket.assigned_to_name,
                'project_link': project.generate_project_link('https://yourdomain.com')
            }
            
        except Exception as e:
            logger.error(f"创建售后工单失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'提交失败: {str(e)}'
            }
    
    @staticmethod
    async def _match_project(db: AsyncSession, customer_id: int) -> Optional[Project]:
        """
        自动匹配客户项目
        优先级：最近更新的、状态为进行中的项目
        """
        result = await db.execute(
            select(Project)
            .where(Project.customer_id == customer_id)
            .order_by(desc(Project.created_at))
        )
        projects = result.scalars().all()
        
        if not projects:
            return None
        
        # 优先返回进行中的项目
        for project in projects:
            if project.status in ['in_progress', 'pending', 'signed']:
                return project
        
        # 否则返回最新的项目
        return projects[0]
    
    @staticmethod
    def _calculate_priority(ticket_type: str) -> str:
        """
        根据工单类型计算优先级
        """
        priority_map = {
            'complaint': 'urgent',    # 投诉：紧急
            'repair': 'high',         # 维修：高
            'return': 'high',         # 退货：高
            'refund': 'high',         # 退款：高
            'maintenance': 'normal',  # 保养：普通
            'consultation': 'low'     # 咨询：低
        }
        return priority_map.get(ticket_type, 'normal')
    
    @staticmethod
    async def _send_notification(
        db: AsyncSession,
        ticket: AfterSalesTicket,
        project: Project
    ):
        """
        推送通知到企业微信
        
        通知对象：
        1. 项目负责人
        2. 销售代表
        3. 内部工作群
        """
        try:
            # 生成项目详情链接
            project_link = project.generate_project_link('https://yourdomain.com')
            
            # 构建消息内容
            message = f"""
【售后工单提醒】
工单号：{ticket.ticket_no}
客户：{ticket.customer_name}（{ticket.customer_phone}）
项目：{ticket.project_title}
类型：{AfterSalesService._get_ticket_type_name(ticket.ticket_type)}
主题：{ticket.subject}
描述：{ticket.description}
优先级：{AfterSalesService._get_priority_name(ticket.priority)}

📋 项目详情：{project_link}

请尽快处理！
            """.strip()
            
            # 推送给负责人
            if ticket.assigned_to:
                await WeChatService.send_text_message(
                    ticket.assigned_to,
                    message
                )
                logger.info(f"已推送通知给负责人: {ticket.assigned_to}")
            
            # 推送到内部群（如果配置了）
            # await WeChatService.send_group_message('售后工作群ID', message)
            
            # 更新推送状态
            ticket.notification_sent = True
            ticket.notification_sent_at = datetime.now()
            await db.commit()
            
        except Exception as e:
            logger.error(f"推送通知失败: {str(e)}", exc_info=True)
    
    @staticmethod
    def _get_ticket_type_name(ticket_type: str) -> str:
        """工单类型中文名称"""
        type_map = {
            'maintenance': '设备保养',
            'repair': '维修服务',
            'complaint': '投诉建议',
            'consultation': '咨询服务',
            'return': '退货申请',
            'refund': '退款申请'
        }
        return type_map.get(ticket_type, ticket_type)
    
    @staticmethod
    def _get_priority_name(priority: str) -> str:
        """优先级中文名称"""
        priority_map = {
            'low': '低',
            'normal': '普通',
            'high': '高',
            'urgent': '紧急'
        }
        return priority_map.get(priority, priority)
    
    @staticmethod
    async def get_customer_tickets(
        db: AsyncSession,
        customer_phone: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        查询客户的售后工单
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            status: 工单状态筛选（可选）
        
        Returns:
            List[Dict]: 工单列表
        """
        try:
            query = select(AfterSalesTicket).where(
                AfterSalesTicket.customer_phone == customer_phone
            )
            
            if status:
                query = query.where(AfterSalesTicket.status == status)
            
            query = query.order_by(desc(AfterSalesTicket.created_at))
            
            result = await db.execute(query)
            tickets = result.scalars().all()
            
            return [
                {
                    'ticket_no': t.ticket_no,
                    'ticket_type': AfterSalesService._get_ticket_type_name(t.ticket_type),
                    'subject': t.subject,
                    'status': t.status,
                    'priority': t.priority,
                    'assigned_to_name': t.assigned_to_name,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                    'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None,
                    'project_title': t.project_title
                }
                for t in tickets
            ]
            
        except Exception as e:
            logger.error(f"查询工单失败: {str(e)}")
            return []
    
    @staticmethod
    async def update_ticket_status(
        db: AsyncSession,
        ticket_no: str,
        status: str,
        operator_userid: str,
        response_content: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> Dict:
        """
        更新工单状态
        
        Args:
            db: 数据库会话
            ticket_no: 工单编号
            status: 新状态
            operator_userid: 操作人UserID
            response_content: 回复内容
            resolution: 解决方案
        
        Returns:
            Dict: 更新结果
        """
        try:
            result = await db.execute(
                select(AfterSalesTicket).where(
                    AfterSalesTicket.ticket_no == ticket_no
                )
            )
            ticket = result.scalar_one_or_null()
            
            if not ticket:
                return {'success': False, 'message': '工单不存在'}
            
            ticket.status = status
            
            if response_content:
                ticket.response_content = response_content
            
            if resolution:
                ticket.resolution = resolution
            
            if status == 'resolved':
                ticket.resolved_at = datetime.now()
            elif status == 'closed':
                ticket.closed_at = datetime.now()
            
            ticket.updated_at = datetime.now()
            
            await db.commit()
            
            logger.info(f"工单状态更新: {ticket_no} -> {status}")
            
            # 推送状态更新通知给客户
            await AfterSalesService._notify_customer_status_update(db, ticket)
            
            return {
                'success': True,
                'message': '状态更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新工单状态失败: {str(e)}")
            await db.rollback()
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
    
    @staticmethod
    async def _notify_customer_status_update(db: AsyncSession, ticket: AfterSalesTicket):
        """通知客户工单状态更新"""
        try:
            result = await db.execute(
                select(Customer).where(Customer.id == ticket.customer_id)
            )
            customer = result.scalar_one_or_null()
            
            if not customer or not customer.wechat_openid:
                return
            
            status_map = {
                'processing': '处理中',
                'resolved': '已解决',
                'closed': '已关闭'
            }
            
            message = f"""
您的售后工单有新进展：

工单号：{ticket.ticket_no}
状态：{status_map.get(ticket.status, ticket.status)}
处理人：{ticket.assigned_to_name}
回复：{ticket.response_content or '暂无'}

感谢您的耐心等待！
            """.strip()
            
            # 发送公众号模板消息
            # await WeChatService.send_template_message(customer.wechat_openid, message)
            
        except Exception as e:
            logger.error(f"通知客户失败: {str(e)}")


class OrderModificationService:
    """订单修改服务"""
    
    @staticmethod
    async def create_modification(
        db: AsyncSession,
        customer_phone: str,
        project_id: int,
        modification_type: str,
        modification_content: Dict,
        reason: str,
        source: str = 'wechat'
    ) -> Dict:
        """
        创建订单修改/退订请求
        
        流程：
        1. 验证客户身份
        2. 验证项目归属
        3. 创建修改记录
        4. 推送审核通知
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            project_id: 项目ID
            modification_type: 修改类型（modify/cancel/refund）
            modification_content: 修改内容
            reason: 修改原因
            source: 来源
        
        Returns:
            Dict: 创建结果
        """
        try:
            # 1. 验证客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            if not customer or not customer.is_verified:
                return {
                    'success': False,
                    'message': '未通过身份验证'
                }
            
            # 2. 验证项目
            result = await db.execute(
                select(Project).where(
                    and_(
                        Project.id == project_id,
                        Project.customer_id == customer.id
                    )
                )
            )
            project = result.scalar_one_or_null()
            
            if not project:
                return {
                    'success': False,
                    'message': '项目不存在或无权限'
                }
            
            # 3. 生成变更单号
            modification_no = f"OM{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"
            
            # 4. 创建修改记录
            modification = OrderModification(
                modification_no=modification_no,
                customer_id=customer.id,
                customer_phone=customer_phone,
                customer_name=customer.name,
                project_id=project.id,
                project_title=project.title,
                modification_type=modification_type,
                modification_content=modification_content,
                reason=reason,
                original_data={
                    'status': project.status,
                    'amount': str(project.amount) if project.amount else None
                },
                status='pending',
                source=source,
                created_at=datetime.now()
            )
            
            db.add(modification)
            await db.commit()
            await db.refresh(modification)
            
            logger.info(f"订单修改请求创建: {modification_no}")
            
            # 5. 推送审核通知
            await OrderModificationService._send_review_notification(
                db, modification, project
            )
            
            return {
                'success': True,
                'message': '修改请求已提交，等待审核',
                'modification_no': modification_no
            }
            
        except Exception as e:
            logger.error(f"创建订单修改失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'提交失败: {str(e)}'
            }
    
    @staticmethod
    async def _send_review_notification(
        db: AsyncSession,
        modification: OrderModification,
        project: Project
    ):
        """推送审核通知"""
        try:
            project_link = project.generate_project_link('https://yourdomain.com')
            
            type_map = {
                'modify': '订单修改',
                'cancel': '订单取消',
                'refund': '退款申请'
            }
            
            message = f"""
【订单变更审核】
变更单号：{modification.modification_no}
客户：{modification.customer_name}（{modification.customer_phone}）
项目：{modification.project_title}
类型：{type_map.get(modification.modification_type, modification.modification_type)}
原因：{modification.reason}

📋 项目详情：{project_link}

请及时审核处理！
            """.strip()
            
            # 推送给销售代表和项目负责人
            if project.assigned_to:
                await WeChatService.send_text_message(
                    project.assigned_to,
                    message
                )
            
            # 更新推送状态
            modification.notification_sent = True
            modification.notification_sent_at = datetime.now()
            await db.commit()
            
        except Exception as e:
            logger.error(f"推送审核通知失败: {str(e)}")
