import sqlite3

conn = sqlite3.connect('customer_system.db')
c = conn.cursor()

# 删除AI配置组的配置项
c.execute("DELETE FROM enhanced_system_config WHERE group_id IN (SELECT id FROM config_groups WHERE group_code='ai')")
print(f"删除了 {c.rowcount} 个AI配置项")

# 删除AI配置组
c.execute("DELETE FROM config_groups WHERE group_code='ai'")
print(f"删除了 {c.rowcount} 个配置组")

# 更新数据库配置的排序
c.execute("UPDATE config_groups SET sort_order=3 WHERE group_code='database'")

conn.commit()

# 查看剩余配置组
c.execute('SELECT group_code, group_name, sort_order FROM config_groups ORDER BY sort_order')
groups = c.fetchall()

print('\n✅ AI配置组已删除')
print('\n剩余配置组:')
for group in groups:
    print(f'  {group[2]}. {group[1]} ({group[0]})')

conn.close()
