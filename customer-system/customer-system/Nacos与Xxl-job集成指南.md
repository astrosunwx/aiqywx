# Nacos + Xxl-job 集成指南

## 📋 概述

本文档介绍如何将 **Nacos动态配置中心** 和 **Xxl-job分布式任务调度** 集成到消息处理系统中。

---

## 🔧 Nacos集成

### 1. 安装Nacos

#### Docker方式（推荐）
```bash
docker run -d \
  --name nacos \
  -e MODE=standalone \
  -p 8848:8848 \
  -p 9848:9848 \
  nacos/nacos-server:latest
```

#### 下载安装包方式
```bash
# 下载Nacos 2.x
wget https://github.com/alibaba/nacos/releases/download/2.2.0/nacos-server-2.2.0.zip

# 解压
unzip nacos-server-2.2.0.zip

# 启动（单机模式）
cd nacos/bin
# Windows
startup.cmd -m standalone
# Linux/Mac
sh startup.sh -m standalone
```

### 2. 访问Nacos控制台

浏览器访问：http://localhost:8848/nacos

**默认账号**：
- 用户名：nacos
- 密码：nacos

### 3. 配置示例

#### 3.1 消息处理配置
在Nacos控制台创建配置：

**Data ID**: `message-config.json`  
**Group**: `DEFAULT_GROUP`  
**配置格式**: `JSON`

```json
{
  "thread_pool": {
    "message_sender": {
      "core_pool_size": 20,
      "max_pool_size": 100,
      "scale_up_threshold": 0.8,
      "scale_down_threshold": 0.2
    },
    "ai_processor": {
      "core_pool_size": 10,
      "max_pool_size": 50,
      "scale_up_threshold": 0.8,
      "scale_down_threshold": 0.2
    }
  },
  "rate_limit": {
    "api_send_message": {
      "qps": 1000,
      "concurrent": 500
    },
    "api_send_batch": {
      "qps": 100,
      "concurrent": 200
    }
  },
  "retry": {
    "max_retry_count": 3,
    "retry_interval_seconds": 60
  },
  "features": {
    "enable_ai_routing": true,
    "enable_chain_trace": true,
    "enable_rate_limit": true
  }
}
```

#### 3.2 AI配置
**Data ID**: `ai-config.json`

```json
{
  "response_style": "professional",
  "max_context_messages": 10,
  "timeout_seconds": 30,
  "fallback_enabled": true,
  "models": {
    "primary": "gpt-4",
    "fallback": "gpt-3.5-turbo"
  }
}
```

### 4. 在代码中使用Nacos

#### 4.1 初始化Nacos客户端
```python
# backend/app/config.py
from app.services.nacos_config_service import NacosConfigService, DynamicConfig

# 初始化Nacos
nacos = NacosConfigService(
    server_addresses="localhost:8848",
    namespace="public",
    username="nacos",
    password="nacos"
)

# 创建动态配置管理器
dynamic_config = DynamicConfig(nacos)

# 注册消息配置
dynamic_config.register_config(
    "message",
    "message-config.json",
    on_update=on_message_config_update
)

# 注册AI配置
dynamic_config.register_config(
    "ai",
    "ai-config.json",
    on_update=on_ai_config_update
)

def on_message_config_update(config):
    """消息配置更新回调"""
    print(f"消息配置已更新: {config}")
    
    # 更新线程池配置
    thread_pool_config = config.get('thread_pool', {})
    # TODO: 动态调整线程池参数

def on_ai_config_update(config):
    """AI配置更新回调"""
    print(f"AI配置已更新: {config}")
    
    # 更新AI配置
    ai_config = config
    # TODO: 动态调整AI参数
```

#### 4.2 使用配置
```python
# 在业务代码中获取配置
from app.config import dynamic_config

# 获取QPS限制
qps_limit = dynamic_config.get("message", {}).get("rate_limit", {}).get("api_send_message", {}).get("qps", 1000)

# 获取AI模型
ai_model = dynamic_config.get("ai", {}).get("models", {}).get("primary", "gpt-4")
```

