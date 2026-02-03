-- ========================================
-- 售后服务扩展 SQL
-- 添加售后工单、订单修改等功能
-- ========================================

-- 1. 扩展 customers 表，添加可信用户标识和客户类型
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;

-- 客户类型：区分商机、正式客户、取消客户
ALTER TABLE customers ADD COLUMN IF NOT EXISTS customer_type VARCHAR(20) DEFAULT 'prospect';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS has_active_order BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS first_order_at TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_order_cancel_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_customers_is_verified ON customers(is_verified);
CREATE INDEX IF NOT EXISTS idx_customers_customer_type ON customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_customers_has_active_order ON customers(has_active_order);

COMMENT ON COLUMN customers.is_verified IS '是否为可信用户（已通过企业微信验证）';
COMMENT ON COLUMN customers.verified_at IS '验证通过时间';
COMMENT ON COLUMN customers.customer_type IS '客户类型：prospect-商机用户, customer-正式客户, cancelled-取消客户';
COMMENT ON COLUMN customers.has_active_order IS '是否有有效订单（未取消的订单）';
COMMENT ON COLUMN customers.first_order_at IS '首次下单时间';
COMMENT ON COLUMN customers.last_order_cancel_at IS '最后一次订单取消时间';

-- 添加约束
ALTER TABLE customers ADD CONSTRAINT IF NOT EXISTS chk_customer_type 
    CHECK (customer_type IN ('prospect', 'customer', 'cancelled'));

-- 2. 扩展 projects 表，添加项目链接token
ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_link_token VARCHAR(100) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_projects_link_token ON projects(project_link_token);

COMMENT ON COLUMN projects.project_link_token IS '项目详情链接Token，用于生成安全访问链接';

-- 3. 创建售后工单表
CREATE TABLE IF NOT EXISTS after_sales_tickets (
    id SERIAL PRIMARY KEY,
    ticket_no VARCHAR(50) UNIQUE NOT NULL,
    
    -- 客户信息
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    
    -- 关联项目
    project_id INTEGER REFERENCES projects(id),
    project_title VARCHAR(200),
    
    -- 工单内容
    ticket_type VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    attachments JSONB,
    
    -- 处理信息
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    assigned_to VARCHAR(100),
    assigned_to_name VARCHAR(100),
    assigned_at TIMESTAMP,
    
    -- 处理记录
    response_content TEXT,
    resolution TEXT,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- 来源渠道
    source VARCHAR(20) DEFAULT 'wechat',
    source_openid VARCHAR(100),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 消息推送记录
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    
    CONSTRAINT chk_ticket_type CHECK (ticket_type IN ('maintenance', 'repair', 'complaint', 'consultation', 'return', 'refund')),
    CONSTRAINT chk_ticket_status CHECK (status IN ('pending', 'processing', 'resolved', 'closed', 'cancelled')),
    CONSTRAINT chk_ticket_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT chk_ticket_source CHECK (source IN ('wechat', 'wework', 'web'))
);

-- 索引
CREATE INDEX idx_after_sales_ticket_no ON after_sales_tickets(ticket_no);
CREATE INDEX idx_after_sales_customer_id ON after_sales_tickets(customer_id);
CREATE INDEX idx_after_sales_customer_phone ON after_sales_tickets(customer_phone);
CREATE INDEX idx_after_sales_project_id ON after_sales_tickets(project_id);
CREATE INDEX idx_after_sales_status ON after_sales_tickets(status);
CREATE INDEX idx_after_sales_assigned_to ON after_sales_tickets(assigned_to);
CREATE INDEX idx_after_sales_created_at ON after_sales_tickets(created_at);

