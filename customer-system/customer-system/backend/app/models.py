from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, TIMESTAMP, ARRAY, CheckConstraint, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))
    company = Column(String(100), comment='公司名称')
    
    # 企业微信和公众号绑定字段
    wework_userid = Column(String(64), index=True, comment='企业微信客户UserID')
    wechat_openid = Column(String(64), index=True, comment='公众号OpenID')
    
    # 绑定状态管理
    binding_status = Column(String(20), default='unbound', index=True, comment='绑定状态：unbound/temp/bound')
    bound_at = Column(TIMESTAMP, comment='正式绑定时间')
    bound_by = Column(String(100), comment='绑定操作的员工UserID')
    
    # 可信用户标识（绑定后自动变为True，拥有查询和售后权限）
    is_verified = Column(Boolean, default=False, index=True, comment='是否为可信用户（已通过企业微信验证）')
    verified_at = Column(TIMESTAMP, comment='验证通过时间')
    
    # 客户类型管理
    customer_type = Column(String(20), default='prospect', index=True, comment='客户类型：prospect-商机, customer-正式客户, cancelled-取消客户')
    has_active_order = Column(Boolean, default=False, index=True, comment='是否有有效订单')
    first_order_at = Column(TIMESTAMP, comment='首次下单时间')
    last_order_cancel_at = Column(TIMESTAMP, comment='最后一次订单取消时间')
    
    # 原有字段
    sales_representative = Column(String(100))  # 销售代表UserID（如：chenghong）
    sales_representative_name = Column(String(100))  # 销售代表姓名（如：程红）
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("binding_status IN ('unbound', 'temp', 'bound')"),
        CheckConstraint("customer_type IN ('prospect', 'customer', 'cancelled')"),
    )

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String(20), nullable=False)
    customer_id = Column(Integer, index=True)  # 关联客户ID
    project_type = Column(String(20))
    status = Column(String(20))
    title = Column(String(200))
    description = Column(String)
    amount = Column(DECIMAL(10, 2))
    sales_id = Column(Integer)
    engineer_id = Column(Integer)
    
    # 工单处理相关字段
    assigned_to = Column(String(100))  # 负责人（企业微信UserID）
    assigned_to_name = Column(String(100))  # 负责人姓名
    progress = Column(Integer, default=0)  # 处理进度（0-100）
    priority = Column(String(20), default='normal')  # 优先级：low, normal, high, urgent
    
    # 项目链接字段
    project_link_token = Column(String(100), unique=True, index=True, comment='项目详情链接Token')
    
    def generate_project_link(self, base_url: str) -> str:
        """生成项目详情链接"""
        if not self.project_link_token:
            import secrets
            self.project_link_token = secrets.token_urlsafe(32)
        return f"{base_url}/project/{self.project_link_token}"
    deadline = Column(TIMESTAMP)  # 处理期限
    
    # 催促与提醒
    reminder_count = Column(Integer, default=0)  # 催促次数
    last_reminder_at = Column(TIMESTAMP)  # 最后催促时间
    
    # 消息关联
    group_message_id = Column(String(200))  # 内部群消息ID（用于回复监听）
    
    # 客户关系转接记录
    original_sales_userid = Column(String(100))  # 原销售UserID（用于转回）
    transfer_timestamp = Column(TIMESTAMP)  # 转接时间
    transfer_reason = Column(String(500))  # 转接原因
    
    # 电器设备行业扩展字段
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True, index=True)
    root_cause = Column(Text, comment='故障根本原因')
    solution = Column(Text, comment='解决方案')
    parts_used = Column(JSONB, comment='使用的配件（JSON格式）')
    service_duration_hours = Column(DECIMAL(5, 2), comment='服务时长（小时）')
    customer_rating = Column(Integer, comment='客户评分')
    customer_feedback = Column(Text, comment='客户反馈')
    
    # 多联系人支持
    additional_contacts = Column(JSONB, default=[], comment='项目额外联系人列表（JSON数组）')
    
    remote_project_id = Column(String(100))
    binding_type = Column(String(20))
    binding_expires_at = Column(TIMESTAMP)
    notification_sent = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("project_type IN ('presale', 'installation', 'aftersale')"),
        CheckConstraint("status IN ('pending', 'assigned', 'processing', 'escalated', 'resolved', 'closed', 'cancelled')"),
        CheckConstraint("binding_type IN ('temporary', 'permanent')"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')"),
        CheckConstraint("customer_rating >= 1 AND customer_rating <= 5"),
    )

