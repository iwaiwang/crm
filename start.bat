@echo off
chcp 65001 >nul

echo.
echo ================================
echo   小微企业 CRM 系统 - 启动脚本
echo ================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto no_python

node --version >nul 2>&1
if errorlevel 1 goto no_node

echo [1/4] 检查并清理端口 8002...
netstat -ano | findstr ":8002" >nul 2>&1
if errorlevel 1 goto port_free

echo [信息] 检测到端口 8002 被占用，正在杀掉旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002"') do (
    echo [信息] 杀掉进程 %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 >nul
echo [OK] 端口已清理
goto backend

:port_free
echo [OK] 端口 8002 空闲

:backend
echo [2/4] 启动后端服务...
cd /d "%~dp0backend"

if not exist "venv" (
    echo [信息] 创建 Python 虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist ".env" (
    echo [信息] 创建环境配置文件...
    copy .env.example .env
)

echo [信息] 安装 Python 依赖...
pip install -r requirements.txt -q

start "CRM Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8002"

echo [3/4] 启动前端服务...
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [信息] 安装 Node.js 依赖...
    call npm install
)

start "CRM Frontend" cmd /k "npm run dev"

echo.
echo ================================
echo   服务启动中...
echo ================================
echo.
echo 后端 API: http://localhost:8002
echo API 文档：http://localhost:8002/docs
echo 前端页面：http://localhost:5173
echo.
echo 默认账号: admin / admin123
echo.
echo 按任意键退出此窗口...
pause >nul
exit /b 0

:no_python
echo [错误] 未找到 Python，请先安装 Python 3.11+
pause
exit /b 1

:no_node
echo [错误] 未找到 Node.js，请先安装 Node.js 18+
pause
exit /b 1