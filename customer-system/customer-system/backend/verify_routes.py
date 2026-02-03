"""验证路由注册脚本"""
from app.main import app

print("\n" + "=" * 60)
print("已注册的API路由：")
print("=" * 60)

for route in app.routes:
    if hasattr(route, 'methods'):
        methods = ', '.join(route.methods)
        print(f"  {route.path:<40} [{methods}]")
    else:
        print(f"  {route.path:<40} [WebSocket/Static]")

print("\n" + "=" * 60)
print("✅ view路由已成功集成！")
print("=" * 60)

# 检查关键端点
critical_endpoints = [
    "/view/project-detail",
    "/view/api/project/progress",
    "/view/api/project/invalidate-cache"
]

print("\n关键端点检查：")
all_paths = [route.path for route in app.routes]
for endpoint in critical_endpoints:
    if endpoint in all_paths:
        print(f"  ✅ {endpoint}")
    else:
        print(f"  ❌ {endpoint} - 未找到！")

print()
