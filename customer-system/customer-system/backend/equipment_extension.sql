-- 电器设备行业扩展数据库脚本
-- 在现有customer-system基础上增加商机、订单、设备档案、配件管理等功能

-- ============================================================================
-- 0. 客户表增强 + 临时绑定表（自动绑定流程）
-- ============================================================================

-- 为customers表添加企业微信和公众号绑定字段
ALTER TABLE customers 
    ADD COLUMN IF NOT EXISTS wework_userid VARCHAR(64) COMMENT '企业微信客户UserID',
    ADD COLUMN IF NOT EXISTS wechat_openid VARCHAR(64) COMMENT '公众号OpenID',
    ADD COLUMN IF NOT EXISTS company VARCHAR(100) COMMENT '公司名称',
    ADD COLUMN IF NOT EXISTS binding_status VARCHAR(20) DEFAULT 'unbound' COMMENT '绑定状态：unbound/temp/bound',
    ADD COLUMN IF NOT EXISTS bound_at TIMESTAMP COMMENT '正式绑定时间',
    ADD COLUMN IF NOT EXISTS bound_by VARCHAR(100) COMMENT '绑定操作的员工UserID';

CREATE INDEX IF NOT EXISTS idx_customers_wework_userid ON customers(wework_userid);
CREATE INDEX IF NOT EXISTS idx_customers_wechat_openid ON customers(wechat_openid);
CREATE INDEX IF NOT EXISTS idx_customers_binding_status ON customers(binding_status);

-- 临时绑定表（公众号用户等待企业微信添加）
CREATE TABLE IF NOT EXISTS temp_bindings (
    id SERIAL PRIMARY KEY,
    wechat_openid VARCHAR(64) NOT NULL COMMENT '公众号OpenID',
    phone_number VARCHAR(20) NOT NULL COMMENT '手机号',
    customer_name VARCHAR(100) COMMENT '客户姓名（可选）',
    source VARCHAR(50) DEFAULT 'wechat_official' COMMENT '来源：wechat_official',
    status VARCHAR(20) DEFAULT 'waiting' COMMENT '状态：waiting/bound/expired',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 days') COMMENT '过期时间（2天后）',
    bound_at TIMESTAMP COMMENT '绑定完成时间'
);

CREATE INDEX idx_temp_bindings_phone ON temp_bindings(phone_number);
CREATE INDEX idx_temp_bindings_openid ON temp_bindings(wechat_openid);
CREATE INDEX idx_temp_bindings_status ON temp_bindings(status);
CREATE INDEX idx_temp_bindings_expires ON temp_bindings(expires_at);

-- 企业微信客户添加记录表（用于追踪企业微信添加事件）
CREATE TABLE IF NOT EXISTS wework_customer_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型：add_external_contact/del_external_contact',
    employee_userid VARCHAR(100) NOT NULL COMMENT '员工UserID',
    employee_name VARCHAR(100) COMMENT '员工姓名',
    external_userid VARCHAR(100) NOT NULL COMMENT '外部联系人UserID',
    customer_phone VARCHAR(20) COMMENT '客户手机号',
    customer_name VARCHAR(100) COMMENT '客户姓名',
    add_way INTEGER COMMENT '添加方式：1-扫描二维码 2-搜索手机号 3-名片分享',
    welcome_code VARCHAR(100) COMMENT '欢迎语code',
    state VARCHAR(200) COMMENT '自定义state参数',
    raw_event JSONB COMMENT '原始事件数据',
    processed BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    processed_at TIMESTAMP COMMENT '处理时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wework_events_external_userid ON wework_customer_events(external_userid);
CREATE INDEX idx_wework_events_phone ON wework_customer_events(customer_phone);
CREATE INDEX idx_wework_events_processed ON wework_customer_events(processed);
CREATE INDEX idx_wework_events_created ON wework_customer_events(created_at);

