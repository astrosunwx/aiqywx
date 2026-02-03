Write-Host "Frontend Starting..." -ForegroundColor Green
Set-Location frontend
if (-not (Test-Path "node_modules")) { npm install }
Write-Host "Frontend running on http://localhost:3000" -ForegroundColor Cyan
npm run dev
