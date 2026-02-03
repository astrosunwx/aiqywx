"""
客户服务请求处理服务
不拒绝任何客户，所有请求都记录并转给销售顾问处理
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Customer, CustomerServiceRequest
from app.services.wechat_service import WeChatService
from typing import Dict, Optional
from datetime import datetime
import logging
import secrets

logger = logging.getLogger(__name__)


class CustomerServiceRequestService:
    """客户服务请求处理 - 包容所有客户"""
    
    # 请求类型对应的紧急程度
    REQUEST_URGENCY_MAP = {
        'inquiry': 'low',           # 咨询 - 低
        'query_order': 'normal',    # 查询订单 - 普通
        'modify_order': 'high',     # 更改订单 - 高
        'cancel_order': 'urgent',   # 取消订单 - 紧急
        'aftersales': 'high'        # 售后 - 高
    }
    
    # 请求类型对应的中文名称
    REQUEST_TYPE_NAME = {
        'inquiry': '咨询',
        'query_order': '查询订单',
        'modify_order': '更改订单',
        'cancel_order': '取消订单',
        'aftersales': '售后服务'
    }
    
    @staticmethod
    async def create_service_request(
        db: AsyncSession,
        customer_phone: str,
        customer_name: Optional[str],
        request_type: str,
        request_content: str,
        source: str = 'wechat',
        source_openid: Optional[str] = None
    ) -> Dict:
        """
        创建服务请求（不拒绝任何客户）
        
        处理流程：
        1. 检查客户身份（商机/正式/取消/不存在）
        2. 如果不是正式客户或无有效订单，标记needs_verification=True
        3. 推送企业微信通知给销售顾问："请先搜索手机号添加客户"
        4. 所有请求都记录，不拒绝
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            customer_name: 客户姓名
            request_type: 请求类型
            request_content: 请求内容
            source: 来源渠道
            source_openid: OpenID
        
        Returns:
            Dict: 请求结果
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            # 确定紧急程度
            urgency = CustomerServiceRequestService.REQUEST_URGENCY_MAP.get(
                request_type, 
                'normal'
            )
            
            # 检查是否需要销售顾问先添加客户
            needs_verification = False
            verification_note = ''
            customer_type = 'unknown'
            customer_id = None
            
            if not customer:
                # 客户不存在
                needs_verification = True
                verification_note = '客户不存在于系统，可能是首次联系或项目联系人变更'
                customer_type = 'unknown'
            else:
                customer_id = customer.id
                customer_type = customer.customer_type
                
                if customer.customer_type == 'prospect':
                    # 商机用户
                    needs_verification = True
                    verification_note = '商机用户，还未下单，请先添加微信联系'
                
                elif customer.customer_type == 'cancelled':
                    # 取消客户
                    needs_verification = True
                    verification_note = '取消客户，订单已全部取消，请先添加微信了解情况'
                
                elif customer.customer_type == 'customer':
                    if not customer.has_active_order:
                        # 正式客户但无有效订单
                        needs_verification = True
                        verification_note = '正式客户但暂无有效订单，可能订单已完成或取消'
                    
                    if not customer.is_verified and request_type in ['modify_order', 'cancel_order', 'aftersales']:
                        # 未验证的客户想进行敏感操作
                        needs_verification = True
                        verification_note = '客户未通过企业微信验证，请先添加客户'
            
            # 生成请求单号
            request_no = f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"
            
            # 创建服务请求
            service_request = CustomerServiceRequest(
                request_no=request_no,
                customer_phone=customer_phone,
                customer_name=customer_name,
                customer_id=customer_id,
                customer_type=customer_type,
                request_type=request_type,
                request_content=request_content,
                urgency=urgency,
                source=source,
                source_openid=source_openid,
                status='pending',
                needs_verification=needs_verification,
                verification_note=verification_note,
                created_at=datetime.now()
            )
            
            db.add(service_request)
            await db.commit()
            await db.refresh(service_request)
            
            logger.info(
                f"服务请求已创建: {request_no}, "
                f"类型={request_type}, "
                f"客户={customer_phone}, "
                f"身份={customer_type}, "
                f"需验证={needs_verification}"
            )
            
            # 分配销售顾问并推送通知
            await CustomerServiceRequestService._assign_and_notify(
                db, 
                service_request
            )
            
            # 返回给客户的消息
            request_type_name = CustomerServiceRequestService.REQUEST_TYPE_NAME.get(
                request_type,
                '服务请求'
            )
            
            return {
                'success': True,
                'message': f'已记录您的{request_type_name}请求，我们的专员会尽快联系您处理，请保持电话畅通。',
                'request_no': request_no,
                'urgency': urgency,
                'needs_verification': needs_verification
            }
            
        except Exception as e:
            logger.error(f"创建服务请求失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'记录失败: {str(e)}'
            }
    
    @staticmethod
    async def _assign_and_notify(
        db: AsyncSession,
        service_request: CustomerServiceRequest
    ):
        """
        分配销售顾问并推送通知
        
        通知内容根据needs_verification区分：
        - 如果需要验证：提示"请先搜索手机号添加客户"
        - 如果正常：直接处理请求
        """
        try:
            # 简化处理，分配给默认销售顾问
            # 实际可以根据负载均衡、区域、产品类型等策略分配
            default_consultant = 'chenghong'
            default_name = '程红'
            
            service_request.assigned_to = default_consultant
            service_request.assigned_to_name = default_name
            service_request.assigned_at = datetime.now()
            service_request.status = 'assigned'
            
            await db.commit()
            
            # 推送企业微信通知
            await CustomerServiceRequestService._send_notification(
                db,
                service_request
            )
            
        except Exception as e:
            logger.error(f"分配销售顾问失败: {str(e)}")
    
    @staticmethod
    async def _send_notification(
        db: AsyncSession,
        service_request: CustomerServiceRequest
    ):
        """推送通知给销售顾问"""
        try:
            request_type_name = CustomerServiceRequestService.REQUEST_TYPE_NAME.get(
                service_request.request_type,
                service_request.request_type
            )
            
            # 紧急程度标识
            urgency_emoji = {
                'low': '📋',
                'normal': '📝',
                'high': '⚠️',
                'urgent': '🚨'
            }
            emoji = urgency_emoji.get(service_request.urgency, '📝')
            
            # 如果需要验证，特殊通知
            if service_request.needs_verification:
                message = f"""
{emoji} 【客户服务请求 - 需要添加客户】
请求单号：{service_request.request_no}
请求类型：{request_type_name}（{service_request.urgency.upper()}）
客户姓名：{service_request.customer_name or '未提供'}
客户电话：{service_request.customer_phone}
客户身份：{service_request.customer_type}

⚠️ 温馨提示：
{service_request.verification_note}

📱 请先"搜索手机号"添加该客户
然后处理客户的{request_type_name}请求

可能原因：
• 商机客户（还未下单）
• 购买了本公司产品但项目库暂时没有信息
• 项目更换了联系人或联系方式变更

请求内容：
{service_request.request_content}

请保持电话畅通，及时联系客户！
                """.strip()
            else:
                # 正常请求
                message = f"""
{emoji} 【客户服务请求】
请求单号：{service_request.request_no}
请求类型：{request_type_name}（{service_request.urgency.upper()}）
客户姓名：{service_request.customer_name}
客户电话：{service_request.customer_phone}
客户身份：正式客户 ✅

请求内容：
{service_request.request_content}

请及时处理客户请求！
                """.strip()
            
            # 推送企业微信消息
            if service_request.assigned_to:
                await WeChatService.send_text_message(
                    service_request.assigned_to,
                    message
                )
                
                service_request.notification_sent = True
                service_request.notification_sent_at = datetime.now()
                await db.commit()
                
                logger.info(
                    f"已推送服务请求通知: {service_request.request_no} → {service_request.assigned_to}"
                )
                
        except Exception as e:
            logger.error(f"推送通知失败: {str(e)}")
    
    @staticmethod
    async def collect_request_info_step_by_step(
        db: AsyncSession,
        message: str,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        request_type: Optional[str] = None,
        source_openid: Optional[str] = None
    ) -> Dict:
        """
        分步收集服务请求信息
        
        对话流程：
        1. 请问怎么称呼您？
        2. 您的电话是多少？
        3. 您要查询订单？还是更改？取消订单？还是售后？
        4. 请简单描述您的需求
        5. 已记录，将帮您转给该项目对应的专员进行处理
        
        Args:
            db: 数据库会话
            message: 用户消息
            phone: 电话（可选）
            name: 姓名（可选）
            request_type: 请求类型（可选）
            source_openid: OpenID
        
        Returns:
            Dict: 收集结果
        """
        try:
            # 步骤1：收集姓名
            if not name:
                return {
                    'success': False,
                    'need_input': True,
                    'prompt': '请问怎么称呼您？',
                    'next_step': 'collect_name'
                }
            
            # 步骤2：收集电话
            if not phone:
                return {
                    'success': False,
                    'need_input': True,
                    'prompt': '请问您的电话是多少？',
                    'next_step': 'collect_phone'
                }
            
            # 步骤3：确定请求类型
            if not request_type:
                # 尝试从消息中识别请求类型
                request_type = CustomerServiceRequestService._detect_request_type(message)
                
                if not request_type:
                    return {
                        'success': False,
                        'need_input': True,
                        'prompt': '请问您要：\n1️⃣ 查询订单\n2️⃣ 更改订单\n3️⃣ 取消订单\n4️⃣ 售后服务\n\n请回复数字或关键词',
                        'next_step': 'collect_request_type'
                    }
            
            # 步骤4：创建服务请求
            result = await CustomerServiceRequestService.create_service_request(
                db=db,
                customer_phone=phone,
                customer_name=name,
                request_type=request_type,
                request_content=message,
                source='wechat',
                source_openid=source_openid
            )
            
            return result
            
        except Exception as e:
            logger.error(f"分步收集请求信息失败: {str(e)}")
            return {
                'success': False,
                'message': f'处理失败: {str(e)}'
            }
    
    @staticmethod
    def _detect_request_type(message: str) -> Optional[str]:
        """从消息中识别请求类型"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['查询', '查看', '订单', '进度', '状态']):
            return 'query_order'
        
        if any(keyword in message_lower for keyword in ['更改', '修改', '变更', '调整']):
            return 'modify_order'
        
        if any(keyword in message_lower for keyword in ['取消', '退单', '不要了']):
            return 'cancel_order'
        
        if any(keyword in message_lower for keyword in ['售后', '维修', '故障', '问题', '坏了']):
            return 'aftersales'
        
        if any(keyword in message_lower for keyword in ['咨询', '了解', '询价', '价格', '多少钱']):
            return 'inquiry'
        
        return None
