"""测试消息发送功能"""
import sqlite3
import json
import asyncio
from datetime import datetime

# 模拟数据库连接池（简化版）
class SimpleDBPool:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def acquire(self):
        return SimpleConnection(self.db_path)

class SimpleConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
    
    async def __aenter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    async def __aexit__(self, *args):
        if self.conn:
            self.conn.close()
    
    async def fetchrow(self, query, *params):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    async def execute(self, query, *params):
        cursor = self.conn.cursor()
        # params已经是tuple，不需要再包装
        if params and isinstance(params[0], (list, tuple)):
            cursor.execute(query, params[0])
        else:
            cursor.execute(query, params)
        self.conn.commit()
        return cursor

# 简化版的UnifiedMessageSender
class SimplifiedMessageSender:
    def __init__(self, db_pool):
        self.db = db_pool
    
    async def get_template(self, template_id):
        """获取模板"""
        async with self.db.acquire() as conn:
            template = await conn.fetchrow("""
                SELECT * FROM message_templates WHERE id = ?
            """, template_id)
            return template
    
    async def render_template(self, content, variables):
        """渲染模板"""
        result = content
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    async def create_message_record(self, template_id, channel_type, recipient, content):
        """创建消息记录"""
        import random
        message_no = f"MSG{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        async with self.db.acquire() as conn:
            cursor = await conn.execute("""
                INSERT INTO messages (
                    message_no,
                    template_id,
                    channel_type,
                    recipient_type,
                    recipient_value,
                    content,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_no,
                template_id,
                channel_type,
                'group_id',
                recipient,
                content,
                'pending',
                datetime.now().isoformat()
            ))
            
            return message_no
    
    async def test_send(self, template_id, variables):
        """测试发送"""
        print(f"\n{'='*60}")
        print(f"测试发送 - 模板ID: {template_id}")
        print(f"{'='*60}")
        
        # 1. 获取模板
        template = await self.get_template(template_id)
        if not template:
            print(f"❌ 模板不存在: {template_id}")
            return
        
        print(f"\n📝 模板信息:")
        print(f"  名称: {template['name']}")
        print(f"  类型: {template['module_type']}")
        print(f"  推送模式: {template['push_mode']}")
        
        # 2. 渲染内容
        rendered_content = await self.render_template(template['content'], variables)
        
        print(f"\n✏️  渲染后的内容:")
        print(f"{'─'*60}")
        print(rendered_content)
        print(f"{'─'*60}")
        
        # 3. 获取目标配置
        target_config = json.loads(template['target_config']) if template['target_config'] else {}
        bot_id = target_config.get('bot_id', 'bot_001')
        
        # 4. 获取群机器人配置
        async with self.db.acquire() as conn:
            config_row = await conn.fetchrow("""
                SELECT config_data FROM channel_configs
                WHERE channel_type = 'GROUP_BOT'
            """)
            
            if config_row:
                config = json.loads(config_row['config_data'])
                bots = config.get('bots', [])
                
                # 查找对应的bot
                bot = next((b for b in bots if b['bot_id'] == bot_id), None)
                
                if bot:
                    print(f"\n📱 发送目标:")
                    print(f"  机器人: {bot['bot_name']}")
                    print(f"  群ID: {bot['group_id']}")
                    print(f"  Webhook: {bot['webhook_url'][:50]}...")
                    
                    # 5. 创建消息记录
                    message_no = await self.create_message_record(
                        template_id,
                        template['module_type'],
                        bot['group_id'],
                        rendered_content
                    )
                    
                    print(f"\n✅ 消息记录已创建:")
                    print(f"  消息编号: {message_no}")
                    print(f"  状态: pending (待发送)")
                    
                    # 模拟发送（实际环境中会调用webhook）
                    print(f"\n💬 模拟发送到群机器人...")
                    print(f"  ⚠️  注意: 这是测试模式，不会真正发送消息")
                    print(f"  ⚠️  实际发送需要配置真实的webhook_url")
                    
                    # 更新状态为已发送
                    async with self.db.acquire() as conn:
                        await conn.execute("""
                            UPDATE messages
                            SET status = 'sent',
                                sent_at = ?
                            WHERE message_no = ?
                        """, (datetime.now().isoformat(), message_no))
                    
                    print(f"\n✅ 测试发送完成!")
                    print(f"  消息状态: sent (已发送)")
                    
                else:
                    print(f"❌ 未找到机器人配置: {bot_id}")
            else:
                print(f"❌ 群机器人配置不存在")

async def main():
    """主函数"""
    db_pool = SimpleDBPool('./customer_system.db')
    sender = SimplifiedMessageSender(db_pool)
    
    print("🚀 消息系统测试程序")
    print("="*60)
    
    # 测试实时推送模板
    print("\n【测试1】实时推送模板")
    await sender.test_send(
        template_id=2,
        variables={
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': '这是一条测试消息，验证消息系统是否正常工作'
        }
    )
    
    # 测试定时推送模板
    print("\n\n【测试2】定时推送模板")
    await sender.test_send(
        template_id=1,
        variables={
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'pending_count': 5,
            'processing_count': 12,
            'completed_count': 38
        }
    )
    
    # 查看消息记录
    print("\n\n📊 消息发送记录:")
    print("="*60)
    
    conn = sqlite3.connect('./customer_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            message_no,
            template_id,
            channel_type,
            status,
            created_at,
            sent_at
        FROM messages
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(f"\n消息编号: {row['message_no']}")
            print(f"  模板ID: {row['template_id']}")
            print(f"  渠道: {row['channel_type']}")
            print(f"  状态: {row['status']}")
            print(f"  创建时间: {row['created_at']}")
            print(f"  发送时间: {row['sent_at'] or '未发送'}")
    else:
        print("暂无消息记录")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
