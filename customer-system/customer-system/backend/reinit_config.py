import sqlite3
import asyncio
import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from init_config import init_config

async def main():
    # 删除现有配置
    conn = sqlite3.connect('customer_system.db')
    c = conn.cursor()
    
    print("正在删除现有配置...")
    c.execute("DELETE FROM enhanced_system_config")
    c.execute("DELETE FROM config_groups")
    conn.commit()
    print("* 旧配置已删除")
    
    conn.close()
    
    # 重新初始化
    print("\n正在初始化新配置...")
    await init_config()
    
    # 验证结果
    conn = sqlite3.connect('customer_system.db')
    c = conn.cursor()
    c.execute('SELECT group_code, group_name, sort_order FROM config_groups ORDER BY sort_order')
    groups = c.fetchall()
    
    print('\n配置组列表:')
    for group in groups:
        c.execute('SELECT COUNT(*) FROM enhanced_system_config WHERE group_id IN (SELECT id FROM config_groups WHERE group_code=?)', (group[0],))
        count = c.fetchone()[0]
        print(f'  {group[2]}. {group[1]} ({group[0]}) - {count}个配置项')
    
    # 显示远程数据库配置项
    print('\n远程数据库配置项:')
    c.execute('''
        SELECT config_key, display_name, description, config_type, is_required
        FROM enhanced_system_config 
        WHERE group_id IN (SELECT id FROM config_groups WHERE group_code='remote_database')
        ORDER BY sort_order
    ''')
    for row in c.fetchall():
        required = "必填" if row[4] else "可选"
        print(f'  - {row[1]} ({row[0]}): {row[2]} [{row[3]}, {required}]')
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
