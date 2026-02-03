# Quick Start - Just run this script
# Dependencies are already installed

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Starting Services..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$backendPath = "G:\aiqywx\customer-system\customer-system\backend"
$frontendPath = "G:\aiqywx\customer-system\customer-system\frontend"

# Start Backend
Write-Host "[1/2] Starting Backend on port 8000..." -ForegroundColor Green
$backendScript = @"
Set-Location '$backendPath'
.\venv\Scripts\Activate.ps1
Write-Host "Backend starting..." -ForegroundColor Cyan
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "[2/2] Starting Frontend on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev"

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Services Started!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Please wait 10-15 seconds for services to initialize..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Then visit:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Check the 2 PowerShell windows for startup logs" -ForegroundColor Gray
Write-Host ""
