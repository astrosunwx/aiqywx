# 快速启动前端服务

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  启动前端服务" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$frontendPath = Join-Path $PSScriptRoot "customer-system\customer-system\frontend"

# 检查路径
if (-not (Test-Path $frontendPath)) {
    Write-Host "❌ 错误：找不到frontend目录" -ForegroundColor Red
    Write-Host "   路径: $frontendPath" -ForegroundColor Yellow
    exit 1
}

# 切换到frontend目录
Set-Location $frontendPath

# 检查Node.js
Write-Host "[1/3] 检查Node.js环境..." -ForegroundColor Yellow
node --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Node.js未安装或未配置到PATH" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "[2/3] 检查依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "⚠️  依赖未安装，正在安装..." -ForegroundColor Yellow
    npm install
}

# 启动服务
Write-Host "[3/3] 启动服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "前端服务将在以下地址启动:" -ForegroundColor Cyan
Write-Host "  • 主界面: http://localhost:5173" -ForegroundColor White
Write-Host "  • 监控大屏: http://localhost:5173/monitor" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

npm run dev
