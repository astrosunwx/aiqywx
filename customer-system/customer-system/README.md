# 智能售前售后系统 + 高并发消息处理平台

基于企业微信和微信公众号的双入口智能客户服务系统，集成企业级高并发消息处理能力。

## ✨ 核心特性

### 🎯 客户服务系统
- **双入口统一处理**: 微信公众号 + 企业微信
- **AI智能路由**: 自动识别客户意图并分配处理
- **全流程管理**: 售前咨询 → 售中跟进 → 售后服务
- **权限精细化**: 客户/员工/管理员三级权限
- **智能工单系统**: 自动派单、进度跟踪、评价反馈

### ⚡ 高并发消息处理（新增）
- **动态线程池**: 10-100线程自动伸缩，应对高峰流量
- **RabbitMQ消息队列**: 4个优先级队列，支持延迟消息
- **Redis链路追踪**: 7天完整追踪，实时性能监控
- **Sentinel限流**: QPS限流 + 并发限流 + 滑动窗口
- **Redisson分布式锁**: 防止重复处理，保证数据一致性
- **ECharts可视化**: 实时监控大屏，4个图表展示
- **Nacos动态配置**: 配置热更新，无需重启
- **Xxl-job定时任务**: 统计、清理、重试自动化

## 🛠️ 技术栈

### 后端核心
- **框架**: Python 3.9+ + FastAPI 0.128.0
- **数据库**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 + AsyncPG
- **缓存**: Redis 6+
- **消息队列**: RabbitMQ 3.8+ (新增)
- **分布式锁**: Redisson (新增)
- **限流**: Sentinel (新增)
- **配置中心**: Nacos (可选)
- **任务调度**: Xxl-job (可选)

### 前端技术
- **框架**: Vue 3 + Vite
- **UI库**: Element Plus
- **可视化**: ECharts 5.5.0 (新增)
- **HTTP**: Axios

### 微信集成
- **企业微信SDK**: 客户联系、群聊管理
- **微信公众号SDK**: 消息推送、模板消息

### DevOps
- Docker + Docker Compose
- PostgreSQL + Redis + RabbitMQ

## 📋 核心功能

### 1. 客户服务系统
#### 双入口统一处理
- **客户入口一**: 微信公众号（AI智能问答）
- **客户入口二**: 企业微信（员工主动添加客户）
- 两个入口共享相同的项目状态、权限规则和业务流程

#### 企业微信员工功能
- **售前流程**: 快捷命令创建售前项目（`#记录客户`）
- **售中/售后流程**: 查询项目进度（`#查询进度`）
- **内部协作**: 转接工程师（`#转接工程师`）、问题解决（`#问题已解决`）

#### 权限与绑定管理
- 公众号绑定：客户提供手机号验证
- 企业微信绑定：员工添加客户后自动匹配
- 权限控制：客户仅看自己项目，员工仅看绑定客户项目，管理员全部可见

### 2. 高并发消息处理系统（新增）
#### 消息模板管理
- 支持5种渠道：SMS、Email、APP、微信、飞书
- 模板变量支持：`{{order_no}}`、`{{customer_name}}` 等
- 模板状态管理：active/inactive

#### 批量发送
- 单次最多10000条消息
- 优先级队列（0-10级）
- 进度实时跟踪

#### 链路追踪
- 4个追踪节点：queue → process → send → callback
- Redis存储，7天保留
- 实时性能统计

#### 可视化监控
- **4个实时数据卡片**: 发送总数、成功率、响应时间、失败数
- **发送趋势折线图**: 7天数据对比
- **渠道分布饼图**: 各渠道占比
- **成功率柱状图**: 渠道对比
- **线程池仪表盘**: 实时使用率

#### 动态配置（Nacos）
- 线程池参数热更新
- 限流规则动态调整
- AI策略实时切换
- 无需重启生效

#### 定时任务（Xxl-job）
- 每日统计汇总
- 自动发送报告
- 过期数据清理
- 失败消息重试

## 项目结构

