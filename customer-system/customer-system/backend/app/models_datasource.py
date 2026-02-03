"""
数据源管理模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_name = Column(String(100), unique=True, nullable=False, comment="数据源名称")
    source_desc = Column(Text, comment="数据源描述")
    db_type = Column(String(20), nullable=False, comment="数据库类型")
    db_host = Column(String(200), nullable=False, comment="数据库主机")
    db_port = Column(Integer, nullable=False, comment="端口号")
    db_name = Column(String(100), nullable=False, comment="数据库名")
    db_username = Column(String(100), nullable=False, comment="用户名")
    db_password = Column(String(200), nullable=False, comment="密码")
    db_charset = Column(String(20), default="utf8mb4", comment="字符集")
    use_ssl = Column(Boolean, default=False, comment="是否启用SSL")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认数据源")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
