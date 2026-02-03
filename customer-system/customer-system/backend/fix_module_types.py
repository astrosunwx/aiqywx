#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复模板的 module_type 字段
根据模板的 channel 字段正确设置 module_type
"""

import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'customer_system.db')

def fix_module_types():
    """修复所有模板的 module_type"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查看当前状态
    cursor.execute("SELECT COUNT(*) FROM message_templates")
    total = cursor.fetchone()[0]
    print(f"📊 数据库中共有 {total} 个模板")
    
    # 根据 channel 更新 module_type
    # AI -> AI
    cursor.execute("""
        UPDATE message_templates 
        SET module_type = 'AI' 
        WHERE channel = 'AI' OR name LIKE '%AI%' OR name LIKE '%智能%'
    """)
    ai_count = cursor.rowcount
    print(f"✅ 更新 {ai_count} 个 AI 模板")
    
    # WORK_WECHAT -> WORK_WECHAT
    cursor.execute("""
        UPDATE message_templates 
        SET module_type = 'WORK_WECHAT' 
        WHERE channel = 'WORK_WECHAT' OR name LIKE '%企业微信%' OR name LIKE '%工单%'
    """)
    work_count = cursor.rowcount
    print(f"✅ 更新 {work_count} 个企业微信模板")
    
    # WECHAT -> WECHAT
    cursor.execute("""
        UPDATE message_templates 
        SET module_type = 'WECHAT' 
        WHERE channel = 'WECHAT' OR name LIKE '%公众号%'
    """)
    wechat_count = cursor.rowcount
    print(f"✅ 更新 {wechat_count} 个微信公众号模板")
    
    # SMS -> SMS
    cursor.execute("""
        UPDATE message_templates 
        SET module_type = 'SMS' 
        WHERE channel = 'SMS' OR name LIKE '%短信%'
    """)
    sms_count = cursor.rowcount
    print(f"✅ 更新 {sms_count} 个短信模板")
    
    # GROUP_BOT 保持不变
    cursor.execute("""
        SELECT COUNT(*) FROM message_templates 
        WHERE module_type = 'GROUP_BOT'
    """)
    bot_count = cursor.fetchone()[0]
    print(f"✅ 保留 {bot_count} 个群机器人模板")
    
    conn.commit()
    
    # 验证结果
    print("\n📊 修复后的分布:")
    cursor.execute("""
        SELECT module_type, COUNT(*) as cnt 
        FROM message_templates 
        GROUP BY module_type 
        ORDER BY cnt DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 个")
    
    conn.close()
    print("\n✅ module_type 修复完成!")

if __name__ == '__main__':
    fix_module_types()
