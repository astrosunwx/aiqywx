"""客户识别与项目关联服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Customer, Project
from typing import List, Optional


class CustomerIdentificationService:
    """客户自动识别服务"""
    
    @staticmethod
    async def get_customer_by_wechat_id(db: AsyncSession, wechat_id: str) -> Optional[Customer]:
        """通过企业微信ID获取客户信息"""
        result = await db.execute(
            select(Customer).where(Customer.wechat_openid == wechat_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_customer_projects(db: AsyncSession, customer_phone: str) -> List[Project]:
        """获取客户的所有项目"""
        result = await db.execute(
            select(Project).where(Project.customer_phone == customer_phone)
        )
        return result.scalars().all()
    
    @staticmethod
    async def auto_identify_customer_and_project(
        db: AsyncSession,
        wechat_id: str,
        message: str
    ) -> dict:
        """
        智能识别客户与项目
        如果客户只有一个项目，自动关联
        如果有多个项目，要求客户选择
        """
        # 1. 通过微信ID查找客户
        customer = await CustomerIdentificationService.get_customer_by_wechat_id(db, wechat_id)
        
        if not customer:
            return {
                "status": "customer_not_found",
                "response": "您好！为了更好地为您服务，请先提供您的手机号。"
            }
        
        # 2. 查询客户的所有项目
        projects = await CustomerIdentificationService.get_customer_projects(db, customer.phone)
        
        if not projects:
            return {
                "status": "no_projects",
                "response": f"您好{customer.name or ''}！未找到您的相关项目记录，请联系销售人员。"
            }
        
        # 3. 只有一个项目，自动关联
        if len(projects) == 1:
            return {
                "status": "single_project",
                "customer": customer,
                "project": projects[0],
                "response": f"已为您定位到项目：{projects[0].title}，请描述您遇到的问题。"
            }
        
        # 4. 多个项目，让客户选择
        project_list = "\n".join([
            f"【项目{chr(65+i)}】{p.title}" 
            for i, p in enumerate(projects[:5])  # 最多显示5个
        ])
        
        return {
            "status": "multiple_projects",
            "customer": customer,
            "projects": projects,
            "response": f"""【智能助手】您好！请问是需要为哪个项目申请售后服务？

{project_list}

请回复项目编号（如：A）或项目名称。"""
        }
    
    @staticmethod
    def extract_project_from_message(message: str, projects: List[Project]) -> Optional[Project]:
        """从消息中提取项目选择"""
        message_upper = message.upper().strip()
        
        # 尝试匹配项目编号（A、B、C等）
        if len(message_upper) == 1 and 'A' <= message_upper <= 'Z':
            index = ord(message_upper) - ord('A')
            if 0 <= index < len(projects):
                return projects[index]
        
        # 尝试匹配项目名称
        for project in projects:
            if project.title in message or message in project.title:
                return project
        
        return None
