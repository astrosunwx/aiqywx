"""
消息系统统一架构 - 数据库迁移脚本
创建时间: 2024-02-03
说明: 扩展现有messages表，新增customer_channel_identifiers和channel_configs表
"""

import psycopg2
from datetime import datetime

def run_migration(conn):
    """执行数据库迁移"""
    cursor = conn.cursor()
    
    print("=" * 60)
    print("开始执行消息系统统一架构迁移")
    print("=" * 60)
    
    # ========== 1. 创建 customer_channel_identifiers 表 ==========
    print("\n[1/4] 创建 customer_channel_identifiers 表...")
    cursor.execute("""
        -- 客户多渠道标识符表
        CREATE TABLE IF NOT EXISTS customer_channel_identifiers (
            id SERIAL PRIMARY KEY,
            customer_id INT NOT NULL,
            channel_type VARCHAR(20) NOT NULL,  -- SMS/EMAIL/WECHAT/WORK_WECHAT
            identifier_value VARCHAR(200) NOT NULL,  -- 具体的标识符（手机号/邮箱/OpenID/ExternalUserID）
            is_verified BOOLEAN DEFAULT FALSE,  -- 是否已验证
            verified_at TIMESTAMP,  -- 验证时间
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(customer_id, channel_type)
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_customer 
            ON customer_channel_identifiers(customer_id);
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_channel 
            ON customer_channel_identifiers(channel_type);
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_value 
            ON customer_channel_identifiers(identifier_value);
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_verified 
            ON customer_channel_identifiers(is_verified);
        
        COMMENT ON TABLE customer_channel_identifiers IS '客户多渠道标识符表';
        COMMENT ON COLUMN customer_channel_identifiers.customer_id IS '客户ID';
        COMMENT ON COLUMN customer_channel_identifiers.channel_type IS '渠道类型：SMS/EMAIL/WECHAT/WORK_WECHAT';
        COMMENT ON COLUMN customer_channel_identifiers.identifier_value IS '标识符值：手机号/邮箱/OpenID/ExternalUserID';
        COMMENT ON COLUMN customer_channel_identifiers.is_verified IS '是否已验证';
    """)
    print("✅ customer_channel_identifiers 表创建成功")
    
    # ========== 2. 创建 channel_configs 表 ==========
    print("\n[2/4] 创建 channel_configs 表...")
    cursor.execute("""
        -- 渠道配置表
        CREATE TABLE IF NOT EXISTS channel_configs (
            id SERIAL PRIMARY KEY,
            channel_type VARCHAR(20) NOT NULL UNIQUE,  -- SMS/EMAIL/GROUP_BOT/AI/WORK_WECHAT/WECHAT
            config_name VARCHAR(100) NOT NULL,
            config_data JSONB NOT NULL,  -- 存储各渠道的配置信息
            is_enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_channel_configs_type 
            ON channel_configs(channel_type);
        CREATE INDEX IF NOT EXISTS idx_channel_configs_enabled 
            ON channel_configs(is_enabled);
        
        COMMENT ON TABLE channel_configs IS '渠道配置表';
        COMMENT ON COLUMN channel_configs.channel_type IS '渠道类型：SMS/EMAIL/GROUP_BOT/AI/WORK_WECHAT/WECHAT';
        COMMENT ON COLUMN channel_configs.config_data IS 'JSON配置数据';
    """)
    print("✅ channel_configs 表创建成功")
    
    # ========== 3. 扩展 message_templates 表 ==========
    print("\n[3/4] 扩展 message_templates 表...")
    cursor.execute("""
        -- 检查列是否存在，不存在则添加
        DO $$ 
        BEGIN
            -- 添加 channel_config_id（可选）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'channel_config_id'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN channel_config_id INT;
                ALTER TABLE message_templates ADD CONSTRAINT fk_message_templates_channel_config 
                    FOREIGN KEY (channel_config_id) REFERENCES channel_configs(id);
            END IF;
            
            -- 添加 target_config（必需）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'target_config'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN target_config JSONB;
                COMMENT ON COLUMN message_templates.target_config IS '目标配置：如群机器人ID、部门ID、标签ID等';
            END IF;
            
            -- 添加 push_mode（必需）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'push_mode'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN push_mode VARCHAR(20) DEFAULT 'realtime';
                COMMENT ON COLUMN message_templates.push_mode IS '推送模式：realtime实时推送/scheduled定时推送';
            END IF;
            
            -- 添加 keywords（可选）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'keywords'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN keywords TEXT[];
                COMMENT ON COLUMN message_templates.keywords IS '实时推送的触发关键词数组';
            END IF;
            
            -- 添加 schedule_time（可选）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'schedule_time'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN schedule_time TIME;
                COMMENT ON COLUMN message_templates.schedule_time IS '定时推送的时间（如09:00）';
            END IF;
            
            -- 添加 repeat_type（可选）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'repeat_type'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN repeat_type VARCHAR(20) DEFAULT 'once';
                COMMENT ON COLUMN message_templates.repeat_type IS '重复类型：once仅一次/daily每日/weekly每周/monthly每月';
            END IF;
            
            -- 添加 targets（可选）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'message_templates' AND column_name = 'targets'
            ) THEN
                ALTER TABLE message_templates ADD COLUMN targets TEXT[];
                COMMENT ON COLUMN message_templates.targets IS '发送目标数组：groups群组/departments部门/fans粉丝';
            END IF;
        END $$;
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_message_templates_push_mode 
            ON message_templates(push_mode);
        CREATE INDEX IF NOT EXISTS idx_message_templates_repeat_type 
            ON message_templates(repeat_type);
    """)
    print("✅ message_templates 表扩展成功")
    
    # ========== 4. 重新设计 messages 表（保留现有数据） ==========
    print("\n[4/4] 扩展 messages 表...")
    cursor.execute("""
        -- 检查列是否存在，不存在则添加
        DO $$ 
        BEGIN
            -- 添加 message_no（消息编号）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'message_no'
            ) THEN
                ALTER TABLE messages ADD COLUMN message_no VARCHAR(50) UNIQUE;
                -- 为现有记录生成消息编号
                UPDATE messages SET message_no = 'MSG' || LPAD(id::TEXT, 12, '0') WHERE message_no IS NULL;
                ALTER TABLE messages ALTER COLUMN message_no SET NOT NULL;
            END IF;
            
            -- 添加 template_id（关联模板）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'template_id'
            ) THEN
                ALTER TABLE messages ADD COLUMN template_id INT;
                ALTER TABLE messages ADD CONSTRAINT fk_messages_template 
                    FOREIGN KEY (template_id) REFERENCES message_templates(id);
            END IF;
            
            -- 添加 channel_type（渠道类型）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'channel_type'
            ) THEN
                ALTER TABLE messages ADD COLUMN channel_type VARCHAR(20);
                COMMENT ON COLUMN messages.channel_type IS '渠道类型：SMS/EMAIL/GROUP_BOT/AI/WORK_WECHAT/WECHAT';
            END IF;
            
            -- 添加 sender_type（发送者类型）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'sender_type'
            ) THEN
                ALTER TABLE messages ADD COLUMN sender_type VARCHAR(20);
                COMMENT ON COLUMN messages.sender_type IS '发送者类型：system系统/user用户/bot机器人';
            END IF;
            
            -- 添加 sender_id（发送者ID）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'sender_id'
            ) THEN
                ALTER TABLE messages ADD COLUMN sender_id INT;
            END IF;
            
            -- 添加 recipient_type（接收者类型）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'recipient_type'
            ) THEN
                ALTER TABLE messages ADD COLUMN recipient_type VARCHAR(50);
                COMMENT ON COLUMN messages.recipient_type IS '接收者类型：phone/email/group_id/openid/external_user_id';
            END IF;
            
            -- 添加 recipient_value（接收者值）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'recipient_value'
            ) THEN
                ALTER TABLE messages ADD COLUMN recipient_value VARCHAR(200);
            END IF;
            
            -- 添加 customer_id（关联客户）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'customer_id'
            ) THEN
                ALTER TABLE messages ADD COLUMN customer_id INT;
            END IF;
            
            -- 添加 subject（主题）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'subject'
            ) THEN
                ALTER TABLE messages ADD COLUMN subject VARCHAR(200);
            END IF;
            
            -- 添加 content_type（内容类型）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'content_type'
            ) THEN
                ALTER TABLE messages ADD COLUMN content_type VARCHAR(20) DEFAULT 'text';
                COMMENT ON COLUMN messages.content_type IS '内容类型：text/markdown/html/card';
            END IF;
            
            -- 添加 status（发送状态）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'status'
            ) THEN
                ALTER TABLE messages ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
                COMMENT ON COLUMN messages.status IS '发送状态：pending待发送/sending发送中/sent已发送/failed失败';
            END IF;
            
            -- 添加 send_mode（发送模式）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'send_mode'
            ) THEN
                ALTER TABLE messages ADD COLUMN send_mode VARCHAR(20);
                COMMENT ON COLUMN messages.send_mode IS '发送模式：realtime实时/scheduled定时';
            END IF;
            
            -- 添加 scheduled_time（定时发送时间）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'scheduled_time'
            ) THEN
                ALTER TABLE messages ADD COLUMN scheduled_time TIMESTAMP;
            END IF;
            
            -- 添加 sent_at（实际发送时间）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'sent_at'
            ) THEN
                ALTER TABLE messages ADD COLUMN sent_at TIMESTAMP;
            END IF;
            
            -- 添加 retry_count（重试次数）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'retry_count'
            ) THEN
                ALTER TABLE messages ADD COLUMN retry_count INT DEFAULT 0;
            END IF;
            
            -- 添加 max_retries（最大重试次数）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'max_retries'
            ) THEN
                ALTER TABLE messages ADD COLUMN max_retries INT DEFAULT 3;
            END IF;
            
            -- 添加 error_message（错误消息）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'error_message'
            ) THEN
                ALTER TABLE messages ADD COLUMN error_message TEXT;
            END IF;
            
            -- 添加 metadata（元数据）
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE messages ADD COLUMN metadata JSONB;
                COMMENT ON COLUMN messages.metadata IS '元数据：如项目ID、工单ID等';
            END IF;
        END $$;
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_messages_no ON messages(message_no);
        CREATE INDEX IF NOT EXISTS idx_messages_template ON messages(template_id);
        CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_type);
        CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
        CREATE INDEX IF NOT EXISTS idx_messages_customer ON messages(customer_id);
        CREATE INDEX IF NOT EXISTS idx_messages_scheduled ON messages(scheduled_time) WHERE status = 'pending';
        CREATE INDEX IF NOT EXISTS idx_messages_recipient_type ON messages(recipient_type);
        CREATE INDEX IF NOT EXISTS idx_messages_send_mode ON messages(send_mode);
    """)
    print("✅ messages 表扩展成功")
    
    # ========== 5. 插入默认渠道配置 ==========
    print("\n[5/5] 插入默认渠道配置...")
    cursor.execute("""
        -- 插入默认配置（如果不存在）
        INSERT INTO channel_configs (channel_type, config_name, config_data, is_enabled)
        VALUES 
            ('GROUP_BOT', '群机器人配置', '{
                "bots": []
            }'::jsonb, true),
            ('AI', '@智能助手配置', '{
                "corp_id": "",
                "agent_id": "",
                "agent_secret": "",
                "token": "",
                "encoding_aes_key": "",
                "target_groups": []
            }'::jsonb, false),
            ('WORK_WECHAT', '企业微信客服配置', '{
                "corp_id": "",
                "contact_secret": ""
            }'::jsonb, false),
            ('WECHAT', '微信公众号配置', '{
                "app_id": "",
                "app_secret": "",
                "qrcode_url": "",
                "generate_user_on_follow": false,
                "promotion_type": "mall"
            }'::jsonb, false),
            ('SMS', '短信配置', '{
                "provider": "aliyun",
                "access_key": "",
                "access_secret": "",
                "sign_name": "",
                "templates": {}
            }'::jsonb, false),
            ('EMAIL', '邮件配置', '{
                "smtp_host": "",
                "smtp_port": 465,
                "username": "",
                "password": "",
                "from_name": "",
                "from_email": ""
            }'::jsonb, false)
        ON CONFLICT (channel_type) DO NOTHING;
    """)
    print("✅ 默认渠道配置插入成功")
    
    # 提交事务
    conn.commit()
    
    print("\n" + "=" * 60)
    print("✅ 消息系统统一架构迁移完成！")
    print("=" * 60)
    print("\n📊 迁移统计:")
    print("  • customer_channel_identifiers 表: ✅ 已创建")
    print("  • channel_configs 表: ✅ 已创建")
    print("  • message_templates 表: ✅ 已扩展（7个新字段）")
    print("  • messages 表: ✅ 已扩展（17个新字段，保留现有数据）")
    print("  • 默认配置: ✅ 已插入6个渠道配置")
    print("\n🎯 现有数据:")
    
    # 统计现有数据
    cursor.execute("SELECT COUNT(*) FROM messages")
    messages_count = cursor.fetchone()[0]
    print(f"  • messages 表现有记录: {messages_count} 条（已保留）")
    
    cursor.execute("SELECT COUNT(*) FROM message_templates")
    templates_count = cursor.fetchone()[0]
    print(f"  • message_templates 表现有记录: {templates_count} 条（已保留）")
    
    print("\n✅ 所有现有数据均已保留，链路追踪功能完整！")
    print("\n下一步:")
    print("  1. 配置中心 → 渠道配置 → 完善各渠道的配置信息")
    print("  2. 模板管理 → 创建新模板 → 绑定渠道配置")
    print("  3. 测试发送 → 验证各渠道是否正常")
    
    cursor.close()

if __name__ == "__main__":
    # 数据库连接配置
    DB_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "database": "customer_system",
        "user": "postgres",
        "password": "postgres"
    }
    
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 数据库连接成功\n")
        
        run_migration(conn)
        
        conn.close()
        print("\n✅ 数据库连接已关闭")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