---

## ⏰ Xxl-job集成

### 1. 安装Xxl-job

#### Docker方式（推荐）
```bash
docker run -d \
  --name xxl-job-admin \
  -p 8080:8080 \
  -e PARAMS="--spring.datasource.url=jdbc:mysql://host.docker.internal:3306/xxl_job?useUnicode=true&characterEncoding=UTF-8&autoReconnect=true&serverTimezone=Asia/Shanghai \
  --spring.datasource.username=root \
  --spring.datasource.password=your_password" \
  xuxueli/xxl-job-admin:2.4.0
```

#### 源码部署方式
```bash
# 下载源码
git clone https://github.com/xuxueli/xxl-job.git
cd xxl-job

# 初始化数据库
# 执行 doc/db/tables_xxl_job.sql

# 修改配置
# xxl-job-admin/src/main/resources/application.properties
# 配置数据库连接

# 编译打包
mvn clean package -DskipTests

# 启动
java -jar xxl-job-admin/target/xxl-job-admin-2.4.0.jar
```

### 2. 访问Xxl-job控制台

浏览器访问：http://localhost:8080/xxl-job-admin

**默认账号**：
- 用户名：admin
- 密码：123456

### 3. 配置执行器

在Xxl-job控制台：

**执行器管理 → 新增执行器**
- AppName: `customer-system-executor`
- 名称: `客户系统执行器`
- 注册方式: `自动注册`
- 机器地址: 自动

### 4. 创建定时任务

#### 任务1：更新消息统计
- 执行器: `customer-system-executor`
- 任务描述: `每天凌晨1点更新消息统计`
- 路由策略: `第一个`
- Cron: `0 0 1 * * ?`
- 运行模式: `BEAN`
- JobHandler: `updateMessageStatistics`
- 阻塞处理策略: `单机串行`
- 任务超时时间: `300`

#### 任务2：发送每日报告
- 执行器: `customer-system-executor`
- 任务描述: `每天早上9点发送报告`
- Cron: `0 0 9 * * ?`
- JobHandler: `sendDailyReport`

#### 任务3：清理过期数据
- 执行器: `customer-system-executor`
- 任务描述: `每天凌晨3点清理30天前的数据`
- Cron: `0 0 3 * * ?`
- JobHandler: `cleanExpiredData`

#### 任务4：重试失败消息
- 执行器: `customer-system-executor`
- 任务描述: `每小时重试失败的消息`
- Cron: `0 0 * * * ?`
- JobHandler: `retryFailedMessages`

### 5. 启动执行器

```bash
# 在单独的终端启动
cd backend
python -m app.services.xxljob_service
```

### 6. Cron表达式参考

| 表达式 | 说明 |
|--------|------|
| `0 0 1 * * ?` | 每天凌晨1点 |
| `0 0 9 * * ?` | 每天早上9点 |
| `0 0 * * * ?` | 每小时执行一次 |
| `0 */30 * * * ?` | 每30分钟执行一次 |
| `0 0 12 * * ?` | 每天中午12点 |
| `0 0 0 1 * ?` | 每月1号凌晨 |

---

## 🚀 完整启动流程

### 1. 启动基础服务
```bash
# PostgreSQL
# Windows: services.msc 启动PostgreSQL服务
# Linux: sudo systemctl start postgresql

# Redis
redis-server

# RabbitMQ
# Windows: rabbitmq-server.bat
# Linux: sudo systemctl start rabbitmq-server

# Nacos（可选）
# Docker: docker start nacos
# 原生: cd nacos/bin && startup.cmd -m standalone

# Xxl-job（可选）
# Docker: docker start xxl-job-admin
# 原生: java -jar xxl-job-admin.jar
```

