# 项目同步功能 - 后端API实现指南

## 功能概述

实现项目状态缓存和定时同步功能，避免AI机器人频繁调取远程项目库。

## 核心机制

1. **缓存优先策略**：客户查看项目详情时，优先返回缓存数据
2. **定时同步**：后台定时任务从远程项目库同步最新状态
3. **状态通知**：仅在状态变更时发送通知给客户
4. **访问控制**：项目详情仅限相关人员查看（通过token验证）

## 需要实现的API

### 1. 验证访问权限

**接口**: `GET /api/projects/{project_id}/verify-access`

**查询参数**:
- `token`: 访问令牌（从消息模板中的链接获取）

**返回**:
```json
{
  "has_access": true,
  "user_id": "user123",
  "user_name": "张三",
  "access_type": "customer|engineer|salesman"
}
```

**实现逻辑**:
1. 解析token，获取用户信息
2. 检查用户与项目的关系（客户、工程师、销售）
3. 返回访问权限结果

### 2. 获取项目详情（带缓存）

**接口**: `GET /api/projects/{project_id}`

**查询参数**:
- `token`: 访问令牌
- `use_cache`: 是否使用缓存（默认true）
- `force_sync`: 是否强制同步（默认false）

**返回**:
```json
{
  "project": {
    "id": "P123456",
    "type": "presale|aftersales|sales",
    "title": "空调销售商机",
    "status": "pending|processing|resolved|shipped|completed",
    "customer_name": "张三",
    "phone": "138****8888",
    // ... 其他字段根据type不同而不同
  },
  "from_cache": true,
  "cache_time": "5分钟前",
  "last_sync": "2024-02-02 15:30:00"
}
```

**实现逻辑**:
1. 验证访问权限
2. 检查缓存是否存在且未过期
3. 如果`use_cache=true`且缓存有效，返回缓存数据
4. 如果`force_sync=true`或缓存过期，从远程项目库获取最新数据
5. 更新缓存并返回

### 3. 获取/保存项目同步配置

**接口**: `GET /api/config/project-sync`

**返回**:
```json
{
  "config": {
    "auto_sync_enabled": true,
    "sync_frequency": "*/15 * * * *",
    "cron_expression": "",
    "cache_ttl": 30,
    "sync_types": ["presale", "aftersales", "sales"],
    "notify_on_change": true,
    "notify_channels": ["wechat", "sms"]
  },
  "last_sync_time": "2024-02-02 15:30:00"
}
```

**接口**: `POST /api/config/project-sync`

**请求体**: 同上config对象

**返回**:
```json
{
  "success": true,
  "message": "配置已保存"
}
```

### 4. 手动触发同步

**接口**: `POST /api/projects/sync`

**请求体**:
```json
{
  "sync_type": "manual|auto",
  "force": true,
  "project_types": ["presale", "aftersales", "sales"]
}
```

**返回**:
```json
{
  "success": true,
  "total": 150,
  "updated": 12,
  "unchanged": 138,
  "sync_time": "2024-02-02 16:00:00",
  "duration": "5.6秒",
  "changes": [
    {
      "project_id": "P123",
      "old_status": "pending",
      "new_status": "processing",
      "notified": true
    }
  ]
}
```

**实现逻辑**:
1. 从远程项目库批量获取项目状态
2. 与缓存数据对比，找出变更
3. 更新缓存
4. 如果启用通知，对有变更的项目发送通知
5. 记录同步历史

### 5. 获取同步历史

**接口**: `GET /api/projects/sync-history`

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）

