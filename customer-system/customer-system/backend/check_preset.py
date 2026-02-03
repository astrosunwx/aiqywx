#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查看 PRESET 类型的模板"""

import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, channel 
    FROM message_templates 
    WHERE module_type = 'PRESET'
""")

for row in cursor.fetchall():
    print(f"ID: {row[0]}, 名称: {row[1]}, 频道: {row[2]}")

conn.close()
