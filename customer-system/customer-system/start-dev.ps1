Write-Host "Starting All Services..." -ForegroundColor Green
$rootDir = Get-Location
Start-Process powershell -ArgumentList "-NoExit", "-File", "$rootDir\start-backend.ps1"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-File", "$rootDir\start-frontend.ps1"
Write-Host "Done! Backend: http://localhost:8000/docs | Frontend: http://localhost:3000" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
