"""
AI模型配置数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class AIModelConfig(Base):
    """AI模型配置表"""
    __tablename__ = "ai_model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_code = Column(String(50), unique=True, nullable=False, index=True, comment='模型代码（唯一标识）')
    model_name = Column(String(100), nullable=False, comment='模型显示名称')
    provider = Column(String(50), nullable=False, comment='服务提供商：wework/zhipu/tencent/doubao/deepseek/custom')
    provider_display_name = Column(String(100), comment='提供商显示名称')
    model_version = Column(String(50), comment='模型版本')
    api_endpoint = Column(Text, comment='API端点URL')
    api_key = Column(Text, comment='API密钥（敏感信息）')
    extra_config = Column(JSON, comment='额外配置（JSON格式）')
    description = Column(Text, comment='模型描述')
    is_official = Column(Boolean, default=False, comment='是否官方企业微信API')
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_default = Column(Boolean, default=False, comment='是否默认模型')
    priority = Column(Integer, default=0, comment='优先级（数字越大优先级越高）')
    usage_count = Column(Integer, default=0, comment='使用次数统计')
    last_used_at = Column(TIMESTAMP, comment='最后使用时间')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AIModelUsageLog(Base):
    """AI模型使用日志表"""
    __tablename__ = "ai_model_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_code = Column(String(50), index=True, nullable=False, comment='模型代码')
    user_message = Column(Text, comment='用户消息')
    ai_response = Column(Text, comment='AI响应')
    intent = Column(String(50), comment='识别出的意图')
    confidence = Column(String(10), comment='置信度')
    response_time_ms = Column(Integer, comment='响应时间（毫秒）')
    success = Column(Boolean, default=True, comment='是否成功')
    error_message = Column(Text, comment='错误消息（如果失败）')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
