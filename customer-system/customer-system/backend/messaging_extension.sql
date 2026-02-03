-- 消息处理系统数据库扩展
-- 支持消息模板、批量任务、链路追踪、统计分析

-- 消息模板表
CREATE TABLE IF NOT EXISTS message_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    channel VARCHAR(20) NOT NULL COMMENT '发送渠道：sms/email/app/wechat/feishu',
    subject VARCHAR(200) COMMENT '消息主题',
    content TEXT NOT NULL COMMENT '消息内容（支持变量：{{variable}}）',
    variables JSONB DEFAULT '[]'::jsonb COMMENT '变量列表',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_message_templates_channel ON message_templates(channel);
CREATE INDEX idx_message_templates_status ON message_templates(status);

-- 批量消息任务表
CREATE TABLE IF NOT EXISTS message_tasks (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES message_templates(id),
    total_count INTEGER NOT NULL DEFAULT 0 COMMENT '总数',
    success_count INTEGER DEFAULT 0 COMMENT '成功数',
    failed_count INTEGER DEFAULT 0 COMMENT '失败数',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed',
    channel VARCHAR(20) NOT NULL COMMENT '发送渠道',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_message_tasks_status ON message_tasks(status);
CREATE INDEX idx_message_tasks_created ON message_tasks(created_at);

-- 消息记录表（单条消息）
CREATE TABLE IF NOT EXISTS message_records (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(100) UNIQUE NOT NULL COMMENT '链路追踪ID',
    task_id INTEGER REFERENCES message_tasks(id),
    template_id INTEGER REFERENCES message_templates(id),
    recipient VARCHAR(200) NOT NULL COMMENT '接收人（手机号/邮箱/用户ID）',
    channel VARCHAR(20) NOT NULL COMMENT '发送渠道',
    subject VARCHAR(200) COMMENT '消息主题',
    content TEXT NOT NULL COMMENT '消息内容',
    variables JSONB COMMENT '变量值',
    priority INTEGER DEFAULT 5 COMMENT '优先级（0-10）',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/sending/success/failed',
    error_message TEXT COMMENT '错误信息',
    retry_count INTEGER DEFAULT 0 COMMENT '重试次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP COMMENT '发送时间',
    delivered_at TIMESTAMP COMMENT '送达时间'
);

CREATE INDEX idx_message_records_trace ON message_records(trace_id);
CREATE INDEX idx_message_records_task ON message_records(task_id);
CREATE INDEX idx_message_records_status ON message_records(status);
CREATE INDEX idx_message_records_created ON message_records(created_at);
CREATE INDEX idx_message_records_channel ON message_records(channel);

-- 消息链路追踪表
CREATE TABLE IF NOT EXISTS message_traces (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(100) NOT NULL COMMENT '追踪ID',
    node_name VARCHAR(50) NOT NULL COMMENT '节点名称：queue/process/send/callback',
    status VARCHAR(20) DEFAULT 'running' COMMENT '状态：running/success/failed',
    metadata JSONB COMMENT '节点元数据',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finish_time TIMESTAMP,
    duration_ms INTEGER COMMENT '耗时（毫秒）'
);

CREATE INDEX idx_message_traces_trace ON message_traces(trace_id);
CREATE INDEX idx_message_traces_node ON message_traces(node_name);
CREATE INDEX idx_message_traces_start ON message_traces(start_time);

-- 消息统计表（按天聚合）
CREATE TABLE IF NOT EXISTS message_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL COMMENT '统计日期',
    channel VARCHAR(20) NOT NULL COMMENT '渠道',
    total_sent INTEGER DEFAULT 0 COMMENT '发送总数',
    success_count INTEGER DEFAULT 0 COMMENT '成功数',
    failed_count INTEGER DEFAULT 0 COMMENT '失败数',
    avg_response_time INTEGER COMMENT '平均响应时间（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date, channel)
);

CREATE INDEX idx_message_statistics_date ON message_statistics(stat_date);
CREATE INDEX idx_message_statistics_channel ON message_statistics(channel);

-- 线程池配置表
CREATE TABLE IF NOT EXISTS thread_pool_configs (
    id SERIAL PRIMARY KEY,
    pool_name VARCHAR(50) UNIQUE NOT NULL COMMENT '线程池名称',
    core_pool_size INTEGER NOT NULL DEFAULT 10 COMMENT '核心线程数',
    max_pool_size INTEGER NOT NULL DEFAULT 50 COMMENT '最大线程数',
    queue_capacity INTEGER DEFAULT 1000 COMMENT '队列容量',
    scale_up_threshold FLOAT DEFAULT 0.8 COMMENT '扩容阈值',
    scale_down_threshold FLOAT DEFAULT 0.2 COMMENT '缩容阈值',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_thread_pool_configs_status ON thread_pool_configs(status);

-- 限流配置表
CREATE TABLE IF NOT EXISTS rate_limit_configs (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL COMMENT '资源标识（如：api:/send_message）',
    limit_type VARCHAR(20) NOT NULL COMMENT '限流类型：qps/concurrent/sliding',
    max_value INTEGER NOT NULL COMMENT '限制值',
    window_seconds INTEGER DEFAULT 1 COMMENT '时间窗口（秒）',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, limit_type)
);

