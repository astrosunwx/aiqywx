# 启动消息消费者
# 用于处理RabbitMQ队列中的消息

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  启动消息消费者服务" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/3] 检查Python环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或未配置到PATH" -ForegroundColor Red
    exit 1
}

# 检查RabbitMQ连接
Write-Host "[2/3] 检查RabbitMQ连接..." -ForegroundColor Yellow
$rabbitmqUrl = "http://localhost:15672"
try {
    $response = Invoke-WebRequest -Uri $rabbitmqUrl -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ RabbitMQ连接正常" -ForegroundColor Green
} catch {
    Write-Host "❌ RabbitMQ未启动，请先启动RabbitMQ" -ForegroundColor Red
    Write-Host "   Windows: rabbitmq-server.bat" -ForegroundColor Yellow
    Write-Host "   Linux: sudo systemctl start rabbitmq-server" -ForegroundColor Yellow
    exit 1
}

# 启动消费者
Write-Host "[3/3] 启动消息消费者..." -ForegroundColor Yellow
Write-Host ""
Write-Host "消费者将监听以下队列:" -ForegroundColor Cyan
Write-Host "  - message.send (消息发送队列)" -ForegroundColor White
Write-Host "  - ai.process (AI处理队列)" -ForegroundColor White
Write-Host "  - notification (通知队列)" -ForegroundColor White
Write-Host "  - delayed (延迟消息队列)" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止消费者" -ForegroundColor Yellow
Write-Host ""

# 切换到backend目录
Set-Location -Path $PSScriptRoot

# 启动消费者
python -m app.services.message_consumer