class WeChatSession(Base):
    __tablename__ = "wechat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    customer_wechat_id = Column(String(100), index=True)
    employee_wechat_id = Column(String(100))
    session_type = Column(String(20))
    related_project_ids = Column(ARRAY(Integer))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("session_type IN ('external', 'internal')"),
    )

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(String(500))
    description = Column(String)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# ============================================================================
# 电器设备行业扩展模型
# ============================================================================

class Opportunity(Base):
    """商机表"""
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100))
    product_name = Column(String(200), comment='产品名称')
    quantity = Column(Integer, default=1, comment='数量')
    estimated_amount = Column(DECIMAL(10, 2), comment='预计金额')
    status = Column(String(20), default='new', comment='状态')
    sales_userid = Column(String(100), index=True, comment='销售UserID')
    sales_name = Column(String(100), comment='销售姓名')
    source = Column(String(50), comment='来源渠道')
    requirements = Column(Text, comment='客户需求描述')
    follow_up_notes = Column(JSONB, comment='跟进记录（JSON格式）')
    quoted_amount = Column(DECIMAL(10, 2), comment='报价金额')
    quoted_at = Column(TIMESTAMP, comment='报价时间')
    won_at = Column(TIMESTAMP, comment='成交时间')
    lost_at = Column(TIMESTAMP, comment='丢单时间')
    lost_reason = Column(String(500), comment='丢单原因')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    followed_up_at = Column(TIMESTAMP, comment='最后跟进时间')
    
    __table_args__ = (
        CheckConstraint("status IN ('new', 'contacted', 'quoted', 'negotiating', 'won', 'lost')"),
    )


class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True, comment='订单编号')
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100))
    product_name = Column(String(200))
    quantity = Column(Integer)
    unit_price = Column(DECIMAL(10, 2))
    total_amount = Column(DECIMAL(10, 2))
    status = Column(String(20), default='pending', index=True, comment='状态')
    sales_userid = Column(String(100))
    sales_name = Column(String(100))
    delivery_address = Column(Text, comment='配送地址')
    delivery_contact = Column(String(100), comment='配送联系人')
    delivery_phone = Column(String(20), comment='配送联系电话')
    delivery_date = Column(Date, comment='计划配送日期')
    delivered_at = Column(TIMESTAMP, comment='实际配送时间')
    install_date = Column(Date, comment='计划安装日期')
    installed_at = Column(TIMESTAMP, comment='实际安装时间')
    installer_userid = Column(String(100), comment='安装人员UserID')
    installer_name = Column(String(100), comment='安装人员姓名')
    notes = Column(Text, comment='订单备注')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'confirmed', 'paid', 'delivered', 'installed', 'completed', 'cancelled')"),
    )


class Equipment(Base):
    """设备档案表"""
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_no = Column(String(50), unique=True, nullable=False, index=True, comment='设备编号')
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100))
    equipment_type = Column(String(50), comment='设备类型')
    brand = Column(String(50), comment='品牌')
    model = Column(String(100), comment='型号')
    serial_number = Column(String(100), comment='序列号')
    install_date = Column(Date, comment='安装日期')
    install_location = Column(String(200), comment='安装位置')
    warranty_months = Column(Integer, default=36, comment='保修月数')
    warranty_end_date = Column(Date, index=True, comment='保修截止日期')
    status = Column(String(20), default='in_use', index=True, comment='状态')
    maintenance_cycle_days = Column(Integer, default=90, comment='维护周期（天）')
    last_maintenance_date = Column(Date, comment='上次维护日期')
    next_maintenance_date = Column(Date, index=True, comment='下次维护日期')
    specifications = Column(JSONB, comment='设备规格参数（JSON格式）')
    notes = Column(Text, comment='备注')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('in_use', 'under_repair', 'retired')"),
    )


class MaintenanceRecord(Base):
    """维护记录表"""
    __tablename__ = "maintenance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_type = Column(String(20), comment='维护类型')
    maintenance_date = Column(Date, nullable=False, index=True)
    engineer_userid = Column(String(100))
    engineer_name = Column(String(100))
    work_description = Column(Text, comment='工作内容')
    parts_replaced = Column(JSONB, comment='更换配件（JSON格式）')
    cost = Column(DECIMAL(10, 2), comment='费用')
    next_maintenance_date = Column(Date, comment='建议下次维护日期')
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, comment='关联工单ID')
    photos = Column(ARRAY(String), comment='维护照片URLs')
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("maintenance_type IN ('routine', 'repair', 'upgrade')"),
    )


