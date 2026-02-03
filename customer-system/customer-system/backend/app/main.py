from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    ai_router, wechat, admin, view, sidebar, auto_notify, 
    customer_transfer, wework_callback, after_sales_router, prospect_router,
    service_request_router, config_center, messages_router, ai_model_router,
    datasource
)
from app.api import template_management, channel_config
import os

app = FastAPI(
    title="智能售前售后系统",
    description="基于企业微信和微信公众号的双入口智能客户服务系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ai_router.router, tags=["AI智能路由"])
app.include_router(ai_model_router.router, tags=["AI模型配置"])
app.include_router(template_management.router, tags=["消息模板管理"])
app.include_router(channel_config.router, tags=["渠道配置管理"])
app.include_router(wechat.router, tags=["企业微信"])
app.include_router(admin.router, tags=["管理后台"])
app.include_router(config_center.router, tags=["配置中心"])
app.include_router(datasource.router, tags=["数据源管理"])
app.include_router(messages_router.router, tags=["消息处理"])
app.include_router(view.router, tags=["页面视图"])
app.include_router(sidebar.router, tags=["聊天工具栏侧边栏"])
app.include_router(auto_notify.router, tags=["自动通知"])
app.include_router(customer_transfer.router, tags=["客户关系转接"])
app.include_router(wework_callback.router, tags=["企业微信回调"])
app.include_router(after_sales_router.router, tags=["售后服务"])
app.include_router(prospect_router.router, tags=["商机管理"])
app.include_router(service_request_router.router, tags=["客户服务请求"])

@app.get("/")
async def root():
    return {
        "message": "智能售前售后系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