-- ============================================================================
-- 1. 商机表 (opportunities)
-- ============================================================================
CREATE TABLE IF NOT EXISTS opportunities (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    product_name VARCHAR(200) COMMENT '产品名称',
    quantity INTEGER DEFAULT 1 COMMENT '数量',
    estimated_amount DECIMAL(10,2) COMMENT '预计金额',
    status VARCHAR(20) CHECK (status IN ('new', 'contacted', 'quoted', 'negotiating', 'won', 'lost')) DEFAULT 'new',
    sales_userid VARCHAR(100) COMMENT '销售UserID',
    sales_name VARCHAR(100) COMMENT '销售姓名',
    source VARCHAR(50) COMMENT '来源渠道：公众号、电话、转介绍',
    requirements TEXT COMMENT '客户需求描述',
    follow_up_notes TEXT COMMENT '跟进记录（JSON格式）',
    quoted_amount DECIMAL(10,2) COMMENT '报价金额',
    quoted_at TIMESTAMP COMMENT '报价时间',
    won_at TIMESTAMP COMMENT '成交时间',
    lost_at TIMESTAMP COMMENT '丢单时间',
    lost_reason VARCHAR(500) COMMENT '丢单原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    followed_up_at TIMESTAMP COMMENT '最后跟进时间'
);

CREATE INDEX idx_opportunities_customer_phone ON opportunities(customer_phone);
CREATE INDEX idx_opportunities_sales_userid ON opportunities(sales_userid);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at);

-- ============================================================================
-- 2. 订单表 (orders)
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL COMMENT '订单编号',
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    product_name VARCHAR(200),
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    status VARCHAR(20) CHECK (status IN ('pending', 'confirmed', 'paid', 'delivered', 'installed', 'completed', 'cancelled')) DEFAULT 'pending',
    sales_userid VARCHAR(100),
    sales_name VARCHAR(100),
    delivery_address TEXT COMMENT '配送地址',
    delivery_contact VARCHAR(100) COMMENT '配送联系人',
    delivery_phone VARCHAR(20) COMMENT '配送联系电话',
    delivery_date DATE COMMENT '计划配送日期',
    delivered_at TIMESTAMP COMMENT '实际配送时间',
    install_date DATE COMMENT '计划安装日期',
    installed_at TIMESTAMP COMMENT '实际安装时间',
    installer_userid VARCHAR(100) COMMENT '安装人员UserID',
    installer_name VARCHAR(100) COMMENT '安装人员姓名',
    notes TEXT COMMENT '订单备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ============================================================================
-- 3. 设备档案表 (equipment)
-- ============================================================================
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    equipment_no VARCHAR(50) UNIQUE NOT NULL COMMENT '设备编号',
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    equipment_type VARCHAR(50) COMMENT '设备类型：中央空调、冰箱、洗衣机等',
    brand VARCHAR(50) COMMENT '品牌',
    model VARCHAR(100) COMMENT '型号',
    serial_number VARCHAR(100) COMMENT '序列号',
    install_date DATE COMMENT '安装日期',
    install_location VARCHAR(200) COMMENT '安装位置',
    warranty_months INTEGER DEFAULT 36 COMMENT '保修月数',
    warranty_end_date DATE COMMENT '保修截止日期',
    status VARCHAR(20) CHECK (status IN ('in_use', 'under_repair', 'retired')) DEFAULT 'in_use',
    maintenance_cycle_days INTEGER DEFAULT 90 COMMENT '维护周期（天）',
    last_maintenance_date DATE COMMENT '上次维护日期',
    next_maintenance_date DATE COMMENT '下次维护日期',
    specifications JSONB COMMENT '设备规格参数（JSON格式）',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_equipment_equipment_no ON equipment(equipment_no);
CREATE INDEX idx_equipment_customer_phone ON equipment(customer_phone);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_equipment_next_maintenance_date ON equipment(next_maintenance_date);
CREATE INDEX idx_equipment_warranty_end_date ON equipment(warranty_end_date);

