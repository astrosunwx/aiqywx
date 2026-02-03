@echo off
cd /d G:\aiqywx\customer-system\customer-system\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
pause
