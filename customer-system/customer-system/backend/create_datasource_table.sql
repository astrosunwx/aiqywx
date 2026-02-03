-- 创建数据源管理表
CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,  -- 数据源名称(唯一标识)
    source_desc TEXT,  -- 数据源描述
    db_type TEXT NOT NULL,  -- 数据库类型: mysql, postgresql, sqlserver
    db_host TEXT NOT NULL,  -- 数据库主机地址
    db_port INTEGER NOT NULL,  -- 端口号
    db_name TEXT NOT NULL,  -- 数据库名
    db_username TEXT NOT NULL,  -- 用户名
    db_password TEXT NOT NULL,  -- 密码(加密存储)
    db_charset TEXT DEFAULT 'utf8mb4',  -- 字符集
    use_ssl BOOLEAN DEFAULT 0,  -- 是否启用SSL
    is_active BOOLEAN DEFAULT 1,  -- 是否启用
    is_default BOOLEAN DEFAULT 0,  -- 是否为默认数据源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_datasource_active ON data_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_datasource_default ON data_sources(is_default);
