# Ngrok 安装和配置指南

## 🚀 快速安装 (Windows)

### 方法1️⃣：直接下载（最简单）

**第1步：下载**
```
访问：https://ngrok.com/download

选择Windows版本（64位）
```

**第2步：解压**
```
解压到某个文件夹，如：
C:\ngrok\

这样你会得到：C:\ngrok\ngrok.exe
```

**第3步：添加到系统PATH（重要！）**

```
Windows 10/11:

1. 右键"此电脑" → 属性
2. 点击"高级系统设置"
3. 点击"环境变量"
4. 在"系统变量"中找"Path"，点"编辑"
5. 点"新建"，输入：C:\ngrok
6. 点"确定"保存
7. 重启PowerShell或CMD
```

**第4步：验证安装**
```powershell
# 打开新的PowerShell窗口，输入：
ngrok --version

# 应该看到版本号，如：
# ngrok version 3.x.x
```

---

### 方法2️⃣：使用Chocolatey（自动化）

```powershell
# 1. 安装Chocolatey（如未安装）
# 访问：https://chocolatey.org/install

# 2. 使用Chocolatey安装ngrok
choco install ngrok

# 3. 验证
ngrok --version
```

---

### 方法3️⃣：通过npm安装

```powershell
# 如果已安装Node.js和npm
npm install -g ngrok

# 验证
ngrok --version
```

---

## 📝 Ngrok 快速使用

### 基础用法

```powershell
# 启动ngrok，将本地3000端口映射到公网
ngrok http 3000

# 输出示例：
# Session Status                online
# Account                       {your-account}
# Version                       3.3.0
# Region                        cn
# Forwarding                    https://xxxx-xxxx-xxxx.ngrok.io -> http://localhost:3000

# 复制这个URL：https://xxxx-xxxx-xxxx.ngrok.io
```

### 在模板中使用

```
原来的本地链接：
http://localhost:3000/project/{order_id}?type=presale

改为ngrok的公网链接：
https://xxxx-xxxx-xxxx.ngrok.io/project/{order_id}?type=presale

现在就可以在微信APP中打开了！
```

---

## 🔐 Ngrok 账号配置（可选）

### 为什么要配置账号？

- 提高URL稳定性（默认每8小时变化一次）
- 增加带宽限制
- 使用自定义域名

### 配置步骤

```powershell
# 1. 注册Ngrok账号
# 访问：https://dashboard.ngrok.com/signup

# 2. 获取认证令牌
# 登录后在 https://dashboard.ngrok.com/get-started/your-authtoken
# 复制你的auth token

# 3. 配置本地
ngrok config add-authtoken your_auth_token_here

# 4. 重新启动ngrok
ngrok http 3000

# 现在会看到你的账号信息
```

---

## 📋 完整的快速启动流程

```
1️⃣ 下载ngrok
   https://ngrok.com/download

2️⃣ 解压到 C:\ngrok\

3️⃣ 将 C:\ngrok 加入系统PATH

4️⃣ 重启PowerShell

5️⃣ 测试安装
   ngrok --version

6️⃣ 启动ngrok
   ngrok http 3000

7️⃣ 复制公网URL
   https://xxxx-xxxx-xxxx.ngrok.io

8️⃣ 在模板管理中使用该URL
```

---

## 🎯 当前的快速方案

**如果安装太麻烦，现在可以：**

### 使用本地开发（推荐）
```
1. 在桌面/手机浏览器测试（不需要ngrok）
   http://localhost:3000/project/{id}?type=presale

2. 在模板管理中配置预设域名
   (等我添加这个功能)

3. 后续需要在微信打开时再配置ngrok
```

### 直接在微信测试
```
1. 安装ngrok后
2. 运行：ngrok http 3000
3. 得到URL：https://xxxx.ngrok.io
4. 在模板中使用该URL发送到微信
5. 在微信APP中点击测试
```

---

## 🐛 常见问题

**Q: ngrok依然找不到？**
```
A: 
1. 检查ngrok.exe路径
   C:\ngrok\ngrok.exe
   
2. 重新添加PATH
   系统变量 → Path → 新建 → C:\ngrok
   
3. 重启PowerShell
   关闭所有PowerShell窗口，重新打开

4. 重试
   ngrok --version
```

**Q: ngrok启动了但不知道URL是什么？**
```
A: 看启动输出的"Forwarding"行：

Session Status                online
Forwarding    https://xxxx-xxxx-xxxx.ngrok.io -> http://localhost:3000
              ↑
              这就是你的公网URL
```

**Q: URL每次都不一样？**
```
A: 免费版ngrok每8小时更换一次URL
   
解决方案：
1. 注册ngrok账号（可固定URL）
2. 或在模板管理中配置自动替换功能
   (我正在为你添加这个功能)
```

**Q: 可以保持URL不变吗？**
```
A: 可以，但需要付费或配置：

免费方案：
- 使用自己的服务器 + 域名

付费方案：
- ngrok Pro ($5/月) → 自定义域名
```

---

## 💡 推荐方案

### 开发阶段（现在）
```
✅ 使用ngrok临时测试
   ngrok http 3000
   
✅ 在模板中手动替换URL
   每次ngrok URL变化时更新模板

⏳ 等我添加"域名配置"功能
   在模板管理中自动替换
```

### 生产部署（后续）
```
✅ 购买自己的域名（¥50/年）
✅ 配置服务器
✅ 申请HTTPS证书
✅ 使用固定域名
```

---

## 📞 需要帮助？

如果ngrok安装有问题：
1. 检查解压位置：`C:\ngrok\ngrok.exe` 是否存在
2. 检查PATH设置：右键运行cmd，输入 `echo %PATH%` 看是否包含ngrok
3. 重启PowerShell后重试

如果还是不行，可以：
- 直接在浏览器中用 `http://localhost:3000` 测试
- 我会为模板管理添加"预设域名配置"功能
- 这样你可以快速切换不同的基础URL

---

**现在就可以尝试安装ngrok！** 🚀

或者先在本地开发，我为你添加模板管理的域名配置功能。
