# E2E 测试运行脚本 (PowerShell)
# 自动启动前端服务并运行 Playwright 测试

Write-Host "=== CRM 系统 E2E 测试 ===" -ForegroundColor Cyan
Write-Host ""

# 检查后端是否运行
Write-Host "Step 1: 检查后端服务..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/docs" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ 后端服务运行中 (http://localhost:8002)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 后端服务未运行" -ForegroundColor Red
    Write-Host "  请先启动后端服务：" -ForegroundColor Yellow
    Write-Host "    cd backend" -ForegroundColor Gray
    Write-Host "    uvicorn app.main:app --reload --port 8002" -ForegroundColor Gray
    exit 1
}

# 启动前端服务
Write-Host ""
Write-Host "Step 2: 启动前端服务..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$PSScriptRoot"
    npm run dev
}
Write-Host "  前端服务启动中 (PID: $($frontendJob.Id))..." -ForegroundColor Gray

# 等待前端服务启动
Write-Host "  等待前端服务就绪..." -ForegroundColor Gray
$maxAttempts = 30
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✓ 前端服务已启动 (http://localhost:5173)" -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

# 检查前端是否正常
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
} catch {
    Write-Host "  ✗ 前端服务启动失败" -ForegroundColor Red
    Stop-Job -Job $frontendJob
    Remove-Job -Job $frontendJob
    exit 1
}

# 运行 Playwright 测试
Write-Host ""
Write-Host "Step 3: 运行 Playwright 测试..." -ForegroundColor Yellow

# 解析命令行参数
$testArgs = $args
if ($testArgs.Count -eq 0) {
    # 默认运行所有测试
    npm run test:e2e
    $testExitCode = $LASTEXITCODE
} else {
    # 运行指定测试
    npm run test:e2e -- $testArgs
    $testExitCode = $LASTEXITCODE
}

# 清理：关闭前端服务
Write-Host ""
Write-Host "Step 4: 清理..." -ForegroundColor Yellow
Stop-Job -Job $frontendJob
Remove-Job -Job $frontendJob
Write-Host "  ✓ 前端服务已停止" -ForegroundColor Green

# 输出测试结果
Write-Host ""
if ($testExitCode -eq 0) {
    Write-Host "=== 测试通过 ===" -ForegroundColor Green
} else {
    Write-Host "=== 测试失败 ===" -ForegroundColor Red
    Write-Host "查看测试报告：npx playwright show-report" -ForegroundColor Yellow
}

exit $testExitCode
