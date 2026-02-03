"""
商机管理服务
负责处理售前商机的创建、更新、跟进等操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from app.models import Opportunity, Customer, OperationLog
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal


class OpportunityService:
    """商机管理服务"""
    
    @staticmethod
    async def create_opportunity(
        db: AsyncSession,
        customer_phone: str,
        product_name: str,
        requirements: str,
        sales_userid: str,
        sales_name: str,
        source: str = "公众号",
        quantity: int = 1,
        estimated_amount: Optional[Decimal] = None
    ) -> Opportunity:
        """
        创建新商机
        
        Args:
            db: 数据库会话
            customer_phone: 客户电话
            product_name: 产品名称
            requirements: 需求描述
            sales_userid: 销售UserID
            sales_name: 销售姓名
            source: 来源渠道
            quantity: 数量
            estimated_amount: 预计金额
        
        Returns:
            创建的商机对象
        """
        # 查找或创建客户
        result = await db.execute(
            select(Customer).where(Customer.phone == customer_phone)
        )
        customer = result.scalar_one_or_none()
        
        # 创建商机
        opportunity = Opportunity(
            customer_id=customer.id if customer else None,
            customer_phone=customer_phone,
            customer_name=customer.name if customer else None,
            product_name=product_name,
            quantity=quantity,
            estimated_amount=estimated_amount,
            status='new',
            sales_userid=sales_userid,
            sales_name=sales_name,
            source=source,
            requirements=requirements,
            follow_up_notes=[],  # 初始化为空列表
            created_at=datetime.now()
        )
        
        db.add(opportunity)
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'create', opportunity.id, sales_userid, sales_name,
            {'action': '创建商机', 'product': product_name}
        )
        
        return opportunity
    
    @staticmethod
    async def claim_opportunity(
        db: AsyncSession,
        opportunity_id: int,
        sales_userid: str,
        sales_name: str
    ) -> Opportunity:
        """
        认领商机
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            sales_userid: 销售UserID
            sales_name: 销售姓名
        
        Returns:
            更新后的商机对象
        """
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        # 更新商机信息
        opportunity.sales_userid = sales_userid
        opportunity.sales_name = sales_name
        opportunity.status = 'contacted'
        opportunity.followed_up_at = datetime.now()
        opportunity.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'claim', opportunity_id, sales_userid, sales_name,
            {'action': '认领商机'}
        )
        
        return opportunity
    
    @staticmethod
    async def add_follow_up(
        db: AsyncSession,
        opportunity_id: int,
        sales_userid: str,
        sales_name: str,
        follow_up_content: str
    ) -> Opportunity:
        """
        添加跟进记录
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            sales_userid: 销售UserID
            sales_name: 销售姓名
            follow_up_content: 跟进内容
        
        Returns:
            更新后的商机对象
        """
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        # 添加跟进记录
        follow_up_notes = opportunity.follow_up_notes or []
        follow_up_notes.append({
            'time': datetime.now().isoformat(),
            'operator': sales_name,
            'content': follow_up_content
        })
        
        opportunity.follow_up_notes = follow_up_notes
        opportunity.followed_up_at = datetime.now()
        opportunity.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'follow_up', opportunity_id, sales_userid, sales_name,
            {'action': '添加跟进', 'content': follow_up_content}
        )
        
        return opportunity
    
    @staticmethod
    async def submit_quote(
        db: AsyncSession,
        opportunity_id: int,
        quoted_amount: Decimal,
        sales_userid: str,
        sales_name: str
    ) -> Opportunity:
        """
        提交报价
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            quoted_amount: 报价金额
            sales_userid: 销售UserID
            sales_name: 销售姓名
        
        Returns:
            更新后的商机对象
        """
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        opportunity.quoted_amount = quoted_amount
        opportunity.quoted_at = datetime.now()
        opportunity.status = 'quoted'
        opportunity.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'quote', opportunity_id, sales_userid, sales_name,
            {'action': '提交报价', 'amount': float(quoted_amount)}
        )
        
        return opportunity
    
    @staticmethod
    async def mark_as_won(
        db: AsyncSession,
        opportunity_id: int,
        sales_userid: str,
        sales_name: str
    ) -> Opportunity:
        """
        标记商机为成交
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            sales_userid: 销售UserID
            sales_name: 销售姓名
        
        Returns:
            更新后的商机对象
        """
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        opportunity.status = 'won'
        opportunity.won_at = datetime.now()
        opportunity.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'win', opportunity_id, sales_userid, sales_name,
            {'action': '商机成交'}
        )
        
        return opportunity
    
    @staticmethod
    async def mark_as_lost(
        db: AsyncSession,
        opportunity_id: int,
        lost_reason: str,
        sales_userid: str,
        sales_name: str
    ) -> Opportunity:
        """
        标记商机为丢单
        
        Args:
            db: 数据库会话
            opportunity_id: 商机ID
            lost_reason: 丢单原因
            sales_userid: 销售UserID
            sales_name: 销售姓名
        
        Returns:
            更新后的商机对象
        """
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"商机ID {opportunity_id} 不存在")
        
        opportunity.status = 'lost'
        opportunity.lost_at = datetime.now()
        opportunity.lost_reason = lost_reason
        opportunity.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(opportunity)
        
        # 记录操作日志
        await OpportunityService._log_operation(
            db, 'lost', opportunity_id, sales_userid, sales_name,
            {'action': '商机丢失', 'reason': lost_reason}
        )
        
        return opportunity
    
    @staticmethod
    async def get_opportunities_by_sales(
        db: AsyncSession,
        sales_userid: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Opportunity]:
        """
        查询销售人员的商机列表
        
        Args:
            db: 数据库会话
            sales_userid: 销售UserID
            status: 商机状态（可选）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            商机列表
        """
        query = select(Opportunity).where(Opportunity.sales_userid == sales_userid)
        
        if status:
            query = query.where(Opportunity.status == status)
        
        query = query.order_by(Opportunity.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_opportunity_stats(
        db: AsyncSession,
        sales_userid: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        获取商机统计数据
        
        Args:
            db: 数据库会话
            sales_userid: 销售UserID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计数据字典
        """
        query = select(Opportunity).where(Opportunity.sales_userid == sales_userid)
        
        if start_date:
            query = query.where(Opportunity.created_at >= start_date)
        if end_date:
            query = query.where(Opportunity.created_at <= end_date)
        
        result = await db.execute(query)
        opportunities = result.scalars().all()
        
        stats = {
            'total_count': len(opportunities),
            'new_count': sum(1 for o in opportunities if o.status == 'new'),
            'contacted_count': sum(1 for o in opportunities if o.status == 'contacted'),
            'quoted_count': sum(1 for o in opportunities if o.status == 'quoted'),
            'negotiating_count': sum(1 for o in opportunities if o.status == 'negotiating'),
            'won_count': sum(1 for o in opportunities if o.status == 'won'),
            'lost_count': sum(1 for o in opportunities if o.status == 'lost'),
            'total_estimated_amount': sum(o.estimated_amount or 0 for o in opportunities),
            'total_won_amount': sum(o.quoted_amount or 0 for o in opportunities if o.status == 'won'),
            'win_rate': round(100.0 * sum(1 for o in opportunities if o.status == 'won') / len(opportunities), 2) if opportunities else 0
        }
        
        return stats
    
    @staticmethod
    async def _log_operation(
        db: AsyncSession,
        operation_type: str,
        opportunity_id: int,
        operator_userid: str,
        operator_name: str,
        detail: Dict,
        source: str = 'group_bot'
    ):
        """记录操作日志"""
        log = OperationLog(
            operation_type=operation_type,
            entity_type='opportunity',
            entity_id=opportunity_id,
            operator_userid=operator_userid,
            operator_name=operator_name,
            operation_source=source,
            operation_detail=detail,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
