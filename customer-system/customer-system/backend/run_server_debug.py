import sys
import os

print("=== 启动后端服务 ===")
print(f"当前目录: {os.getcwd()}")
print(f"Python版本: {sys.version}")

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
print(f"Backend目录: {backend_dir}")
print(f"Python路径: {sys.path[:3]}")

try:
    print("\n导入app.main...")
    from app.main import app
    print("✅ app.main导入成功")
    
    print("\n导入uvicorn...")
    import uvicorn
    print("✅ uvicorn导入成功")
    
    print("\n启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")
