#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""统一修复 module_type 和 channel 字段"""

import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

# 删除 channel 列（如果存在）
try:
    cursor.execute("ALTER TABLE message_templates DROP COLUMN channel")
    print("✅ 已删除 channel 列")
except:
    print("ℹ️  channel 列不存在或无法删除")

# 重新添加 channel 列并设置为与 module_type 相同
cursor.execute("""
    ALTER TABLE message_templates 
    ADD COLUMN channel VARCHAR(50)
""")
print("✅ 已添加 channel 列")

# 将 module_type 的值复制到 channel
cursor.execute("""
    UPDATE message_templates 
    SET channel = module_type
""")
print("✅ 已同步 channel = module_type")

conn.commit()

# 验证结果
cursor.execute("""
    SELECT module_type, COUNT(*) as cnt
    FROM message_templates
    GROUP BY module_type
    ORDER BY cnt DESC
""")

print("\n📊 最终分布:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} 个")

# 显示几个示例
cursor.execute("""
    SELECT id, name, module_type, channel
    FROM message_templates
    LIMIT 5
""")
print("\n📝 前5个模板示例:")
for row in cursor.fetchall():
    print(f"  ID{row[0]}: module_type={row[2]}, channel={row[3]}")

conn.close()
print("\n✅ 修复完成!")
