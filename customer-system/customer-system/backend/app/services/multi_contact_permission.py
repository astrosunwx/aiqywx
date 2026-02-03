"""
多联系人项目权限服务
处理项目多联系人的查询权限验证
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models import Project, Customer
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MultiContactPermissionService:
    """多联系人项目权限服务"""
    
    @staticmethod
    async def check_project_access(
        db: AsyncSession,
        customer_phone: str,
        project_id: int
    ) -> Dict:
        """
        检查客户是否有权限访问项目
        
        权限规则：
        1. 主客户（project.customer_id = customer.id）→ 有权限
        2. 项目额外联系人（phone在additional_contacts中）→ 有权限
        3. 其他情况 → 无权限（走服务请求流程）
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
            project_id: 项目ID
        
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
                    'has_access': False,
                    'reason': 'customer_not_found',
                    'message': '未找到客户信息'
                }
            
            # 查找项目
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_null()
            
            if not project:
                return {
                    'has_access': False,
                    'reason': 'project_not_found',
                    'message': '项目不存在'
                }
            
            # 检查1：是否是主客户
            if project.customer_id == customer.id:
                return {
                    'has_access': True,
                    'access_type': 'primary_customer',
                    'message': '主客户，拥有完整权限'
                }
            
            # 检查2：是否在额外联系人列表中
            additional_contacts = project.additional_contacts or []
            
            for contact in additional_contacts:
                if contact.get('phone') == customer_phone:
                    return {
                        'has_access': True,
                        'access_type': 'additional_contact',
                        'contact_role': contact.get('role', '联系人'),
                        'message': f'项目联系人（{contact.get("role", "联系人")}），拥有查询权限'
                    }
            
            # 无权限
            return {
                'has_access': False,
                'reason': 'not_project_contact',
                'message': '您不是该项目的联系人，无法查询',
                'project_id': project_id,
                'customer_id': customer.id
            }
            
        except Exception as e:
            logger.error(f"检查项目访问权限失败: {str(e)}", exc_info=True)
            return {
                'has_access': False,
                'reason': 'system_error',
                'message': f'权限检查失败: {str(e)}'
            }
    
    @staticmethod
    async def get_accessible_projects(
        db: AsyncSession,
        customer_phone: str
    ) -> List[Project]:
        """
        获取客户可访问的所有项目
        
        包括：
        1. 主客户的项目（customer_id匹配）
        2. 作为额外联系人的项目（additional_contacts包含phone）
        
        Args:
            db: 数据库会话
            customer_phone: 客户手机号
        
        Returns:
            List[Project]: 可访问的项目列表
        """
        try:
            # 查找客户
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_phone)
            )
            customer = result.scalar_one_or_null()
            
            if not customer:
                return []
            
            # 查询项目：主客户 OR 额外联系人
            # PostgreSQL JSONB查询：additional_contacts @> '[{"phone":"13800138000"}]'
            result = await db.execute(
                select(Project).where(
                    or_(
                        # 条件1：主客户
                        Project.customer_id == customer.id,
                        # 条件2：额外联系人（JSONB数组包含该phone）
                        Project.additional_contacts.op('@>')(
                            f'[{{"phone":"{customer_phone}"}}]'
                        )
                    )
                )
            )
            projects = result.scalars().all()
            
            logger.info(
                f"客户 {customer_phone} 可访问 {len(projects)} 个项目 "
                f"（主客户项目 + 额外联系人项目）"
            )
            
            return projects
            
        except Exception as e:
            logger.error(f"获取可访问项目失败: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    async def add_project_contact(
        db: AsyncSession,
        project_id: int,
        phone: str,
        name: str,
        role: str = '联系人'
    ) -> Dict:
        """
        为项目添加额外联系人
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            phone: 联系人手机号
            name: 联系人姓名
            role: 联系人角色（如：技术负责人、采购负责人）
        
        Returns:
            Dict: 添加结果
        """
        try:
            # 查找项目
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_null()
            
            if not project:
                return {
                    'success': False,
                    'message': '项目不存在'
                }
            
            # 获取当前联系人列表
            additional_contacts = project.additional_contacts or []
            
            # 检查是否已存在
            for contact in additional_contacts:
                if contact.get('phone') == phone:
                    return {
                        'success': False,
                        'message': f'联系人 {phone} 已存在'
                    }
            
            # 添加新联系人
            new_contact = {
                'phone': phone,
                'name': name,
                'role': role
            }
            additional_contacts.append(new_contact)
            
            # 更新项目（注意：JSONB需要重新赋值才能触发更新）
            project.additional_contacts = additional_contacts
            
            await db.commit()
            
            logger.info(
                f"项目 {project_id} 添加联系人: {name}({phone}) - {role}"
            )
            
            return {
                'success': True,
                'message': f'已添加联系人 {name}',
                'contact': new_contact
            }
            
        except Exception as e:
            logger.error(f"添加项目联系人失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'添加失败: {str(e)}'
            }
    
    @staticmethod
    async def remove_project_contact(
        db: AsyncSession,
        project_id: int,
        phone: str
    ) -> Dict:
        """
        移除项目额外联系人
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            phone: 联系人手机号
        
        Returns:
            Dict: 移除结果
        """
        try:
            # 查找项目
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_null()
            
            if not project:
                return {
                    'success': False,
                    'message': '项目不存在'
                }
            
            # 获取当前联系人列表
            additional_contacts = project.additional_contacts or []
            
            # 过滤掉要删除的联系人
            updated_contacts = [
                contact for contact in additional_contacts 
                if contact.get('phone') != phone
            ]
            
            if len(updated_contacts) == len(additional_contacts):
                return {
                    'success': False,
                    'message': f'联系人 {phone} 不存在'
                }
            
            # 更新项目
            project.additional_contacts = updated_contacts
            
            await db.commit()
            
            logger.info(f"项目 {project_id} 移除联系人: {phone}")
            
            return {
                'success': True,
                'message': f'已移除联系人 {phone}'
            }
            
        except Exception as e:
            logger.error(f"移除项目联系人失败: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                'success': False,
                'message': f'移除失败: {str(e)}'
            }
