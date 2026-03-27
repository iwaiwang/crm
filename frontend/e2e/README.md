# E2E 自动化测试

本目录包含 CRM 系统的 Playwright E2E 自动化测试。

## 测试范围

### 发票管理模块 (`e2e/invoice.spec.ts`)
- 发票列表页面显示
- 创建发票（包含购买方/销售方信息）
- **编辑发票时购买方/销售方信息显示验证**
- 更新发票并持久化购买方/销售方信息
- 删除发票

### Bug 修复验证 (`e2e/invoice-buyer-seller.spec.ts`)
- 专项测试：验证发票保存后，编辑时购买方/销售方信息是否正确显示

## 环境要求

- Node.js 16+
- 后端服务运行在 `http://localhost:8002`

## 安装

```bash
# 安装依赖
npm install

# 安装 Playwright 浏览器
npx playwright install
```

## 运行测试

### 方式 1：直接运行（需要手动启动前端）

```bash
# 1. 启动前端服务
npm run dev

# 2. 在另一个终端运行测试
npm run test:e2e
```

### 方式 2：使用脚本自动运行

```bash
# Linux/macOS
bash run-e2e-tests.sh

# Windows PowerShell
.\run-e2e-tests.ps1
```

### 运行特定测试

```bash
# 运行发票管理模块测试
npx playwright test e2e/invoice.spec.ts

# 运行 Bug 修复验证测试
npx playwright test e2e/invoice-buyer-seller.spec.ts

# 运行单个测试用例
npx playwright test e2e/invoice.spec.ts -g "should show buyer and seller info when editing invoice"
```

### 调试模式

```bash
# 开启调试模式（会打开浏览器并慢速执行）
npx playwright test --debug

# 或使用 UI 模式
npx playwright test --ui
```

### 查看测试报告

```bash
npx playwright show-report
```

## 测试配置

配置文件：`playwright.config.ts`

```typescript
{
  testDir: './e2e',
  baseURL: 'http://localhost:5173',  // 前端开发服务器
  retries: 0,                         // 失败重试次数
  workers: 1,                         // 并行工作线程数
}
```

## 测试用例说明

### `invoice.spec.ts`

| 测试用例 | 说明 |
|---------|------|
| `should display invoice list page` | 验证发票列表页面正常显示 |
| `should create invoice with buyer and seller info` | 创建包含购买方/销售方信息的发票 |
| `should show buyer and seller info when editing invoice` | **关键测试**：验证编辑时购买方/销售方信息显示 |
| `should update invoice and persist buyer/seller info` | 验证更新后信息持久化 |
| `should delete invoice` | 验证删除功能 |

### `invoice-buyer-seller.spec.ts`

专项 Bug 修复验证测试，包含详细的日志输出，用于验证"购买方/销售方信息保存"问题是否修复。

## CI/CD

测试已集成到 GitHub Actions，每次 push 和 PR 时自动运行。

配置文件：`.github/workflows/e2e-tests.yml`

## 常见问题

### Q: 测试失败 "Timeout waiting for selector"
A: 确保前端和后端服务都已启动，并且可以正常访问。

### Q: 登录失败
A: 检查后端服务是否运行在 `http://localhost:8002`，数据库是否正常初始化。

### Q: 如何添加新的测试用例？
A: 在 `e2e/` 目录下创建新的 `.spec.ts` 文件，参考现有测试用例的格式。

## 最佳实践

1. **测试数据隔离**：每个测试用例使用唯一标识（如时间戳）创建数据，避免相互干扰
2. **清晰的断言**：使用有意义的期望值和实际值输出
3. **详细日志**：使用 `console.log` 记录关键步骤，便于调试
4. **等待策略**：使用 `waitForSelector` 而不是固定 `sleep`
5. **清理资源**：测试完成后清理创建的测试数据
