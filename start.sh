#!/bin/bash

echo "================================"
echo "  小微企业 CRM 系统 - 启动脚本"
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js"
    exit 1
fi

echo "[1/4] 启动后端服务..."
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "[信息] 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f ".env" ]; then
    echo "[信息] 创建环境配置文件..."
    cp .env.example .env
fi

echo "[信息] 安装 Python 依赖..."
pip install -r requirements.txt -q

uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 &
BACKEND_PID=$!

echo "[2/4] 启动前端服务..."
cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "[信息] 安装 Node.js 依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "================================"
echo "  服务已启动"
echo "================================"
echo ""
echo "后端 API: http://localhost:8000"
echo "API 文档：http://localhost:8000/docs"
echo "前端页面：http://localhost:5173"
echo ""
echo "默认账号：admin / admin123"
echo ""
echo "按 Ctrl+C 停止服务"

wait