-- ============================================================================
-- 4. 维护记录表 (maintenance_records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    maintenance_type VARCHAR(20) CHECK (maintenance_type IN ('routine', 'repair', 'upgrade')) COMMENT '维护类型',
    maintenance_date DATE NOT NULL,
    engineer_userid VARCHAR(100),
    engineer_name VARCHAR(100),
    work_description TEXT COMMENT '工作内容',
    parts_replaced JSONB COMMENT '更换配件（JSON格式）',
    cost DECIMAL(10,2) COMMENT '费用',
    next_maintenance_date DATE COMMENT '建议下次维护日期',
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL COMMENT '关联工单ID',
    photos TEXT[] COMMENT '维护照片URLs',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_maintenance_equipment_id ON maintenance_records(equipment_id);
CREATE INDEX idx_maintenance_date ON maintenance_records(maintenance_date);

-- ============================================================================
-- 5. 配件库存表 (parts_inventory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS parts_inventory (
    id SERIAL PRIMARY KEY,
    part_code VARCHAR(50) UNIQUE NOT NULL COMMENT '配件编码',
    part_name VARCHAR(200) NOT NULL COMMENT '配件名称',
    category VARCHAR(50) COMMENT '配件类别',
    specification VARCHAR(200) COMMENT '规格型号',
    applicable_models TEXT COMMENT '适用设备型号',
    stock_quantity INTEGER DEFAULT 0 COMMENT '库存数量',
    unit_price DECIMAL(10,2) COMMENT '单价',
    supplier VARCHAR(100) COMMENT '供应商',
    supplier_contact VARCHAR(100) COMMENT '供应商联系方式',
    min_stock_alert INTEGER DEFAULT 5 COMMENT '最低库存预警',
    location VARCHAR(100) COMMENT '存放位置',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parts_part_code ON parts_inventory(part_code);
CREATE INDEX idx_parts_category ON parts_inventory(category);
CREATE INDEX idx_parts_stock_quantity ON parts_inventory(stock_quantity);

-- ============================================================================
-- 6. 配件领用记录表 (parts_usage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS parts_usage (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES projects(id) ON DELETE SET NULL COMMENT '关联工单ID',
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    part_code VARCHAR(50) REFERENCES parts_inventory(part_code) ON DELETE RESTRICT,
    part_name VARCHAR(200),
    quantity INTEGER NOT NULL COMMENT '领用数量',
    unit_price DECIMAL(10,2) COMMENT '领用时单价',
    total_cost DECIMAL(10,2) COMMENT '总成本',
    engineer_userid VARCHAR(100),
    engineer_name VARCHAR(100),
    usage_date DATE NOT NULL,
    purpose VARCHAR(20) CHECK (purpose IN ('repair', 'maintenance', 'replacement')),
    approved_by VARCHAR(100) COMMENT '批准人',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parts_usage_ticket_id ON parts_usage(ticket_id);
CREATE INDEX idx_parts_usage_part_code ON parts_usage(part_code);
CREATE INDEX idx_parts_usage_date ON parts_usage(usage_date);

-- ============================================================================
-- 7. 扩展现有projects表（工单表）
-- ============================================================================
ALTER TABLE projects 
    ADD COLUMN IF NOT EXISTS opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS root_cause TEXT COMMENT '故障根本原因',
    ADD COLUMN IF NOT EXISTS solution TEXT COMMENT '解决方案',
    ADD COLUMN IF NOT EXISTS parts_used JSONB COMMENT '使用的配件（JSON格式）',
    ADD COLUMN IF NOT EXISTS service_duration_hours DECIMAL(5,2) COMMENT '服务时长（小时）',
    ADD COLUMN IF NOT EXISTS customer_rating INTEGER CHECK (customer_rating BETWEEN 1 AND 5) COMMENT '客户评分',
    ADD COLUMN IF NOT EXISTS customer_feedback TEXT COMMENT '客户反馈';

CREATE INDEX IF NOT EXISTS idx_projects_equipment_id ON projects(equipment_id);
CREATE INDEX IF NOT EXISTS idx_projects_order_id ON projects(order_id);

-- ============================================================================
-- 8. 操作日志表 (operation_logs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) COMMENT '操作类型',
    entity_type VARCHAR(50) COMMENT '实体类型：opportunity, order, ticket, equipment',
    entity_id INTEGER COMMENT '实体ID',
    operator_userid VARCHAR(100),
    operator_name VARCHAR(100),
    operation_source VARCHAR(20) CHECK (operation_source IN ('group_bot', 'web_ui', 'api', 'system')) COMMENT '操作来源',
    operation_detail JSONB COMMENT '操作详情（JSON格式）',
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operation_logs_entity ON operation_logs(entity_type, entity_id);
CREATE INDEX idx_operation_logs_operator ON operation_logs(operator_userid);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);

-- ============================================================================
-- 9. 数据字典表 (data_dictionary)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_dictionary (
    id SERIAL PRIMARY KEY,
    dict_type VARCHAR(50) NOT NULL COMMENT '字典类型：equipment_type, part_category, etc',
    dict_code VARCHAR(50) NOT NULL COMMENT '字典编码',
    dict_value VARCHAR(200) NOT NULL COMMENT '字典值',
    dict_order INTEGER DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_dict_type_code ON data_dictionary(dict_type, dict_code);

-- 插入常见设备类型
INSERT INTO data_dictionary (dict_type, dict_code, dict_value, dict_order) VALUES
    ('equipment_type', 'central_ac', '中央空调', 1),
    ('equipment_type', 'split_ac', '分体空调', 2),
    ('equipment_type', 'refrigerator', '冰箱', 3),
    ('equipment_type', 'washing_machine', '洗衣机', 4),
    ('equipment_type', 'water_heater', '热水器', 5),
    ('equipment_type', 'range_hood', '油烟机', 6),
    ('equipment_type', 'dishwasher', '洗碗机', 7),
    ('part_category', 'compressor', '压缩机', 1),
    ('part_category', 'motor', '电机', 2),
    ('part_category', 'filter', '滤网/滤芯', 3),
    ('part_category', 'sensor', '传感器', 4),
    ('part_category', 'control_board', '控制板', 5),
    ('part_category', 'fan', '风扇', 6)
ON CONFLICT (dict_type, dict_code) DO NOTHING;

-- ============================================================================
-- 10. 创建自动生成订单编号的函数
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_order_no()
RETURNS VARCHAR(50) AS $$
DECLARE
    new_order_no VARCHAR(50);
    current_date_str VARCHAR(8);
    sequence_num INTEGER;
BEGIN
    -- 格式：OR + YYYYMMDD + 3位序号
    current_date_str := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    -- 获取今天的订单数量
    SELECT COUNT(*) + 1 INTO sequence_num
    FROM orders
    WHERE order_no LIKE 'OR' || current_date_str || '%';
    
    new_order_no := 'OR' || current_date_str || LPAD(sequence_num::TEXT, 3, '0');
    
    RETURN new_order_no;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. 创建自动生成设备编号的函数
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_equipment_no()
RETURNS VARCHAR(50) AS $$
DECLARE
    new_equipment_no VARCHAR(50);
    current_date_str VARCHAR(8);
    sequence_num INTEGER;
BEGIN
    -- 格式：EQ + YYYYMMDD + 3位序号
    current_date_str := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    -- 获取今天的设备数量
    SELECT COUNT(*) + 1 INTO sequence_num
    FROM equipment
    WHERE equipment_no LIKE 'EQ' || current_date_str || '%';
    
    new_equipment_no := 'EQ' || current_date_str || LPAD(sequence_num::TEXT, 3, '0');
    
    RETURN new_equipment_no;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 12. 创建自动更新updated_at字段的触发器函数
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为各表添加自动更新时间戳的触发器
CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parts_inventory_updated_at BEFORE UPDATE ON parts_inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 13. 创建视图：设备全生命周期视图
-- ============================================================================
CREATE OR REPLACE VIEW equipment_lifecycle_view AS
SELECT 
    e.id AS equipment_id,
    e.equipment_no,
    e.equipment_type,
    e.brand,
    e.model,
    e.customer_name,
    e.customer_phone,
    o.order_no,
    o.total_amount AS purchase_amount,
    e.install_date,
    e.warranty_end_date,
    e.status,
    e.next_maintenance_date,
    COUNT(DISTINCT mr.id) AS maintenance_count,
    COUNT(DISTINCT p.id) AS ticket_count,
    MAX(mr.maintenance_date) AS last_maintenance_date,
    SUM(pu.total_cost) AS total_parts_cost
FROM equipment e
LEFT JOIN orders o ON e.order_id = o.id
LEFT JOIN maintenance_records mr ON e.id = mr.equipment_id
LEFT JOIN projects p ON e.id = p.equipment_id
LEFT JOIN parts_usage pu ON e.id = pu.equipment_id
GROUP BY e.id, e.equipment_no, e.equipment_type, e.brand, e.model, 
         e.customer_name, e.customer_phone, o.order_no, o.total_amount, 
         e.install_date, e.warranty_end_date, e.status, e.next_maintenance_date;

-- ============================================================================
-- 14. 创建视图：商机转化漏斗
-- ============================================================================
CREATE OR REPLACE VIEW opportunity_funnel_view AS
SELECT 
    sales_userid,
    sales_name,
    COUNT(*) FILTER (WHERE status = 'new') AS new_count,
    COUNT(*) FILTER (WHERE status = 'contacted') AS contacted_count,
    COUNT(*) FILTER (WHERE status = 'quoted') AS quoted_count,
    COUNT(*) FILTER (WHERE status = 'negotiating') AS negotiating_count,
    COUNT(*) FILTER (WHERE status = 'won') AS won_count,
    COUNT(*) FILTER (WHERE status = 'lost') AS lost_count,
    SUM(estimated_amount) FILTER (WHERE status = 'won') AS total_won_amount,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'won') / NULLIF(COUNT(*), 0), 2) AS win_rate
FROM opportunities
GROUP BY sales_userid, sales_name;

-- ============================================================================
-- 15. 创建函数：检查需要维护提醒的设备
-- ============================================================================
CREATE OR REPLACE FUNCTION get_equipment_needing_maintenance(days_ahead INTEGER DEFAULT 7)
RETURNS TABLE (
    equipment_id INTEGER,
    equipment_no VARCHAR(50),
    equipment_type VARCHAR(50),
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    next_maintenance_date DATE,
    days_until_maintenance INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.equipment_no,
        e.equipment_type,
        e.customer_name,
        e.customer_phone,
        e.next_maintenance_date,
        (e.next_maintenance_date - CURRENT_DATE)::INTEGER AS days_until
    FROM equipment e
    WHERE e.status = 'in_use'
      AND e.next_maintenance_date IS NOT NULL
      AND e.next_maintenance_date <= CURRENT_DATE + days_ahead
      AND e.next_maintenance_date >= CURRENT_DATE
    ORDER BY e.next_maintenance_date;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 16. 创建函数：检查保修即将到期的设备
-- ============================================================================
CREATE OR REPLACE FUNCTION get_equipment_warranty_expiring(days_ahead INTEGER DEFAULT 30)
RETURNS TABLE (
    equipment_id INTEGER,
    equipment_no VARCHAR(50),
    equipment_type VARCHAR(50),
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    warranty_end_date DATE,
    days_until_expiry INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.equipment_no,
        e.equipment_type,
        e.customer_name,
        e.customer_phone,
        e.warranty_end_date,
        (e.warranty_end_date - CURRENT_DATE)::INTEGER AS days_until
    FROM equipment e
    WHERE e.status = 'in_use'
      AND e.warranty_end_date IS NOT NULL
      AND e.warranty_end_date <= CURRENT_DATE + days_ahead
      AND e.warranty_end_date >= CURRENT_DATE
    ORDER BY e.warranty_end_date;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 17. 插入示例数据（可选，用于测试）
-- ============================================================================

-- 插入示例配件
INSERT INTO parts_inventory (part_code, part_name, category, specification, applicable_models, stock_quantity, unit_price, supplier, min_stock_alert) VALUES
    ('AC-COMP-2023', '中央空调压缩机', 'compressor', 'GMV-H120专用', '格力GMV-H120', 5, 3500.00, '格力售后', 2),
    ('AC-FILTER-001', '空调滤网', 'filter', '通用型', '所有空调', 50, 35.00, '通用配件商', 10),
    ('AC-MOTOR-001', '室外机风扇电机', 'motor', '220V 50W', '格力GMV系列', 8, 280.00, '格力售后', 3)
ON CONFLICT (part_code) DO NOTHING;

-- 完成
SELECT '数据库扩展脚本执行完成！' AS message;