class PartsInventory(Base):
    """配件库存表"""
    __tablename__ = "parts_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    part_code = Column(String(50), unique=True, nullable=False, index=True, comment='配件编码')
    part_name = Column(String(200), nullable=False, comment='配件名称')
    category = Column(String(50), index=True, comment='配件类别')
    specification = Column(String(200), comment='规格型号')
    applicable_models = Column(Text, comment='适用设备型号')
    stock_quantity = Column(Integer, default=0, index=True, comment='库存数量')
    unit_price = Column(DECIMAL(10, 2), comment='单价')
    supplier = Column(String(100), comment='供应商')
    supplier_contact = Column(String(100), comment='供应商联系方式')
    min_stock_alert = Column(Integer, default=5, comment='最低库存预警')
    location = Column(String(100), comment='存放位置')
    notes = Column(Text, comment='备注')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class PartsUsage(Base):
    """配件领用记录表"""
    __tablename__ = "parts_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True, comment='关联工单ID')
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    part_code = Column(String(50), ForeignKey("parts_inventory.part_code", ondelete="RESTRICT"), nullable=False, index=True)
    part_name = Column(String(200))
    quantity = Column(Integer, nullable=False, comment='领用数量')
    unit_price = Column(DECIMAL(10, 2), comment='领用时单价')
    total_cost = Column(DECIMAL(10, 2), comment='总成本')
    engineer_userid = Column(String(100))
    engineer_name = Column(String(100))
    usage_date = Column(Date, nullable=False, index=True)
    purpose = Column(String(20), comment='用途')
    approved_by = Column(String(100), comment='批准人')
    notes = Column(Text, comment='备注')
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("purpose IN ('repair', 'maintenance', 'replacement')"),
    )


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), comment='操作类型')
    entity_type = Column(String(50), index=True, comment='实体类型')
    entity_id = Column(Integer, index=True, comment='实体ID')
    operator_userid = Column(String(100), index=True)
    operator_name = Column(String(100))
    operation_source = Column(String(20), comment='操作来源')
    operation_detail = Column(JSONB, comment='操作详情（JSON格式）')
    ip_address = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("operation_source IN ('group_bot', 'web_ui', 'api', 'system')"),
    )


class DataDictionary(Base):
    """数据字典表"""
    __tablename__ = "data_dictionary"
    
    id = Column(Integer, primary_key=True, index=True)
    dict_type = Column(String(50), nullable=False, comment='字典类型')
    dict_code = Column(String(50), nullable=False, comment='字典编码')
    dict_value = Column(String(200), nullable=False, comment='字典值')
    dict_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


# ============================================================================
# 自动绑定流程相关模型
# ============================================================================

class TempBinding(Base):
    """临时绑定表 - 公众号用户等待企业微信添加"""
    __tablename__ = "temp_bindings"
    
    id = Column(Integer, primary_key=True, index=True)
    wechat_openid = Column(String(64), nullable=False, index=True, comment='公众号OpenID')
    phone_number = Column(String(20), nullable=False, index=True, comment='手机号')
    customer_name = Column(String(100), comment='客户姓名（可选）')
    source = Column(String(50), default='wechat_official', comment='来源')
    status = Column(String(20), default='waiting', index=True, comment='状态')
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP, server_default=func.now() + func.make_interval(0, 0, 0, 2), index=True, comment='过期时间（2天后）')
    bound_at = Column(TIMESTAMP, comment='绑定完成时间')
    
    __table_args__ = (
        CheckConstraint("status IN ('waiting', 'bound', 'expired')"),
    )


class WeWorkCustomerEvent(Base):
    """企业微信客户添加事件记录表"""
    __tablename__ = "wework_customer_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, comment='事件类型')
    employee_userid = Column(String(100), nullable=False, comment='员工UserID')
    employee_name = Column(String(100), comment='员工姓名')
    external_userid = Column(String(100), nullable=False, index=True, comment='外部联系人UserID')
    customer_phone = Column(String(20), index=True, comment='客户手机号')
    customer_name = Column(String(100), comment='客户姓名')
    add_way = Column(Integer, comment='添加方式：1-扫描二维码 2-搜索手机号 3-名片分享')
    welcome_code = Column(String(100), comment='欢迎语code')
    state = Column(String(200), comment='自定义state参数')
    raw_event = Column(JSONB, comment='原始事件数据')
    processed = Column(Boolean, default=False, index=True, comment='是否已处理')
    processed_at = Column(TIMESTAMP, comment='处理时间')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("event_type IN ('add_external_contact', 'del_external_contact', 'edit_external_contact')"),
        CheckConstraint("add_way IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 201, 202)"),  # 企业微信定义的添加方式
    )


