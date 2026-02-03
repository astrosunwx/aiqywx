"""
初始化系统配置数据
运行此脚本将创建默认的配置分组和配置项
"""
import asyncio
from app.database import async_session_maker
from app.models_config import ConfigGroup, EnhancedSystemConfig
from sqlalchemy import select


async def init_config():
    """初始化配置数据"""
    async with async_session_maker() as session:
        # 检查是否已有配置
        result = await session.execute(select(ConfigGroup))
        existing_groups = result.scalars().all()
        
        if existing_groups:
            print("✅ 配置已存在，跳过初始化")
            return
        
        # 创建配置分组
        groups_data = [
            {
                "group_code": "wework",
                "group_name": "企业微信配置",
                "description": "企业微信应用配置信息",
                "icon": "ChatLineRound",
                "sort_order": 1,
                "is_active": True
            },
            {
                "group_code": "ai",
                "group_name": "AI模型配置",
                "description": "配置智能问答使用的AI模型",
                "icon": "MagicStick",
                "sort_order": 2,
                "is_active": True
            },
            {
                "group_code": "database",
                "group_name": "数据库配置",
                "description": "数据库连接信息（可选）",
                "icon": "Coin",
                "sort_order": 3,
                "is_active": True
            }
        ]
        
        groups = []
        for group_data in groups_data:
            group = ConfigGroup(**group_data)
            session.add(group)
            groups.append(group)
        
        await session.commit()
        
        # 为每个分组创建配置项
        for group in groups:
            await session.refresh(group)
        
        # 企业微信配置项
        wework_group = next(g for g in groups if g.group_code == "wework")
        wework_configs = [
            {
                "group_id": wework_group.id,
                "config_key": "corp_id",
                "config_value": "",
                "config_type": "string",
                "display_name": "企业ID (CorpID)",
                "description": "企业微信管理后台获取",
                "is_required": True,
                "is_sensitive": False,
                "sort_order": 1
            },
            {
                "group_id": wework_group.id,
                "config_key": "agent_id",
                "config_value": "",
                "config_type": "string",
                "display_name": "应用AgentID",
                "description": "应用的AgentID",
                "is_required": True,
                "is_sensitive": False,
                "sort_order": 2
            },
            {
                "group_id": wework_group.id,
                "config_key": "secret",
                "config_value": "",
                "config_type": "password",
                "display_name": "应用Secret",
                "description": "应用的Secret密钥",
                "is_required": True,
                "is_sensitive": True,
                "sort_order": 3
            },
            {
                "group_id": wework_group.id,
                "config_key": "token",
                "config_value": "",
                "config_type": "string",
                "display_name": "消息Token",
                "description": "接收消息的Token",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 4
            },
            {
                "group_id": wework_group.id,
                "config_key": "encoding_aes_key",
                "config_value": "",
                "config_type": "password",
                "display_name": "EncodingAESKey",
                "description": "消息加解密密钥",
                "is_required": False,
                "is_sensitive": True,
                "sort_order": 5
            }
        ]
        
        # AI配置项
        ai_group = next(g for g in groups if g.group_code == "ai")
        ai_configs = [
            {
                "group_id": ai_group.id,
                "config_key": "ai_provider",
                "config_value": "openai",
                "config_type": "select",
                "display_name": "AI提供商",
                "description": "选择AI服务提供商：openai, azure, 通义千问",
                "is_required": True,
                "is_sensitive": False,
                "sort_order": 1
            },
            {
                "group_id": ai_group.id,
                "config_key": "ai_api_key",
                "config_value": "",
                "config_type": "password",
                "display_name": "API密钥",
                "description": "AI服务的API密钥",
                "is_required": True,
                "is_sensitive": True,
                "sort_order": 2
            },
            {
                "group_id": ai_group.id,
                "config_key": "ai_model",
                "config_value": "gpt-3.5-turbo",
                "config_type": "string",
                "display_name": "模型名称",
                "description": "使用的模型，如：gpt-3.5-turbo",
                "is_required": True,
                "is_sensitive": False,
                "sort_order": 3
            }
        ]
        
        # 数据库配置项
        db_group = next(g for g in groups if g.group_code == "database")
        db_configs = [
            {
                "group_id": db_group.id,
                "config_key": "db_type",
                "config_value": "sqlite",
                "config_type": "select",
                "display_name": "数据库类型",
                "description": "SQLite（默认）或PostgreSQL",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 1
            },
            {
                "group_id": db_group.id,
                "config_key": "db_host",
                "config_value": "localhost",
                "config_type": "string",
                "display_name": "数据库主机",
                "description": "PostgreSQL数据库地址",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 2
            }
        ]
        
        # 添加所有配置项
        all_configs = wework_configs + ai_configs + db_configs
        for config_data in all_configs:
            config = EnhancedSystemConfig(**config_data)
            session.add(config)
        
        await session.commit()
        
        print("✅ 配置初始化完成！")
        print(f"   创建了 {len(groups)} 个配置分组")
        print(f"   创建了 {len(all_configs)} 个配置项")


if __name__ == "__main__":
    asyncio.run(init_config())
