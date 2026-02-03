"""
创建配置管理相关数据库表
"""
import asyncio
from app.database import async_session_maker, engine
from app.models_config import Base


async def create_tables():
    """创建所有表"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建成功!")
    print("   - config_groups (配置分组表)")
    print("   - enhanced_system_configs (配置项表)")
    print("   - workflow_templates (业务流程模板表)")
    print("   - robot_webhooks (群机器人表)")
    print("   - admin_users (管理员用户表)")
    print("   - roles (角色表)")
    print("   - permissions (权限表)")
    print("   - operation_logs (操作日志表)")


if __name__ == "__main__":
    asyncio.run(create_tables())
