# 完整系统启动脚本
# 按顺序启动所有服务

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  客户系统 - 完整启动" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = $PSScriptRoot

# 检查基础服务
Write-Host "[检查] 基础服务状态..." -ForegroundColor Yellow

# 检查PostgreSQL
Write-Host "  PostgreSQL..." -NoNewline
try {
    $pgResult = psql -U postgres -c "SELECT 1" 2>&1
    Write-Host " ✅" -ForegroundColor Green
} catch {
    Write-Host " ❌ 未启动" -ForegroundColor Red
    exit 1
}

# 检查Redis
Write-Host "  Redis..." -NoNewline
try {
    $redisResult = redis-cli ping 2>&1
    if ($redisResult -eq "PONG") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌ 未启动" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host " ❌ 未安装" -ForegroundColor Red
    exit 1
}

# 检查RabbitMQ
Write-Host "  RabbitMQ..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:15672" -TimeoutSec 3 -ErrorAction Stop
    Write-Host " ✅" -ForegroundColor Green
} catch {
    Write-Host " ❌ 未启动" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[启动] 正在启动所有服务..." -ForegroundColor Yellow
Write-Host ""

# 启动后端
Write-Host "1️⃣ 启动后端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptPath\start-backend.ps1"
Start-Sleep -Seconds 3

# 启动前端
Write-Host "2️⃣ 启动前端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptPath\start-frontend.ps1"
Start-Sleep -Seconds 2

# 启动消息消费者
Write-Host "3️⃣ 启动消息消费者..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptPath\start-consumer.ps1"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  ✅ 所有服务已启动" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 访问地址:" -ForegroundColor Cyan
Write-Host "  • 前端界面: http://localhost:5173" -ForegroundColor White
Write-Host "  • 监控大屏: http://localhost:5173/monitor" -ForegroundColor White
Write-Host "  • API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • RabbitMQ管理: http://localhost:15672" -ForegroundColor White
Write-Host ""
Write-Host "📊 系统组件:" -ForegroundColor Cyan
Write-Host "  • FastAPI后端: http://localhost:8000" -ForegroundColor White
Write-Host "  • Vue3前端: http://localhost:5173" -ForegroundColor White
Write-Host "  • 消息消费者: 运行中" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "  • 关闭任意PowerShell窗口即可停止对应服务" -ForegroundColor Gray
Write-Host "  • 查看各窗口的日志输出了解服务状态" -ForegroundColor Gray
Write-Host ""
