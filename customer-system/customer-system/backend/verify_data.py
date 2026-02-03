"""
验证数据库中的模板数据
"""
import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

print("=" * 60)
print("📊 数据库模板数据验证")
print("=" * 60)
print()

# 查询所有模板
cursor.execute("SELECT id, name, channel, is_system FROM message_templates ORDER BY channel, id")
templates = cursor.fetchall()

if not templates:
    print("❌ 数据库中没有模板数据！")
else:
    print(f"✅ 找到 {len(templates)} 个模板：")
    print()
    
    current_channel = None
    for template_id, name, channel, is_system in templates:
        if channel != current_channel:
            current_channel = channel
            print(f"\n【{channel}】")
        
        system_flag = "🔒系统" if is_system else "  自定义"
        print(f"  {system_flag} | ID:{template_id:3d} | {name}")

print()
print("=" * 60)

# 检查是否有系统预留模板
cursor.execute("SELECT COUNT(*) FROM message_templates WHERE is_system = 1")
system_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM message_templates WHERE is_system = 0")
custom_count = cursor.fetchone()[0]

print(f"📦 系统预留模板：{system_count} 个")
print(f"📝 自定义模板：{custom_count} 个")
print(f"📊 总计：{system_count + custom_count} 个")
print("=" * 60)

conn.close()
