-- AI模型配置系统数据库迁移脚本
-- 执行时间：2026-02-02

-- 1. 创建AI模型配置表
CREATE TABLE IF NOT EXISTS ai_model_configs (
    id SERIAL PRIMARY KEY,
    model_code VARCHAR(50) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_display_name VARCHAR(100),
    model_version VARCHAR(50),
    api_endpoint TEXT,
    api_key TEXT,
    extra_config JSON,
    description TEXT,
    is_official BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ai_model_code ON ai_model_configs(model_code);
CREATE INDEX IF NOT EXISTS idx_ai_model_provider ON ai_model_configs(provider);
CREATE INDEX IF NOT EXISTS idx_ai_model_active ON ai_model_configs(is_active);

-- 添加注释
COMMENT ON TABLE ai_model_configs IS 'AI模型配置表';
COMMENT ON COLUMN ai_model_configs.model_code IS '模型代码（唯一标识）';
COMMENT ON COLUMN ai_model_configs.model_name IS '模型显示名称';
COMMENT ON COLUMN ai_model_configs.provider IS '服务提供商：wework/zhipu/tencent/doubao/deepseek/custom';
COMMENT ON COLUMN ai_model_configs.provider_display_name IS '提供商显示名称';
COMMENT ON COLUMN ai_model_configs.is_official IS '是否官方企业微信API';
COMMENT ON COLUMN ai_model_configs.is_active IS '是否启用';
COMMENT ON COLUMN ai_model_configs.is_default IS '是否默认模型';
COMMENT ON COLUMN ai_model_configs.priority IS '优先级（数字越大优先级越高）';


-- 2. 创建AI模型使用日志表
CREATE TABLE IF NOT EXISTS ai_model_usage_logs (
    id SERIAL PRIMARY KEY,
    model_code VARCHAR(50) NOT NULL,
    user_message TEXT,
    ai_response TEXT,
    intent VARCHAR(50),
    confidence VARCHAR(10),
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_usage_model_code ON ai_model_usage_logs(model_code);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON ai_model_usage_logs(created_at);

-- 添加注释
COMMENT ON TABLE ai_model_usage_logs IS 'AI模型使用日志表';
COMMENT ON COLUMN ai_model_usage_logs.model_code IS '模型代码';
COMMENT ON COLUMN ai_model_usage_logs.response_time_ms IS '响应时间（毫秒）';


-- 3. 插入预置AI模型配置（企业微信官方API + 第三方大模型）
INSERT INTO ai_model_configs (
    model_code, model_name, provider, provider_display_name, 
    description, is_official, is_active, is_default, priority
) VALUES 
-- 企业微信官方API（最高优先级）
(
    'wework-official',
    '企业微信官方API',
    'wework',
    '腾讯企业微信',
    '使用企业微信官方消息推送API，无需第三方大模型，基于规则引擎的智能回复系统。安全可靠，无封号风险。',
    TRUE,
    TRUE,
    TRUE,
    100
),

-- 腾讯云混元大模型（暂不启用，但支持）
(
    'tencent-hunyuan-a13b',
    '腾讯云混元-A13B',
    'tencent',
    '腾讯云',
    '腾讯云混元大模型 Hunyuan-A13B，高性能AI对话引擎，适合复杂对话场景。',
    FALSE,
    FALSE,
    FALSE,
    90
),

-- 智谱GLM-4（第三方，需要API密钥）
(
    'zhipu-glm4',
    '智谱 GLM-4',
    'zhipu',
    '智谱AI',
    '智谱AI提供的GLM-4大模型，适合通用对话和文本生成。需要配置API密钥。',
    FALSE,
    TRUE,
    FALSE,
    80
),

-- 豆包（第三方）
(
    'doubao',
    '豆包 Doubao',
    'doubao',
    '字节跳动',
    '字节跳动豆包大模型，适合中文对话场景。需要配置API密钥。',
    FALSE,
    TRUE,
    FALSE,
    70
),

-- DeepSeek（第三方）
(
    'deepseek',
    'DeepSeek',
    'deepseek',
    'DeepSeek',
    'DeepSeek大模型，适合代码和技术对话。需要配置API密钥。',
    FALSE,
    TRUE,
    FALSE,
    60
)
ON CONFLICT (model_code) DO NOTHING;


-- 4. 验证插入结果
SELECT 
    model_code,
    model_name,
    provider_display_name,
    is_official,
    is_active,
    is_default,
    priority
FROM ai_model_configs
ORDER BY priority DESC;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AI模型配置系统安装完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已安装5个AI模型配置：';
    RAISE NOTICE '1. 企业微信官方API（默认启用）- 官方API，无风险';
    RAISE NOTICE '2. 腾讯云混元-A13B（暂不启用）- 可在管理界面启用';
    RAISE NOTICE '3. 智谱GLM-4（已启用）- 第三方大模型';
    RAISE NOTICE '4. 豆包Doubao（已启用）- 第三方大模型';
    RAISE NOTICE '5. DeepSeek（已启用）- 第三方大模型';
    RAISE NOTICE '';
    RAISE NOTICE '管理路径：';
    RAISE NOTICE '  - API文档: http://localhost:8000/docs';
    RAISE NOTICE '  - 模型列表: GET /api/admin/ai-models/list';
    RAISE NOTICE '  - 创建模型: POST /api/admin/ai-models/create';
    RAISE NOTICE '  - 更新模型: PUT /api/admin/ai-models/update/{id}';
    RAISE NOTICE '  - 删除模型: DELETE /api/admin/ai-models/delete/{id}';
    RAISE NOTICE '========================================';
END $$;
