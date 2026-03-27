# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

小微企业 CRM 系统 - 客户、合同、发票、应收款、产品库存、项目进度、收支管理

## 技术栈

**后端 (backend/)**
- FastAPI 0.109 + Python 3.11+
- SQLAlchemy 2.0 + AsyncSession (aiosqlite)
- Pydantic 2.5
- JWT 认证 (python-jose + bcrypt)
- SQLite 数据库

**前端 (frontend/)**
- Vue 3 + Vite 5
- Element Plus UI
- Vue Router + Pinia
- Axios

## 开发命令

### 启动开发环境
```bash
# 推荐方式：使用启动脚本（自动处理端口占用）
cd crm-system
start.bat  # Windows
```

### 手动启动
```bash
# 后端（端口 8002）
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8002

# 前端（端口 5173）
cd frontend
npm run dev
```

### 测试后端 API
```bash
cd backend
.\venv\Scripts\python.exe -c "
import http.client, json
conn = http.client.HTTPConnection('127.0.0.1', 8002)
conn.request('GET', '/docs')
print(conn.getresponse().status)
"
```

### 访问服务
- 前端：http://localhost:5173
- 后端 API 文档：http://localhost:8002/docs
- 默认账号：admin / admin123

## 架构结构

### 后端目录结构
```
backend/app/
├── main.py          # FastAPI 应用入口，路由注册
├── config.py        # 配置管理 (Settings)
├── database.py      # 数据库连接、Session 工厂
├── models/          # SQLAlchemy 模型定义
│   ├── customer.py  # 客户
│   ├── contract.py  # 合同
│   ├── invoice.py   # 发票
│   └── ...
├── schemas/         # Pydantic 请求/响应 Schema
│   ├── customer.py
│   ├── contract.py
│   └── ...
└── api/             # API 路由
    ├── customers.py
    ├── contracts.py
    ├── invoices.py
    └── ...
```

### 前端目录结构
```
frontend/src/
├── App.vue
├── router/index.js     # 路由配置 + 权限守卫
├── store/              # Pinia 状态管理
│   └── user.js         # 用户信息、token
├── api/                # API 调用封装
│   ├── request.js      # Axios 实例 + 拦截器
│   ├── customer.js
│   ├── contract.js
│   └── ...
├── views/              # 页面组件
│   ├── Dashboard.vue
│   ├── Customers.vue
│   ├── Contracts.vue
│   └── ...
└── components/         # 公共组件
    └── DocumentUploader.vue  # 文件上传+AI 解析
```

### 数据流
1. 前端通过 Axios 实例 (`api/request.js`) 发送请求，自动携带 JWT token
2. 后端 JWT 依赖 (`api/auth.py` 中的 `get_current_user`) 验证 token
3. API 路由使用 `async Session` 执行数据库操作
4. 返回数据通过 Pydantic Schema 验证和序列化

### 关键模块
- **认证**: `backend/app/api/auth.py` - JWT token 签发和验证
- **数据库**: `backend/app/database.py` - AsyncSession 管理
- **API 路由**: 各模块在 `backend/app/api/` 下定义，统一在 `main.py` 注册
- **前端请求**: `frontend/src/api/request.js` - 统一处理 token、错误、参数过滤

## 端口管理

**固定端口，禁止随意更改：**
| 服务 | 端口 | 配置文件 |
|------|------|----------|
| 前端 (Vite) | 5173 | `frontend/vite.config.js` |
| 后端 (FastAPI) | 8002 | 启动命令 |

每次启动后端前，必须先用 `netstat -ano | findstr ":8002"` 检查端口占用，如有占用需先杀掉旧进程。

## 新增 API 开发顺序

1. 在 `backend/app/models/` 定义或修改模型
2. 在 `backend/app/schemas/` 定义 Pydantic Schema
3. 在 `backend/app/api/` 实现路由逻辑
4. 用 Python/http.client 测试 API（验证返回格式）
5. 在 Swagger /docs 确认端点已注册
6. 最后对接前端

## 数据库迁移

SQLite 不支持直接修改表结构。添加字段时：
- 新增列：`ALTER TABLE table_name ADD COLUMN column_name TYPE DEFAULT value`
- 修改约束：需要重建表

修改模型后记得手动更新数据库表结构。

## 已知问题与修复记录

### 合同页面无法输入
- **问题**: `Contracts.vue` 中新增按钮直接设置 `formData = {}` 破坏响应性
- **修复**: 使用 `Object.assign(formData, {...})` 重置表单

### 合同创建 422 错误
- **问题**: 前端空字符串 `''` 无法被 Pydantic 解析为日期
- **修复**: 提交前将空字符串转换为 `null`

### 发票列表 500 错误
- **问题**: 数据库缺少 `invoice_type` 列
- **修复**: 执行 `ALTER TABLE invoices ADD COLUMN invoice_type VARCHAR(20) DEFAULT 'sales'`

## 调试排查顺序

遇到前端报错时按此顺序排查：
1. 确认后端是否运行：`Invoke-WebRequest http://localhost:8002/docs`
2. 用 PowerShell 直接测试出问题的 API
3. 检查 `vite.config.js` 的 proxy 端口是否是 8002
4. 检查前端请求 URL path 是否和后端路由一致
5. 才开始看前端代码逻辑

## 规则引用

项目级 bug 修复流程参考 `.claude/rules/bugfix.md`：
1. 复述 bug 现象
2. 定位相关文件、函数、调用链
3. 给出 1~3 个根因
4. 先做最小修复，不要顺手重构
5. 修改后运行最小验证
6. 输出：根因、修改点、验证结果、剩余风险
