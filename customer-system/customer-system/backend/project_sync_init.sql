-- 项目同步功能 - 数据库初始化脚本
-- 创建时间: 2024-02-02
-- 说明: 创建4个数据库表用于项目缓存、同步历史、配置和访问控制

-- ============================================================================
-- 1. 项目缓存表 (project_cache)
-- 说明: 存储项目的缓存数据，避免频繁调取远程API
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_cache (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL COMMENT '项目ID',
    project_type VARCHAR(20) NOT NULL COMMENT '项目类型: presale(售前) | aftersales(售后) | sales(销售)',
    title VARCHAR(255) COMMENT '项目标题',
    status VARCHAR(50) COMMENT '项目状态',
    data LONGTEXT NOT NULL COMMENT '项目完整数据（JSON格式）',
    remote_updated_at TIMESTAMP NULL COMMENT '远程数据更新时间',
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '本地缓存时间',
    expires_at TIMESTAMP NULL COMMENT '缓存过期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_project_id (project_id),
    KEY idx_project_type (project_type),
    KEY idx_expires_at (expires_at),
    KEY idx_status (status),
    KEY idx_cached_at (cached_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目缓存表';

-- ============================================================================
-- 2. 项目同步历史表 (project_sync_history)
-- 说明: 记录每次项目同步的详细信息，用于监控和审计
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_sync_history (
    id SERIAL PRIMARY KEY,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同步时间',
    sync_type VARCHAR(10) NOT NULL COMMENT '同步类型: auto(自动) | manual(手动)',
    total_projects INT DEFAULT 0 COMMENT '同步的项目总数',
    updated_count INT DEFAULT 0 COMMENT '更新的项目数',
    unchanged_count INT DEFAULT 0 COMMENT '未变更的项目数',
    failed_count INT DEFAULT 0 COMMENT '同步失败的项目数',
    duration FLOAT DEFAULT 0 COMMENT '耗时（秒）',
    status VARCHAR(20) DEFAULT 'success' COMMENT '同步状态: success(成功) | failed(失败) | partial(部分失败)',
    message TEXT COMMENT '同步信息',
    error_detail LONGTEXT COMMENT '错误详情',
    changes LONGTEXT COMMENT '变更详情（JSON格式）',
    triggered_by VARCHAR(100) COMMENT '触发者（auto/user_id）',
    sync_config LONGTEXT COMMENT '同步时的配置（JSON格式）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_sync_time (sync_time DESC),
    KEY idx_sync_type (sync_type),
    KEY idx_status (status),
    KEY idx_triggered_by (triggered_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目同步历史表';

-- ============================================================================
-- 3. 项目同步配置表 (project_sync_config)
-- 说明: 存储项目同步的配置信息
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_sync_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL COMMENT '配置键',
    config_value LONGTEXT NOT NULL COMMENT '配置值（JSON格式）',
    description VARCHAR(500) COMMENT '配置描述',
    updated_by VARCHAR(100) COMMENT '更新者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目同步配置表';

-- ============================================================================
-- 4. 项目访问令牌表 (project_access_tokens)
-- 说明: 存储项目详情的访问令牌，用于权限控制和安全访问
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_access_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL COMMENT '访问令牌（JWT或其他格式）',
    project_id VARCHAR(50) NOT NULL COMMENT '项目ID',
    user_id VARCHAR(100) COMMENT '用户ID',
    user_type VARCHAR(50) COMMENT '用户类型: customer(客户) | engineer(工程师) | salesman(销售)',
    user_name VARCHAR(255) COMMENT '用户名称',
    user_phone VARCHAR(20) COMMENT '用户电话',
    access_type VARCHAR(50) COMMENT '访问类型: read(只读) | read_write(读写)',
    ip_address VARCHAR(50) COMMENT '创建令牌的IP地址',
    expires_at TIMESTAMP NOT NULL COMMENT '令牌过期时间',
    last_accessed_at TIMESTAMP NULL COMMENT '上次访问时间',
    access_count INT DEFAULT 0 COMMENT '访问次数',
    revoked TINYINT(1) DEFAULT 0 COMMENT '是否被撤销',
    revoked_at TIMESTAMP NULL COMMENT '撤销时间',
    revoke_reason VARCHAR(500) COMMENT '撤销原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_token (token),
    KEY idx_project_id (project_id),
    KEY idx_user_id (user_id),
    KEY idx_expires_at (expires_at),
    KEY idx_revoked (revoked),
    KEY idx_user_type (user_type),
    FOREIGN KEY (project_id) REFERENCES project_cache(project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目访问令牌表';

-- ============================================================================
-- 5. 项目状态变更通知表 (project_status_notifications)
-- 说明: 记录项目状态变更和发送的通知
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_status_notifications (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL COMMENT '项目ID',
    old_status VARCHAR(50) COMMENT '原状态',
    new_status VARCHAR(50) NOT NULL COMMENT '新状态',
    notify_to VARCHAR(100) COMMENT '通知对象ID',
    notify_type VARCHAR(20) NOT NULL COMMENT '通知类型: wechat(微信) | sms(短信) | email(邮件)',
    notify_content TEXT COMMENT '通知内容',
    send_status VARCHAR(20) DEFAULT 'pending' COMMENT '发送状态: pending(待发送) | sent(已发送) | failed(失败)',
    send_time TIMESTAMP NULL COMMENT '发送时间',
    send_message VARCHAR(500) COMMENT '发送结果信息',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_project_id (project_id),
    KEY idx_notify_to (notify_to),
    KEY idx_send_status (send_status),
    KEY idx_created_at (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目状态变更通知表';

-- ============================================================================
-- 初始化同步配置数据
-- ============================================================================

-- 插入默认的同步配置
INSERT INTO project_sync_config (config_key, config_value, description) VALUES 
(
    'auto_sync_enabled',
    '{"value": true}',
    '是否启用自动同步'
),
(
    'sync_frequency',
    '{"value": "*/15 * * * *"}',
    '同步频率Cron表达式（默认15分钟）'
),
(
    'cache_ttl',
    '{"value": 30}',
    '缓存过期时间（分钟）'
),
(
    'sync_types',
    '{"value": ["presale", "aftersales", "sales"]}',
    '同步的项目类型'
),
(
    'notify_on_change',
    '{"value": true}',
    '状态变更时是否发送通知'
),
(
    'notify_channels',
    '{"value": ["wechat", "sms"]}',
    '通知渠道'
),
(
    'aftersales_time_format',
    '{"value": "YYYY-MM-DD HH:mm"}',
    '售后工单时间显示格式'
),
(
    'sales_time_format',
    '{"value": "YYYY-MM-DD HH:mm"}',
    '订单时间显示格式'
),
(
    'show_payment_time',
    '{"value": true}',
    '是否显示付款时间'
),
(
    'timezone',
    '{"value": "Asia/Shanghai"}',
    '时区设置'
),
(
    'token_expiry_days',
    '{"value": 7}',
    '访问令牌过期天数'
),
(
    'max_sync_duration',
    '{"value": 300}',
    '最大同步耗时（秒）'
)
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- ============================================================================
-- 创建视图：获取即将过期的缓存数据
-- ============================================================================
CREATE OR REPLACE VIEW v_expiring_cache AS
SELECT 
    id,
    project_id,
    project_type,
    title,
    status,
    cached_at,
    expires_at,
    TIMESTAMPDIFF(MINUTE, NOW(), expires_at) as minutes_until_expire
FROM project_cache
WHERE expires_at IS NOT NULL
    AND expires_at <= DATE_ADD(NOW(), INTERVAL 5 MINUTE)
    AND expires_at > NOW()
ORDER BY expires_at ASC;

-- ============================================================================
-- 创建视图：获取过期的缓存数据
-- ============================================================================
CREATE OR REPLACE VIEW v_expired_cache AS
SELECT 
    id,
    project_id,
    project_type,
    title,
    status,
    cached_at,
    expires_at,
    TIMESTAMPDIFF(MINUTE, expires_at, NOW()) as minutes_expired
FROM project_cache
WHERE expires_at IS NOT NULL AND expires_at <= NOW()
ORDER BY expires_at DESC;

-- ============================================================================
-- 创建视图：获取待发送的通知
-- ============================================================================
CREATE OR REPLACE VIEW v_pending_notifications AS
SELECT 
    id,
    project_id,
    old_status,
    new_status,
    notify_to,
    notify_type,
    notify_content,
    send_status,
    retry_count,
    created_at
FROM project_status_notifications
WHERE send_status = 'pending'
    AND retry_count < 3
    AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY created_at ASC
LIMIT 100;

-- ============================================================================
-- 创建视图：同步统计
-- ============================================================================
CREATE OR REPLACE VIEW v_sync_statistics AS
SELECT 
    DATE(sync_time) as sync_date,
    COUNT(*) as total_syncs,
    SUM(CASE WHEN sync_type = 'auto' THEN 1 ELSE 0 END) as auto_syncs,
    SUM(CASE WHEN sync_type = 'manual' THEN 1 ELSE 0 END) as manual_syncs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    SUM(total_projects) as total_projects_synced,
    SUM(updated_count) as total_updates,
    AVG(duration) as avg_duration,
    MAX(duration) as max_duration,
    MIN(duration) as min_duration
FROM project_sync_history
WHERE sync_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(sync_time)
ORDER BY sync_date DESC;

-- ============================================================================
-- 创建存储过程：清理过期的缓存数据
-- ============================================================================
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_cleanup_expired_cache()
BEGIN
    DECLARE v_deleted_count INT;
    
    DELETE FROM project_cache 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    SET v_deleted_count = ROW_COUNT();
    
    INSERT INTO project_sync_history 
    (sync_time, sync_type, total_projects, updated_count, status, message, triggered_by)
    VALUES 
    (NOW(), 'manual', 0, 0, 'success', CONCAT('清理过期缓存: 删除', v_deleted_count, '条记录'), 'system');
END //

DELIMITER ;

-- ============================================================================
-- 创建存储过程：清理过期的访问令牌
-- ============================================================================
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_cleanup_expired_tokens()
BEGIN
    DECLARE v_deleted_count INT;
    
    DELETE FROM project_access_tokens 
    WHERE expires_at < NOW() OR revoked = 1;
    
    SET v_deleted_count = ROW_COUNT();
    
    INSERT INTO project_sync_history 
    (sync_time, sync_type, total_projects, updated_count, status, message, triggered_by)
    VALUES 
    (NOW(), 'manual', 0, 0, 'success', CONCAT('清理过期令牌: 删除', v_deleted_count, '条记录'), 'system');
END //

DELIMITER ;

-- ============================================================================
-- 创建定期维护任务
-- ============================================================================

-- 创建事件：每天凌晨2点清理过期缓存
CREATE EVENT IF NOT EXISTS evt_cleanup_expired_cache
ON SCHEDULE EVERY 1 DAY
STARTS DATE_ADD(CURDATE(), INTERVAL 2 HOUR)
DO CALL sp_cleanup_expired_cache();

-- 创建事件：每天凌晨3点清理过期令牌
CREATE EVENT IF NOT EXISTS evt_cleanup_expired_tokens
ON SCHEDULE EVERY 1 DAY
STARTS DATE_ADD(CURDATE(), INTERVAL 3 HOUR)
DO CALL sp_cleanup_expired_tokens();

-- ============================================================================
-- 创建索引优化查询性能
-- ============================================================================

-- 项目缓存表的复合索引
ALTER TABLE project_cache ADD KEY idx_type_expires (project_type, expires_at);
ALTER TABLE project_cache ADD KEY idx_status_expires (status, expires_at);

-- 同步历史表的复合索引
ALTER TABLE project_sync_history ADD KEY idx_type_time (sync_type, sync_time DESC);
ALTER TABLE project_sync_history ADD KEY idx_status_time (status, sync_time DESC);

-- 访问令牌表的复合索引
ALTER TABLE project_access_tokens ADD KEY idx_project_expires (project_id, expires_at);
ALTER TABLE project_access_tokens ADD KEY idx_user_type_expires (user_type, expires_at);

-- 通知表的复合索引
ALTER TABLE project_status_notifications ADD KEY idx_status_time (send_status, created_at DESC);
ALTER TABLE project_status_notifications ADD KEY idx_project_status_time (project_id, send_status, created_at DESC);

-- ============================================================================
-- 创建触发器：自动更新缓存过期时间
-- ============================================================================
DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_update_cache_expiry_time
BEFORE INSERT ON project_cache
FOR EACH ROW
BEGIN
    IF NEW.expires_at IS NULL THEN
        SET NEW.expires_at = DATE_ADD(NOW(), INTERVAL 30 MINUTE);
    END IF;
END //

DELIMITER ;

-- ============================================================================
-- 创建触发器：同步配置变更日志
-- ============================================================================
DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_log_config_update
AFTER UPDATE ON project_sync_config
FOR EACH ROW
BEGIN
    INSERT INTO project_sync_history 
    (sync_time, sync_type, status, message, triggered_by)
    VALUES 
    (NOW(), 'manual', 'success', CONCAT('配置变更: ', OLD.config_key), NEW.updated_by);
END //

DELIMITER ;

-- ============================================================================
-- 完成标记
-- ============================================================================
-- 所有表已创建完成，可以开始实现API接口了
SELECT 'Project Sync Tables Initialized Successfully' as status;