-- 注释
COMMENT ON TABLE after_sales_tickets IS '售后工单表 - 客户可在公众号或企业微信提交售后请求';
COMMENT ON COLUMN after_sales_tickets.ticket_no IS '工单编号，格式：AS20240202123456ABC';
COMMENT ON COLUMN after_sales_tickets.ticket_type IS '工单类型：maintenance-保养, repair-维修, complaint-投诉, consultation-咨询, return-退货, refund-退款';
COMMENT ON COLUMN after_sales_tickets.status IS '状态：pending-待处理, processing-处理中, resolved-已解决, closed-已关闭, cancelled-已取消';
COMMENT ON COLUMN after_sales_tickets.priority IS '优先级：low-低, normal-普通, high-高, urgent-紧急';
COMMENT ON COLUMN after_sales_tickets.source IS '来源：wechat-公众号, wework-企业微信, web-网页';

-- 4. 创建订单修改记录表
CREATE TABLE IF NOT EXISTS order_modifications (
    id SERIAL PRIMARY KEY,
    modification_no VARCHAR(50) UNIQUE NOT NULL,
    
    -- 客户信息
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    
    -- 关联项目
    project_id INTEGER NOT NULL REFERENCES projects(id),
    project_title VARCHAR(200),
    
    -- 变更类型
    modification_type VARCHAR(50) NOT NULL,
    
    -- 变更内容
    modification_content JSONB NOT NULL,
    reason TEXT,
    attachments JSONB,
    
    -- 原始数据
    original_data JSONB,
    modified_data JSONB,
    
    -- 审核状态
    status VARCHAR(20) DEFAULT 'pending',
    
    -- 审核信息
    reviewer_userid VARCHAR(100),
    reviewer_name VARCHAR(100),
    reviewed_at TIMESTAMP,
    review_comment TEXT,
    
    -- 处理信息
    processor_userid VARCHAR(100),
    processor_name VARCHAR(100),
    processed_at TIMESTAMP,
    
    -- 来源渠道
    source VARCHAR(20) DEFAULT 'wechat',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 消息推送记录
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    
    CONSTRAINT chk_modification_type CHECK (modification_type IN ('modify', 'cancel', 'refund')),
    CONSTRAINT chk_modification_status CHECK (status IN ('pending', 'approved', 'rejected', 'processing', 'completed', 'cancelled')),
    CONSTRAINT chk_modification_source CHECK (source IN ('wechat', 'wework', 'web'))
);

-- 索引
CREATE INDEX idx_order_modifications_no ON order_modifications(modification_no);
CREATE INDEX idx_order_modifications_customer_id ON order_modifications(customer_id);
CREATE INDEX idx_order_modifications_customer_phone ON order_modifications(customer_phone);
CREATE INDEX idx_order_modifications_project_id ON order_modifications(project_id);
CREATE INDEX idx_order_modifications_status ON order_modifications(status);
CREATE INDEX idx_order_modifications_created_at ON order_modifications(created_at);

-- 注释
COMMENT ON TABLE order_modifications IS '订单修改记录表 - 记录客户的订单变更/退订请求';
COMMENT ON COLUMN order_modifications.modification_no IS '变更单号，格式：OM20240202123456ABC';
COMMENT ON COLUMN order_modifications.modification_type IS '变更类型：modify-修改, cancel-取消, refund-退款';
COMMENT ON COLUMN order_modifications.status IS '状态：pending-待审核, approved-已批准, rejected-已驳回, processing-处理中, completed-已完成, cancelled-已取消';

-- 5. 创建客户身份变更日志表
CREATE TABLE IF NOT EXISTS customer_type_change_logs (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    customer_phone VARCHAR(20) NOT NULL,
    
    -- 变更信息
    old_type VARCHAR(20),
    new_type VARCHAR(20) NOT NULL,
    change_reason VARCHAR(100) NOT NULL,
    
    -- 触发原因
    trigger_event VARCHAR(50),
    project_id INTEGER,
    order_id INTEGER,
    
    -- 操作人
    operator_userid VARCHAR(100),
    operator_name VARCHAR(100),
    
    -- 额外数据
    extra_data JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_old_type CHECK (old_type IN ('prospect', 'customer', 'cancelled')),
    CONSTRAINT chk_new_type CHECK (new_type IN ('prospect', 'customer', 'cancelled')),
    CONSTRAINT chk_change_reason CHECK (change_reason IN ('first_order', 'order_cancelled', 'order_refunded', 'manual_change', 'wework_added'))
);

