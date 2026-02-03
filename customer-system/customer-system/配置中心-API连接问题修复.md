# 🔧 配置中心页面 - API连接问题修复

## 🐛 问题描述

访问 `http://localhost:3000/config` 时，所有API请求都失败，错误信息：
```
GET http://localhost:3000/api/admin/config/... - ERR_CONNECTION_REFUSED
```

## 🔍 问题原因

**API_BASE 配置错误**：
```javascript
// 错误配置
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 请求URL变成了：
// http://localhost:8000/api/admin/config/...
// 但浏览器实际发送到了 localhost:3000
```

**根本原因**：
- 开发环境应该使用**空字符串**作为 `API_BASE`
- 让Vite的代理配置处理API请求
- 代理会自动将 `/api/*` 转发到 `http://localhost:8000`

---

## ✅ 修复方案

### 1. 修改 ConfigCenter.vue

```javascript
// 修复前
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// 修复后
const API_BASE = import.meta.env.VITE_API_BASE || ''
```

### 2. 创建环境变量文件

**`.env.development`**（开发环境）：
```bash
# API基础URL（开发环境留空，使用Vite代理）
VITE_API_BASE=
```

**`.env.production`**（生产环境）：
```bash
# API基础URL（生产环境使用完整URL）
VITE_API_BASE=https://your-production-domain.com
```

### 3. Vite代理配置（vite.config.js）

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 🚀 如何使用

### 开发环境
1. **确保后端运行**：
   ```powershell
   cd G:\aiqywx\customer-system\customer-system\backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **启动前端**：
   ```powershell
   cd G:\aiqywx\customer-system\customer-system\frontend
   npm run dev
   ```

3. **请求流程**：
   ```
   浏览器请求：/api/admin/config/overview
   ↓
   Vite代理：localhost:3000/api/...
   ↓
   转发到：localhost:8000/api/...
   ↓
   后端处理并返回
   ```

### 生产环境
1. **构建前端**：
   ```powershell
   npm run build
   ```

2. **请求流程**：
   ```
   浏览器请求：/api/admin/config/overview
   ↓
   拼接API_BASE：https://your-domain.com/api/...
   ↓
   直接请求生产环境后端
   ```

---

## 🔍 验证步骤

### 1. 重启前端开发服务器

**重要**：必须重启才能加载新的环境变量！

```powershell
# 在运行 npm run dev 的终端中按 Ctrl+C 停止
# 然后重新启动
npm run dev
```

### 2. 清除浏览器缓存

**硬刷新**：`Ctrl + Shift + R`

### 3. 访问配置中心

打开：`http://localhost:3000/config`

### 4. 检查控制台

**期望结果**：
- ✅ 无 `ERR_CONNECTION_REFUSED` 错误
- ✅ 看到 `GET /api/admin/config-center/overview 200 OK`
- ✅ 页面正常显示配置数据

### 5. 检查Network标签

**正确的请求URL**：
```
Request URL: http://localhost:3000/api/admin/config-center/overview
(由Vite代理到 http://localhost:8000/api/admin/config-center/overview)
```

**错误的请求URL**（修复前）：
```
Request URL: http://localhost:3000/api/admin/config-center/overview
但没有代理，直接请求 localhost:3000，导致失败
```

---

## 📊 其他可能受影响的页面

检查其他Vue组件是否也使用了 `API_BASE`：

```powershell
cd G:\aiqywx\customer-system\customer-system\frontend
# 搜索所有使用 API_BASE 的文件
findstr /s /i "API_BASE" src\views\*.vue
```

如果发现其他文件也有同样的问题，需要统一修复。

---

## 🎯 最佳实践

### 统一API请求配置

**创建 `src/utils/request.js`**：
```javascript
import axios from 'axios'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API请求失败:', error)
    return Promise.reject(error)
  }
)

export default request
```

**使用方式**：
```javascript
// 在组件中
import request from '@/utils/request'

// 发送请求
const response = await request.get('/api/admin/config-center/overview')
```

---

## ✅ 修复清单

| 问题 | 状态 | 说明 |
|------|------|------|
| API_BASE配置错误 | ✅ 已修复 | 改为空字符串 |
| 缺少环境变量文件 | ✅ 已创建 | .env.development |
| 生产环境配置 | ✅ 已创建 | .env.production |
| Vite代理配置 | ✅ 已确认 | 正确配置 |

---

## 🚨 重要提醒

### 必须重启前端服务器！

环境变量的修改**只有在重启后才会生效**！

```powershell
# 1. 停止当前的 npm run dev（Ctrl+C）
# 2. 重新启动
npm run dev
```

### 必须清除浏览器缓存！

```
Ctrl + Shift + R（硬刷新）
或者
F12 → Network → 勾选 "Disable cache"
```

---

## 📞 如果还有问题

1. **检查后端是否运行**：
   ```powershell
   netstat -ano | findstr :8000
   ```

2. **检查Network标签**：
   - 请求的URL是什么？
   - 状态码是什么？
   - 响应内容是什么？

3. **检查Console标签**：
   - 是否有其他JavaScript错误？
   - 是否有CORS错误？

---

**现在请重启前端服务器，然后告诉我结果！** 🚀
