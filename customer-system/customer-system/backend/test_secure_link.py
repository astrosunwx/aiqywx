"""
安全链接功能测试脚本
演示如何生成和验证项目详情链接
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.secure_link_service import SecureLinkService
from app.services.cache_service import cache_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


async def test_generate_link():
    """测试生成安全链接"""
    print("=" * 60)
    print("📌 测试1：生成项目详情安全链接")
    print("=" * 60)
    
    # 模拟参数
    user_id = "test_user_001"
    project_id = 1
    wechat_user_id = "test_user_001"
    
    # 生成1小时有效链接（客户链接）
    customer_link = SecureLinkService.generate_project_detail_link(
        user_id=user_id,
        project_id=project_id,
        wechat_user_id=wechat_user_id,
        expiry_hours=1
    )
    
    print(f"\n✅ 客户链接（1小时有效）：")
    print(f"   {customer_link}")
    
    # 生成24小时有效链接（内部链接）
    internal_link = SecureLinkService.generate_project_detail_link(
        user_id=user_id,
        project_id=project_id,
        wechat_user_id=wechat_user_id,
        expiry_hours=24
    )
    
    print(f"\n✅ 内部链接（24小时有效）：")
    print(f"   {internal_link}")
    
    return customer_link


async def test_verify_token():
    """测试验证令牌"""
    print("\n" + "=" * 60)
    print("📌 测试2：验证令牌")
    print("=" * 60)
    
    # 生成一个新令牌
    user_id = "test_user_002"
    project_id = 2
    
    link = SecureLinkService.generate_project_detail_link(
        user_id=user_id,
        project_id=project_id,
        wechat_user_id=user_id,
        expiry_hours=1
    )
    
    # 提取token
    token = link.split("token=")[1]
    
    try:
        # 验证令牌
        payload = SecureLinkService.verify_token(token)
        print(f"\n✅ 令牌验证成功！")
        print(f"   用户ID: {payload['user_id']}")
        print(f"   项目ID: {payload['project_id']}")
        print(f"   类型: {payload['type']}")
        print(f"   签发时间: {payload['iat']}")
        print(f"   过期时间: {payload['exp']}")
        
    except ValueError as e:
        print(f"\n❌ 令牌验证失败: {e}")


async def test_cache_service():
    """测试Redis缓存服务"""
    print("\n" + "=" * 60)
    print("📌 测试3：Redis缓存服务")
    print("=" * 60)
    
    project_id = 123
    
    # 测试数据
    test_data = {
        'status': '进行中',
        'progress': 75,
        'updated_at': '2026-02-01T15:30:00',
        'team_members': ['张三', '李四', '王五']
    }
    
    print(f"\n📝 写入缓存（项目ID: {project_id}）...")
    success = cache_service.set_project_progress(project_id, test_data, expire_seconds=60)
    
    if success:
        print(f"✅ 缓存写入成功（60秒过期）")
        
        # 读取缓存
        print(f"\n📖 读取缓存...")
        cached_data = cache_service.get_project_progress(project_id)
        
        if cached_data:
            print(f"✅ 缓存命中！数据：")
            print(f"   状态: {cached_data['status']}")
            print(f"   进度: {cached_data['progress']}%")
            print(f"   更新时间: {cached_data['updated_at']}")
            print(f"   团队成员: {', '.join(cached_data['team_members'])}")
        else:
            print(f"❌ 缓存未命中")
        
        # 清除缓存
        print(f"\n🗑️  清除缓存...")
        cache_service.invalidate_project_cache(project_id)
        print(f"✅ 缓存已清除")
        
        # 再次读取（应该未命中）
        cached_data = cache_service.get_project_progress(project_id)
        if cached_data is None:
            print(f"✅ 验证成功：缓存已被清除")
        
    else:
        print(f"⚠️  缓存写入失败（Redis可能未启动）")
        print(f"   提示：Redis未配置时系统会自动降级为数据库查询")


async def test_invalid_token():
    """测试无效令牌"""
    print("\n" + "=" * 60)
    print("📌 测试4：测试无效令牌")
    print("=" * 60)
    
    # 测试1：篡改过的令牌
    print("\n🔒 测试篡改过的令牌...")
    fake_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.fake_payload.fake_signature"
    
    try:
        SecureLinkService.verify_token(fake_token)
        print("❌ 验证应该失败但却通过了！")
    except ValueError as e:
        print(f"✅ 正确拦截：{e}")
    
    # 测试2：过期令牌（生成一个立即过期的令牌）
    print("\n⏰ 测试过期令牌...")
    import jwt
    import datetime
    
    expired_payload = {
        'user_id': 'test',
        'project_id': 1,
        'wechat_user_id': 'test',
        'type': 'project_detail',
        'iat': datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)  # 1小时前过期
    }
    
    expired_token = jwt.encode(
        expired_payload,
        SecureLinkService.SECRET_KEY,
        algorithm=SecureLinkService.ALGORITHM
    )
    
    try:
        SecureLinkService.verify_token(expired_token)
        print("❌ 验证应该失败但却通过了！")
    except ValueError as e:
        print(f"✅ 正确拦截：{e}")


async def main():
    """运行所有测试"""
    print("\n")
    print("🚀 " + "=" * 56 + " 🚀")
    print("     安全链接与缓存策略 - 功能测试")
    print("🚀 " + "=" * 56 + " 🚀")
    print("\n")
    
    try:
        # 测试1：生成链接
        await test_generate_link()
        
        # 测试2：验证令牌
        await test_verify_token()
        
        # 测试3：缓存服务
        await test_cache_service()
        
        # 测试4：无效令牌
        await test_invalid_token()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
        print("\n💡 下一步操作：")
        print("   1. 确保后端服务正在运行：python -m uvicorn app.main:app --reload")
        print("   2. 访问 API 文档：http://localhost:8000/docs")
        print("   3. 查看 /view/project-detail 端点")
        print("   4. 使用上面生成的链接访问项目详情页面")
        print("   5. 在企业微信中发送消息触发工单创建（自动包含安全链接）\n")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
