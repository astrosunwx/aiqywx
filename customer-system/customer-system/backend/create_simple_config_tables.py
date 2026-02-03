"""
简单直接创建config_groups和enhanced_system_config表
"""
import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

# 创建config_groups表
cursor.execute('''
CREATE TABLE IF NOT EXISTS config_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_code TEXT UNIQUE NOT NULL,
    group_name TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    icon TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建enhanced_system_config表
cursor.execute('''
CREATE TABLE IF NOT EXISTS enhanced_system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    config_type TEXT DEFAULT 'string',
    group_id INTEGER,
    display_name TEXT,
    description TEXT,
    is_required INTEGER DEFAULT 0,
    is_sensitive INTEGER DEFAULT 0,
    default_value TEXT,
    validation_rule TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES config_groups(id)
)
''')

conn.commit()
conn.close()

print("✅ 配置表创建成功!")
print("   - config_groups")
print("   - enhanced_system_config")
