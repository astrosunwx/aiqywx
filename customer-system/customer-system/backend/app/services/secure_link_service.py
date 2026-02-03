"""
安全链接生成与验证服务
实现基于JWT的有时效性、唯一且与身份绑定的访问链接
"""
import jwt
import datetime
from typing import Optional, Dict, Any
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Customer, Project, WeChatSession
import os


class SecureLinkService:
    """安全链接管理服务"""
    
    # JWT密钥，建议从环境变量读取
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production-12345678")
    ALGORITHM = "HS256"
    
    # 链接有效期配置（小时）
    DEFAULT_EXPIRY_HOURS = 1  # 默认1小时
    LONG_EXPIRY_HOURS = 24    # 长期有效24小时
    
    @classmethod
    def generate_project_detail_link(
        cls,
        user_id: str,
        project_id: int,
        wechat_user_id: str,
        expiry_hours: int = None
    ) -> str:
        """
        生成项目详情访问链接
        
        Args:
            user_id: 企业微信用户ID
            project_id: 项目ID
            wechat_user_id: 微信会话用户ID（用于二次验证）
            expiry_hours: 过期时间（小时），默认1小时
            
        Returns:
            完整的安全访问URL
        """
        expiry = expiry_hours or cls.DEFAULT_EXPIRY_HOURS
        
        payload = {
            'user_id': user_id,
            'project_id': project_id,
            'wechat_user_id': wechat_user_id,
            'type': 'project_detail',
            'iat': datetime.datetime.utcnow(),  # 签发时间
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiry)
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
        # 从环境变量读取域名，或使用默认值
        domain = os.getenv("APP_DOMAIN", "http://localhost:8000")
        secure_url = f"{domain}/view/project-detail?token={token}"
        
        return secure_url
    
    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        验证令牌并返回解析后的数据
        
        Args:
            token: JWT令牌
            
        Returns:
            解析后的payload数据
            
        Raises:
            jwt.ExpiredSignatureError: 令牌已过期
            jwt.InvalidTokenError: 无效的令牌
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("链接已过期，请重新申请")
        except jwt.InvalidTokenError:
            raise ValueError("无效的访问链接")
    
    @classmethod
    async def verify_and_get_project_data(
        cls,
        token: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        验证令牌并获取项目数据
        
        Args:
            token: JWT令牌
            db: 数据库会话
            
        Returns:
            项目数据字典
        """
        # 1. 验证令牌
        payload = cls.verify_token(token)
        
        # 2. 提取信息
        user_id = payload.get('user_id')
        project_id = payload.get('project_id')
        wechat_user_id = payload.get('wechat_user_id')
        
        if not all([user_id, project_id, wechat_user_id]):
            raise ValueError("令牌数据不完整")
        
        # 3. 验证用户身份（可选的二次验证）
        stmt = select(WeChatSession).where(
            WeChatSession.wechat_user_id == wechat_user_id
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("用户身份验证失败")
        
        # 4. 获取项目数据
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError("项目不存在")
        
        # 5. 获取客户信息
        customer = None
        if project.customer_id:
            stmt = select(Customer).where(Customer.id == project.customer_id)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
        
        # 6. 组装返回数据
        project_data = {
            'id': project.id,
            'name': project.name,
            'type': project.type,
            'status': project.status,
            'progress': project.progress,
            'amount': float(project.amount) if project.amount else None,
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
            'description': project.description,
            'requirements': project.requirements,
            'technical_stack': project.technical_stack,
            'team_members': project.team_members,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'company': customer.company,
                'phone': customer.phone,
                'email': customer.email
            } if customer else None,
            'token_info': {
                'issued_at': payload.get('iat'),
                'expires_at': payload.get('exp'),
                'user_id': user_id
            }
        }
        
        return project_data