```
customer-system/
├── backend/                  # 后端应用
│   ├── app/
│   │   ├── main.py          # FastAPI主程序
│   │   ├── models.py        # 数据模型
│   │   ├── database.py      # 数据库连接
│  🚀 快速开始

### 方式一：一键启动（推荐）

```powershell
# Windows PowerShell
.\start-all.ps1
```

这将自动启动：
- ✅ FastAPI后端服务（端口8000）
- ✅ Vue3前端服务（端口5173）
- ✅ RabbitMQ消息消费者

### 方式二：Docker部署

```bash
docker-compose up -d
```

### 方式三：手动启动

#### 1. 启动基础服务
```bash
# PostgreSQL（确保已启动）
# Redis
redis-server

# RabbitMQ
rabbitmq-server
```

#### 2. 初始化数据库
```bash
# 执行所有迁移脚本
psql -U postgres -d customer_system -f backend/init.sql
psql -U postgres -d customer_system -f backend/after_sales_extension.sql
psql -U postgres -d customer_system -f backend/equipment_extension.sql
psql -U postgres -d customer_system -f backend/messaging_extension.sql
```

#### 3. 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
```

#### 5. 启动消息消费者
```bash
cd backend
python -m app.services.message_consumer
```

### 📍 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 前端界面 | http://localhost:5173 | Vue3主界面 |
| 📊 监控大屏 | http://localhost:5173/monitor | ECharts可视化 |
| 📖 API文档 | http://localhost:8000/docs | Swagger UI |
| 🐰 RabbitMQ | http://localhost:15672 | 队列管理（guest/guest） |
| 🔧 Nacos | http://localhost:8848/nacos | 配置中心（可选） |
| ⏰ Xxl-job | http://localhost:8080/xxl-job-admin | 任务调度（可选） |

---

## 📚 文档导航

### 快速入门
1. **[消息系统-快速启动指南](./消息系统-快速启动指南.md)** - 5分钟快速部署
2. **[本地开发指南](./本地开发指南.md)** - 开发环境配置

### 功能详解
3. **[高并发消息处理系统-完整实施方案](./高并发消息处理系统-完整实施方案.md)** - 技术架构详解
4. **[Nacos与Xxl-job集成指南](./Nacos与Xxl-job集成指南.md)** - 动态配置与定时任务
5. **[客户联系功能-完整配置指南](./客户联系功能-完整配置指南.md)** - 企业微信集成
6. **[智能工单交互系统-完整实现方案](./智能工单交互系统-完整实现方案.md)** - 工单系统

### 项目总结
7. **[消息系统-实施完成总结](./消息系统-实施完成总结.md)** - 项目交付清单
8. **[实施完成总结](./实施完成总结.md)** - 整体实施总结

---

## 🎯 核心API接口

### 消息处理
```http
# 发送单条消息
POST /api/messages/send
{
  "template_id": 1,
  "recipient": "13800138000",
  "variables": {"order_no": "202401010001"},
  "priority": 8
}

# 批量发送消息
POST /api/messages/send-batch
{
  "template_id": 2,
  "recipients": ["user1@example.com", "user2@example.com"],
  "priority": 5
}

# 获取消息追踪
GET /api/messages/traces/{trace_id}

# 获取统计概览
GET /api/messages/statistics/overview

# 获取实时统计
GET /api/messages/statistics/realtime
```

### 配置管理
```http
# 获取配置列表
GET /api/config/configs

# 创建配置
POST /api/config/configs

# 更新配置
PUT /api/config/configs/{id}
```

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   前端层（Vue 3）                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 客户界面 │  │ 配置中心 │  │ 监控大屏 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                       ↓↑ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                   API网关层（FastAPI）                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ AI路由   │  │ 消息API  │  │ 限流中间 │              │
│  └──────────┘  └──────────┘  │ 件       │              │
└─────────────────────────────────────────────────────────┘
         ↓              ↓              ↓
