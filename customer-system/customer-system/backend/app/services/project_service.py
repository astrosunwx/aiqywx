from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Project, Customer
from typing import List, Optional

class ProjectService:
    """项目管理服务"""
    
    @staticmethod
    async def get_projects_by_phone(db: AsyncSession, phone: str, employee_id: Optional[int] = None) -> List[Project]:
        """
        根据手机号查询项目列表
        权限控制：仅本人和绑定员工可见
        """
        query = select(Project).where(Project.customer_phone == phone)
        
        if employee_id:
            # 员工只能查看自己负责的项目
            query = query.where(
                (Project.sales_id == employee_id) | (Project.engineer_id == employee_id)
            )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_project(db: AsyncSession, project_data: dict) -> Project:
        """创建新项目"""
        project = Project(**project_data)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    
    @staticmethod
    async def update_project_status(db: AsyncSession, project_id: int, new_status: str) -> Project:
        """更新项目状态"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project.status = new_status
        await db.commit()
        await db.refresh(project)
        return project
