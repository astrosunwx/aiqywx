"""
自动绑定服务
实现公众号用户与企业微信客户的自动绑定流程
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from app.models import Customer, TempBinding, WeWorkCustomerEvent, OperationLog
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AutoBindingService:
    """自动绑定服务"""
    
    # ========================================================================
    # 第一步：公众号侧 - 客户发起绑定
    # ========================================================================
    
    @staticmethod
    async def create_temp_binding(
        db: AsyncSession,
        wechat_openid: str,
        phone_number: str,
        customer_name: Optional[str] = None
    ) -> TempBinding:
        """
        创建临时绑定记录（客户在公众号发送手机号后调用）
        
        Args:
            db: 数据库会话
            wechat_openid: 公众号OpenID
            phone_number: 客户手机号
            customer_name: 客户姓名（可选）
        
        Returns:
            临时绑定记录
        """
        # 检查是否已存在等待绑定的记录
        result = await db.execute(
            select(TempBinding).where(
                and_(
                    TempBinding.phone_number == phone_number,
                    TempBinding.status == 'waiting',
                    TempBinding.expires_at > datetime.now()
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新现有记录
            existing.wechat_openid = wechat_openid
            existing.customer_name = customer_name or existing.customer_name
            existing.created_at = datetime.now()
            existing.expires_at = datetime.now() + timedelta(days=2)
            await db.commit()
            await db.refresh(existing)
            
            logger.info(f"更新临时绑定记录: phone={phone_number}, openid={wechat_openid}")
            return existing
        
        # 创建新的临时绑定记录
        temp_binding = TempBinding(
            wechat_openid=wechat_openid,
            phone_number=phone_number,
            customer_name=customer_name,
            source='wechat_official',
            status='waiting',
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=2)
        )
        
        db.add(temp_binding)
        await db.commit()
        await db.refresh(temp_binding)
        
        logger.info(f"创建临时绑定记录: phone={phone_number}, openid={wechat_openid}")
        
        return temp_binding
    
    @staticmethod
    async def check_binding_status(
        db: AsyncSession,
        phone_number: str
    ) -> Dict:
        """
        检查手机号的绑定状态
        
        Args:
            db: 数据库会话
            phone_number: 手机号
        
        Returns:
            绑定状态信息
        """
        # 检查是否已正式绑定
        result = await db.execute(
            select(Customer).where(Customer.phone == phone_number)
        )
        customer = result.scalar_one_or_none()
        
        if customer and customer.binding_status == 'bound':
            return {
                'status': 'bound',
                'message': '已完成绑定',
                'customer_id': customer.id,
                'bound_at': customer.bound_at.isoformat() if customer.bound_at else None
            }
        
        # 检查临时绑定状态
        result = await db.execute(
            select(TempBinding).where(
                and_(
                    TempBinding.phone_number == phone_number,
                    TempBinding.status == 'waiting',
                    TempBinding.expires_at > datetime.now()
                )
            )
        )
        temp_binding = result.scalar_one_or_none()
        
        if temp_binding:
            return {
                'status': 'waiting',
                'message': '等待企业微信员工添加',
                'expires_at': temp_binding.expires_at.isoformat(),
                'hours_remaining': int((temp_binding.expires_at - datetime.now()).total_seconds() / 3600)
            }
        
        return {
            'status': 'not_found',
            'message': '未找到绑定记录，请先发送手机号'
        }
    
    # ========================================================================
    # 第二步：企业微信侧 - 接收添加客户事件
    # ========================================================================
    
    @staticmethod
    async def handle_wework_add_customer_event(
        db: AsyncSession,
        event_data: Dict
    ) -> Dict:
        """
        处理企业微信添加客户事件
        
        企业微信回调事件格式示例：
        {
            "ToUserName": "企业ID",
            "CreateTime": 1234567890,
            "MsgType": "event",
            "Event": "change_external_contact",
            "ChangeType": "add_external_contact",
            "UserID": "员工UserID",
            "ExternalUserID": "外部联系人UserID",
            "State": "自定义state",
            "WelcomeCode": "欢迎语code"
        }
        
        Args:
            db: 数据库会话
            event_data: 企业微信回调事件数据
        
        Returns:
            处理结果
        """
        try:
            # 解析事件数据
            employee_userid = event_data.get('UserID')
            external_userid = event_data.get('ExternalUserID')
            welcome_code = event_data.get('WelcomeCode')
            state = event_data.get('State', '')
            
            if not employee_userid or not external_userid:
                logger.error("企业微信事件缺少必要字段")
                return {'success': False, 'message': '事件数据不完整'}
            
            # 通过企业微信API获取客户详情（包括手机号）
            from app.services.wechat_service import WeChatService
            customer_info = await WeChatService.get_external_contact_info(external_userid)
            
            if not customer_info:
                logger.error(f"无法获取外部联系人信息: {external_userid}")
                return {'success': False, 'message': '无法获取客户信息'}
            
            customer_phone = customer_info.get('mobile')
            customer_name = customer_info.get('name')
            add_way = customer_info.get('add_way')  # 添加方式：2表示搜索手机号
            
            # 记录企业微信事件
            event_record = WeWorkCustomerEvent(
                event_type='add_external_contact',
                employee_userid=employee_userid,
                external_userid=external_userid,
                customer_phone=customer_phone,
                customer_name=customer_name,
                add_way=add_way,
                welcome_code=welcome_code,
                state=state,
                raw_event=event_data,
                processed=False,
                created_at=datetime.now()
            )
            
            db.add(event_record)
            await db.commit()
            await db.refresh(event_record)
            
            logger.info(f"记录企业微信添加客户事件: employee={employee_userid}, external={external_userid}")
            
            # 如果没有手机号，无法自动绑定
            if not customer_phone:
                logger.warning(f"客户信息中无手机号，无法自动绑定: {external_userid}")
                event_record.processed = True
                event_record.processed_at = datetime.now()
                await db.commit()
                
                return {
                    'success': False,
                    'message': '客户信息中无手机号',
                    'need_manual_binding': True
                }
            
            # 执行自动绑定
            binding_result = await AutoBindingService.auto_bind_customer(
                db, customer_phone, external_userid, employee_userid, customer_name
            )
            
            # 更新事件处理状态
            event_record.processed = True
            event_record.processed_at = datetime.now()
            await db.commit()
            
            return binding_result
            
        except Exception as e:
            logger.error(f"处理企业微信添加客户事件失败: {str(e)}", exc_info=True)
            return {'success': False, 'message': f'处理失败: {str(e)}'}
    
    # ========================================================================
    # 第三步：自动绑定 - 核心逻辑
    # ========================================================================
    
    @staticmethod
    async def auto_bind_customer(
        db: AsyncSession,
        customer_phone: str,
        external_userid: str,
        employee_userid: str,
        customer_name: Optional[str] = None
    ) -> Dict:
        """
        自动绑定客户（查询临时绑定表并完成正式绑定）
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            external_userid: 企业微信外部联系人UserID
            employee_userid: 员工UserID
            customer_name: 客户姓名
        
        Returns:
            绑定结果
        """
        try:
            # 1. 查询临时绑定表
            result = await db.execute(
                select(TempBinding).where(
                    and_(
                        TempBinding.phone_number == customer_phone,
                        TempBinding.status == 'waiting',
                        TempBinding.expires_at > datetime.now()
                    )
                )
            )
            temp_binding = result.scalar_one_or_none()
            
            if not temp_binding:
                logger.info(f"未找到临时绑定记录: phone={customer_phone}")
                # 没有临时绑定记录，可能是直接通过企业微信添加的客户
                # 仍然创建客户记录，但不关联公众号OpenID
                return await AutoBindingService._create_customer_without_openid(
                    db, customer_phone, external_userid, employee_userid, customer_name
                )
            
            # 2. 找到匹配的OpenID，执行正式绑定
            wechat_openid = temp_binding.wechat_openid
            
            # 3. 查找或创建客户记录
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_none()
            
            if customer:
                # 更新现有客户记录
                customer.wework_userid = external_userid
                customer.wechat_openid = wechat_openid
                customer.name = customer_name or customer.name
                customer.binding_status = 'bound'
                customer.bound_at = datetime.now()
                customer.bound_by = employee_userid
                customer.sales_representative = employee_userid
                # 🔥 设置为可信用户，拥有查询和售后权限
                customer.is_verified = True
                customer.verified_at = datetime.now()
                
                # 🔥 如果是商机用户，企业微信添加后自动转为正式客户
                if customer.customer_type == 'prospect':
                    from app.models import CustomerTypeChangeLog
                    
                    old_type = customer.customer_type
                    customer.customer_type = 'customer'
                    customer.first_order_at = customer.first_order_at or datetime.now()
                    
                    # 记录身份变更日志
                    type_log = CustomerTypeChangeLog(
                        customer_id=customer.id,
                        customer_phone=customer_phone,
                        old_type=old_type,
                        new_type='customer',
                        change_reason='wework_added',
                        trigger_event='auto_binding',
                        operator_userid=employee_userid,
                        created_at=datetime.now()
                    )
                    db.add(type_log)
                    
                    logger.info(f"商机用户自动转化为正式客户: {customer_phone}")
            else:
                # 创建新客户记录
                customer = Customer(
                    phone=customer_phone,
                    name=customer_name or temp_binding.customer_name,
                    wework_userid=external_userid,
                    wechat_openid=wechat_openid,
                    binding_status='bound',
                    bound_at=datetime.now(),
                    bound_by=employee_userid,
                    sales_representative=employee_userid,
                    # 🔥 设置为可信用户
                    is_verified=True,
                    verified_at=datetime.now(),
                    # 🔥 新客户默认为商机用户，企业微信添加后转为正式客户
                    customer_type='customer',
                    created_at=datetime.now()
                )
                db.add(customer)
                
                # 记录身份变更日志（新客户：从无到customer）
                from app.models import CustomerTypeChangeLog
                await db.flush()  # 获取customer.id
                
                type_log = CustomerTypeChangeLog(
                    customer_id=customer.id,
                    customer_phone=customer_phone,
                    old_type='prospect',  # 假设之前是商机
                    new_type='customer',
                    change_reason='wework_added',
                    trigger_event='auto_binding',
                    operator_userid=employee_userid,
                    created_at=datetime.now()
                )
                db.add(type_log)
                
                logger.info(f"新客户创建并设置为正式客户: {customer_phone}")
            
            # 4. 更新临时绑定状态
            temp_binding.status = 'bound'
            temp_binding.bound_at = datetime.now()
            
            await db.commit()
            await db.refresh(customer)
            
            logger.info(f"自动绑定成功: phone={customer_phone}, customer_id={customer.id}")
            
            # 5. 记录操作日志
            await AutoBindingService._log_binding(
                db, customer.id, employee_userid, 
                {'action': '自动绑定成功', 'source': 'wework_add_event'}
            )
            
            # 6. （可选）发送公众号模板消息通知客户
            # await AutoBindingService._send_binding_notification(wechat_openid)
            
            return {
                'success': True,
                'message': '自动绑定成功',
                'customer_id': customer.id,
                'customer_name': customer.name,
                'binding_type': 'auto',
                'bound_at': customer.bound_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"自动绑定失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {'success': False, 'message': f'绑定失败: {str(e)}'}
    
    @staticmethod
    async def _create_customer_without_openid(
        db: AsyncSession,
        customer_phone: str,
        external_userid: str,
        employee_userid: str,
        customer_name: Optional[str] = None
    ) -> Dict:
        """
        创建客户记录（不关联公众号OpenID）
        适用于直接通过企业微信添加，未经过公众号的客户
        """
        try:
            # 查找或创建客户记录
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_none()
            
            if customer:
                # 更新企业微信信息
                customer.wework_userid = external_userid
                customer.name = customer_name or customer.name
                customer.sales_representative = employee_userid
            else:
                # 创建新客户
                customer = Customer(
                    phone=customer_phone,
                    name=customer_name,
                    wework_userid=external_userid,
                    binding_status='unbound',  # 未关联公众号
                    sales_representative=employee_userid,
                    created_at=datetime.now()
                )
                db.add(customer)
            
            await db.commit()
            await db.refresh(customer)
            
            logger.info(f"创建企业微信客户记录（无公众号绑定）: phone={customer_phone}")
            
            return {
                'success': True,
                'message': '客户记录已创建（未关联公众号）',
                'customer_id': customer.id,
                'binding_type': 'wework_only',
                'note': '客户未通过公众号验证，仅企业微信联系'
            }
            
        except Exception as e:
            logger.error(f"创建客户记录失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {'success': False, 'message': f'创建失败: {str(e)}'}
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    @staticmethod
    async def clean_expired_temp_bindings(db: AsyncSession) -> int:
        """
        清理过期的临时绑定记录（定时任务）
        
        Args:
            db: 数据库会话
        
        Returns:
            清理的记录数量
        """
        result = await db.execute(
            update(TempBinding)
            .where(
                and_(
                    TempBinding.status == 'waiting',
                    TempBinding.expires_at <= datetime.now()
                )
            )
            .values(status='expired')
        )
        
        await db.commit()
        count = result.rowcount
        
        logger.info(f"清理过期临时绑定记录: {count}条")
        return count
    
    @staticmethod
    async def check_customer_can_query(
        db: AsyncSession,
        customer_phone: str
    ) -> bool:
        """
        检查客户是否有权限查询项目
        只有通过企业微信搜索手机号添加的客户才能查询
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
        
        Returns:
            是否有权限
        """
        # 查询客户记录
        result = await db.execute(
            select(Customer).where(Customer.phone == customer_phone)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            return False
        
        # 必须有企业微信UserID（说明被企业微信员工添加）
        if not customer.wework_userid:
            return False
        
        # 检查添加方式是否为搜索手机号（add_way=2）
        result = await db.execute(
            select(WeWorkCustomerEvent).where(
                and_(
                    WeWorkCustomerEvent.customer_phone == customer_phone,
                    WeWorkCustomerEvent.add_way == 2,  # 搜索手机号添加
                    WeWorkCustomerEvent.event_type == 'add_external_contact'
                )
            )
        )
        event = result.scalar_one_or_none()
        
        return event is not None
    
    @staticmethod
    async def check_binding_status(
        db: AsyncSession,
        phone: str
    ) -> Dict:
        """
        查询客户绑定状态
        
        用于客户在公众号查询绑定进度
        
        Args:
            db: 数据库会话
            phone: 客户手机号
        
        Returns:
            绑定状态信息
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == phone)
            )
            customer = result.scalar_one_or_null()
            
            if customer:
                return {
                    'status': customer.binding_status,
                    'bound_at': customer.bound_at.isoformat() if customer.bound_at else None,
                    'has_wework': bool(customer.wework_userid),
                    'has_wechat': bool(customer.wechat_openid),
                    'message': '已绑定' if customer.binding_status == 'bound' else '部分绑定'
                }
            
            # 查找临时绑定记录
            result = await db.execute(
                select(TempBinding)
                .where(
                    TempBinding.phone_number == phone,
                    TempBinding.status == 'waiting'
                )
                .order_by(TempBinding.created_at.desc())
            )
            temp_binding = result.scalar_one_or_null()
            
            if temp_binding:
                # 检查是否过期
                if datetime.now() > temp_binding.expires_at:
                    return {
                        'status': 'expired',
                        'message': '临时绑定已过期，请重新提交手机号'
                    }
                
                return {
                    'status': 'pending',
                    'created_at': temp_binding.created_at.isoformat(),
                    'expires_at': temp_binding.expires_at.isoformat(),
                    'message': '等待企业微信员工添加'
                }
            
            return {
                'status': 'not_found',
                'message': '未找到绑定记录，请先在公众号发送手机号'
            }
            
        except Exception as e:
            logger.error(f"查询绑定状态失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }

    
    @staticmethod
    async def _log_binding(
        db: AsyncSession,
        customer_id: int,
        operator_userid: str,
        detail: Dict
    ):
        """记录绑定操作日志"""
        log = OperationLog(
            operation_type='customer_binding',
            entity_type='customer',
            entity_id=customer_id,
            operator_userid=operator_userid,
            operator_name='System',
            operation_source='system',
            operation_detail=detail,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