class AfterSalesTicket(Base):
    """售后工单表 - 客户可在公众号或企业微信提交售后请求"""
    __tablename__ = "after_sales_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_no = Column(String(50), unique=True, nullable=False, index=True, comment='工单编号')
    
    # 客户信息
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    customer_phone = Column(String(20), nullable=False, index=True, comment='客户手机号')
    customer_name = Column(String(100), comment='客户姓名')
    
    # 关联项目/订单
    project_id = Column(Integer, ForeignKey('projects.id'), index=True, comment='关联项目ID')
    project_title = Column(String(200), comment='项目标题')
    
    # 工单内容
    ticket_type = Column(String(50), nullable=False, comment='工单类型：maintenance/repair/complaint/consultation/return')
    subject = Column(String(200), nullable=False, comment='工单主题')
    description = Column(Text, comment='详细描述')
    attachments = Column(JSONB, comment='附件列表（图片、文件URL）')
    
    # 处理信息
    status = Column(String(20), default='pending', index=True, comment='状态：pending/processing/resolved/closed/cancelled')
    priority = Column(String(20), default='normal', comment='优先级：low/normal/high/urgent')
    assigned_to = Column(String(100), index=True, comment='处理人UserID')
    assigned_to_name = Column(String(100), comment='处理人姓名')
    assigned_at = Column(TIMESTAMP, comment='分配时间')
    
    # 处理记录
    response_content = Column(Text, comment='处理回复')
    resolution = Column(Text, comment='解决方案')
    resolved_at = Column(TIMESTAMP, comment='解决时间')
    closed_at = Column(TIMESTAMP, comment='关闭时间')
    
    # 来源渠道
    source = Column(String(20), default='wechat', comment='来源：wechat/wework/web')
    source_openid = Column(String(100), comment='公众号OpenID或企业微信ExternalUserID')
    
    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 消息推送记录
    notification_sent = Column(Boolean, default=False, comment='是否已推送通知')
    notification_sent_at = Column(TIMESTAMP, comment='推送时间')
    
    __table_args__ = (
        CheckConstraint("ticket_type IN ('maintenance', 'repair', 'complaint', 'consultation', 'return', 'refund')"),
        CheckConstraint("status IN ('pending', 'processing', 'resolved', 'closed', 'cancelled')"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')"),
        CheckConstraint("source IN ('wechat', 'wework', 'web')"),
    )


class OrderModification(Base):
    """订单修改记录表 - 记录客户的订单变更/退订请求"""
    __tablename__ = "order_modifications"
    
    id = Column(Integer, primary_key=True, index=True)
    modification_no = Column(String(50), unique=True, nullable=False, index=True, comment='变更单号')
    
    # 客户信息
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100))
    
    # 关联项目/订单
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    project_title = Column(String(200))
    
    # 变更类型
    modification_type = Column(String(50), nullable=False, comment='变更类型：modify/cancel/refund')
    
    # 变更内容
    modification_content = Column(JSONB, nullable=False, comment='变更内容详情')
    reason = Column(Text, comment='变更原因')
    attachments = Column(JSONB, comment='附件（如退款凭证）')
    
    # 原始数据
    original_data = Column(JSONB, comment='原订单数据快照')
    modified_data = Column(JSONB, comment='修改后数据')
    
    # 审核状态
    status = Column(String(20), default='pending', index=True, comment='状态：pending/approved/rejected/processing/completed')
    
    # 审核信息
    reviewer_userid = Column(String(100), comment='审核人UserID')
    reviewer_name = Column(String(100), comment='审核人姓名')
    reviewed_at = Column(TIMESTAMP, comment='审核时间')
    review_comment = Column(Text, comment='审核意见')
    
    # 处理信息
    processor_userid = Column(String(100), comment='处理人UserID')
    processor_name = Column(String(100), comment='处理人姓名')
    processed_at = Column(TIMESTAMP, comment='处理完成时间')
    
    # 来源渠道
    source = Column(String(20), default='wechat', comment='来源：wechat/wework/web')
    
    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 消息推送记录
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(TIMESTAMP)
    
    __table_args__ = (
        CheckConstraint("modification_type IN ('modify', 'cancel', 'refund')"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'processing', 'completed', 'cancelled')"),
        CheckConstraint("source IN ('wechat', 'wework', 'web')"),
    )


