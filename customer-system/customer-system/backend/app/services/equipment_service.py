"""
设备档案管理服务
负责处理设备的创建、更新、维护记录等操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models import Equipment, Order, MaintenanceRecord, OperationLog
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal


class EquipmentService:
    """设备档案管理服务"""
    
    @staticmethod
    async def create_equipment_from_order(
        db: AsyncSession,
        order_id: int,
        operator_userid: str,
        operator_name: str,
        equipment_type: Optional[str] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        install_location: Optional[str] = None,
        warranty_months: int = 36,
        maintenance_cycle_days: int = 90
    ) -> Equipment:
        """
        从订单创建设备档案
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
            equipment_type: 设备类型
            brand: 品牌
            model: 型号
            serial_number: 序列号
            install_location: 安装位置
            warranty_months: 保修月数
            maintenance_cycle_days: 维护周期（天）
        
        Returns:
            创建的设备对象
        """
        # 获取订单信息
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"订单ID {order_id} 不存在")
        
        # 生成设备编号
        equipment_no = await EquipmentService._generate_equipment_no(db)
        
        # 计算保修截止日期
        install_date = date.today()
        warranty_end_date = install_date + timedelta(days=warranty_months * 30)
        
        # 计算下次维护日期
        next_maintenance_date = install_date + timedelta(days=maintenance_cycle_days)
        
        # 创建设备档案
        equipment = Equipment(
            equipment_no=equipment_no,
            order_id=order_id,
            customer_id=order.customer_id,
            customer_phone=order.customer_phone,
            customer_name=order.customer_name,
            equipment_type=equipment_type,
            brand=brand,
            model=model,
            serial_number=serial_number,
            install_date=install_date,
            install_location=install_location,
            warranty_months=warranty_months,
            warranty_end_date=warranty_end_date,
            status='in_use',
            maintenance_cycle_days=maintenance_cycle_days,
            last_maintenance_date=None,
            next_maintenance_date=next_maintenance_date,
            created_at=datetime.now()
        )
        
        db.add(equipment)
        await db.commit()
        await db.refresh(equipment)
        
        # 记录操作日志
        await EquipmentService._log_operation(
            db, 'create', equipment.id, operator_userid, operator_name,
            {'action': '创建设备档案', 'equipment_no': equipment_no, 'order_id': order_id}
        )
        
        return equipment
    
    @staticmethod
    async def add_maintenance_record(
        db: AsyncSession,
        equipment_id: int,
        maintenance_type: str,
        engineer_userid: str,
        engineer_name: str,
        work_description: str,
        parts_replaced: Optional[List[Dict]] = None,
        cost: Optional[Decimal] = None,
        project_id: Optional[int] = None,
        photos: Optional[List[str]] = None
    ) -> MaintenanceRecord:
        """
        添加维护记录
        
        Args:
            db: 数据库会话
            equipment_id: 设备ID
            maintenance_type: 维护类型（routine/repair/upgrade）
            engineer_userid: 工程师UserID
            engineer_name: 工程师姓名
            work_description: 工作内容
            parts_replaced: 更换的配件列表
            cost: 费用
            project_id: 关联工单ID
            photos: 维护照片URLs
        
        Returns:
            创建的维护记录对象
        """
        # 获取设备信息
        result = await db.execute(
            select(Equipment).where(Equipment.id == equipment_id)
        )
        equipment = result.scalar_one_or_none()
        
        if not equipment:
            raise ValueError(f"设备ID {equipment_id} 不存在")
        
        # 计算下次维护日期
        maintenance_date = date.today()
        next_maintenance_date = maintenance_date + timedelta(days=equipment.maintenance_cycle_days)
        
        # 创建维护记录
        record = MaintenanceRecord(
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            maintenance_date=maintenance_date,
            engineer_userid=engineer_userid,
            engineer_name=engineer_name,
            work_description=work_description,
            parts_replaced=parts_replaced or [],
            cost=cost,
            next_maintenance_date=next_maintenance_date,
            project_id=project_id,
            photos=photos or [],
            created_at=datetime.now()
        )
        
        db.add(record)
        
        # 更新设备的维护时间
        equipment.last_maintenance_date = maintenance_date
        equipment.next_maintenance_date = next_maintenance_date
        equipment.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(record)
        
        # 记录操作日志
        await EquipmentService._log_operation(
            db, 'maintenance', equipment_id, engineer_userid, engineer_name,
            {'action': '添加维护记录', 'type': maintenance_type, 'record_id': record.id}
        )
        
        return record
    
    @staticmethod
    async def get_equipment_by_customer(
        db: AsyncSession,
        customer_phone: str
    ) -> List[Equipment]:
        """
        查询客户的所有设备
        
        Args:
            db: 数据库会话
            customer_phone: 客户电话
        
        Returns:
            设备列表
        """
        result = await db.execute(
            select(Equipment).where(Equipment.customer_phone == customer_phone)
            .order_by(Equipment.install_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_equipment_needing_maintenance(
        db: AsyncSession,
        days_ahead: int = 7
    ) -> List[Equipment]:
        """
        获取需要维护的设备列表
        
        Args:
            db: 数据库会话
            days_ahead: 提前天数
        
        Returns:
            设备列表
        """
        target_date = date.today() + timedelta(days=days_ahead)
        
        result = await db.execute(
            select(Equipment).where(
                and_(
                    Equipment.status == 'in_use',
                    Equipment.next_maintenance_date.isnot(None),
                    Equipment.next_maintenance_date <= target_date,
                    Equipment.next_maintenance_date >= date.today()
                )
            ).order_by(Equipment.next_maintenance_date)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_equipment_warranty_expiring(
        db: AsyncSession,
        days_ahead: int = 30
    ) -> List[Equipment]:
        """
        获取保修即将到期的设备列表
        
        Args:
            db: 数据库会话
            days_ahead: 提前天数
        
        Returns:
            设备列表
        """
        target_date = date.today() + timedelta(days=days_ahead)
        
        result = await db.execute(
            select(Equipment).where(
                and_(
                    Equipment.status == 'in_use',
                    Equipment.warranty_end_date.isnot(None),
                    Equipment.warranty_end_date <= target_date,
                    Equipment.warranty_end_date >= date.today()
                )
            ).order_by(Equipment.warranty_end_date)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_equipment_history(
        db: AsyncSession,
        equipment_id: int
    ) -> Dict:
        """
        获取设备的完整历史记录
        
        Args:
            db: 数据库会话
            equipment_id: 设备ID
        
        Returns:
            包含设备信息、订单信息、维护记录的字典
        """
        # 获取设备信息
        result = await db.execute(
            select(Equipment).where(Equipment.id == equipment_id)
        )
        equipment = result.scalar_one_or_none()
        
        if not equipment:
            raise ValueError(f"设备ID {equipment_id} 不存在")
        
        # 获取订单信息
        order = None
        if equipment.order_id:
            result = await db.execute(
                select(Order).where(Order.id == equipment.order_id)
            )
            order = result.scalar_one_or_none()
        
        # 获取维护记录
        result = await db.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.equipment_id == equipment_id)
            .order_by(MaintenanceRecord.maintenance_date.desc())
        )
        maintenance_records = result.scalars().all()
        
        return {
            'equipment': equipment,
            'order': order,
            'maintenance_records': maintenance_records
        }
    
    @staticmethod
    async def _generate_equipment_no(db: AsyncSession) -> str:
        """
        生成设备编号
        格式：EQ + YYYYMMDD + 3位序号
        
        Args:
            db: 数据库会话
        
        Returns:
            设备编号
        """
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"EQ{today}"
        
        # 查询今天已有的设备数量
        result = await db.execute(
            select(Equipment).where(Equipment.equipment_no.like(f"{prefix}%"))
        )
        count = len(result.scalars().all())
        
        # 生成新编号
        sequence = str(count + 1).zfill(3)
        return f"{prefix}{sequence}"
    
    @staticmethod
    async def _log_operation(
        db: AsyncSession,
        operation_type: str,
        equipment_id: int,
        operator_userid: str,
        operator_name: str,
        detail: Dict,
        source: str = 'web_ui'
    ):
        """记录操作日志"""
        log = OperationLog(
            operation_type=operation_type,
            entity_type='equipment',
            entity_id=equipment_id,
            operator_userid=operator_userid,
            operator_name=operator_name,
            operation_source=source,
            operation_detail=detail,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
