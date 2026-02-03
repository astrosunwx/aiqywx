"""
消息管理系统数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base
import enum


class MessageStatus(enum.Enum):
    """消息状态枚举"""
    PENDING = "pending"  # 待发送
    PROCESSING = "processing"  # 发送中
    SUCCESS = "success"  # 发送成功
    FAILED = "failed"  # 发送失败
    CANCELLED = "cancelled"  # 已取消


class MessageChannel(enum.Enum):
    """消息渠道枚举"""
    WEWORK = "wework"  # 企业微信
    WECHAT = "wechat"  # 微信公众号
    SMS = "sms"  # 短信
    EMAIL = "email"  # 邮箱


class MessageTemplate(Base):
    """消息模板表"""
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(50), unique=True, nullable=False, index=True, comment='模板代码')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    template_type = Column(String(20), nullable=False, comment='模板类型：instant/scheduled')
    channel = Column(String(20), nullable=False, comment='发送渠道')
    title = Column(String(200), comment='标题')
    content_template = Column(Text, nullable=False, comment='内容模板（支持变量）')
    variables = Column(JSONB, comment='变量列表')
    send_rules = Column(JSONB, comment='发送规则（时间、频率等）')
    is_active = Column(Boolean, default=True, comment='是否启用')
    priority = Column(Integer, default=0, comment='优先级（越大越优先）')
    created_by = Column(String(100), comment='创建人')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("template_type IN ('instant', 'scheduled')"),
        CheckConstraint("channel IN ('wework', 'wechat', 'sms', 'email')"),
    )


class MessageTask(Base):
    """消息发送任务表"""
    __tablename__ = "message_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True, comment='任务ID')
    template_id = Column(Integer, ForeignKey('message_templates.id'), comment='模板ID')
    template_code = Column(String(50), comment='模板代码（冗余）')
    
    # 发送目标
    target_type = Column(String(20), comment='目标类型：single/batch/broadcast')
    target_phones = Column(JSONB, comment='目标手机号列表')
    target_userids = Column(JSONB, comment='目标UserID列表')
    target_count = Column(Integer, default=0, comment='目标数量')
    
    # 消息内容
    title = Column(String(200), comment='标题')
    content = Column(Text, comment='内容')
    variables_data = Column(JSONB, comment='变量数据')
    
    # 状态追踪
    status = Column(String(20), default='pending', index=True, comment='任务状态')
    scheduled_time = Column(TIMESTAMP, comment='计划发送时间')
    started_at = Column(TIMESTAMP, comment='开始时间')
    finished_at = Column(TIMESTAMP, comment='完成时间')
    
    # 发送统计
    total_count = Column(Integer, default=0, comment='总数')
    success_count = Column(Integer, default=0, comment='成功数')
    failed_count = Column(Integer, default=0, comment='失败数')
    
    # 限流控制
    rate_limit = Column(Integer, comment='发送速率限制（条/秒）')
    
    # 重试配置
    max_retry = Column(Integer, default=3, comment='最大重试次数')
    retry_count = Column(Integer, default=0, comment='当前重试次数')
    
    # 链路追踪
    trace_id = Column(String(100), index=True, comment='链路追踪ID')
    
    created_by = Column(String(100), comment='创建人')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'success', 'failed', 'cancelled')"),
        CheckConstraint("target_type IN ('single', 'batch', 'broadcast')"),
    )


class MessageRecord(Base):
    """消息发送记录表（单条消息）"""
    __tablename__ = "message_records"
    
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(100), unique=True, nullable=False, index=True, comment='记录ID')
    task_id = Column(String(100), ForeignKey('message_tasks.task_id'), index=True, comment='任务ID')
    
    # 接收方信息
    receiver_phone = Column(String(20), index=True, comment='接收者手机号')
    receiver_userid = Column(String(100), index=True, comment='接收者UserID')
    receiver_name = Column(String(100), comment='接收者姓名')
    
    # 消息内容
    channel = Column(String(20), comment='发送渠道')
    title = Column(String(200), comment='标题')
    content = Column(Text, comment='内容')
    
    # 状态追踪
    status = Column(String(20), default='pending', index=True, comment='发送状态')
    send_time = Column(TIMESTAMP, comment='发送时间')
    delivery_time = Column(TIMESTAMP, comment='送达时间')
    read_time = Column(TIMESTAMP, comment='阅读时间')
    
    # 结果信息
    error_code = Column(String(50), comment='错误码')
    error_message = Column(Text, comment='错误信息')
    retry_count = Column(Integer, default=0, comment='重试次数')
    
    # 第三方响应
    third_party_id = Column(String(200), comment='第三方消息ID')
    third_party_response = Column(JSONB, comment='第三方响应数据')
    
    # 链路追踪
    trace_id = Column(String(100), index=True, comment='链路追踪ID')
    duration_ms = Column(Integer, comment='处理耗时（毫秒）')
    
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'success', 'failed', 'cancelled')"),
        CheckConstraint("channel IN ('wework', 'wechat', 'sms', 'email')"),
    )


class MessageTrace(Base):
    """消息链路追踪表"""
    __tablename__ = "message_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(100), index=True, comment='链路追踪ID')
    record_id = Column(String(100), index=True, comment='消息记录ID')
    
    # 链路节点
    node_name = Column(String(50), comment='节点名称')
    node_type = Column(String(20), comment='节点类型：queue/process/send/callback')
    
    # 时间信息
    started_at = Column(TIMESTAMP, comment='开始时间')
    finished_at = Column(TIMESTAMP, comment='完成时间')
    duration_ms = Column(Integer, comment='耗时（毫秒）')
    
    # 状态信息
    status = Column(String(20), comment='状态')
    error_message = Column(Text, comment='错误信息')
    
    # 详细数据
    input_data = Column(JSONB, comment='输入数据')
    output_data = Column(JSONB, comment='输出数据')
    extra_metadata = Column(JSONB, comment='元数据（线程ID、IP等）')
    
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("node_type IN ('queue', 'process', 'send', 'callback')"),
    )


class MessageStatistics(Base):
    """消息统计表（按日汇总）"""
    __tablename__ = "message_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(TIMESTAMP, nullable=False, index=True, comment='统计日期')
    stat_hour = Column(Integer, comment='统计小时（0-23）')
    
    # 维度
    channel = Column(String(20), comment='渠道')
    template_code = Column(String(50), comment='模板代码')
    
    # 发送统计
    total_count = Column(Integer, default=0, comment='总发送量')
    success_count = Column(Integer, default=0, comment='成功数')
    failed_count = Column(Integer, default=0, comment='失败数')
    
    # 性能统计
    avg_duration_ms = Column(Integer, comment='平均耗时')
    max_duration_ms = Column(Integer, comment='最大耗时')
    min_duration_ms = Column(Integer, comment='最小耗时')
    
    # 到达率统计
    delivered_count = Column(Integer, default=0, comment='送达数')
    read_count = Column(Integer, default=0, comment='阅读数')
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ThreadPoolConfig(Base):
    """动态线程池配置表"""
    __tablename__ = "thread_pool_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_name = Column(String(50), unique=True, nullable=False, comment='线程池名称')
    
    # 核心配置
    core_pool_size = Column(Integer, default=10, comment='核心线程数')
    max_pool_size = Column(Integer, default=50, comment='最大线程数')
    queue_capacity = Column(Integer, default=1000, comment='队列容量')
    keep_alive_seconds = Column(Integer, default=60, comment='空闲线程存活时间')
    
    # 动态调整参数
    auto_scale = Column(Boolean, default=True, comment='是否自动扩缩容')
    scale_up_threshold = Column(Integer, default=80, comment='扩容阈值（队列使用率%）')
    scale_down_threshold = Column(Integer, default=20, comment='缩容阈值（队列使用率%）')
    
    # 监控阈值
    alert_threshold = Column(Integer, default=90, comment='告警阈值（队列使用率%）')
    
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class RateLimitConfig(Base):
    """限流配置表"""
    __tablename__ = "rate_limit_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), unique=True, nullable=False, comment='规则名称')
    
    # 限流维度
    limit_type = Column(String(20), comment='限流类型：api/user/ip/global')
    resource = Column(String(100), comment='资源标识')
    
    # 限流参数
    limit_count = Column(Integer, comment='限流次数')
    limit_period = Column(Integer, comment='限流周期（秒）')
    
    # Sentinel配置
    grade = Column(String(20), default='QPS', comment='限流模式：QPS/Thread')
    control_behavior = Column(String(20), default='Reject', comment='流控效果')
    
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("limit_type IN ('api', 'user', 'ip', 'global')"),
    )