┌────────────┐  ┌──────────────┐  ┌──────────────┐
│ RabbitMQ   │  │ 动态线程池    │  │ Redis锁&追踪 │
│ 消息队列   │  │ 自动伸缩     │  │ 链路追踪     │
└────────────┘  └──────────────┘  └──────────────┘
         ↓              ↓              ↓
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL数据库                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 客户数据 │  │ 消息记录 │  │ 统计数据 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 配置说明

### 环境变量（.env）
```ini
# 数据库
DATABASE_URL=postgresql://postgres:password@localhost/customer_system

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# 企业微信
WEWORK_CORP_ID=your_corp_id
WEWORK_SECRET=your_secret

# JWT
SECRET_KEY=your-secret-key
```

### 性能参数
```python
# 线程池配置（可在Nacos中动态调整）
{
  "message_sender": {
    "core_pool_size": 20,
    "max_pool_size": 100,
    "scale_up_threshold": 0.8,
    "scale_down_threshold": 0.2
  }
}

# 限流配置
{
  "api_send_message": {
    "qps": 1000,
    "concurrent": 500
  }
}
```

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 单机QPS | 1000+ |
| 并发处理 | 500+ |
| 消息队列容量 | 10000+ |
| 线程池伸缩 | 10-100 |
| 平均响应时间 | <100ms |
| 成功率 | >99% |

---

## 🛠️ 运维工具

### 日志查看
```bash
# 后端日志
tail -f backend/logs/app.log

# 消费者日志
tail -f backend/logs/consumer.log

# Nacos日志
tail -f nacos/logs/nacos.log
```

### 监控命令
```bash
# 检查线程池状态
curl http://localhost:8000/api/messages/statistics/realtime

# 检查队列积压
rabbitmqctl list_queues

# 检查Redis连接
redis-cli info clients
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 📞 技术支持

- 📖 查看[完整文档](./高并发消息处理系统-完整实施方案.md)
- 🔍 访问[监控大屏](http://localhost:5173/monitor)
- 💬 提交[Issue](https://github.com/your-repo/issues)

---

**版本**: v2.0.0  
**更新时间**: 2026-02-02  
**开发团队**: AI智能助手
│   │   │   ├── Dashboard.vue
│   │   │   └── Reports.vue
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── router.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml       # Docker编排
└── README.md
```

## 数据库设计

### 核心表
1. **customers** - 客户信息表
2. **projects** - 项目管理表（售前/售中/售后统一管理）
3. **wechat_sessions** - 微信会话表
4. **system_config** - 系统配置表

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd customer-system
```

### 2. 启动服务
```bash
docker-compose up -d
```

### 3. 访问应用
- **前端**: http://localhost
- **后端API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432
- **Redis**: localhost:6379

## API接口

### 智能路由
- `POST /api/ai/router` - 统一处理公众号和企业微信消息

### 企业微信
- `POST /api/wechat/work/command` - 处理快捷命令
- `POST /api/wechat/work-message` - 接收企业微信消息
- `GET /api/wechat/sidebar-data` - 侧边栏应用数据
- `POST /api/wechat/group-bot-notify` - 内部群机器人推送

### 管理后台
- `GET /api/admin/config` - 获取系统配置
- `POST /api/admin/config` - 更新系统配置
- `GET /api/admin/reports/sales` - 销售报表
- `GET /api/projects` - 查询项目列表

## 环境变量

```env
DATABASE_URL=postgresql+asyncpg://postgres:123456@postgres:5432/customer_system
REDIS_URL=redis://redis:6379/0
PORT=8000
```

## 开发指南

### 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## 生产部署

### 1. 配置环境变量
编辑 `docker-compose.yml` 中的环境变量，修改数据库密码等敏感信息。

### 2. 配置企业微信
- 创建企业微信自建应用
- 配置消息接收URL: `https://your-domain.com/api/wechat/work-message`
- 配置侧边栏应用URL: `https://your-domain.com/api/wechat/sidebar-data`

### 3. 启动服务
```bash
docker-compose up -d
```

## 贡献指南

欢迎提交Issue和Pull Request。

## 许可证

MIT License

## 联系方式

如有问题，请联系项目维护者。
