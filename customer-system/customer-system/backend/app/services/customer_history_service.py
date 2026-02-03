"""
客户历史工单查询服务
实现智能关联：根据客户ID自动带出相关产品和历史工单
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from datetime import datetime, timedelta
from ..models import Project, Customer


class CustomerHistoryService:
    """客户历史工单查询服务"""
    
    @staticmethod
    async def get_customer_tickets_summary(
        db: AsyncSession,
        customer_id: int = None,
        customer_phone: str = None
    ) -> Dict[str, Any]:
        """
        获取客户工单汇总
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            customer_phone: 客户手机号
        
        Returns:
            客户工单汇总数据
        """
        
        # 查询客户
        if customer_id:
            stmt = select(Customer).where(Customer.id == customer_id)
        elif customer_phone:
            stmt = select(Customer).where(Customer.phone == customer_phone)
        else:
            raise ValueError("必须提供customer_id或customer_phone")
        
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            return {
                "customer": None,
                "total_tickets": 0,
                "pending_tickets": 0,
                "resolved_tickets": 0,
                "recent_tickets": [],
                "products": []
            }
        
        # 查询该客户的所有工单
        stmt = select(Project).where(
            or_(
                Project.customer_id == customer.id,
                Project.customer_phone == customer.phone
            )
        ).order_by(desc(Project.created_at))
        
        result = await db.execute(stmt)
        all_tickets = list(result.scalars().all())
        
        # 统计数据
        total_tickets = len(all_tickets)
        pending_tickets = len([t for t in all_tickets if t.status in ['pending', 'assigned', 'processing']])
        resolved_tickets = len([t for t in all_tickets if t.status in ['resolved', 'closed']])
        
        # 最近5个工单
        recent_tickets = all_tickets[:5]
        
        # 提取产品/项目列表（去重）
        products = list(set([t.title for t in all_tickets if t.title]))
        
        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "company": customer.company,
                "email": customer.email
            },
            "total_tickets": total_tickets,
            "pending_tickets": pending_tickets,
            "resolved_tickets": resolved_tickets,
            "recent_tickets": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "progress": t.progress,
                    "created_at": t.created_at.isoformat(),
                    "assigned_to": t.assigned_to_name
                }
                for t in recent_tickets
            ],
            "products": products,
            "customer_since": customer.created_at.isoformat() if customer.created_at else None
        }
    
    @staticmethod
    async def get_similar_issues(
        db: AsyncSession,
        description: str,
        limit: int = 5
    ) -> List[Project]:
        """
        查询类似问题（基于关键词匹配）
        
        Args:
            db: 数据库会话
            description: 问题描述
            limit: 返回数量限制
        
        Returns:
            类似问题工单列表
        """
        
        # 提取关键词（简化处理）
        keywords = []
        common_words = ['无法', '不能', '失败', '错误', '问题', '登录', '连接', '服务器', '网络']
        
        for word in common_words:
            if word in description:
                keywords.append(word)
        
        if not keywords:
            return []
        
        # 查询包含这些关键词的历史工单
        conditions = []
        for keyword in keywords:
            conditions.append(Project.description.like(f'%{keyword}%'))
        
        stmt = select(Project).where(
            and_(
                Project.project_type == 'aftersale',
                Project.status == 'resolved',  # 仅查询已解决的
                or_(*conditions)
            )
        ).order_by(desc(Project.updated_at)).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def generate_customer_report(
        db: AsyncSession,
        customer_id: int
    ) -> str:
        """
        生成客户服务报告（Markdown格式）
        
        用于在群里快速展示客户历史
        """
        
        summary = await CustomerHistoryService.get_customer_tickets_summary(
            db, customer_id=customer_id
        )
        
        if not summary['customer']:
            return "❌ 客户不存在"
        
        customer = summary['customer']
        
        report = f"""### 📊 客户服务报告

**客户信息**
> 姓名：{customer['name'] or '未填写'}
> 公司：{customer['company'] or '未填写'}
> 联系：{customer['phone']}
> 邮箱：{customer['email'] or '未填写'}
> 客户自：{summary['customer_since'][:10] if summary['customer_since'] else '未知'}

**工单统计**
> 总工单数：{summary['total_tickets']}
> 待处理：{summary['pending_tickets']} 个
> 已解决：{summary['resolved_tickets']} 个

**涉及产品**
"""
        
        if summary['products']:
            for i, product in enumerate(summary['products'], 1):
                report += f"> {i}. {product}\n"
        else:
            report += "> 暂无记录\n"
        
        report += "\n**最近工单**\n"
        
        if summary['recent_tickets']:
            for ticket in summary['recent_tickets']:
                status_icon = {
                    'pending': '🟡',
                    'assigned': '🔵',
                    'processing': '🟢',
                    'escalated': '🔴',
                    'resolved': '✅',
                    'closed': '⚫'
                }.get(ticket['status'], '⚪')
                
                report += f"""> {status_icon} #{ticket['id']} {ticket['title'][:30]}
>    状态：{ticket['status']} | 进度：{ticket['progress']}% | 负责人：{ticket['assigned_to'] or '未分配'}
>    创建时间：{ticket['created_at'][:10]}

"""
        else:
            report += "> 暂无工单记录\n"
        
        return report
    
    @staticmethod
    async def get_customer_stats_by_period(
        db: AsyncSession,
        customer_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取客户在指定时间段内的统计数据
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            days: 统计天数
        
        Returns:
            统计数据
        """
        
        since_date = datetime.now() - timedelta(days=days)
        
        # 查询该时间段内的工单
        stmt = select(Project).where(
            and_(
                Project.customer_id == customer_id,
                Project.created_at >= since_date
            )
        )
        
        result = await db.execute(stmt)
        tickets = list(result.scalars().all())
        
        # 统计各状态数量
        status_counts = {}
        for ticket in tickets:
            status = ticket.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 平均处理时间（仅统计已解决的）
        resolved_tickets = [t for t in tickets if t.status in ['resolved', 'closed']]
        avg_resolution_hours = 0
        
        if resolved_tickets:
            total_hours = 0
            for ticket in resolved_tickets:
                if ticket.updated_at and ticket.created_at:
                    hours = (ticket.updated_at - ticket.created_at).total_seconds() / 3600
                    total_hours += hours
            avg_resolution_hours = int(total_hours / len(resolved_tickets))
        
        return {
            "period_days": days,
            "total_tickets": len(tickets),
            "status_breakdown": status_counts,
            "average_resolution_hours": avg_resolution_hours,
            "tickets_by_type": {
                "presale": len([t for t in tickets if t.project_type == 'presale']),
                "aftersale": len([t for t in tickets if t.project_type == 'aftersale']),
                "installation": len([t for t in tickets if t.project_type == 'installation'])
            }
        }
