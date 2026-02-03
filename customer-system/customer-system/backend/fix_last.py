#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('customer_system.db')
conn.execute('UPDATE message_templates SET module_type = "GROUP_BOT" WHERE id = 25')
conn.commit()
print('✅ 已修复群机器人模板')

# 验证结果
cursor = conn.cursor()
cursor.execute('SELECT module_type, COUNT(*) FROM message_templates GROUP BY module_type')
print('\n最终分布:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 个')

conn.close()
