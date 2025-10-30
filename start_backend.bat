@echo off
REM 启动FastAPI后端服务
echo Starting TopMat Agent Backend...
echo.

cd /d "%~dp0"
call conda activate Agent
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

pause
