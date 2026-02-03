# Simple Startup Script - Skip dependency checks
# Start all services directly

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Starting All Services" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = $PSScriptRoot
$projectPath = Join-Path $rootPath "customer-system\customer-system"
$backendPath = Join-Path $projectPath "backend"
$frontendPath = Join-Path $projectPath "frontend"

# Check paths
if (-not (Test-Path $projectPath)) {
    Write-Host "[ERROR] Project directory not found: $projectPath" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Project path: $projectPath" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "[1/2] Starting backend (port 8000)..." -ForegroundColor Cyan
$backendCmd = "cd '$backendPath'; if (Test-Path '.\venv\Scripts\Activate.ps1') { .\venv\Scripts\Activate.ps1 }; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Sleep -Seconds 2

# Start frontend  
Write-Host "[2/2] Starting frontend (port 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Services Started Successfully" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  (Or check the frontend window for actual port)" -ForegroundColor Gray
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Note:" -ForegroundColor Yellow
Write-Host "  Backend needs 5-10 seconds to initialize" -ForegroundColor Gray
Write-Host "  Frontend needs 10-15 seconds to compile" -ForegroundColor Gray
Write-Host "  Check the opened PowerShell windows for logs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C or close this window to exit" -ForegroundColor Yellow
Write-Host ""

# Keep window open
Read-Host "Press Enter to close this window"
