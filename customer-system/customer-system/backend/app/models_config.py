"""
配置管理和权限系统的数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
# 从 models.py 导入共享的 OperationLog
from app.models import OperationLog


class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False, comment='角色名称')
    role_display_name = Column(String(100), nullable=False, comment='角色显示名称')
    description = Column(Text, comment='角色描述')
    permissions = Column(JSONB, default=[], comment='权限列表（JSON数组）')
    is_system = Column(Boolean, default=False, comment='是否系统角色（不可删除）')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AdminUser(Base):
    """管理员用户表"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    real_name = Column(String(100), comment='真实姓名')
    email = Column(String(100), comment='邮箱')
    phone = Column(String(20), comment='手机号')
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='SET NULL'), comment='角色ID')
    wework_userid = Column(String(100), index=True, comment='企业微信UserID（用于单点登录）')
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_login_at = Column(TIMESTAMP, comment='最后登录时间')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_code = Column(String(100), unique=True, nullable=False, comment='权限代码')
    permission_name = Column(String(100), nullable=False, comment='权限名称')
    module = Column(String(50), nullable=False, index=True, comment='所属模块')
    description = Column(Text, comment='权限描述')
    resource = Column(String(100), comment='资源路径')
    action = Column(String(50), comment='操作类型（read/write/delete/execute）')
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_at = Column(TIMESTAMP, server_default=func.now())


class ConfigGroup(Base):
    """系统配置分组表"""
    __tablename__ = "config_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_code = Column(String(50), unique=True, nullable=False, comment='分组代码')
    group_name = Column(String(100), nullable=False, comment='分组名称')
    description = Column(Text, comment='分组描述')
    sort_order = Column(Integer, default=0, comment='排序序号')
    icon = Column(String(50), comment='图标')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=func.now())


class EnhancedSystemConfig(Base):
    """增强的系统配置表"""
    __tablename__ = "enhanced_system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment='配置键')
    config_value = Column(Text, comment='配置值')
    config_type = Column(String(20), default='string', comment='配置类型：string/number/boolean/json/password')
    group_id = Column(Integer, ForeignKey('config_groups.id', ondelete='SET NULL'), index=True, comment='所属分组')
    display_name = Column(String(100), comment='显示名称')
    description = Column(Text, comment='配置说明')
    is_required = Column(Boolean, default=False, comment='是否必填')
    is_sensitive = Column(Boolean, default=False, comment='是否敏感信息')
    default_value = Column(Text, comment='默认值')
    validation_rule = Column(Text, comment='验证规则（正则表达式）')
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("config_type IN ('string', 'number', 'boolean', 'json', 'password')"),
    )


class WorkflowTemplate(Base):
    """业务流程模板表"""
    __tablename__ = "workflow_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(50), unique=True, nullable=False, index=True, comment='模板代码')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    template_type = Column(String(20), nullable=False, comment='模板类型：presale/aftersale/mixed/custom')
    description = Column(Text, comment='模板描述')
    workflow_steps = Column(JSONB, nullable=False, comment='流程步骤（JSON数组）')
    auto_rules = Column(JSONB, comment='自动化规则（JSON对象）')
    notification_config = Column(JSONB, comment='通知配置（JSON对象）')
    is_default = Column(Boolean, default=False, comment='是否默认模板')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("template_type IN ('presale', 'aftersale', 'mixed', 'custom')"),
    )


class RobotWebhook(Base):
    """群机器人配置表"""
    __tablename__ = "robot_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_name = Column(String(100), nullable=False, comment='Webhook名称')
    webhook_url = Column(Text, nullable=False, comment='Webhook URL')
    webhook_type = Column(String(50), comment='Webhook类型（新客户通知/日报/技术支援等）')
    description = Column(Text, comment='描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    send_count = Column(Integer, default=0, comment='发送次数统计')
    last_send_at = Column(TIMESTAMP, comment='最后发送时间')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