CREATE INDEX idx_rate_limit_configs_resource ON rate_limit_configs(resource);
CREATE INDEX idx_rate_limit_configs_status ON rate_limit_configs(status);

-- 插入默认线程池配置
INSERT INTO thread_pool_configs (pool_name, core_pool_size, max_pool_size, queue_capacity)
VALUES 
    ('message_sender', 20, 100, 2000),
    ('ai_processor', 10, 50, 1000),
    ('notifier', 5, 20, 500)
ON CONFLICT (pool_name) DO NOTHING;

-- 插入默认限流配置
INSERT INTO rate_limit_configs (resource, limit_type, max_value, window_seconds)
VALUES 
    ('api:/messages/send', 'qps', 1000, 1),
    ('api:/messages/send-batch', 'qps', 100, 1),
    ('global', 'concurrent', 500, 60)
ON CONFLICT (resource, limit_type) DO NOTHING;

-- 插入示例消息模板
INSERT INTO message_templates (name, channel, subject, content, variables)
VALUES 
    ('订单发货通知', 'sms', '', '您的订单{{order_no}}已发货，快递单号：{{express_no}}，预计{{delivery_days}}天送达。', 
     '["order_no", "express_no", "delivery_days"]'::jsonb),
    ('促销活动通知', 'email', '限时优惠活动开始啦！', 
     '尊敬的{{customer_name}}，我们的{{product_name}}正在进行限时促销，优惠力度高达{{discount}}折！活动时间：{{start_time}}至{{end_time}}。',
     '["customer_name", "product_name", "discount", "start_time", "end_time"]'::jsonb),
    ('设备维保提醒', 'app', '', '您的设备{{device_name}}（编号：{{device_no}}）将于{{maintenance_date}}到期，请及时安排保养。',
     '["device_name", "device_no", "maintenance_date"]'::jsonb),
    ('系统通知', 'wechat', '重要通知', '{{content}}',
     '["content"]'::jsonb)
ON CONFLICT DO NOTHING;

-- 创建定时任务统计函数
CREATE OR REPLACE FUNCTION update_message_statistics()
RETURNS void AS $$
BEGIN
    -- 按天、按渠道聚合统计
    INSERT INTO message_statistics (stat_date, channel, total_sent, success_count, failed_count, avg_response_time)
    SELECT 
        DATE(created_at) as stat_date,
        channel,
        COUNT(*) as total_sent,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
        AVG(EXTRACT(EPOCH FROM (sent_at - created_at)) * 1000)::INTEGER as avg_response_time
    FROM message_records
    WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY DATE(created_at), channel
    ON CONFLICT (stat_date, channel) 
    DO UPDATE SET
        total_sent = EXCLUDED.total_sent,
        success_count = EXCLUDED.success_count,
        failed_count = EXCLUDED.failed_count,
        avg_response_time = EXCLUDED.avg_response_time;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器：更新任务统计
CREATE OR REPLACE FUNCTION update_task_statistics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status != OLD.status AND NEW.task_id IS NOT NULL THEN
        UPDATE message_tasks
        SET 
            success_count = (
                SELECT COUNT(*) FROM message_records 
                WHERE task_id = NEW.task_id AND status = 'success'
            ),
            failed_count = (
                SELECT COUNT(*) FROM message_records 
                WHERE task_id = NEW.task_id AND status = 'failed'
            ),
            status = CASE 
                WHEN (SELECT COUNT(*) FROM message_records WHERE task_id = NEW.task_id AND status IN ('pending', 'sending')) = 0 
                THEN 'completed'
                ELSE 'processing'
            END
        WHERE id = NEW.task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_statistics
AFTER UPDATE ON message_records
FOR EACH ROW
EXECUTE FUNCTION update_task_statistics();

COMMENT ON TABLE message_templates IS '消息模板表';
COMMENT ON TABLE message_tasks IS '批量消息任务表';
COMMENT ON TABLE message_records IS '消息记录表';
COMMENT ON TABLE message_traces IS '消息链路追踪表';
COMMENT ON TABLE message_statistics IS '消息统计表';
COMMENT ON TABLE thread_pool_configs IS '线程池配置表';
COMMENT ON TABLE rate_limit_configs IS '限流配置表';
