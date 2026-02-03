"""
商机收集与客户身份管理服务
处理商机用户→正式客户→取消客户的身份转换
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models import (
    Customer, ProspectInquiry, CustomerTypeChangeLog, 
    Project, AfterSalesTicket
)
from app.services.wechat_service import WeChatService
from typing import Dict, Optional
from datetime import datetime
import logging
import secrets
import re

logger = logging.getLogger(__name__)


class ProspectService:
    """商机服务 - 处理潜在客户的询价和转化"""
    
    @staticmethod
    async def collect_inquiry(
        db: AsyncSession,
        phone: Optional[str],
        name: Optional[str],
        inquiry_content: str,
        source: str = 'wechat',
        source_openid: Optional[str] = None,
        product_interest: Optional[str] = None
    ) -> Dict:
        """
        收集商机信息
        
        API自动询问流程：
        1. 请问怎么称呼您？
        2. 您的电话是多少？
        3. 记录信息并分配销售顾问
        4. 推送通知给销售顾问
        
        Args:
            db: 数据库会话
            phone: 客户手机号（可选，分步收集）
            name: 客户姓名（可选，分步收集）
            inquiry_content: 咨询内容
            source: 来源
            source_openid: OpenID
            product_interest: 感兴趣的产品
        
        Returns:
            Dict: 收集结果
        """
        try:
            # 验证手机号格式（如果提供）
            if phone and not re.match(r'^1[3-9]\d{9}$', phone):
                return {
                    'success': False,
                    'message': '手机号格式不正确',
                    'need_phone': True
                }
            
            # 生成咨询单号
            inquiry_no = f"INQ{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"
            
            # 查找或创建客户记录
            customer_id = None
            if phone:
                result = await db.execute(
                    select(Customer).where(Customer.phone == phone)
                )
                customer = result.scalar_one_or_null()
                
                if customer:
                    customer_id = customer.id
                else:
                    # 创建商机客户
                    customer = Customer(
                        phone=phone,
                        name=name,
                        customer_type='prospect',  # 商机用户
                        has_active_order=False,
                        is_verified=False,
                        binding_status='unbound',
                        created_at=datetime.now()
                    )
                    db.add(customer)
                    await db.flush()
                    customer_id = customer.id
                    
                    logger.info(f"创建商机客户: {phone}")
            
            # 创建咨询记录
            inquiry = ProspectInquiry(
                inquiry_no=inquiry_no,
                customer_phone=phone,
                customer_name=name,
                customer_id=customer_id,
                inquiry_type='product',
                inquiry_content=inquiry_content,
                product_interest=product_interest,
                urgency='normal',
                source=source,
                source_openid=source_openid,
                status='pending',
                created_at=datetime.now()
            )
            
            db.add(inquiry)
            await db.commit()
            await db.refresh(inquiry)
            
            logger.info(f"商机咨询记录创建: {inquiry_no}")
            
            # 自动分配销售顾问
            await ProspectService._assign_sales_consultant(db, inquiry)
            
            return {
                'success': True,
                'message': '我已记录您的信息，我们的销售顾问会尽快联系您',
                'inquiry_no': inquiry_no,
                'need_phone': not bool(phone),
                'need_name': not bool(name)
            }
            
        except Exception as e:
            logger.error(f"收集商机信息失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'记录失败: {str(e)}'
            }
    
    @staticmethod
    async def _assign_sales_consultant(
        db: AsyncSession,
        inquiry: ProspectInquiry
    ):
        """
        自动分配销售顾问
        
        分配策略：
        1. 负载均衡（分配给当前待跟进最少的顾问）
        2. 或随机分配
        3. 或根据产品类型分配
        """
        try:
            # 这里简化处理，实际可以从配置中读取销售团队
            # 或根据负载均衡算法分配
            default_consultant = 'chenghong'  # 默认销售顾问
            default_name = '程红'
            
            inquiry.assigned_to = default_consultant
            inquiry.assigned_to_name = default_name
            inquiry.assigned_at = datetime.now()
            inquiry.status = 'assigned'
            
            await db.commit()
            
            # 推送通知给销售顾问
            await ProspectService._notify_sales_consultant(db, inquiry)
            
        except Exception as e:
            logger.error(f"分配销售顾问失败: {str(e)}")
    
    @staticmethod
    async def _notify_sales_consultant(
        db: AsyncSession,
        inquiry: ProspectInquiry
    ):
        """推送商机通知给销售顾问"""
        try:
            message = f"""
