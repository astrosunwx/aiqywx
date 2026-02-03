"""删除远程数据库配置组"""
import sqlite3

conn = sqlite3.connect('customer_system.db')
c = conn.cursor()

# 删除远程数据库配置项
c.execute('DELETE FROM enhanced_system_config WHERE group_id IN (SELECT id FROM config_groups WHERE group_code="remote_database")')
deleted_configs = c.rowcount

# 删除远程数据库配置组
c.execute('DELETE FROM config_groups WHERE group_code="remote_database"')
deleted_groups = c.rowcount

# 更新本地数据库配置组的排序
c.execute('UPDATE config_groups SET sort_order=3 WHERE group_code="database"')

conn.commit()

print(f'✓ 删除了 {deleted_configs} 个配置项')
print(f'✓ 删除了 {deleted_groups} 个配置组')
print('\n剩余配置组:')
for row in c.execute('SELECT group_code, group_name, sort_order FROM config_groups ORDER BY sort_order'):
    print(f'  {row[2]}. {row[1]} ({row[0]})')

conn.close()
print('\n✓ 完成!')
