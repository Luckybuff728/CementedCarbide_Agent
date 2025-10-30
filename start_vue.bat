@echo off
chcp 65001 >nul
title TopMat Agent - Vue 3 前端启动

echo ╔══════════════════════════════════════════╗
echo ║  TopMat Agent - Vue 3 现代化前端         ║
echo ╚══════════════════════════════════════════╝
echo.

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js 16+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查环境文件
if not exist .env (
    echo [警告] 未找到.env文件
    copy .env.example .env >nul 2>&1
    echo 请编辑.env文件，填入阿里云百炼API密钥
    notepad .env
)

REM 检查Python依赖
echo.
echo [1/4] 检查Python依赖...
pip show langgraph >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装Python依赖...
    pip install -r requirements.txt
)

REM 检查前端依赖
echo.
echo [2/4] 检查前端依赖...
if not exist frontend\node_modules (
    echo 正在安装前端依赖（首次运行需要几分钟）...
    cd frontend
    call npm install
    cd ..
)

REM 启动后端服务
echo.
echo [3/4] 启动FastAPI后端服务...
start "TopMat Backend" cmd /k "title TopMat Backend && echo 启动FastAPI后端... && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM 启动前端服务
echo.
echo [4/4] 启动Vue 3前端...
cd frontend
start "TopMat Frontend" cmd /k "title TopMat Frontend && echo 启动Vue 3前端... && npm run dev"
cd ..

echo.
echo ╔══════════════════════════════════════════╗
echo ║           服务启动完成！                  ║
echo ╚══════════════════════════════════════════╝
echo.
echo 📱 前端界面: http://localhost:3000
echo 📚 API文档:  http://localhost:8000/docs
echo.
echo 💡 提示:
echo   - 请等待前端编译完成（约10-30秒）
echo   - 浏览器将自动打开前端页面
echo   - 关闭此窗口将停止所有服务
echo.
echo 按任意键退出启动器...
pause >nul

REM 清理：关闭所有启动的窗口
taskkill /FI "WindowTitle eq TopMat Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq TopMat Frontend*" /T /F >nul 2>&1
echo 服务已停止
