#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库字段格式"""

import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, keywords, targets 
    FROM message_templates 
    LIMIT 3
""")

print("前3个模板的字段值:")
for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"名称: {row[1]}")
    print(f"keywords: {row[2]} (类型: {type(row[2])})")
    print(f"targets: {row[3]} (类型: {type(row[3])})")

conn.close()