CREATE INDEX idx_customer_type_logs_customer_id ON customer_type_change_logs(customer_id);
CREATE INDEX idx_customer_type_logs_customer_phone ON customer_type_change_logs(customer_phone);
CREATE INDEX idx_customer_type_logs_created_at ON customer_type_change_logs(created_at);

COMMENT ON TABLE customer_type_change_logs IS '客户身份变更日志表 - 记录商机→正式客户→取消客户的转换';
COMMENT ON COLUMN customer_type_change_logs.change_reason IS '变更原因：first_order-首次下单, order_cancelled-订单取消, order_refunded-订单退款, manual_change-手动修改, wework_added-企业微信添加';

-- 6. 创建商机信息收集表
CREATE TABLE IF NOT EXISTS prospect_inquiries (
    id SERIAL PRIMARY KEY,
    inquiry_no VARCHAR(50) UNIQUE NOT NULL,
    
    -- 客户信息
    customer_phone VARCHAR(20),
    customer_name VARCHAR(100),
    customer_company VARCHAR(200),
    customer_id INTEGER REFERENCES customers(id),
    
    -- 咨询内容
    inquiry_type VARCHAR(50) DEFAULT 'product',
    inquiry_content TEXT,
    product_interest VARCHAR(200),
    budget_range VARCHAR(50),
    urgency VARCHAR(20) DEFAULT 'normal',
    
    -- 来源渠道
    source VARCHAR(20) DEFAULT 'wechat',
    source_openid VARCHAR(100),
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    assigned_to_name VARCHAR(100),
    assigned_at TIMESTAMP,
    
    -- 跟进记录
    follow_up_count INTEGER DEFAULT 0,
    last_follow_up_at TIMESTAMP,
    converted_to_customer BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 消息推送
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    
    CONSTRAINT chk_inquiry_type CHECK (inquiry_type IN ('product', 'service', 'price', 'consultation', 'complaint')),
    CONSTRAINT chk_inquiry_status CHECK (status IN ('pending', 'assigned', 'following', 'converted', 'lost')),
    CONSTRAINT chk_urgency CHECK (urgency IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT chk_inquiry_source CHECK (source IN ('wechat', 'wework', 'web', 'phone'))
);

CREATE INDEX idx_prospect_inquiries_no ON prospect_inquiries(inquiry_no);
CREATE INDEX idx_prospect_inquiries_phone ON prospect_inquiries(customer_phone);
CREATE INDEX idx_prospect_inquiries_status ON prospect_inquiries(status);
CREATE INDEX idx_prospect_inquiries_assigned_to ON prospect_inquiries(assigned_to);
CREATE INDEX idx_prospect_inquiries_created_at ON prospect_inquiries(created_at);

COMMENT ON TABLE prospect_inquiries IS '商机信息收集表 - 记录潜在客户的咨询和需求';
COMMENT ON COLUMN prospect_inquiries.inquiry_no IS '咨询单号，格式：INQ20240202123456ABC';
COMMENT ON COLUMN prospect_inquiries.inquiry_type IS '咨询类型：product-产品, service-服务, price-价格, consultation-咨询, complaint-投诉';
COMMENT ON COLUMN prospect_inquiries.status IS '状态：pending-待分配, assigned-已分配, following-跟进中, converted-已转化, lost-已流失';
COMMENT ON COLUMN prospect_inquiries.urgency IS '紧急程度：low-低, normal-普通, high-高, urgent-紧急';

-- 7. 创建客户服务请求表（统一处理所有客户的请求，不论身份）
CREATE TABLE IF NOT EXISTS customer_service_requests (
    id SERIAL PRIMARY KEY,
    request_no VARCHAR(50) UNIQUE NOT NULL,
    
    -- 客户信息（可能还不是正式客户）
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    customer_id INTEGER REFERENCES customers(id),
    customer_type VARCHAR(20),
    
    -- 请求类型和内容
    request_type VARCHAR(50) NOT NULL,
    request_content TEXT,
    urgency VARCHAR(20) DEFAULT 'normal',
    
    -- 来源渠道
    source VARCHAR(20) DEFAULT 'wechat',
    source_openid VARCHAR(100),
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    assigned_to_name VARCHAR(100),
    assigned_at TIMESTAMP,
    
    -- 特殊标记
    needs_verification BOOLEAN DEFAULT FALSE,
    verification_note TEXT,
    
    -- 处理记录
    response_content TEXT,
    resolved_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 消息推送
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    
    CONSTRAINT chk_request_type CHECK (request_type IN ('query_order', 'modify_order', 'cancel_order', 'aftersales', 'inquiry')),
    CONSTRAINT chk_request_status CHECK (status IN ('pending', 'assigned', 'processing', 'resolved', 'closed')),
    CONSTRAINT chk_request_urgency CHECK (urgency IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT chk_request_source CHECK (source IN ('wechat', 'wework', 'web', 'phone'))
);

CREATE INDEX idx_service_requests_no ON customer_service_requests(request_no);
CREATE INDEX idx_service_requests_phone ON customer_service_requests(customer_phone);
CREATE INDEX idx_service_requests_type ON customer_service_requests(request_type);
CREATE INDEX idx_service_requests_status ON customer_service_requests(status);
CREATE INDEX idx_service_requests_urgency ON customer_service_requests(urgency);
CREATE INDEX idx_service_requests_needs_verification ON customer_service_requests(needs_verification);
CREATE INDEX idx_service_requests_created_at ON customer_service_requests(created_at);

COMMENT ON TABLE customer_service_requests IS '客户服务请求表 - 统一处理所有客户的请求（不论身份）';
COMMENT ON COLUMN customer_service_requests.request_no IS '请求单号，格式：REQ20240202123456ABC';
COMMENT ON COLUMN customer_service_requests.request_type IS '请求类型：query_order-查询订单, modify_order-更改订单, cancel_order-取消订单, aftersales-售后, inquiry-咨询';
COMMENT ON COLUMN customer_service_requests.urgency IS '紧急程度：low-咨询, normal-查询, high-更改/售后, urgent-取消';
COMMENT ON COLUMN customer_service_requests.needs_verification IS '是否需要销售顾问先添加客户（商机用户/取消客户/未找到）';
COMMENT ON COLUMN customer_service_requests.verification_note IS '验证提示：如"商机用户，请先搜索手机号添加"';

-- 8. 扩展项目表：添加多联系人支持
ALTER TABLE projects ADD COLUMN IF NOT EXISTS additional_contacts JSONB DEFAULT '[]'::jsonb COMMENT '项目额外联系人列表（JSON数组，格式：[{"phone":"13800138000","name":"张三","role":"技术负责人"}]）';

CREATE INDEX IF NOT EXISTS idx_projects_additional_contacts ON projects USING gin(additional_contacts);

COMMENT ON COLUMN projects.additional_contacts IS '项目额外联系人：除主客户外，其他可查询此项目的联系人';

-- 9. 创建工单处理日志表
CREATE TABLE IF NOT EXISTS ticket_action_logs (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES after_sales_tickets(id),
    ticket_no VARCHAR(50) NOT NULL,
    
    -- 操作信息
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT,
    
    -- 操作人
    operator_userid VARCHAR(100),
    operator_name VARCHAR(100),
    
    -- 状态变更
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    
    -- 额外数据
    extra_data JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_action_type CHECK (action_type IN ('create', 'assign', 'update', 'resolve', 'close', 'cancel', 'comment'))
);

CREATE INDEX idx_ticket_logs_ticket_id ON ticket_action_logs(ticket_id);
CREATE INDEX idx_ticket_logs_ticket_no ON ticket_action_logs(ticket_no);
CREATE INDEX idx_ticket_logs_created_at ON ticket_action_logs(created_at);

COMMENT ON TABLE ticket_action_logs IS '工单处理日志表 - 记录工单的所有操作历史';
COMMENT ON COLUMN ticket_action_logs.action_type IS '操作类型：create-创建, assign-分配, update-更新, resolve-解决, close-关闭, cancel-取消, comment-评论';

-- 6. 创建自动更新触发器
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为after_sales_tickets表添加触发器
DROP TRIGGER IF EXISTS update_after_sales_tickets_modtime ON after_sales_tickets;
CREATE TRIGGER update_after_sales_tickets_modtime
    BEFORE UPDATE ON after_sales_tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- 为order_modifications表添加触发器
DROP TRIGGER IF EXISTS update_order_modifications_modtime ON order_modifications;
CREATE TRIGGER update_order_modifications_modtime
    BEFORE UPDATE ON order_modifications
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- 7. 创建视图：待处理售后工单统计
CREATE OR REPLACE VIEW pending_tickets_summary AS
SELECT 
    assigned_to,
    assigned_to_name,
    COUNT(*) as total_tickets,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_count,
    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent_count,
    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_count
FROM after_sales_tickets
WHERE status IN ('pending', 'processing')
GROUP BY assigned_to, assigned_to_name;

COMMENT ON VIEW pending_tickets_summary IS '待处理售后工单统计 - 按负责人分组';

-- 8. 创建视图：客户售后统计
CREATE OR REPLACE VIEW customer_aftersales_summary AS
SELECT 
    c.id as customer_id,
    c.phone,
    c.name,
    c.is_verified,
    COUNT(DISTINCT ast.id) as total_tickets,
    COUNT(DISTINCT CASE WHEN ast.status = 'resolved' THEN ast.id END) as resolved_tickets,
    COUNT(DISTINCT om.id) as total_modifications,
    MAX(ast.created_at) as last_ticket_time
FROM customers c
LEFT JOIN after_sales_tickets ast ON c.id = ast.customer_id
LEFT JOIN order_modifications om ON c.id = om.customer_id
GROUP BY c.id, c.phone, c.name, c.is_verified;

COMMENT ON VIEW customer_aftersales_summary IS '客户售后统计 - 包含工单和订单修改数量';

-- 9. 创建触发器：订单状态变更时自动更新客户类型
CREATE OR REPLACE FUNCTION update_customer_type_on_order_change()
RETURNS TRIGGER AS $$
DECLARE
    v_customer_id INTEGER;
    v_customer_phone VARCHAR(20);
    v_old_type VARCHAR(20);
    v_active_order_count INTEGER;
BEGIN
    -- 获取客户信息
    SELECT customer_id, customer_phone INTO v_customer_id, v_customer_phone 
    FROM projects WHERE id = NEW.id;
    
    IF v_customer_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- 获取当前客户类型
    SELECT customer_type INTO v_old_type FROM customers WHERE id = v_customer_id;
    
    -- 检查是否有有效订单（未取消的订单）
    SELECT COUNT(*) INTO v_active_order_count 
    FROM projects 
    WHERE customer_id = v_customer_id 
    AND status NOT IN ('cancelled', 'refunded');
    
    -- 情况1：首次下单，从商机变为正式客户
    IF NEW.status = 'signed' AND v_old_type = 'prospect' THEN
        UPDATE customers 
        SET customer_type = 'customer',
            has_active_order = TRUE,
            first_order_at = COALESCE(first_order_at, NOW())
        WHERE id = v_customer_id;
        
        -- 记录日志
        INSERT INTO customer_type_change_logs (
            customer_id, customer_phone, old_type, new_type, 
            change_reason, trigger_event, project_id, created_at
        ) VALUES (
            v_customer_id, v_customer_phone, v_old_type, 'customer',
            'first_order', 'order_signed', NEW.id, NOW()
        );
    END IF;
    
    -- 情况2：订单取消，且没有其他有效订单
    IF NEW.status IN ('cancelled', 'refunded') AND v_active_order_count = 0 THEN
        UPDATE customers 
        SET customer_type = 'cancelled',
            has_active_order = FALSE,
            last_order_cancel_at = NOW()
        WHERE id = v_customer_id;
        
        -- 记录日志
        INSERT INTO customer_type_change_logs (
            customer_id, customer_phone, old_type, new_type, 
            change_reason, trigger_event, project_id, created_at
        ) VALUES (
            v_customer_id, v_customer_phone, v_old_type, 'cancelled',
            CASE WHEN NEW.status = 'refunded' THEN 'order_refunded' ELSE 'order_cancelled' END,
            'order_status_change', NEW.id, NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为projects表添加触发器
DROP TRIGGER IF EXISTS trigger_update_customer_type ON projects;
CREATE TRIGGER trigger_update_customer_type
    AFTER UPDATE OF status ON projects
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_customer_type_on_order_change();

-- 10. 创建视图：客户权限视图
CREATE OR REPLACE VIEW customer_permissions AS
SELECT 
    c.id,
    c.phone,
    c.name,
    c.customer_type,
    c.is_verified,
    c.has_active_order,
    -- 权限计算
    CASE 
        WHEN c.customer_type = 'customer' AND c.has_active_order = TRUE THEN TRUE
        ELSE FALSE
    END as can_query_projects,
    CASE 
        WHEN c.customer_type = 'customer' AND c.has_active_order = TRUE AND c.is_verified = TRUE THEN TRUE
        ELSE FALSE
    END as can_submit_aftersales,
    -- 统计信息
    (SELECT COUNT(*) FROM projects WHERE customer_id = c.id AND status NOT IN ('cancelled', 'refunded')) as active_project_count,
    (SELECT COUNT(*) FROM after_sales_tickets WHERE customer_id = c.id) as ticket_count,
    c.created_at,
    c.first_order_at,
    c.last_order_cancel_at
FROM customers c;

COMMENT ON VIEW customer_permissions IS '客户权限视图 - 显示每个客户的权限状态';

-- 11. 创建视图：商机转化统计
CREATE OR REPLACE VIEW prospect_conversion_stats AS
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_inquiries,
    COUNT(CASE WHEN converted_to_customer = TRUE THEN 1 END) as converted_count,
    ROUND(100.0 * COUNT(CASE WHEN converted_to_customer = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 2) as conversion_rate,
    AVG(EXTRACT(EPOCH FROM (converted_at - created_at)) / 86400) as avg_days_to_convert
FROM prospect_inquiries
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

COMMENT ON VIEW prospect_conversion_stats IS '商机转化统计 - 按月统计转化率';

-- 12. 初始化数据
-- 为现有已绑定的客户设置为可信用户
UPDATE customers 
SET is_verified = TRUE, 
    verified_at = bound_at,
    customer_type = 'customer',  -- 已绑定的视为正式客户
    has_active_order = TRUE
WHERE binding_status = 'bound' AND is_verified IS FALSE;

-- 为有项目的客户设置为正式客户
UPDATE customers c
SET customer_type = 'customer',
    has_active_order = TRUE
WHERE EXISTS (
    SELECT 1 FROM projects p 
    WHERE p.customer_id = c.id 
    AND p.status NOT IN ('cancelled', 'refunded')
)
AND c.customer_type = 'prospect';

COMMIT;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '售后服务扩展 SQL 执行完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建表：';
    RAISE NOTICE '  - after_sales_tickets (售后工单表)';
    RAISE NOTICE '  - order_modifications (订单修改记录表)';
    RAISE NOTICE '  - ticket_action_logs (工单处理日志表)';
    RAISE NOTICE '';
    RAISE NOTICE '已创建视图：';
    RAISE NOTICE '  - pending_tickets_summary (待处理工单统计)';
    RAISE NOTICE '  - customer_aftersales_summary (客户售后统计)';
    RAISE NOTICE '';
    RAISE NOTICE '已更新字段：';
    RAISE NOTICE '  - customers.is_verified (可信用户标识)';
    RAISE NOTICE '  - projects.project_link_token (项目链接)';
    RAISE NOTICE '========================================';
END $$;
