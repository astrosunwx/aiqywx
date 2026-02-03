-- 智能售前售后系统 - PostgreSQL 数据库初始化脚本

-- 客户表
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100),
    wechat_openid VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表（售前售中售后统一管理）
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    customer_phone VARCHAR(20) NOT NULL REFERENCES customers(phone),
    project_type VARCHAR(20) CHECK (project_type IN ('presale', 'installation', 'aftersale')),
    status VARCHAR(20) CHECK (status IN ('pending', 'contacted', 'quoted', 'paid', 'processing', 'completed', 'cancelled')),
    title VARCHAR(200),
    description TEXT,
    amount DECIMAL(10,2),
    sales_id INTEGER,
    engineer_id INTEGER,
    remote_project_id VARCHAR(100),
    binding_type VARCHAR(20) CHECK (binding_type IN ('temporary', 'permanent')),
    binding_expires_at TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 微信会话表
CREATE TABLE IF NOT EXISTS wechat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    customer_wechat_id VARCHAR(100),
    employee_wechat_id VARCHAR(100),
    session_type VARCHAR(20) CHECK (session_type IN ('external', 'internal')),
    related_project_ids INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value VARCHAR(500),
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_phone_status ON projects(customer_phone, status);
CREATE INDEX IF NOT EXISTS idx_projects_createdat ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_wechat_sessions_session_id ON wechat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_wechat_sessions_customer_id ON wechat_sessions(customer_wechat_id);

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('group_binding', '技术支持群', '内部技术支持群名称'),
    ('temp_expiry_days', '7', '临时绑定过期天数')
ON CONFLICT (config_key) DO NOTHING;
