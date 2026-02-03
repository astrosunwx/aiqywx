"""
执行AI模型配置数据库迁移脚本（支持SQLite）
"""
import os
import sqlite3

def run_migration():
    """执行迁移脚本"""
    
    print("="*60)
    print("开始执行AI模型配置数据库迁移（SQLite）")
    print("="*60)
    
    try:
        # 连接SQLite数据库
        db_path = "./customer_system.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n✅ 已连接到数据库: {db_path}")
        
        # 1. 创建AI模型配置表
        print("\n1️⃣  创建ai_model_configs表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_model_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_code TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_display_name TEXT,
                model_version TEXT,
                api_endpoint TEXT,
                api_key TEXT,
                extra_config TEXT,
                description TEXT,
                is_official INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ ai_model_configs表创建成功")
        
        # 2. 创建AI模型使用日志表
        print("\n2️⃣  创建ai_model_usage_logs表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_model_usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_code TEXT NOT NULL,
                user_message TEXT,
                ai_response TEXT,
                intent TEXT,
                confidence TEXT,
                response_time_ms INTEGER,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ ai_model_usage_logs表创建成功")
        
        # 3. 插入预置AI模型配置
        print("\n3️⃣  插入预置AI模型配置...")
        
        models = [
            ('wework-official', '企业微信官方API', 'wework', '腾讯企业微信', None, None, None, None, 
             '使用企业微信官方消息推送API，无需第三方大模型，基于规则引擎的智能回复系统。安全可靠，无封号风险。', 
             1, 1, 1, 100),
            
            ('tencent-hunyuan-a13b', '腾讯云混元-A13B', 'tencent', '腾讯云', 'hunyuan-A13B', 'https://hunyuan.tencentcloudapi.com', None, None,
             '腾讯云混元大模型 Hunyuan-A13B，高性能AI对话引擎，适合复杂对话场景。',
             0, 0, 0, 90),
            
            ('zhipu-glm4', '智谱 GLM-4', 'zhipu', '智谱AI', 'glm-4', None, None, None,
             '智谱AI提供的GLM-4大模型，适合通用对话和文本生成。需要配置API密钥。',
             0, 0, 0, 80),
            
            ('doubao', '豆包 Doubao', 'doubao', '字节跳动', None, None, None, None,
             '字节跳动豆包大模型，适合中文对话场景。需要配置API密钥。',
             0, 0, 0, 70),
            
            ('deepseek', 'DeepSeek', 'deepseek', 'DeepSeek', None, None, None, None,
             'DeepSeek大模型，适合代码和技术对话。需要配置API密钥。',
             0, 0, 0, 60)
        ]
        
        for model in models:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO ai_model_configs (
                        model_code, model_name, provider, provider_display_name,
                        model_version, api_endpoint, api_key, extra_config,
                        description, is_official, is_active, is_default, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, model)
                print(f"   ✅ {model[1]}")
            except Exception as e:
                print(f"   ⚠️  {model[1]} (可能已存在)")
        
        conn.commit()
        
        # 4. 查询已安装的AI模型
        print("\n4️⃣  查询已安装的AI模型：")
        print("-"*80)
        print(f"{'模型名称':<30} | {'服务商':<15} | {'类型':<8} | {'状态':<8} | 优先级")
        print("-"*80)
        
        cursor.execute("""
            SELECT 
                model_code,
                model_name,
                provider_display_name,
                is_official,
                is_active,
                is_default,
                priority
            FROM ai_model_configs
            ORDER BY priority DESC
        """)
        
        rows = cursor.fetchall()
        for row in rows:
            official = "✅官方" if row[3] else "第三方"
            default = " ⭐" if row[5] else ""
            active = "✅启用" if row[4] else "❌禁用"
            print(f"{row[1]:<28} | {row[2] or row[0]:<13} | {official:<6} | {active:<6} | {row[6]:3}{default}")
        
        print("-"*80)
        
        cursor.close()
        conn.close()
        
        print("\n🎉 数据库迁移完成！")
        print("\n📍 下一步:")
        print("   1. 重启后端服务（已自动加载新路由）")
        print("   2. 访问API文档: http://localhost:8000/docs")
        print("   3. 访问AI模型管理界面: http://localhost:3001/ai-models")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
