"""
订单管理服务
负责处理订单的创建、更新、配送、安装等操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Order, Opportunity, Customer, Equipment, OperationLog
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal


class OrderService:
    """订单管理服务"""
    
    @staticmethod
    async def create_order_from_opportunity(
        db: AsyncSession,
        opportunity_id: int,
        sales_userid: str,
        sales_name: str,
        delivery_address: str,
        delivery_contact: str,
        delivery_phone: str,
        delivery_date: Optional[date] = None,
        install_date: Optional[date] = None
    ) -> Order:
        """
        从商机创建订单
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            sales_userid: 销售UserID
            sales_name: 销售姓名
            delivery_address: 配送地址
            delivery_contact: 配送联系人
            delivery_phone: 配送联系电话
            delivery_date: 计划配送日期
            install_date: 计划安装日期
        
        Returns:
            创建的订单对象
        """
        # 获取商机信息
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        if opportunity.status != 'won':
            raise ValueError(f"商机状态必须为'won'才能创建订单，当前状态: {opportunity.status}")
        
        # 生成订单编号
        order_no = await OrderService._generate_order_no(db)
        
        # 创建订单
        order = Order(
            order_no=order_no,
            opportunity_id=opportunity_id,
            customer_id=opportunity.customer_id,
            customer_phone=opportunity.customer_phone,
            customer_name=opportunity.customer_name,
            product_name=opportunity.product_name,
            quantity=opportunity.quantity,
            unit_price=opportunity.quoted_amount / opportunity.quantity if opportunity.quantity else opportunity.quoted_amount,
            total_amount=opportunity.quoted_amount,
            status='pending',
            sales_userid=sales_userid,
            sales_name=sales_name,
            delivery_address=delivery_address,
            delivery_contact=delivery_contact,
            delivery_phone=delivery_phone,
            delivery_date=delivery_date,
            install_date=install_date,
            created_at=datetime.now()
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        # 记录操作日志
        await OrderService._log_operation(
            db, 'create', order.id, sales_userid, sales_name,
            {'action': '创建订单', 'order_no': order_no, 'opportunity_id': opportunity_id}
        )
        
        return order
    
    @staticmethod
    async def confirm_order(
        db: AsyncSession,
        order_id: int,
        operator_userid: str,
        operator_name: str
    ) -> Order:
        """
        确认订单
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
        
        Returns:
            更新后的订单对象
        """
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        order.status = 'confirmed'
        order.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(order)
        
        # 记录操作日志
        await OrderService._log_operation(
            db, 'confirm', order_id, operator_userid, operator_name,
            {'action': '确认订单'}
        )
        
        return order
    
    @staticmethod
    async def mark_as_paid(
        db: AsyncSession,
        order_id: int,
        operator_userid: str,
        operator_name: str
    ) -> Order:
        """
        标记订单为已支付
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
        
        Returns:
            更新后的订单对象
        """
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        order.status = 'paid'
        order.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(order)
        
        # 记录操作日志
        await OrderService._log_operation(
            db, 'paid', order_id, operator_userid, operator_name,
            {'action': '标记已支付'}
        )
        
        return order
    
    @staticmethod
    async def mark_as_delivered(
        db: AsyncSession,
        order_id: int,
        operator_userid: str,
        operator_name: str
    ) -> Order:
        """
        标记订单为已配送
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
        
        Returns:
            更新后的订单对象
        """
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        order.status = 'delivered'
        order.delivered_at = datetime.now()
        order.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(order)
        
        # 记录操作日志
        await OrderService._log_operation(
            db, 'delivered', order_id, operator_userid, operator_name,
            {'action': '标记已配送'}
        )
        
        return order
    
    @staticmethod
    async def mark_as_installed(
        db: AsyncSession,
        order_id: int,
        installer_userid: str,
        installer_name: str,
        create_equipment: bool = True
    ) -> Order:
        """
        标记订单为已安装
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            installer_userid: 安装人员UserID
            installer_name: 安装人员姓名
            create_equipment: 是否自动创建设备档案
        
        Returns:
            更新后的订单对象
        """
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        order.status = 'installed'
        order.installed_at = datetime.now()
        order.installer_userid = installer_userid
        order.installer_name = installer_name
        order.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(order)
        
        # 记录操作日志
        await OrderService._log_operation(
            db, 'installed', order_id, installer_userid, installer_name,
            {'action': '标记已安装'}
        )
        
        # 自动创建设备档案
        if create_equipment:
            from app.services.equipment_service import EquipmentService
            await EquipmentService.create_equipment_from_order(
                db, order_id, installer_userid, installer_name
            )
        
        return order
    
    @staticmethod
    async def get_orders_by_customer(
        db: AsyncSession,
        customer_phone: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """
        查询客户的订单列表
        
        Args:
            db: 数据库会话
            customer_phone: 客户电话
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            订单列表
        """
        query = select(Order).where(Order.customer_phone == customer_phone)
        query = query.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_orders_by_status(
        db: AsyncSession,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """
        按状态查询订单
        
        Args:
            db: 数据库会话
            status: 订单状态
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            订单列表
        """
        query = select(Order).where(Order.status == status)
        query = query.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_order_by_no(
        db: AsyncSession,
        order_no: str
    ) -> Optional[Order]:
        """
        根据订单号查询订单
        
        Args:
            db: 数据库会话
            order_no: 订单号
        
        Returns:
            订单对象或None
        """
        result = await db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def _generate_order_no(db: AsyncSession) -> str:
        """
        生成订单编号
        格式：OR + YYYYMMDD + 3位序号
        
        Args:
            db: 数据库会话
        
        Returns:
            订单编号
        """
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"OR{today}"
        
        # 查询今天已有的订单数量
        result = await db.execute(
            select(Order).where(Order.order_no.like(f"{prefix}%"))
        )
        count = len(result.scalars().all())
        
        # 生成新编号
        sequence = str(count + 1).zfill(3)
        return f"{prefix}{sequence}"
    
    @staticmethod
    async def _log_operation(
        db: AsyncSession,
        operation_type: str,
        order_id: int,
        operator_userid: str,
        operator_name: str,
        detail: Dict,
        source: str = 'web_ui'
    ):
        """记录操作日志"""
        log = OperationLog(
            operation_type=operation_type,
            entity_type='order',
            entity_id=order_id,
            operator_userid=operator_userid,
            operator_name=operator_name,
            operation_source=source,
            operation_detail=detail,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
