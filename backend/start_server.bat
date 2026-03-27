@echo off
chcp 65001 >nul
echo.
echo ================================
echo   CRM 后端服务启动
echo ================================
echo.

echo [1/2] 检查并清理端口 8002...
REM 先检查端口是否被占用
netstat -ano | findstr ":8002" >nul 2>&1
if %errorlevel% equ 0 (
    echo [信息] 检测到端口 8002 被占用，正在杀掉旧进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002"') do (
        echo [信息] 杀掉进程 %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 1 >nul
    echo [OK] 端口已清理
) else (
    echo [OK] 端口 8002 空闲
)

echo [2/2] 启动后端服务...
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

echo.
echo [OK] 启动后端服务...
echo.
echo 后端 API: http://localhost:8002
echo API 文档：http://localhost:8002/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
