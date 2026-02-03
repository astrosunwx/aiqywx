# Install Dependencies and Start Services
# This script will install all required dependencies and start both backend and frontend

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Install & Start All Services" -ForegroundColor Cyan
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

# ==================== BACKEND SETUP ====================
Write-Host "[BACKEND] Setting up backend..." -ForegroundColor Yellow
Set-Location $backendPath

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to create virtual environment" -ForegroundColor Red
        Write-Host "  Please make sure Python is installed and in PATH" -ForegroundColor Yellow
        exit 1
    }
}

# Activate venv and install dependencies
Write-Host "  Installing backend dependencies..." -ForegroundColor Cyan
$installCmd = @"
cd '$backendPath'
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host 'Backend dependencies installed successfully!' -ForegroundColor Green
pause
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $installCmd -Wait

# ==================== FRONTEND SETUP ====================
Write-Host ""
Write-Host "[FRONTEND] Setting up frontend..." -ForegroundColor Yellow
Set-Location $frontendPath

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to install npm packages" -ForegroundColor Red
        Write-Host "  Please make sure Node.js and npm are installed" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  Checking for missing packages..." -ForegroundColor Cyan
    npm install
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Now starting services..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# ==================== START SERVICES ====================

# Start backend
Write-Host ""
Write-Host "[1/2] Starting backend (port 8000)..." -ForegroundColor Cyan
$backendCmd = "cd '$backendPath'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Sleep -Seconds 3

# Start frontend  
Write-Host "[2/2] Starting frontend (port 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  All Services Started!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Monitor:   http://localhost:3000/monitor" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Note:" -ForegroundColor Yellow
Write-Host "  Backend needs 5-10 seconds to start" -ForegroundColor Gray
Write-Host "  Frontend needs 10-15 seconds to compile" -ForegroundColor Gray
Write-Host "  Check the PowerShell windows for logs" -ForegroundColor Gray
Write-Host ""
Write-Host "Waiting 15 seconds to verify services..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Verify services
Write-Host ""
Write-Host "[VERIFY] Checking services..." -ForegroundColor Yellow

# Check backend
Write-Host "  Backend (port 8000)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [OK]" -ForegroundColor Green
} catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "    Check backend window for errors" -ForegroundColor Yellow
}

# Check frontend
Write-Host "  Frontend (port 3000)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [OK]" -ForegroundColor Green
} catch {
    Write-Host " [STARTING...]" -ForegroundColor Yellow
    Write-Host "    Wait a bit longer and refresh browser" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Setup complete! You can now use the system." -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to close this window..." -ForegroundColor Gray
Read-Host
