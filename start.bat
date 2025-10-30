@echo off
chcp 65001 >nul
title TopMat Agent - 涂层优化专家系统

echo ╔══════════════════════════════════════════╗
echo ║     TopMat Agent - 涂层优化专家系统      ║
echo ╚══════════════════════════════════════════╝
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查环境文件
if not exist .env (
    echo [提示] 未找到.env文件，正在从模板创建...
    copy .env.example .env >nul 2>&1
    echo [警告] 请编辑.env文件，填入阿里云百炼API密钥
    notepad .env
    pause
)

REM 检查依赖是否安装
pip show langgraph >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo.
echo 请选择运行模式:
echo 1. 完整模式 (Streamlit + FastAPI)
echo 2. 仅Streamlit前端
echo 3. 仅FastAPI后端
echo 4. 演示模式
echo 5. 运行测试
echo 6. 退出
echo.

set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" (
    echo.
    echo 正在启动完整模式...
    start cmd /k "title FastAPI服务 && python -c \"from src.api.main import *; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\""
    timeout /t 3 /nobreak >nul
    start cmd /k "title Streamlit前端 && streamlit run streamlit_app.py"
    echo.
    echo 服务已启动:
    echo - Streamlit UI: http://localhost:8501
    echo - FastAPI Docs: http://localhost:8000/docs
    echo.
    echo 按任意键退出...
    pause >nul
) else if "%choice%"=="2" (
    echo.
    echo 正在启动Streamlit前端...
    streamlit run streamlit_app.py
) else if "%choice%"=="3" (
    echo.
    echo 正在启动FastAPI后端...
    python -c "from src.api.main import *; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)"
) else if "%choice%"=="4" (
    echo.
    echo 正在运行演示模式...
    python run.py demo
    pause
) else if "%choice%"=="5" (
    echo.
    echo 正在运行测试...
    pytest tests/ -v
    pause
) else if "%choice%"=="6" (
    echo 再见!
    exit /b 0
) else (
    echo 无效的选项!
    pause
    exit /b 1
)
