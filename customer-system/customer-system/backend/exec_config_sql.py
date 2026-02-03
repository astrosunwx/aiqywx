"""
执行config_management_extension.sql来创建表
"""
import sqlite3

# 读取SQL文件
with open('config_management_extension.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# SQLite不支持的语法需要替换
sql_content = sql_content.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
sql_content = sql_content.replace('JSONB', 'TEXT')
sql_content = sql_content.replace('COMMENT', '--')
sql_content = sql_content.replace('TEXT DEFAULT \'[]\'', 'TEXT DEFAULT \'[]\'')

# 连接数据库并执行
conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

# 分割并执行每个语句
statements = sql_content.split(';')
for statement in statements:
    statement = statement.strip()
    if statement and not statement.startswith('--'):
        try:
            cursor.execute(statement)
            print(f"✅ 执行成功: {statement[:60]}...")
        except Exception as e:
            if 'already exists' not in str(e):
                print(f"❌ 错误: {e}")
                print(f"   SQL: {statement[:100]}...")

conn.commit()
conn.close()

print("\n✅ 数据库表创建完成!")
