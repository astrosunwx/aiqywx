Write-Host "Backend Starting..." -ForegroundColor Green
Set-Location backend
if (-not (Test-Path "venv")) { python -m venv venv }
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip -q
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic httpx -i https://pypi.tuna.tsinghua.edu.cn/simple -q
$env:DATABASE_URL = "sqlite+aiosqlite:///./customer_system.db"
python -c "import asyncio; from app.database import engine, Base; from app import models; asyncio.run(engine.begin().__aenter__().run_sync(Base.metadata.create_all))" 2>$null
Write-Host "Backend running on http://localhost:8000/docs" -ForegroundColor Cyan
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
