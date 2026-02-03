# Ngrok 快速安装和配置指南

## 📚 目录
1. [什么是Ngrok](#什么是ngrok)
2. [Windows安装步骤](#windows安装步骤)
3. [快速使用](#快速使用)
4. [故障排查](#故障排查)
5. [高级配置](#高级配置)

---

## 什么是Ngrok

**Ngrok** 是一个神奇的工具，它可以：

| 功能 | 说明 |
|-----|------|
| 🌐 **公网穿透** | 让本地项目可以通过公网URL访问 |
| 🔗 **动态域名** | 自动生成公网URL，无需购买域名 |
| 📱 **微信测试** | 在微信APP中测试本地开发的功能 |
| 🔒 **安全连接** | 提供HTTPS加密连接 |

**类比**：如果你的电脑是一个房间，Ngrok就像在房间外开了一个临时窗口，让外面的人能看到里面发生的事。

---

## Windows安装步骤

### 方法1：自动安装（推荐）

**下载**：https://bin.equinox.io/c/4VmDzA7iaHg/ngrok-stable-windows-amd64.zip

**解压**：
```
1. 下载后是一个 .zip 文件
2. 右键 → 解压全部
3. 得到一个文件夹，里面有 ngrok.exe
```

**配置环境变量**（让系统认识 ngrok）：

**第1步**：复制 ngrok.exe 的路径

假设你解压到：`C:\Users\YourName\Downloads\ngrok`

那么路径就是：`C:\Users\YourName\Downloads\ngrok`

**第2步**：添加到 Windows PATH

```
1️⃣ 按 Windows键 + X，选择"系统"

2️⃣ 点击"高级系统设置"（或在搜索框输入"环境变量"）

3️⃣ 点击"环境变量"按钮

4️⃣ 在"系统变量"中找到 Path，点击"编辑"

5️⃣ 点击"新建"，粘贴你的 ngrok 文件夹路径
   例如：C:\Users\YourName\Downloads\ngrok

6️⃣ 点击"确定"保存

7️⃣ 重启 PowerShell 或 CMD
```

**验证安装**：

打开 PowerShell，输入：
```powershell
ngrok --version
```

看到版本号就说明成功了！

```
例如输出：
ngrok version 3.3.4
```

---

### 方法2：使用 Chocolatey（高级用户）

如果你已经安装了 Chocolatey：

```powershell
choco install ngrok
```

然后验证：
```powershell
ngrok --version
```

---

## 快速使用

### 基本命令

**在本地运行你的项目**：
```powershell
# 前端（如果在3000端口）
npm run dev

# 后端（如果在8000端口）
python -m uvicorn app.main:app --reload
```

**启动 Ngrok 穿透**：

```powershell
ngrok http 3000
```

**输出**：
```
ngrok by @inconshreveable

Session Status    online
Session Expires   2024-XX-XX XX:XX:XX +0800 CST

Version           3.3.4
Region            CN (China)
Forwarding        http://a1b2c3d4e5f6g7h8.ngrok.io -> http://localhost:3000
Forwarding        https://a1b2c3d4e5f6g7h8.ngrok.io -> http://localhost:3000
```

**💡 关键部分**：
```
Forwarding        https://a1b2c3d4e5f6g7h8.ngrok.io -> http://localhost:3000
                  ↑ 这是你的公网URL，用这个！
```

---

### 实际使用流程

#### 场景：在微信中测试订单链接

**Step1: 启动 Ngrok**
```powershell
ngrok http 3000
```

**Step2: 复制公网URL**
```
https://a1b2c3d4e5f6g7h8.ngrok.io
```

**Step3: 配置到模板管理**

打开浏览器：`http://localhost:3000/templates`

在"⚙️ 域名配置 & 快速模板"面板中：
```
输入：https://a1b2c3d4e5f6g7h8.ngrok.io
点击：💾 保存域名配置
```

**Step4: 使用预设模板**

点击"📦 订单确认模板"，编辑后保存。

模板中的链接会自动变成：
```
https://a1b2c3d4e5f6g7h8.ngrok.io/project/123?type=sales
```

**Step5: 分享到微信**

```
1. 在模板列表中找到刚才创建的模板
2. 点击"预览"或复制链接
3. 分享到微信
4. 在微信中打开，测试功能
```

---

## 故障排查

### 问题1：ngrok 命令找不到

**症状**：
```powershell
> ngrok --version
ngrok : 无法将"ngrok"识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

**解决方案**：

```
1️⃣ 确认 ngrok.exe 已解压

2️⃣ 再次检查 PATH 配置
   - 按 Win + X → 系统 → 高级系统设置
   - 环境变量 → Path 中是否有 ngrok 路径

3️⃣ 重启 PowerShell（必须关闭后重新打开）

4️⃣ 再试一次：ngrok --version
```

### 问题2：Ngrok 无法访问

**症状**：
```
在浏览器中打开 https://a1b2c3d4.ngrok.io
得到错误：无法访问
```

**解决方案**：

```
1️⃣ 确认你的项目在运行
   - 前端：npm run dev 已执行
   - 后端：python app 已运行

2️⃣ 确认 Ngrok 正在运行
   - PowerShell 窗口还开着吗？
   - 显示 "Session Status    online" ？

3️⃣ 检查本地访问
   - 先试试：http://localhost:3000
   - 如果本地也访问不了，问题不在 ngrok

4️⃣ 等待几秒
   - 第一次连接可能较慢
   - 刷新浏览器重试
```

### 问题3：Ngrok URL 24小时后失效

**症状**：
```
今天的 URL：https://a1b2c3d4.ngrok.io
明天的 URL：https://x9y8z7w6.ngrok.io （变了！）
```

**解决方案**：

#### 方案A：获取稳定URL（需要注册账号）

**第1步**：注册 Ngrok 账号
```
打开：https://dashboard.ngrok.com/signup
使用 Google/GitHub 账号快速注册
```

**第2步**：获取 AuthToken
```
登录后，复制你的 Auth Token
```

**第3步**：配置 AuthToken
```powershell
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

例如：
```powershell
ngrok config add-authtoken 2X2c0qf_5h0Sn7F8Z9aB7D2E6F9a_abc123
```

**第4步**：创建固定 URL（需要付费）

```
1️⃣ 登录 https://dashboard.ngrok.com
2️⃣ 点击"Reserve a domain"
3️⃣ 设置你的二级域名，例如：myapp.ngrok.io
4️⃣ 完成！（付费后 URL 永久固定）
```

然后启动时指定这个 URL：
```powershell
ngrok http 3000 --domain=myapp.ngrok.io
```

#### 方案B：配置脚本自动更新（高级）

创建 PowerShell 脚本：`update_domain.ps1`

```powershell
# 每次 ngrok 启动时自动更新域名配置
while ($true) {
    # 获取当前 ngrok URL（通过 API）
    $ngrokUrl = Invoke-WebRequest http://localhost:4040/api/tunnels | ConvertFrom-Json
    $publicUrl = $ngrokUrl.tunnels[0].public_url
    
    # 保存到本地文件
    Set-Content -Path "ngrok_url.txt" -Value $publicUrl
    
    Start-Sleep -Seconds 60
}
```

#### 方案C：购买自己的域名（最稳定）

```
成本：50-100 元/年
好处：永久固定，专业形象
步骤：
  1. 在阿里云/腾讯云购买域名
  2. 配置 DNS 指向你的服务器
  3. 绑定 SSL 证书
```

---

## 高级配置

### 配置1：配置文件方式

创建 `~/.ngrok2/ngrok.yml`：

```yaml
authtoken: YOUR_AUTH_TOKEN
region: cn
web_addr: 127.0.0.1:4040
tunnels:
  frontend:
    proto: http
    addr: 3000
  backend:
    proto: http
    addr: 8000
```

然后启动：
```powershell
ngrok start --all
```

同时穿透多个端口！

### 配置2：监控 Ngrok 状态

Ngrok 提供了一个 Web 界面，可以查看流量：

```
打开：http://localhost:4040
可以看到：
- 所有的 HTTP 请求
- 请求详情
- 响应内容
- 用于调试 API
```

### 配置3：保持连接不中断

默认 Ngrok 连接可能会断，添加此参数：

```powershell
ngrok http 3000 --region=cn --log=stdout
```

参数说明：
```
--region=cn     指定中国服务器（更稳定）
--log=stdout    输出详细日志（便于调试）
```

---

## 📊 常用命令速查表

| 命令 | 说明 |
|------|------|
| `ngrok --version` | 查看版本 |
| `ngrok http 3000` | 穿透 3000 端口 |
| `ngrok http -auth=user:password 3000` | 添加密码保护 |
| `ngrok http 3000 --region=cn` | 使用中国服务器 |
| `ngrok http 3000 --domain=myapp.ngrok.io` | 使用固定域名 |
| `ngrok start --all` | 启动配置文件中的所有隧道 |
| `ngrok config add-authtoken TOKEN` | 添加认证令牌 |

---

## 🎯 完整示例：从安装到使用

```
💻 打开 PowerShell

# Step 1: 验证 ngrok 已安装
> ngrok --version
ngrok version 3.3.4

# Step 2: 启动 Ngrok 穿透
> ngrok http 3000

# 输出：
# Session Status    online
# Forwarding        https://a1b2c3d4.ngrok.io -> http://localhost:3000

# Step 3: 在另一个 PowerShell 中打开浏览器
> start https://a1b2c3d4.ngrok.io

# Step 4: 看到你的项目了！
```

---

## 🔐 安全建议

**Ngrok 是公网URL，注意安全**：

```
✅ 推荐做法
- 在模板中使用 HTTPS（自动）
- 测试环境不放敏感数据
- 及时关闭不需要的穿透

❌ 不推荐做法
- 把敏感密钥放在返回的HTML中
- 长期使用免费版本的不稳定URL
- 把生产数据库连接信息暴露
```

---

## 📞 需要帮助？

| 问题 | 链接 |
|------|------|
| 官方文档 | https://ngrok.com/docs |
| 状态页面 | https://ngrok.statuspage.io |
| GitHub 讨论 | https://github.com/ngrok/ngrok |

---

## 🎉 现在开始

1. 下载 ngrok
2. 解压并配置 PATH
3. 运行 `ngrok http 3000`
4. 复制公网 URL
5. 在模板管理中配置域名
6. 创建模板，分享链接
7. 在微信测试！

**就这么简单！** 🚀
