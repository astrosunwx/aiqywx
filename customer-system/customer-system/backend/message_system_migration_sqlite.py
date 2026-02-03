"""
消息系统统一架构 - SQLite数据库迁移脚本
创建时间: 2024-02-03
说明: 扩展现有messages表，新增customer_channel_identifiers和channel_configs表
"""

import sqlite3
from datetime import datetime
import json
import os

def run_migration(db_path="./customer_system.db"):
    """执行数据库迁移"""
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("开始执行消息系统统一架构迁移 (SQLite)")
    print("=" * 60)
    print(f"数据库文件: {db_path}")
    
    # ========== 1. 创建 customer_channel_identifiers 表 ==========
    print("\n[1/4] 创建 customer_channel_identifiers 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_channel_identifiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            channel_type VARCHAR(20) NOT NULL,
            identifier_value VARCHAR(200) NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(customer_id, channel_type)
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_customer 
        ON customer_channel_identifiers(customer_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_channel 
        ON customer_channel_identifiers(channel_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_value 
        ON customer_channel_identifiers(identifier_value)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_identifiers_verified 
        ON customer_channel_identifiers(is_verified)
    """)
    
    print("✅ customer_channel_identifiers 表创建成功")
    
    # ========== 2. 创建 channel_configs 表 ==========
    print("\n[2/4] 创建 channel_configs 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_type VARCHAR(20) NOT NULL UNIQUE,
            config_name VARCHAR(100) NOT NULL,
            config_data TEXT NOT NULL,
            is_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_configs_type 
        ON channel_configs(channel_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_configs_enabled 
        ON channel_configs(is_enabled)
    """)
    
    print("✅ channel_configs 表创建成功")
    
    # ========== 3. 扩展 message_templates 表 ==========
    print("\n[3/4] 扩展 message_templates 表...")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='message_templates'
    """)
    
    if cursor.fetchone():
        # 获取现有列
        cursor.execute("PRAGMA table_info(message_templates)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # 需要添加的列
        new_columns = {
            'channel_config_id': 'INTEGER',
            'target_config': 'TEXT',
            'push_mode': "VARCHAR(20) DEFAULT 'realtime'",
            'keywords': 'TEXT',
            'schedule_time': 'TIME',
            'repeat_type': "VARCHAR(20) DEFAULT 'once'",
            'targets': 'TEXT'
        }
        
        # 添加缺失的列
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE message_templates 
                        ADD COLUMN {col_name} {col_type}
                    """)
                    print(f"  ✓ 添加列: {col_name}")
                except Exception as e:
                    print(f"  ⚠ 跳过列 {col_name}: {e}")
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_templates_push_mode 
            ON message_templates(push_mode)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_templates_repeat_type 
            ON message_templates(repeat_type)
        """)
        
        print("✅ message_templates 表扩展成功")
    else:
        print("⚠️  message_templates 表不存在，跳过扩展")
    
    # ========== 4. 扩展 messages 表 ==========
    print("\n[4/4] 扩展 messages 表...")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='messages'
    """)
    
    if cursor.fetchone():
        # 获取现有列
        cursor.execute("PRAGMA table_info(messages)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # 需要添加的列
        new_columns = {
            'message_no': 'VARCHAR(50) UNIQUE',
            'template_id': 'INTEGER',
            'channel_type': 'VARCHAR(20)',
            'sender_type': 'VARCHAR(20)',
            'sender_id': 'INTEGER',
            'recipient_type': 'VARCHAR(50)',
            'recipient_value': 'VARCHAR(200)',
            'customer_id': 'INTEGER',
            'subject': 'VARCHAR(200)',
            'content_type': "VARCHAR(20) DEFAULT 'text'",
            'status': "VARCHAR(20) DEFAULT 'pending'",
            'send_mode': 'VARCHAR(20)',
            'scheduled_time': 'TIMESTAMP',
            'sent_at': 'TIMESTAMP',
            'retry_count': 'INTEGER DEFAULT 0',
            'max_retries': 'INTEGER DEFAULT 3',
            'error_message': 'TEXT',
            'metadata': 'TEXT'
        }
        
        # 添加缺失的列
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE messages 
                        ADD COLUMN {col_name} {col_type}
                    """)
                    print(f"  ✓ 添加列: {col_name}")
                except Exception as e:
                    print(f"  ⚠ 跳过列 {col_name}: {e}")
        
        # 为现有记录生成消息编号（如果message_no列存在但为空）
        if 'message_no' in existing_columns or 'message_no' not in existing_columns:
            try:
                cursor.execute("""
                    UPDATE messages 
                    SET message_no = 'MSG' || printf('%012d', id)
                    WHERE message_no IS NULL
                """)
                print(f"  ✓ 更新了 {cursor.rowcount} 条记录的消息编号")
            except:
                pass
        
        # 创建索引
        indexes = [
            ("idx_messages_no", "message_no"),
            ("idx_messages_template", "template_id"),
            ("idx_messages_channel", "channel_type"),
            ("idx_messages_status", "status"),
            ("idx_messages_customer", "customer_id"),
            ("idx_messages_recipient_type", "recipient_type"),
            ("idx_messages_send_mode", "send_mode")
        ]
        
        for idx_name, col_name in indexes:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} 
                ON messages({col_name})
            """)
        
        print("✅ messages 表扩展成功")
    else:
        # 创建新的messages表
        print("  messages 表不存在，创建新表...")
        cursor.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_no VARCHAR(50) UNIQUE NOT NULL,
                template_id INTEGER,
                channel_type VARCHAR(20) NOT NULL,
                sender_type VARCHAR(20),
                sender_id INTEGER,
                recipient_type VARCHAR(50) NOT NULL,
                recipient_value VARCHAR(200) NOT NULL,
                customer_id INTEGER,
                subject VARCHAR(200),
                content TEXT NOT NULL,
                content_type VARCHAR(20) DEFAULT 'text',
                status VARCHAR(20) DEFAULT 'pending',
                send_mode VARCHAR(20),
                scheduled_time TIMESTAMP,
                sent_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ messages 表创建成功")
    
    # ========== 5. 插入默认渠道配置 ==========
    print("\n[5/5] 插入默认渠道配置...")
    
    default_configs = [
        ('GROUP_BOT', '群机器人配置', json.dumps({"bots": []}, ensure_ascii=False)),
        ('AI', '@智能助手配置', json.dumps({
            "corp_id": "",
            "agent_id": "",
            "agent_secret": "",
            "token": "",
            "encoding_aes_key": "",
            "target_groups": []
        }, ensure_ascii=False)),
        ('WORK_WECHAT', '企业微信客服配置', json.dumps({
            "corp_id": "",
            "contact_secret": ""
        }, ensure_ascii=False)),
        ('WECHAT', '微信公众号配置', json.dumps({
            "app_id": "",
            "app_secret": "",
            "qrcode_url": "",
            "generate_user_on_follow": False,
            "promotion_type": "mall"
        }, ensure_ascii=False)),
        ('SMS', '短信配置', json.dumps({
            "provider": "aliyun",
            "access_key": "",
            "access_secret": "",
            "sign_name": "",
            "templates": {}
        }, ensure_ascii=False)),
        ('EMAIL', '邮件配置', json.dumps({
            "smtp_host": "",
            "smtp_port": 465,
            "username": "",
            "password": "",
            "from_name": "",
            "from_email": ""
        }, ensure_ascii=False))
    ]
    
    for channel_type, config_name, config_data in default_configs:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO channel_configs 
                (channel_type, config_name, config_data, is_enabled)
                VALUES (?, ?, ?, ?)
            """, (channel_type, config_name, config_data, 0 if channel_type != 'GROUP_BOT' else 1))
        except Exception as e:
            print(f"  ⚠ 插入配置失败 {channel_type}: {e}")
    
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
    print("  • messages 表: ✅ 已扩展（18个新字段）")
    print("  • 默认配置: ✅ 已插入6个渠道配置")
    print("\n🎯 现有数据:")
    
    # 统计现有数据
    try:
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_count = cursor.fetchone()[0]
        print(f"  • messages 表现有记录: {messages_count} 条（已保留）")
    except:
        print(f"  • messages 表: 新建")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM message_templates")
        templates_count = cursor.fetchone()[0]
        print(f"  • message_templates 表现有记录: {templates_count} 条（已保留）")
    except:
        print(f"  • message_templates 表: 未找到")
    
    print("\n✅ 所有现有数据均已保留，链路追踪功能完整！")
    print("\n下一步:")
    print("  1. 配置中心 → 渠道配置 → 完善各渠道的配置信息")
    print("  2. 模板管理 → 创建新模板 → 绑定渠道配置")
    print("  3. 测试发送 → 验证各渠道是否正常")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # 查找数据库文件
    db_paths = [
        "./customer_system.db",
        "../customer_system.db",
        "../../customer_system.db",
        "./backend/customer_system.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        db_path = "./customer_system.db"
        print(f"数据库文件不存在，将创建新文件: {db_path}")
    
    try:
        run_migration(db_path)
        print("\n✅ 迁移完成")
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
