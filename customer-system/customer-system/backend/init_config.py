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
                "group_code": "wechat_official",
                "group_name": "微信公众号配置",
                "description": "微信公众号对接配置（可选）",
                "icon": "Message",
                "sort_order": 2,
                "is_active": True
            },
            {
                "group_code": "database",
                "group_name": "本地数据库配置",
                "description": "本地数据库连接信息(可选)",
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
        
        # 微信公众号配置项
        wechat_official_group = next(g for g in groups if g.group_code == "wechat_official")
        wechat_official_configs = [
            {
                "group_id": wechat_official_group.id,
                "config_key": "wechat_appid",
                "config_value": "",
                "config_type": "string",
                "display_name": "AppID",
                "description": "微信公众号的AppID",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 1
            },
            {
                "group_id": wechat_official_group.id,
                "config_key": "wechat_appsecret",
                "config_value": "",
                "config_type": "password",
                "display_name": "AppSecret",
                "description": "微信公众号的AppSecret",
                "is_required": False,
                "is_sensitive": True,
                "sort_order": 2
            },
            {
                "group_id": wechat_official_group.id,
                "config_key": "wechat_token",
                "config_value": "",
                "config_type": "string",
                "display_name": "Token",
                "description": "微信公众号服务器配置的Token",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 3
            },
            {
                "group_id": wechat_official_group.id,
                "config_key": "wechat_encoding_aes_key",
                "config_value": "",
                "config_type": "password",
                "display_name": "EncodingAESKey",
                "description": "消息加解密密钥（可选）",
                "is_required": False,
                "is_sensitive": True,
                "sort_order": 4
            },
            {
                "group_id": wechat_official_group.id,
                "config_key": "wechat_server_url",
                "config_value": "",
                "config_type": "string",
                "display_name": "服务器地址(URL)",
                "description": "配置到微信公众平台的服务器URL，例如: https://yourdomain.com/api/wechat/official",
                "is_required": False,
                "is_sensitive": False,
                "sort_order": 5
            }
        ]
        
        # 本地数据库配置项
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
        all_configs = wework_configs + wechat_official_configs + db_configs
        for config_data in all_configs:
            config = EnhancedSystemConfig(**config_data)
            session.add(config)
        
        await session.commit()
        
        print("✅ 配置初始化完成！")
        print(f"   创建了 {len(groups)} 个配置分组")
        print(f"   创建了 {len(all_configs)} 个配置项")


if __name__ == "__main__":
    asyncio.run(init_config())