class ProspectInquiry(Base):
    """商机咨询表 - 记录潜在客户的询价和咨询"""
    __tablename__ = "prospect_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    inquiry_no = Column(String(50), unique=True, nullable=False, index=True, comment='咨询单号')
    
    # 客户信息
    customer_phone = Column(String(20), index=True, comment='客户手机号')
    customer_name = Column(String(100), comment='客户姓名')
    customer_company = Column(String(200), comment='客户公司')
    customer_id = Column(Integer, ForeignKey('customers.id'), index=True, comment='关联客户ID')
    
    # 咨询内容
    inquiry_type = Column(String(50), default='product', comment='咨询类型')
    inquiry_content = Column(Text, comment='咨询内容')
    product_interest = Column(String(200), comment='感兴趣的产品')
    budget_range = Column(String(50), comment='预算范围')
    urgency = Column(String(20), default='normal', comment='紧急程度')
    
    # 来源渠道
    source = Column(String(20), default='wechat', comment='来源')
    source_openid = Column(String(100), comment='OpenID或ExternalUserID')
    
    # 处理状态
    status = Column(String(20), default='pending', index=True, comment='状态')
    assigned_to = Column(String(100), index=True, comment='分配给谁')
    assigned_to_name = Column(String(100), comment='销售顾问姓名')
    assigned_at = Column(TIMESTAMP, comment='分配时间')
    
    # 跟进记录
    follow_up_count = Column(Integer, default=0, comment='跟进次数')
    last_follow_up_at = Column(TIMESTAMP, comment='最后跟进时间')
    converted_to_customer = Column(Boolean, default=False, comment='是否转化为正式客户')
    converted_at = Column(TIMESTAMP, comment='转化时间')
    
    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 消息推送
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(TIMESTAMP)
    
    __table_args__ = (
        CheckConstraint("inquiry_type IN ('product', 'service', 'price', 'consultation', 'complaint')"),
        CheckConstraint("status IN ('pending', 'assigned', 'following', 'converted', 'lost')"),
        CheckConstraint("urgency IN ('low', 'normal', 'high', 'urgent')"),
        CheckConstraint("source IN ('wechat', 'wework', 'web', 'phone')"),
    )


class CustomerTypeChangeLog(Base):
    """客户身份变更日志表 - 记录商机→正式客户→取消客户的转换"""
    __tablename__ = "customer_type_change_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    customer_phone = Column(String(20), nullable=False, index=True)
    
    # 变更信息
    old_type = Column(String(20), comment='旧类型')
    new_type = Column(String(20), nullable=False, comment='新类型')
    change_reason = Column(String(100), nullable=False, comment='变更原因')
    
    # 触发原因
    trigger_event = Column(String(50), comment='触发事件')
    project_id = Column(Integer, comment='关联项目ID')
    order_id = Column(Integer, comment='关联订单ID')
    
    # 操作人
    operator_userid = Column(String(100), comment='操作人UserID')
    operator_name = Column(String(100), comment='操作人姓名')
    
    # 额外数据
    extra_data = Column(JSONB, comment='额外数据')
    
    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("old_type IN ('prospect', 'customer', 'cancelled')"),
        CheckConstraint("new_type IN ('prospect', 'customer', 'cancelled')"),
        CheckConstraint("change_reason IN ('first_order', 'order_cancelled', 'order_refunded', 'manual_change', 'wework_added')"),
    )


class CustomerServiceRequest(Base):
    """客户服务请求模型 - 不拒绝任何客户，记录并转给销售"""
    __tablename__ = 'customer_service_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    request_no = Column(String(50), unique=True, nullable=False, index=True)
    
    # 客户信息（可能还不是正式客户）
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer_type = Column(String(20))
    
    # 请求类型
    request_type = Column(String(50), nullable=False, index=True)  # query_order, modify_order, cancel_order, aftersales, inquiry
    request_content = Column(Text)
    urgency = Column(String(20), default='normal', index=True)  # low, normal, high, urgent
    
    # 来源
    source = Column(String(20), default='wechat')
    source_openid = Column(String(100))
    
    # 处理状态
    status = Column(String(20), default='pending', index=True)
    assigned_to = Column(String(100))
    assigned_to_name = Column(String(100))
    assigned_at = Column(TIMESTAMP)
    
    # 特殊标记
    needs_verification = Column(Boolean, default=False, index=True, comment='是否需要销售先添加客户')
    verification_note = Column(Text, comment='验证提示：商机用户/取消客户/未找到')
    
    # 处理记录
    response_content = Column(Text)
    resolved_at = Column(TIMESTAMP)
    
    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 消息推送
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(TIMESTAMP)
    
    __table_args__ = (
        CheckConstraint("request_type IN ('query_order', 'modify_order', 'cancel_order', 'aftersales', 'inquiry')", name='chk_request_type'),
        CheckConstraint("status IN ('pending', 'assigned', 'processing', 'resolved', 'closed')", name='chk_request_status'),
        CheckConstraint("urgency IN ('low', 'normal', 'high', 'urgent')", name='chk_request_urgency'),
    )


