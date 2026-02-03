# 智能售前售后系统

基于企业微信和微信公众号的双入口智能客户服务系统 + 高并发消息处理平台

## 🚀 快速启动

### 方式一：一键启动（推荐）

```powershell
# 在项目根目录执行
.\start-all.ps1
```

### 方式二：分别启动

```powershell
# 启动后端
.\start-backend.ps1

# 启动前端（新开窗口）
.\start-frontend.ps1
```

## 📍 访问地址

启动后访问：
- 🌐 **前端界面**: http://localhost:5173
- 📊 **监控大屏**: http://localhost:5173/monitor  
- 📖 **API文档**: http://localhost:8000/docs

## ⚠️ 前置要求

请确保已安装：
- ✅ PostgreSQL 12+
- ✅ Redis 6+
- ✅ Python 3.9+
- ✅ Node.js 16+
- ⚙️ RabbitMQ 3.8+（消息队列功能需要）

### 数据源驱动（可选）

系统支持多数据源管理，根据需要安装对应驱动：

**测试阶段（当前）**
- ✅ MySQL: `aiomysql`（已安装）
- ✅ PostgreSQL: `asyncpg`（已安装）
- ⏸️ SQL Server: 暂时不需要

**生产环境（如需对接 SQL Server）**
```powershell
# 仅在需要连接 SQL Server 时安装
pip install pyodbc
```

> 💡 **说明**: 
> - 测试阶段可先用 MySQL/PostgreSQL 测试数据源管理功能
> - SQL Server 选项已保留在界面，需要时再安装 pyodbc
> - 确保已安装 ODBC Driver 17 for SQL Server

## 📚 详细文档

完整文档位于 `customer-system/customer-system/` 目录：

- **[快速启动指南](customer-system/customer-system/消息系统-快速启动指南.md)** - 5分钟部署
- **[完整实施方案](customer-system/customer-system/高并发消息处理系统-完整实施方案.md)** - 技术架构
- **[项目总览](customer-system/customer-system/项目完成总览.md)** - 功能清单
- **[README](customer-system/customer-system/README.md)** - 项目详细说明

## 🔧 常见问题

### 1. 后端启动失败
```powershell
# 检查PostgreSQL是否启动
psql -U postgres -c "SELECT 1"

# 检查Redis是否启动
redis-cli ping
```

### 2. 前端无法访问
```powershell
# 等待10-15秒，前端需要编译
# 查看前端窗口的日志输出
```

### 3. API返回错误
```powershell
# 检查数据库是否初始化
psql -U postgres -d customer_system -f customer-system/customer-system/backend/init.sql
```

## 📞 获取帮助

遇到问题？
1. 查看各PowerShell窗口的日志输出
2. 访问 http://localhost:8000/docs 检查API状态
3. 查看详细文档

---

cd "g:\aiqywx\customer-system\customer-system\frontend"; npm run dev
==========


**版本**: v2.0.0  
**更新时间**: 2026-02-02
