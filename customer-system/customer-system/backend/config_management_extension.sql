-- 配置管理和权限系统扩展

-- 1. 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL COMMENT '角色名称',
    role_display_name VARCHAR(100) NOT NULL COMMENT '角色显示名称',
    description TEXT COMMENT '角色描述',
    permissions JSONB DEFAULT '[]' COMMENT '权限列表（JSON数组）',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统角色（不可删除）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 用户表（管理员）
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(100) COMMENT '真实姓名',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL COMMENT '角色ID',
    wework_userid VARCHAR(100) COMMENT '企业微信UserID（用于单点登录）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_login_at TIMESTAMP COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    permission_code VARCHAR(100) UNIQUE NOT NULL COMMENT '权限代码',
    permission_name VARCHAR(100) NOT NULL COMMENT '权限名称',
    module VARCHAR(50) NOT NULL COMMENT '所属模块',
    description TEXT COMMENT '权限描述',
    resource VARCHAR(100) COMMENT '资源路径',
    action VARCHAR(50) COMMENT '操作类型（read/write/delete/execute）',
    sort_order INTEGER DEFAULT 0 COMMENT '排序序号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 系统配置分组表
CREATE TABLE IF NOT EXISTS config_groups (
    id SERIAL PRIMARY KEY,
    group_code VARCHAR(50) UNIQUE NOT NULL COMMENT '分组代码',
    group_name VARCHAR(100) NOT NULL COMMENT '分组名称',
    description TEXT COMMENT '分组描述',
    sort_order INTEGER DEFAULT 0 COMMENT '排序序号',
    icon VARCHAR(50) COMMENT '图标',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 增强的系统配置表（如果不存在）
CREATE TABLE IF NOT EXISTS enhanced_system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '配置类型：string/number/boolean/json/password',
    group_id INTEGER REFERENCES config_groups(id) ON DELETE SET NULL COMMENT '所属分组',
    display_name VARCHAR(100) COMMENT '显示名称',
    description TEXT COMMENT '配置说明',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    is_sensitive BOOLEAN DEFAULT FALSE COMMENT '是否敏感信息',
    default_value TEXT COMMENT '默认值',
    validation_rule TEXT COMMENT '验证规则（正则表达式）',
    sort_order INTEGER DEFAULT 0 COMMENT '排序序号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 业务流程模板表
CREATE TABLE IF NOT EXISTS workflow_templates (
    id SERIAL PRIMARY KEY,
    template_code VARCHAR(50) UNIQUE NOT NULL COMMENT '模板代码',
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    template_type VARCHAR(20) NOT NULL COMMENT '模板类型：presale/aftersale/mixed/custom',
    description TEXT COMMENT '模板描述',
    workflow_steps JSONB NOT NULL COMMENT '流程步骤（JSON数组）',
    auto_rules JSONB COMMENT '自动化规则（JSON对象）',
    notification_config JSONB COMMENT '通知配置（JSON对象）',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认模板',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 群机器人配置表
CREATE TABLE IF NOT EXISTS robot_webhooks (
    id SERIAL PRIMARY KEY,
    webhook_name VARCHAR(100) NOT NULL COMMENT 'Webhook名称',
    webhook_url TEXT NOT NULL COMMENT 'Webhook URL',
    webhook_type VARCHAR(50) COMMENT 'Webhook类型（新客户通知/日报/技术支援等）',
    description TEXT COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    send_count INTEGER DEFAULT 0 COMMENT '发送次数统计',
    last_send_at TIMESTAMP COMMENT '最后发送时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    username VARCHAR(50) COMMENT '操作用户名',
    operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) COMMENT '操作模块',
    description TEXT COMMENT '操作描述',
    request_path VARCHAR(255) COMMENT '请求路径',
    request_method VARCHAR(10) COMMENT '请求方法',
    request_params JSONB COMMENT '请求参数',
    response_status INTEGER COMMENT '响应状态码',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认角色
INSERT INTO roles (role_name, role_display_name, description, permissions, is_system) VALUES
('super_admin', '超级管理员', '拥有所有权限的超级管理员', '["*"]', TRUE),
('admin', '管理员', '系统管理员，拥有大部分权限', '["config:read", "config:write", "user:read", "user:write", "workflow:read", "workflow:write", "customer:read", "order:read", "project:read"]', TRUE),
('sales', '销售人员', '销售人员角色', '["customer:read", "customer:write", "opportunity:read", "opportunity:write", "order:read", "project:read"]', TRUE),
('service', '客服人员', '客服人员角色', '["customer:read", "project:read", "project:write", "service_request:read", "service_request:write"]', TRUE),
('engineer', '工程师', '技术工程师角色', '["project:read", "project:write", "equipment:read", "equipment:write", "parts:read"]', TRUE),
('viewer', '只读用户', '只能查看数据，不能修改', '["*:read"]', TRUE)
ON CONFLICT (role_name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (permission_code, permission_name, module, description, resource, action) VALUES
('config:read', '查看配置', '系统配置', '查看系统配置信息', '/api/admin/config', 'read'),
('config:write', '修改配置', '系统配置', '修改系统配置信息', '/api/admin/config', 'write'),
('user:read', '查看用户', '用户管理', '查看用户列表', '/api/admin/users', 'read'),
('user:write', '管理用户', '用户管理', '创建、修改、删除用户', '/api/admin/users', 'write'),
('role:read', '查看角色', '角色管理', '查看角色列表', '/api/admin/roles', 'read'),
('role:write', '管理角色', '角色管理', '创建、修改、删除角色', '/api/admin/roles', 'write'),
('workflow:read', '查看工作流', '工作流管理', '查看工作流模板', '/api/admin/workflows', 'read'),
('workflow:write', '管理工作流', '工作流管理', '创建、修改、删除工作流', '/api/admin/workflows', 'write'),
('customer:read', '查看客户', '客户管理', '查看客户信息', '/api/customers', 'read'),
('customer:write', '管理客户', '客户管理', '创建、修改客户信息', '/api/customers', 'write'),
('opportunity:read', '查看商机', '商机管理', '查看商机信息', '/api/opportunities', 'read'),
('opportunity:write', '管理商机', '商机管理', '创建、修改商机', '/api/opportunities', 'write'),
('order:read', '查看订单', '订单管理', '查看订单信息', '/api/orders', 'read'),
('order:write', '管理订单', '订单管理', '创建、修改订单', '/api/orders', 'write'),
('project:read', '查看项目', '项目管理', '查看项目信息', '/api/projects', 'read'),
('project:write', '管理项目', '项目管理', '创建、修改项目', '/api/projects', 'write'),
('equipment:read', '查看设备', '设备管理', '查看设备信息', '/api/equipment', 'read'),
('equipment:write', '管理设备', '设备管理', '创建、修改设备', '/api/equipment', 'write'),
('service_request:read', '查看服务请求', '服务管理', '查看服务请求', '/api/service-requests', 'read'),
('service_request:write', '管理服务请求', '服务管理', '处理服务请求', '/api/service-requests', 'write'),
('parts:read', '查看配件', '配件管理', '查看配件库存', '/api/parts', 'read'),
('parts:write', '管理配件', '配件管理', '管理配件库存', '/api/parts', 'write'),
('report:view', '查看报表', '数据报表', '查看各类数据报表', '/api/reports', 'read'),
('log:view', '查看日志', '系统日志', '查看操作日志', '/api/logs', 'read')
ON CONFLICT (permission_code) DO NOTHING;

-- 插入配置分组
INSERT INTO config_groups (group_code, group_name, description, sort_order, icon) VALUES
('wework', '企业微信配置', '企业微信基础配置信息', 1, 'wechat'),
('message', '消息接收配置', '消息接收服务器配置', 2, 'message'),
('robot', '群机器人配置', '企业微信群机器人Webhook配置', 3, 'robot'),
('workflow', '业务流程配置', '业务流程模板选择', 4, 'flow'),
('notification', '通知配置', '各类通知开关和模板配置', 5, 'notification'),
('advanced', '高级配置', '高级功能配置项', 6, 'settings')
ON CONFLICT (group_code) DO NOTHING;

-- 插入默认配置项
INSERT INTO enhanced_system_config (config_key, config_value, config_type, group_id, display_name, description, is_required, is_sensitive, sort_order) VALUES
-- 企业微信配置
('wework_corp_id', '', 'string', (SELECT id FROM config_groups WHERE group_code = 'wework'), '企业微信CorpID', '企业微信的企业ID', TRUE, FALSE, 1),
('wework_app_secret', '', 'password', (SELECT id FROM config_groups WHERE group_code = 'wework'), '企业微信应用Secret', '企业微信应用的Secret密钥', TRUE, TRUE, 2),
('wework_agent_id', '', 'string', (SELECT id FROM config_groups WHERE group_code = 'wework'), '应用AgentId', '企业微信应用的AgentId', TRUE, FALSE, 3),

-- 消息接收配置
('callback_url', '', 'string', (SELECT id FROM config_groups WHERE group_code = 'message'), '接收消息服务器URL', '企业微信回调URL（自动生成）', FALSE, FALSE, 1),
('callback_token', '', 'string', (SELECT id FROM config_groups WHERE group_code = 'message'), 'Token', '用于验证消息来源的Token', TRUE, FALSE, 2),
('callback_encoding_aes_key', '', 'password', (SELECT id FROM config_groups WHERE group_code = 'message'), 'EncodingAESKey', '消息加密密钥', TRUE, TRUE, 3),
('message_receive_enabled', 'true', 'boolean', (SELECT id FROM config_groups WHERE group_code = 'message'), '启用消息接收', '是否启用企业微信消息接收功能', FALSE, FALSE, 4),

-- 工作流配置
('active_workflow_template', 'standard_presale', 'string', (SELECT id FROM config_groups WHERE group_code = 'workflow'), '当前业务流程', '当前启用的业务流程模板', TRUE, FALSE, 1),
('auto_assign_enabled', 'true', 'boolean', (SELECT id FROM config_groups WHERE group_code = 'workflow'), '自动分配启用', '是否启用自动分配销售/工程师', FALSE, FALSE, 2),
('auto_notify_enabled', 'true', 'boolean', (SELECT id FROM config_groups WHERE group_code = 'workflow'), '自动通知启用', '是否启用自动群通知', FALSE, FALSE, 3)
ON CONFLICT (config_key) DO NOTHING;

-- 插入默认业务流程模板
INSERT INTO workflow_templates (template_code, template_name, template_type, description, workflow_steps, auto_rules, notification_config, is_default, is_active) VALUES
('standard_presale', '标准售前流程', 'presale', '适用于商机咨询、报价、成交的标准售前流程', 
'[
  {"step": 1, "name": "客户咨询", "action": "record_inquiry", "next": 2},
  {"step": 2, "name": "记录意向", "action": "create_opportunity", "next": 3},
  {"step": 3, "name": "自动分配销售", "action": "assign_sales", "notify": "new_customer_group", "next": 4},
  {"step": 4, "name": "销售联系", "action": "sales_contact", "next": 5},
  {"step": 5, "name": "报价", "action": "send_quote", "next": 6},
  {"step": 6, "name": "成交/丢单", "action": "close_deal", "notify": "deal_result_group"}
]'::jsonb,
'{"auto_assign": true, "assign_rule": "round_robin", "auto_notify": true}'::jsonb,
'{"new_customer": true, "deal_won": true, "deal_lost": false}'::jsonb,
TRUE, TRUE),

('standard_aftersale', '标准售后流程', 'aftersale', '适用于报修、维修、回访的标准售后流程',
'[
  {"step": 1, "name": "客户报修", "action": "submit_request", "next": 2},
  {"step": 2, "name": "验证手机号", "action": "verify_customer", "next": 3},
  {"step": 3, "name": "创建工单", "action": "create_project", "notify": "service_group", "next": 4},
  {"step": 4, "name": "分配技术", "action": "assign_engineer", "next": 5},
  {"step": 5, "name": "处理中", "action": "processing", "next": 6},
  {"step": 6, "name": "完成", "action": "complete", "notify": "customer", "next": 7},
  {"step": 7, "name": "客户评价", "action": "customer_rating"}
]'::jsonb,
'{"auto_assign": true, "assign_rule": "skill_based", "auto_verify": true, "auto_notify": true}'::jsonb,
'{"new_request": true, "assigned": true, "completed": true}'::jsonb,
FALSE, TRUE),

('mixed_workflow', '混合流程（售前+售后）', 'mixed', '同时支持售前和售后的混合流程',
'[
  {"step": 1, "name": "智能识别", "action": "ai_classify", "next": 2},
  {"step": 2, "name": "售前分支", "action": "presale_flow", "condition": "type==presale", "next": 3},
  {"step": 2, "name": "售后分支", "action": "aftersale_flow", "condition": "type==aftersale", "next": 4}
]'::jsonb,
'{"auto_classify": true, "ai_enabled": true, "auto_assign": true}'::jsonb,
'{"all_events": true}'::jsonb,
FALSE, TRUE)
ON CONFLICT (template_code) DO NOTHING;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_wework ON admin_users(wework_userid);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role_id);
CREATE INDEX IF NOT EXISTS idx_permissions_module ON permissions(module);
CREATE INDEX IF NOT EXISTS idx_config_group ON enhanced_system_config(group_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_user ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created ON operation_logs(created_at);

-- 创建默认管理员账户（密码: admin123，实际使用时应修改）
-- 密码哈希使用 bcrypt，这里是 'admin123' 的哈希值
INSERT INTO admin_users (username, password_hash, real_name, role_id, is_active) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqRG.q3k6e', '系统管理员', 
 (SELECT id FROM roles WHERE role_name = 'super_admin'), TRUE)
ON CONFLICT (username) DO NOTHING;

COMMENT ON TABLE roles IS '角色表';
COMMENT ON TABLE admin_users IS '管理员用户表';
COMMENT ON TABLE permissions IS '权限表';
COMMENT ON TABLE config_groups IS '配置分组表';
COMMENT ON TABLE enhanced_system_config IS '增强型系统配置表';
COMMENT ON TABLE workflow_templates IS '业务流程模板表';
COMMENT ON TABLE robot_webhooks IS '群机器人配置表';
COMMENT ON TABLE operation_logs IS '操作日志表';
