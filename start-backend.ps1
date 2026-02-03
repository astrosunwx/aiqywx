# 快速启动后端服务

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  启动后端服务" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$backendPath = Join-Path $PSScriptRoot "customer-system\customer-system\backend"

# 检查路径
if (-not (Test-Path $backendPath)) {
    Write-Host "❌ 错误：找不到backend目录" -ForegroundColor Red
    Write-Host "   路径: $backendPath" -ForegroundColor Yellow
    exit 1
}

# 切换到backend目录
Set-Location $backendPath

# 检查Python
Write-Host "[1/3] 检查Python环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或未配置到PATH" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "[2/3] 检查依赖..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "[3/3] 启动服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "后端服务将在 http://localhost:8000 启动" -ForegroundColor Cyan
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 启动服务
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}

uvicorn app.main:app --reload --port 8000
