"""
导入预留模板到数据库的脚本
"""
import sqlite3
import os

def import_templates():
    """导入SQL脚本到数据库"""
    db_path = 'customer_system.db'
    sql_file = 'init_message_templates.sql'
    
    # 检查文件是否存在
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 读取SQL文件
        print(f"📖 正在读取SQL文件: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 执行SQL脚本
        print(f"⚙️ 正在导入预留模板...")
        cursor.executescript(sql_script)
        
        # 提交事务
        conn.commit()
        
        # 验证导入结果
        print(f"\n✅ SQL脚本执行成功！")
        print(f"\n📊 验证导入结果：")
        print("-" * 50)
        
        cursor.execute("""
            SELECT channel, COUNT(*) as count 
            FROM message_templates 
            WHERE is_system = 1 
            GROUP BY channel
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        total = 0
        
        channel_names = {
            'AI': 'AI回复模板',
            'WORK_WECHAT': '企业微信模板',
            'WECHAT': '微信公众号模板',
            'GROUP_BOT': '群机器人模板',
            'SMS': '短信模板'
        }
        
        for channel, count in results:
            channel_name = channel_names.get(channel, channel)
            print(f"📋 {channel_name:15s} {count:2d} 个")
            total += count
        
        print("-" * 50)
        print(f"📦 总计：{total} 个预留模板")
        
        # 关闭连接
        conn.close()
        
        print(f"\n🎉 导入完成！现在可以刷新前端查看新模板了！")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("📝 消息模板管理 - 预留模板导入工具")
    print("=" * 50)
    print()
    
    success = import_templates()
    
    if success:
        print("\n" + "=" * 50)
        print("✨ 下一步操作：")
        print("=" * 50)
        print("1. 刷新浏览器（Ctrl + Shift + R 硬刷新）")
        print("2. 进入【消息模板管理】页面")
        print("3. 查看各个标签页的预留模板")
        print("4. 点击【编辑】按钮修改模板内容")
        print("5. 点击【测试发送】体验新功能")
        print()
        print("📖 查看文档：")
        print("   - 消息模板管理-完整升级指南.md")
        print("   - 消息模板管理-快速对照表.md")
        print("=" * 50)
