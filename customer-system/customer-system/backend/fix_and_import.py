"""
一键修复表结构并导入预留模板
"""
import sqlite3
import os

def fix_and_import():
    db_path = 'customer_system.db'
    sql_file = 'init_message_templates.sql'
    
    print("=" * 60)
    print("📝 消息模板管理 - 一键修复并导入工具")
    print("=" * 60)
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 步骤1：检查表是否存在
        print("🔍 步骤1：检查表结构...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='message_templates'
        """)
        
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("   ❌ message_templates 表不存在")
            print("   ⚙️ 正在创建表...")
            
            # 创建完整的表结构
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    channel VARCHAR(50) NOT NULL,
                    category VARCHAR(100),
                    type VARCHAR(50) DEFAULT 'text',
                    content TEXT NOT NULL,
                    ai_model VARCHAR(100),
                    push_mode VARCHAR(50),
                    keywords TEXT,
                    targets TEXT,
                    schedule_time TIMESTAMP,
                    repeat_type VARCHAR(50),
                    repeat_days TEXT,
                    status BOOLEAN DEFAULT 1,
                    is_system BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✅ 表创建成功")
        else:
            # 检查是否有channel字段
            cursor.execute("PRAGMA table_info(message_templates)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'channel' not in column_names:
                print("   ⚠️ 缺少 channel 字段，正在添加...")
                cursor.execute("ALTER TABLE message_templates ADD COLUMN channel VARCHAR(50) DEFAULT 'SMS'")
                print("   ✅ channel 字段添加成功")
            
            # 检查其他必要字段
            required_fields = {
                'category': 'VARCHAR(100)',
                'type': "VARCHAR(50) DEFAULT 'text'",
                'ai_model': 'VARCHAR(100)',
                'push_mode': 'VARCHAR(50)',
                'keywords': 'TEXT',
                'targets': 'TEXT',
                'schedule_time': 'TIMESTAMP',
                'repeat_type': 'VARCHAR(50)',
                'repeat_days': 'TEXT',
                'status': 'BOOLEAN DEFAULT 1',
                'is_system': 'BOOLEAN DEFAULT 0'
            }
            
            for field, field_type in required_fields.items():
                if field not in column_names:
                    print(f"   ⚙️ 添加字段: {field}")
                    try:
                        cursor.execute(f"ALTER TABLE message_templates ADD COLUMN {field} {field_type}")
                    except sqlite3.OperationalError:
                        pass  # 字段可能已存在
            
            print("   ✅ 表结构检查完成")
        
        conn.commit()
        
        # 步骤2：导入SQL脚本
        print("\n📖 步骤2：读取SQL文件...")
        if not os.path.exists(sql_file):
            print(f"   ❌ SQL文件不存在: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("   ✅ SQL文件读取成功")
        
        print("\n⚙️ 步骤3：导入预留模板...")
        
        # 检查module_type字段，如果存在且NOT NULL，则需要特殊处理
        cursor.execute("PRAGMA table_info(message_templates)")
        columns = cursor.fetchall()
        
        has_module_type = False
        module_type_not_null = False
        for col in columns:
            if col[1] == 'module_type':
                has_module_type = True
                module_type_not_null = col[3] == 1  # not_null flag
                break
        
        if has_module_type and module_type_not_null:
            print("   ⚙️ 检测到NOT NULL的module_type字段，正在处理...")
            # 修改SQL脚本，为所有INSERT添加module_type字段
            sql_script = sql_script.replace(
                "INSERT INTO message_templates (",
                "INSERT INTO message_templates (module_type, "
            ).replace(
                ") VALUES (",
                ") VALUES ('PRESET', "
            )
            print("   ✅ 已为所有INSERT语句添加module_type='PRESET'")
        
        # 先删除旧的系统模板（如果有）
        cursor.execute("DELETE FROM message_templates WHERE is_system = 1")
        print(f"   🗑️ 清理旧数据: 删除了 {cursor.rowcount} 条旧记录")
        
        # 执行SQL脚本
        cursor.executescript(sql_script)
        conn.commit()
        print("   ✅ SQL脚本执行成功")
        
        # 步骤4：验证导入结果
        print("\n📊 步骤4：验证导入结果...")
        print("-" * 60)
        
        cursor.execute("""
            SELECT channel, COUNT(*) as count 
            FROM message_templates 
            WHERE is_system = 1 
            GROUP BY channel
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        total = 0
        
        channel_names = {
            'AI': 'AI回复模板',
            'WORK_WECHAT': '企业微信模板',
            'WECHAT': '微信公众号模板',
            'GROUP_BOT': '群机器人模板',
            'SMS': '短信模板'
        }
        
        for channel, count in results:
            channel_name = channel_names.get(channel, channel)
            print(f"   📋 {channel_name:20s} {count:2d} 个")
            total += count
        
        print("-" * 60)
        print(f"   📦 总计：{total} 个预留模板")
        
        conn.close()
        
        if total > 0:
            print("\n" + "=" * 60)
            print("🎉 导入成功！")
            print("=" * 60)
            print("\n✨ 下一步操作：")
            print("   1. 刷新浏览器（Ctrl + Shift + R 硬刷新）")
            print("   2. 进入【消息模板管理】页面")
            print("   3. 查看各个标签页的预留模板")
            print("   4. 点击【编辑】按钮修改模板内容")
            print("   5. 点击【测试发送】体验新功能")
            print("\n📖 查看文档：")
            print("   - 消息模板管理-完整升级指南.md")
            print("   - 消息模板管理-快速对照表.md")
            print("=" * 60)
            return True
        else:
            print("\n⚠️ 警告：没有导入任何模板")
            return False
            
    except sqlite3.Error as e:
        print(f"\n❌ 数据库错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_and_import()
