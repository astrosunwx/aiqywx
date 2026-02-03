import sqlite3
conn = sqlite3.connect('customer_system.db')
conn.execute('UPDATE message_templates SET module_type="GROUP_BOT", channel="GROUP_BOT" WHERE id=24')
conn.commit()
print('✅ 已将 ID 24 修复为 GROUP_BOT')

# 验证
cursor = conn.cursor()
cursor.execute('SELECT module_type, COUNT(*) FROM message_templates GROUP BY module_type')
print('\n最终分布:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 个')
conn.close()