【新商机提醒】
咨询单号：{inquiry.inquiry_no}
客户：{inquiry.customer_name or '未提供'}
电话：{inquiry.customer_phone or '未提供'}
内容：{inquiry.inquiry_content}
产品：{inquiry.product_interest or '未指定'}

请及时跟进联系！
            """.strip()
            
            # 推送企业微信消息
            if inquiry.assigned_to:
                await WeChatService.send_text_message(
                    inquiry.assigned_to,
                    message
                )
                
                inquiry.notification_sent = True
                inquiry.notification_sent_at = datetime.now()
                await db.commit()
                
                logger.info(f"已推送商机通知给: {inquiry.assigned_to}")
                
        except Exception as e:
            logger.error(f"推送商机通知失败: {str(e)}")


class CustomerTypeService:
    """客户身份管理服务 - 处理身份转换"""
    
    @staticmethod
    async def convert_to_customer(
        db: AsyncSession,
        customer_phone: str,
        operator_userid: str,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        将商机用户转化为正式客户
        
        触发场景：
        1. 首次下单
        2. 企业微信添加后手动转化
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            operator_userid: 操作人UserID
            project_id: 关联项目ID（可选）
        
        Returns:
            Dict: 转化结果
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            if not customer:
                return {'success': False, 'message': '客户不存在'}
            
            if customer.customer_type == 'customer':
                return {'success': False, 'message': '已经是正式客户'}
            
            old_type = customer.customer_type
            
            # 更新客户类型
            customer.customer_type = 'customer'
            customer.has_active_order = True
            customer.first_order_at = customer.first_order_at or datetime.now()
            
            # 记录变更日志
            log = CustomerTypeChangeLog(
                customer_id=customer.id,
                customer_phone=customer_phone,
                old_type=old_type,
                new_type='customer',
                change_reason='first_order',
                trigger_event='manual_convert',
                project_id=project_id,
                operator_userid=operator_userid,
                created_at=datetime.now()
            )
            db.add(log)
            
            await db.commit()
            
            logger.info(f"客户身份转化: {customer_phone} {old_type} → customer")
            
            # 更新相关商机记录为已转化
            await db.execute(
                update(ProspectInquiry)
                .where(
                    and_(
                        ProspectInquiry.customer_phone == customer_phone,
                        ProspectInquiry.converted_to_customer == False
                    )
                )
                .values(
                    converted_to_customer=True,
                    converted_at=datetime.now(),
                    status='converted'
                )
            )
            await db.commit()
            
            return {
                'success': True,
                'message': '已转化为正式客户',
                'old_type': old_type,
                'new_type': 'customer'
            }
            
        except Exception as e:
            logger.error(f"客户身份转化失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {'success': False, 'message': f'转化失败: {str(e)}'}
    
    @staticmethod
    async def cancel_customer(
        db: AsyncSession,
        customer_phone: str,
        reason: str = 'order_cancelled',
        project_id: Optional[int] = None
    ) -> Dict:
        """
        取消客户身份
        
        触发场景：
        1. 所有订单都被取消
        2. 订单退款
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            reason: 取消原因
            project_id: 关联项目ID
        
        Returns:
            Dict: 取消结果
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            if not customer:
                return {'success': False, 'message': '客户不存在'}
            
            # 检查是否还有有效订单
            result = await db.execute(
                select(Project).where(
                    and_(
                        Project.customer_id == customer.id,
                        Project.status.notin_(['cancelled', 'refunded'])
                    )
                )
            )
            active_projects = result.scalars().all()
            
            if active_projects:
                return {
                    'success': False,
                    'message': f'客户还有{len(active_projects)}个有效订单，不能取消'
                }
            
            old_type = customer.customer_type
            
            # 更新客户类型
            customer.customer_type = 'cancelled'
            customer.has_active_order = False
            customer.last_order_cancel_at = datetime.now()
            
            # 记录变更日志
            log = CustomerTypeChangeLog(
                customer_id=customer.id,
                customer_phone=customer_phone,
                old_type=old_type,
                new_type='cancelled',
                change_reason=reason,
                trigger_event='order_cancel',
                project_id=project_id,
                created_at=datetime.now()
            )
            db.add(log)
            
            await db.commit()
            
            logger.info(f"客户身份取消: {customer_phone} {old_type} → cancelled")
            
            return {
                'success': True,
                'message': '客户身份已取消',
                'old_type': old_type,
                'new_type': 'cancelled'
            }
            
        except Exception as e:
            logger.error(f"取消客户身份失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {'success': False, 'message': f'取消失败: {str(e)}'}
    
    @staticmethod
    async def check_customer_permission(
        db: AsyncSession,
        customer_phone: str,
        permission_type: str  # 'query_project' 或 'submit_aftersales'
    ) -> Dict:
        """
        检查客户权限
        
        权限规则：
        - 商机用户（prospect）：❌ 不能查询项目，❌ 不能售后
        - 正式客户（customer）：✅ 可以查询自己的项目，✅ 可以售后（需is_verified=True）
        - 取消客户（cancelled）：❌ 失去所有权限
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            permission_type: 权限类型
        
        Returns:
            Dict: 权限检查结果
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            if not customer:
                return {
                    'has_permission': False,
                    'reason': '客户不存在',
                    'message': '未找到您的信息，请先联系我们的销售顾问'
                }
            
            # 检查查询项目权限
            if permission_type == 'query_project':
                if customer.customer_type == 'prospect':
                    return {
                        'has_permission': False,
                        'reason': 'customer_type_is_prospect',
                        'message': '您还不是正式客户，无法查询项目。请先下单或联系销售顾问。',
                        'customer_type': 'prospect'
                    }
                
                if customer.customer_type == 'cancelled':
                    return {
                        'has_permission': False,
                        'reason': 'customer_type_is_cancelled',
                        'message': '您的订单已取消，无法查询项目。如需帮助请联系客服。',
                        'customer_type': 'cancelled'
                    }
                
                if not customer.has_active_order:
                    return {
                        'has_permission': False,
                        'reason': 'no_active_order',
                        'message': '您暂无有效订单，无法查询项目。',
                        'customer_type': customer.customer_type
                    }
                
                # 正式客户且有有效订单
                return {
                    'has_permission': True,
                    'customer_id': customer.id,
                    'customer_type': 'customer',
                    'message': '您可以查询项目'
                }
            
            # 检查售后权限
            elif permission_type == 'submit_aftersales':
                if customer.customer_type != 'customer':
                    return {
                        'has_permission': False,
                        'reason': f'customer_type_is_{customer.customer_type}',
                        'message': '只有正式客户才能提交售后请求',
                        'customer_type': customer.customer_type
                    }
                
                if not customer.has_active_order:
                    return {
                        'has_permission': False,
                        'reason': 'no_active_order',
                        'message': '您暂无有效订单，无法提交售后请求',
                        'customer_type': customer.customer_type
                    }
                
                if not customer.is_verified:
                    return {
                        'has_permission': False,
                        'reason': 'not_verified',
                        'message': '请先通过企业微信员工添加验证',
                        'customer_type': customer.customer_type,
                        'need_verification': True
                    }
                
                # 正式客户、有订单、已验证
                return {
                    'has_permission': True,
                    'customer_id': customer.id,
                    'customer_type': 'customer',
                    'message': '您可以提交售后请求'
                }
            
            return {
                'has_permission': False,
                'reason': 'unknown_permission_type',
                'message': '未知的权限类型'
            }
            
        except Exception as e:
            logger.error(f"检查客户权限失败: {str(e)}")
            return {
                'has_permission': False,
                'reason': 'system_error',
                'message': f'检查权限失败: {str(e)}'
            }