### 2. 启动应用服务
```powershell
# 使用启动脚本（推荐）
.\start-all.ps1

# 或手动启动各服务
# Terminal 1: 后端
cd backend
uvicorn app.main:app --reload

# Terminal 2: 前端
cd frontend
npm run dev

# Terminal 3: 消息消费者
cd backend
python -m app.services.message_consumer

# Terminal 4: Xxl-job执行器（可选）
cd backend
python -m app.services.xxljob_service
```

### 3. 验证服务

访问以下地址检查服务状态：
- ✅ 前端: http://localhost:5173
- ✅ 监控大屏: http://localhost:5173/monitor
- ✅ API文档: http://localhost:8000/docs
- ✅ RabbitMQ: http://localhost:15672
- ✅ Nacos: http://localhost:8848/nacos
- ✅ Xxl-job: http://localhost:8080/xxl-job-admin

---

## 🎯 配置热更新示例

### 场景1：调整线程池大小

1. 打开Nacos控制台
2. 找到 `message-config.json`
3. 修改配置：
```json
{
  "thread_pool": {
    "message_sender": {
      "core_pool_size": 30,  // 从20改为30
      "max_pool_size": 150   // 从100改为150
    }
  }
}
```
4. 点击"发布"
5. **无需重启，配置立即生效！**

### 场景2：调整限流规则

促销活动期间提高QPS：
```json
{
  "rate_limit": {
    "api_send_message": {
      "qps": 2000,      // 从1000提高到2000
      "concurrent": 1000 // 从500提高到1000
    }
  }
}
```

活动结束后恢复：
```json
{
  "rate_limit": {
    "api_send_message": {
      "qps": 1000,
      "concurrent": 500
    }
  }
}
```

### 场景3：切换AI模型

```json
{
  "models": {
    "primary": "gpt-3.5-turbo",  // 从gpt-4降级
    "fallback": "gpt-3.5-turbo"
  }
}
```

---

## 📊 监控与告警

### Nacos监控
- 配置监听数: 查看"监听查询"
- 配置版本历史: 查看"历史版本"
- 配置对比: 对比不同版本差异

### Xxl-job监控
- 任务执行情况: 查看"调度日志"
- 执行成功率: 查看"任务统计"
- 执行耗时: 查看"执行明细"

---

## 🔧 故障排查

### Nacos连接失败
```bash
# 检查Nacos是否启动
curl http://localhost:8848/nacos/

# 检查网络
ping localhost

# 检查防火墙
# Windows: netsh advfirewall show allprofiles
```

### Xxl-job执行器注册失败
```bash
# 检查执行器配置
# app/services/xxljob_service.py
# admin_addresses是否正确

# 检查网络连通性
curl http://localhost:8080/xxl-job-admin/

# 查看执行器日志
```

### 配置不生效
```python
# 检查配置监听是否添加
dynamic_config.register_config(...)

# 检查回调函数是否执行
def on_config_update(config):
    print(f"配置更新: {config}")  # 添加日志
```

---

## 📝 最佳实践

### 1. 配置分组
```
├── DEFAULT_GROUP
│   ├── message-config.json (消息配置)
│   ├── ai-config.json (AI配置)
├── PROD_GROUP (生产环境)
│   ├── message-config.json
├── DEV_GROUP (开发环境)
│   ├── message-config.json
```

### 2. 配置版本管理
- 每次修改配置前，先查看历史版本
- 重大变更前做好回滚准备
- 在Nacos中添加配置描述

### 3. 定时任务监控
- 设置任务超时告警
- 定期检查任务执行日志
- 失败任务及时处理

---

## 🎉 集成完成

现在您的系统具备：
- ✅ 动态配置（Nacos）
- ✅ 定时任务（Xxl-job）
- ✅ 消息队列（RabbitMQ）
- ✅ 链路追踪（Redis）
- ✅ 限流保护（Sentinel）
- ✅ 可视化监控（ECharts）

**完整的企业级高并发消息处理系统！** 🚀
