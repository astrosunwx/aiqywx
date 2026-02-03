"""
初始化AI模型配置数据
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models_ai import AIModelConfig
from sqlalchemy import select

async def init_ai_models():
    """初始化默认的AI模型配置"""
    async with async_session_maker() as db:
        # 检查是否已有数据
        result = await db.execute(select(AIModelConfig))
        existing_models = result.scalars().all()
        
        if len(existing_models) > 0:
            print(f"✅ 数据库中已有 {len(existing_models)} 个AI模型配置")
            for model in existing_models:
                print(f"   - {model.model_name} ({model.model_code}) - {'启用' if model.is_active else '禁用'}")
            
            user_input = input("\n是否要重新初始化？这将删除现有配置 (y/n): ")
            if user_input.lower() != 'y':
                print("❌ 已取消")
                return
            
            # 删除现有配置
            for model in existing_models:
                await db.delete(model)
            await db.commit()
            print("🗑️ 已删除现有配置")
        
        # 创建默认AI模型
        default_models = [
            AIModelConfig(
                model_code="wework-official",
                model_name="企业微信官方API",
                provider="wework",
                provider_display_name="企业微信",
                description="使用企业微信官方API进行智能问答",
                is_official=True,
                is_active=True,
                is_default=True,
                priority=100
            ),
            AIModelConfig(
                model_code="zhipu-chatglm-turbo",
                model_name="智谱AI ChatGLM-Turbo",
                provider="zhipu",
                provider_display_name="智谱AI",
                model_version="chatglm-turbo",
                api_endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
                description="智谱AI的ChatGLM-Turbo模型，速度快、成本低",
                is_official=False,
                is_active=True,
                is_default=False,
                priority=90
            ),
            AIModelConfig(
                model_code="tencent-hunyuan",
                model_name="腾讯混元",
                provider="tencent",
                provider_display_name="腾讯云",
                model_version="hunyuan-lite",
                api_endpoint="https://hunyuan.tencentcloudapi.com",
                description="腾讯自研的混元大模型",
                is_official=False,
                is_active=True,
                is_default=False,
                priority=85
            ),
            AIModelConfig(
                model_code="doubao-lite",
                model_name="字节豆包-Lite",
                provider="doubao",
                provider_display_name="字节跳动",
                model_version="doubao-lite-4k",
                api_endpoint="https://ark.cn-beijing.volces.com/api/v3",
                description="字节跳动的豆包大模型轻量版",
                is_official=False,
                is_active=False,
                is_default=False,
                priority=80
            ),
            AIModelConfig(
                model_code="deepseek-chat",
                model_name="DeepSeek Chat",
                provider="deepseek",
                provider_display_name="DeepSeek",
                model_version="deepseek-chat",
                api_endpoint="https://api.deepseek.com/v1",
                description="DeepSeek的对话模型，性价比高",
                is_official=False,
                is_active=False,
                is_default=False,
                priority=75
            )
        ]
        
        for model in default_models:
            db.add(model)
        
        await db.commit()
        print(f"\n✅ 成功初始化 {len(default_models)} 个AI模型配置：")
        for model in default_models:
            status = "✅启用" if model.is_active else "❌禁用"
            default = " ⭐默认" if model.is_default else ""
            official = " 🏢官方" if model.is_official else ""
            print(f"   {status} {model.model_name} ({model.model_code}){default}{official}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI模型配置初始化工具")
    print("=" * 60)
    asyncio.run(init_ai_models())
    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
