# Smart Customer Service System - One-Click Startup Script
# Start all services from root directory

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Smart Customer Service System - Startup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = $PSScriptRoot
$projectPath = Join-Path $rootPath "customer-system\customer-system"

# Check if project directory exists
if (-not (Test-Path $projectPath)) {
    Write-Host "[ERROR] Project directory not found" -ForegroundColor Red
    Write-Host "   Path: $projectPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "[CHECK] Project directory: $projectPath" -ForegroundColor Green
Write-Host ""

# Check basic services
Write-Host "[CHECK] Checking service status..." -ForegroundColor Yellow

# Check PostgreSQL
Write-Host "  PostgreSQL..." -NoNewline
try {
    $pgResult = & psql -U postgres -c "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [NOT RUNNING]" -ForegroundColor Red
        Write-Host "   Please start PostgreSQL service first" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host " [NOT INSTALLED]" -ForegroundColor Red
    Write-Host "   Please install PostgreSQL first" -ForegroundColor Yellow
    exit 1
}

# Check Redis
Write-Host "  Redis..." -NoNewline
try {
    $redisResult = & redis-cli ping 2>&1
    if ($redisResult -eq "PONG") {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [NOT RUNNING]" -ForegroundColor Red
        Write-Host "   Please run: redis-server" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host " [NOT INSTALLED]" -ForegroundColor Red
    Write-Host "   Please install Redis first" -ForegroundColor Yellow
    exit 1
}

# Check RabbitMQ (optional)
Write-Host "  RabbitMQ..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:15672" -TimeoutSec 3 -ErrorAction Stop
    Write-Host " [OK]" -ForegroundColor Green
} catch {
    Write-Host " [OPTIONAL - Not running]" -ForegroundColor Yellow
    Write-Host "   For message queue features, run: rabbitmq-server" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[START] Starting all services..." -ForegroundColor Yellow
Write-Host ""

# Switch to project directory
Set-Location $projectPath

# Start backend
Write-Host "1. Starting backend service..." -ForegroundColor Cyan
$backendPath = Join-Path $projectPath "backend"
if (Test-Path (Join-Path $backendPath "start-backend.ps1")) {
    Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $backendPath "start-backend.ps1")
    Start-Sleep -Seconds 3
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; uvicorn app.main:app --reload --port 8000"
    Start-Sleep -Seconds 3
}

# Start frontend
Write-Host "2. Starting frontend service..." -ForegroundColor Cyan
$frontendPath = Join-Path $projectPath "frontend"
if (Test-Path (Join-Path $frontendPath "start-frontend.ps1")) {
    Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $frontendPath "start-frontend.ps1")
    Start-Sleep -Seconds 2
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
    Start-Sleep -Seconds 2
}

# Start message consumer (optional)
$consumerScript = Join-Path $projectPath "start-consumer.ps1"
if (Test-Path $consumerScript) {
    Write-Host "3. Starting message consumer..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-File", $consumerScript
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  All services started" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "  Monitor:   http://localhost:5173/monitor" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  Backend needs 3-5 seconds to start" -ForegroundColor Gray
Write-Host "  Frontend needs 5-10 seconds to start" -ForegroundColor Gray
Write-Host "  Check PowerShell windows for logs if services fail" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  Close the corresponding PowerShell windows" -ForegroundColor Gray
Write-Host ""

# Wait and verify
Write-Host "Waiting 10 seconds to verify services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "[VERIFY] Checking service status..." -ForegroundColor Yellow

# Check backend
Write-Host "  Backend API..." -NoNewline
try {
    $apiResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [RUNNING]" -ForegroundColor Green
} catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "   Check backend window for errors" -ForegroundColor Yellow
}

# Check frontend
Write-Host "  Frontend..." -NoNewline
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [RUNNING]" -ForegroundColor Green
} catch {
    Write-Host " [STARTING...]" -ForegroundColor Yellow
    Write-Host "   Frontend needs 10-15 seconds, please wait" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Startup complete! Visit URLs above in your browser" -ForegroundColor Green
Write-Host ""
