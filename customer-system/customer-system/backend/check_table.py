"""
检查message_templates表结构
"""
import sqlite3

def check_table_structure():
    conn = sqlite3.connect('customer_system.db')
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='message_templates'
    """)
    
    if not cursor.fetchone():
        print("❌ message_templates 表不存在")
        print("\n💡 建议：先启动后端服务让它自动创建表结构")
        conn.close()
        return
    
    # 获取表结构
    cursor.execute("PRAGMA table_info(message_templates)")
    columns = cursor.fetchall()
    
    print("📋 message_templates 表结构：")
    print("-" * 60)
    print(f"{'列名':<20} {'类型':<15} {'非空':<5} {'默认值':<10}")
    print("-" * 60)
    
    for col in columns:
        col_id, name, col_type, not_null, default_val, pk = col
        print(f"{name:<20} {col_type:<15} {'是' if not_null else '否':<5} {str(default_val) if default_val else '':<10}")
    
    print("-" * 60)
    print(f"总计：{len(columns)} 个字段")
    
    # 检查是否有channel字段
    has_channel = any(col[1] == 'channel' for col in columns)
    
    if not has_channel:
        print("\n⚠️ 缺少 channel 字段！")
        print("\n💡 解决方案：")
        print("1. 需要先运行后端的数据库迁移")
        print("2. 或者修改表结构添加channel字段")
        print("\n建议执行：")
        print("   python -c \"from app.database import init_db; init_db()\"")
    else:
        print("\n✅ 表结构完整，可以导入模板")
    
    conn.close()

if __name__ == '__main__':
    check_table_structure()
