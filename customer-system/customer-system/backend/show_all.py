#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, module_type, channel 
    FROM message_templates 
    ORDER BY id
""")

print("所有模板:")
for row in cursor.fetchall():
    print(f"ID:{row[0]:3d} | {row[1]:30s} | module_type:{row[2]:15s} | channel:{row[3] or 'NULL'}")

conn.close()
