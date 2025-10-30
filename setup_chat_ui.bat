@echo off
chcp 65001 >nul
echo ========================================
echo   TopMat Agent - ChatGPT 风格界面安装
echo ========================================
echo.

cd frontend

echo [1/3] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Node.js，请先安装 Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo ✓ Node.js 环境正常
echo.

echo [2/3] 安装前端依赖（包含 marked）...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖安装完成
echo.

echo [3/3] 安装完成！
echo.
echo ========================================
echo   接下来的步骤:
echo ========================================
echo 1. 启动后端服务: python run.py (选择选项3)
echo 2. 启动前端界面: start_vue.bat
echo 3. 访问 http://localhost:5173
echo ========================================
echo.
pause
