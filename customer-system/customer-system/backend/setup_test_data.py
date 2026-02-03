"""创建message_templates表和配置测试数据"""
import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('./customer_system.db')
cursor = conn.cursor()

# 1. 创建message_templates表
print("创建message_templates表...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS message_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        module_type VARCHAR(20) NOT NULL,
        category VARCHAR(50),
        content TEXT NOT NULL,
        content_type VARCHAR(20) DEFAULT 'text',
        channel_config_id INTEGER,
        target_config TEXT,
        push_mode VARCHAR(20) DEFAULT 'realtime',
        keywords TEXT,
        schedule_time TIME,
        repeat_type VARCHAR(20) DEFAULT 'once',
        targets TEXT,
        is_enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ message_templates表创建成功")

# 2. 配置群机器人（示例配置）
print("\n配置群机器人...")
cursor.execute("""
    UPDATE channel_configs
    SET config_data = ?,
        is_enabled = 1
    WHERE channel_type = 'GROUP_BOT'
""", (json.dumps({
    "bots": [
        {
            "bot_id": "bot_001",
            "bot_name": "测试群机器人",
            "group_id": "test_group_001",
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test_key"
        }
    ]
}, ensure_ascii=False),))
print("✅ 群机器人配置完成")

# 3. 创建测试模板
print("\n创建测试模板...")
cursor.execute("""
    INSERT INTO message_templates (
        name,
        module_type,
        category,
        content,
        content_type,
        push_mode,
        schedule_time,
        repeat_type,
        target_config,
        is_enabled
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    '每日工作提醒',
    'GROUP_BOT',
    '系统通知',
    '''📅 今日工作提醒（{current_date}）

待处理工单：{pending_count} ↑
进行中工单：{processing_count} ↑
已完成工单：{completed_count} ↑

请各位同事及时跟进，保证服务质量！''',
    'markdown',
    'scheduled',
    '09:00',
    'daily',
    json.dumps({"bot_id": "bot_001"}, ensure_ascii=False),
    1
))

template_id = cursor.lastrowid
print(f"✅ 测试模板创建成功 (ID: {template_id})")

# 4. 创建实时推送测试模板
print("\n创建实时推送测试模板...")
cursor.execute("""
    INSERT INTO message_templates (
        name,
        module_type,
        category,
        content,
        content_type,
        push_mode,
        keywords,
        target_config,
        is_enabled
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    '测试消息',
    'GROUP_BOT',
    '系统通知',
    '''🔔 测试消息

时间：{current_time}
内容：{message}

这是一条测试消息！''',
    'markdown',
    'realtime',
    json.dumps(['测试', 'test'], ensure_ascii=False),
    json.dumps({"bot_id": "bot_001"}, ensure_ascii=False),
    1
))

test_template_id = cursor.lastrowid
print(f"✅ 实时推送测试模板创建成功 (ID: {test_template_id})")

# 提交事务
conn.commit()

print("\n" + "=" * 60)
print("✅ 所有配置完成！")
print("=" * 60)
print(f"\n📊 创建的资源:")
print(f"  • message_templates表: ✅ 已创建")
print(f"  • 群机器人配置: ✅ 已更新")
print(f"  • 定时推送模板: ✅ ID={template_id} (每日9:00)")
print(f"  • 实时推送模板: ✅ ID={test_template_id}")

print(f"\n🎯 下一步:")
print(f"  1. 测试实时推送模板 (ID: {test_template_id})")
print(f"  2. 验证定时任务模板 (ID: {template_id})")

cursor.close()
conn.close()
