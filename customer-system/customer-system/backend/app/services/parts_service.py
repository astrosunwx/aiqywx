"""
配件库存管理服务
负责处理配件的库存管理、领用、统计等操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models import PartsInventory, PartsUsage, Project, Equipment, OperationLog
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal


class PartsService:
    """配件库存管理服务"""
    
    @staticmethod
    async def create_part(
        db: AsyncSession,
        part_code: str,
        part_name: str,
        category: str,
        specification: str,
        applicable_models: str,
        stock_quantity: int,
        unit_price: Decimal,
        supplier: str,
        operator_userid: str,
        operator_name: str,
        supplier_contact: Optional[str] = None,
        min_stock_alert: int = 5,
        location: Optional[str] = None
    ) -> PartsInventory:
        """
        创建配件
        
        Args:
            db: 数据库会话
            part_code: 配件编码
            part_name: 配件名称
            category: 配件类别
            specification: 规格型号
            applicable_models: 适用设备型号
            stock_quantity: 库存数量
            unit_price: 单价
            supplier: 供应商
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
            supplier_contact: 供应商联系方式
            min_stock_alert: 最低库存预警
            location: 存放位置
        
        Returns:
            创建的配件对象
        """
        # 检查配件编码是否已存在
        result = await db.execute(
            select(PartsInventory).where(PartsInventory.part_code == part_code)
        )
        existing_part = result.scalar_one_or_none()
        
        if existing_part:
            raise ValueError(f"配件编码 {part_code} 已存在")
        
        # 创建配件
        part = PartsInventory(
            part_code=part_code,
            part_name=part_name,
            category=category,
            specification=specification,
            applicable_models=applicable_models,
            stock_quantity=stock_quantity,
            unit_price=unit_price,
            supplier=supplier,
            supplier_contact=supplier_contact,
            min_stock_alert=min_stock_alert,
            location=location,
            created_at=datetime.now()
        )
        
        db.add(part)
        await db.commit()
        await db.refresh(part)
        
        # 记录操作日志
        await PartsService._log_operation(
            db, 'create', part.id, operator_userid, operator_name,
            {'action': '创建配件', 'part_code': part_code, 'part_name': part_name}
        )
        
        return part
    
    @staticmethod
    async def request_parts(
        db: AsyncSession,
        ticket_id: int,
        part_code: str,
        quantity: int,
        engineer_userid: str,
        engineer_name: str,
        equipment_id: Optional[int] = None,
        purpose: str = 'repair'
    ) -> PartsUsage:
        """
        申请领用配件
        
        Args:
            db: 数据库会话
            ticket_id: 工单ID
            part_code: 配件编码
            quantity: 领用数量
            engineer_userid: 工程师UserID
            engineer_name: 工程师姓名
            equipment_id: 设备ID
            purpose: 用途（repair/maintenance/replacement）
        
        Returns:
            配件领用记录对象
        """
        # 获取配件信息
        result = await db.execute(
            select(PartsInventory).where(PartsInventory.part_code == part_code)
        )
        part = result.scalar_one_or_none()
        
        if not part:
            raise ValueError(f"配件编码 {part_code} 不存在")
        
        # 检查库存是否充足
        if part.stock_quantity < quantity:
            raise ValueError(f"配件 {part_code} 库存不足，当前库存: {part.stock_quantity}，需求: {quantity}")
        
        # 创建领用记录
        usage = PartsUsage(
            ticket_id=ticket_id,
            equipment_id=equipment_id,
            part_code=part_code,
            part_name=part.part_name,
            quantity=quantity,
            unit_price=part.unit_price,
            total_cost=part.unit_price * quantity,
            engineer_userid=engineer_userid,
            engineer_name=engineer_name,
            usage_date=date.today(),
            purpose=purpose,
            created_at=datetime.now()
        )
        
        db.add(usage)
        
        # 扣减库存
        part.stock_quantity -= quantity
        part.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(usage)
        
        # 检查是否需要库存预警
        if part.stock_quantity <= part.min_stock_alert:
            # TODO: 发送库存预警通知
            pass
        
        # 记录操作日志
        await PartsService._log_operation(
            db, 'request', part.id, engineer_userid, engineer_name,
            {'action': '领用配件', 'quantity': quantity, 'ticket_id': ticket_id, 'usage_id': usage.id}
        )
        
        return usage
    
    @staticmethod
    async def restock_parts(
        db: AsyncSession,
        part_code: str,
        quantity: int,
        operator_userid: str,
        operator_name: str,
        new_unit_price: Optional[Decimal] = None
    ) -> PartsInventory:
        """
        配件入库
        
        Args:
            db: 数据库会话
            part_code: 配件编码
            quantity: 入库数量
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
            new_unit_price: 新单价（可选）
        
        Returns:
            更新后的配件对象
        """
        # 获取配件信息
        result = await db.execute(
            select(PartsInventory).where(PartsInventory.part_code == part_code)
        )
        part = result.scalar_one_or_none()
        
        if not part:
            raise ValueError(f"配件编码 {part_code} 不存在")
        
        # 更新库存
        part.stock_quantity += quantity
        if new_unit_price:
            part.unit_price = new_unit_price
        part.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(part)
        
        # 记录操作日志
        await PartsService._log_operation(
            db, 'restock', part.id, operator_userid, operator_name,
            {'action': '配件入库', 'quantity': quantity, 'new_stock': part.stock_quantity}
        )
        
        return part
    
    @staticmethod
    async def get_part_by_code(
        db: AsyncSession,
        part_code: str
    ) -> Optional[PartsInventory]:
        """
        根据配件编码查询配件
        
        Args:
            db: 数据库会话
            part_code: 配件编码
        
        Returns:
            配件对象或None
        """
        result = await db.execute(
            select(PartsInventory).where(PartsInventory.part_code == part_code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_parts_by_category(
        db: AsyncSession,
        category: str
    ) -> List[PartsInventory]:
        """
        按类别查询配件
        
        Args:
            db: 数据库会话
            category: 配件类别
        
        Returns:
            配件列表
        """
        result = await db.execute(
            select(PartsInventory).where(PartsInventory.category == category)
            .order_by(PartsInventory.part_name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_low_stock_parts(
        db: AsyncSession
    ) -> List[PartsInventory]:
        """
        获取库存不足的配件列表
        
        Args:
            db: 数据库会话
        
        Returns:
            配件列表
        """
        result = await db.execute(
            select(PartsInventory).where(
                PartsInventory.stock_quantity <= PartsInventory.min_stock_alert
            ).order_by(PartsInventory.stock_quantity)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_parts_usage_by_ticket(
        db: AsyncSession,
        ticket_id: int
    ) -> List[PartsUsage]:
        """
        查询工单的配件使用记录
        
        Args:
            db: 数据库会话
            ticket_id: 工单ID
        
        Returns:
            配件使用记录列表
        """
        result = await db.execute(
            select(PartsUsage).where(PartsUsage.ticket_id == ticket_id)
            .order_by(PartsUsage.usage_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_parts_usage_stats(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        获取配件使用统计
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计数据字典
        """
        query = select(PartsUsage)
        
        if start_date:
            query = query.where(PartsUsage.usage_date >= start_date)
        if end_date:
            query = query.where(PartsUsage.usage_date <= end_date)
        
        result = await db.execute(query)
        usages = result.scalars().all()
        
        # 按配件汇总
        parts_summary = {}
        total_cost = Decimal(0)
        
        for usage in usages:
            if usage.part_code not in parts_summary:
                parts_summary[usage.part_code] = {
                    'part_code': usage.part_code,
                    'part_name': usage.part_name,
                    'total_quantity': 0,
                    'total_cost': Decimal(0)
                }
            
            parts_summary[usage.part_code]['total_quantity'] += usage.quantity
            parts_summary[usage.part_code]['total_cost'] += usage.total_cost or Decimal(0)
            total_cost += usage.total_cost or Decimal(0)
        
        return {
            'total_usage_count': len(usages),
            'total_cost': float(total_cost),
            'parts_summary': list(parts_summary.values())
        }
    
    @staticmethod
    async def _log_operation(
        db: AsyncSession,
        operation_type: str,
        part_id: int,
        operator_userid: str,
        operator_name: str,
        detail: Dict,
        source: str = 'web_ui'
    ):
        """记录操作日志"""
        log = OperationLog(
            operation_type=operation_type,
            entity_type='parts',
            entity_id=part_id,
            operator_userid=operator_userid,
            operator_name=operator_name,
            operation_source=source,
            operation_detail=detail,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
