#!/usr/bin/env bash
# E2E 测试运行脚本
# 自动启动前端服务并运行 Playwright 测试

echo "=== CRM 系统 E2E 测试 ==="
echo ""

# 检查后端是否运行
echo "Step 1: 检查后端服务..."
if curl -s http://localhost:8002/docs > /dev/null 2>&1; then
    echo "✓ 后端服务运行中 (http://localhost:8002)"
else
    echo "✗ 后端服务未运行，请先启动后端："
    echo "  cd backend"
    echo "  uvicorn app.main:app --reload --port 8002"
    exit 1
fi

# 启动前端服务
echo ""
echo "Step 2: 启动前端服务..."
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!
echo "前端服务启动中 (PID: $FRONTEND_PID)..."

# 等待前端服务启动
echo "等待前端服务就绪..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✓ 前端服务已启动 (http://localhost:5173)"
        break
    fi
    sleep 1
done

# 检查前端是否正常
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✗ 前端服务启动失败"
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

# 运行 Playwright 测试
echo ""
echo "Step 3: 运行 Playwright 测试..."
npm run test:e2e -- "$@"
TEST_EXIT_CODE=$?

# 清理：关闭前端服务
echo ""
echo "Step 4: 清理..."
kill $FRONTEND_PID 2>/dev/null
echo "✓ 前端服务已停止"

# 输出测试结果
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=== 测试通过 ==="
else
    echo ""
    echo "=== 测试失败 ==="
    echo "查看测试报告：npx playwright show-report"
fi

exit $TEST_EXIT_CODE