**返回**:
```json
{
  "history": [
    {
      "sync_time": "2024-02-02 15:30:00",
      "sync_type": "auto|manual",
      "total_projects": 150,
      "updated_count": 5,
      "duration": "2.3秒",
      "status": "success|failed",
      "message": "自动同步完成",
      "error_detail": null
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 6. 获取/保存时间显示配置

**接口**: `GET /api/config/time-display`

**返回**:
```json
{
  "aftersales_time_format": "YYYY-MM-DD HH:mm",
  "sales_time_format": "YYYY-MM-DD HH:mm",
  "show_payment_time": true,
  "timezone": "Asia/Shanghai"
}
```

**接口**: `POST /api/config/time-display`

**请求体**: 同上对象

## 数据库表设计

### 项目缓存表 (project_cache)

```sql
CREATE TABLE project_cache (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_type VARCHAR(20) NOT NULL,  -- presale|aftersales|sales
    data JSONB NOT NULL,  -- 项目完整数据
    remote_updated_at TIMESTAMP,  -- 远程数据更新时间
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 缓存时间
    expires_at TIMESTAMP,  -- 过期时间
    INDEX idx_project_id (project_id),
    INDEX idx_expires_at (expires_at)
);
```

### 同步历史表 (project_sync_history)

```sql
CREATE TABLE project_sync_history (
    id SERIAL PRIMARY KEY,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_type VARCHAR(10) NOT NULL,  -- auto|manual
    total_projects INT,
    updated_count INT,
    unchanged_count INT,
    duration FLOAT,  -- 秒
    status VARCHAR(20) DEFAULT 'success',  -- success|failed
    message TEXT,
    error_detail TEXT,
    changes JSONB,  -- 变更详情
    INDEX idx_sync_time (sync_time DESC)
);
```

### 项目同步配置表 (project_sync_config)

```sql
CREATE TABLE project_sync_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 访问令牌表 (project_access_tokens)

```sql
CREATE TABLE project_access_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    project_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    user_type VARCHAR(20),  -- customer|engineer|salesman
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_token (token),
    INDEX idx_project_id (project_id)
);
```

## 定时任务实现

### 使用APScheduler

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

async def sync_projects_task():
    """定时同步项目状态"""
    # 获取配置
    config = await get_project_sync_config()
    
    if not config.get('auto_sync_enabled'):
        return
    
    # 执行同步
    await sync_all_projects(sync_type='auto')

# 启动定时任务
def start_project_sync_scheduler():
    config = get_project_sync_config()
    cron_expr = config.get('sync_frequency', '*/15 * * * *')
    
    # 解析Cron表达式
    parts = cron_expr.split()
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1] if len(parts) > 1 else '*',
        day=parts[2] if len(parts) > 2 else '*',
        month=parts[3] if len(parts) > 3 else '*',
        day_of_week=parts[4] if len(parts) > 4 else '*'
    )
    
    scheduler.add_job(sync_projects_task, trigger, id='project_sync')
    scheduler.start()
```

## 远程项目库接口示例

假设远程项目库提供以下接口：

```python
import httpx

async def fetch_remote_project(project_id: str):
    """从远程项目库获取单个项目"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://remote-api.example.com/projects/{project_id}",
            headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
        )
        return response.json()

async def fetch_all_remote_projects(project_types: list):
    """批量获取所有项目"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://remote-api.example.com/projects",
            params={"types": ",".join(project_types)},
            headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
        )
        return response.json()
```

## 通知逻辑

当项目状态发生变更时：

1. 检查是否启用了`notify_on_change`
2. 根据项目类型和用户关系，获取需要通知的人员
3. 使用消息模板发送通知

```python
async def notify_project_change(project_id: str, old_status: str, new_status: str):
    """发送项目状态变更通知"""
    config = await get_project_sync_config()
    
    if not config.get('notify_on_change'):
        return
    
    # 获取项目和相关人员
    project = await get_project_from_cache(project_id)
    recipients = await get_project_stakeholders(project_id)
    
    # 生成通知内容
    message = f"您的{project['type']}项目【{project['title']}】状态已更新：{old_status} → {new_status}"
    
    # 发送通知
    for channel in config.get('notify_channels', []):
        if channel == 'wechat':
            await send_wechat_notification(recipients, message, project_id)
        elif channel == 'sms':
            await send_sms_notification(recipients, message)
        elif channel == 'email':
            await send_email_notification(recipients, message)
```

## 安全性

1. **Token加密**: 使用JWT生成访问令牌
2. **Token过期**: 设置合理的过期时间（如7天）
3. **HTTPS**: 所有API必须使用HTTPS
4. **权限验证**: 每次访问都验证token和用户权限
5. **日志记录**: 记录所有访问和操作日志

## 性能优化

1. **批量同步**: 一次性获取所有项目，而不是逐个请求
2. **异步处理**: 使用异步IO提高并发性能
3. **缓存策略**: 合理设置缓存过期时间
4. **增量更新**: 只更新有变化的项目
5. **数据库索引**: 为常用查询字段添加索引

## 错误处理

1. 远程API不可用时，返回缓存数据（即使过期）
2. 同步失败时，记录错误日志，不影响下次同步
3. Token过期时，提示用户重新获取链接
4. 访问被拒时，显示友好的错误页面
