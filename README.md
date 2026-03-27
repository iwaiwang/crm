# 小微企业 CRM 系统

面向小微企业的客户管理系统，支持客户管理、合同管理、发票管理、应收款管理、产品库存管理和项目进度管理。

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT

### 前端
- **框架**: Vue 3
- **UI 组件**: Element Plus
- **图表**: ECharts
- **构建工具**: Vite

## 功能模块

- **客户管理**: 客户信息、分类、状态、搜索筛选
- **合同管理**: 合同 CRUD、文件上传、状态跟踪
- **发票管理**: 发票记录、状态跟踪、关联合同
- **应收款管理**: 应收/实收登记、账龄分析、逾期提醒
- **产品库存**: 产品 CRUD、出入库管理、库存预警
- **项目进度**: 销售跟进、投标管理、实施计划、任务管理
- **数据分析**: 仪表盘统计图表
- **系统管理**: 用户认证、角色权限、操作日志

## 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问：
- 前端：http://localhost
- 后端 API: http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 默认账号

```
用户名：admin
密码：admin123
```

首次使用时请修改默认密码！

## 项目结构

```
crm-system/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic 模式
│   │   ├── services/     # 业务逻辑
│   │   ├── utils/        # 工具函数
│   │   ├── config.py     # 配置管理
│   │   ├── database.py   # 数据库连接
│   │   └── main.py       # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面
│   │   ├── router/       # 路由
│   │   ├── store/        # 状态管理
│   │   └── main.js       # 入口文件
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API 集成

### OpenClaw Webhook

系统提供 Webhook 接口接收 OpenClaw 推送的合同和发票数据：

```bash
POST /api/webhooks/contract
Content-Type: application/json
X-API-Key: your-api-key

{
  "source": "openclaw",
  "data": {
    "customer_name": "客户公司名称",
    "customer_contact": "联系人",
    "customer_phone": "联系电话",
    "contract_name": "合同名称",
    "contract_amount": 100000,
    "contract_date": "2026-03-22",
    "invoice_needed": true,
    "invoice_amount": 100000
  }
}
```

## 配置说明

编辑 `backend/.env` 文件：

```env
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/crm.db

# JWT 认证（生产环境务必修改）
SECRET_KEY=your-secret-key-change-in-production

# Webhook API Key
WEBHOOK_API_KEY=your-webhook-api-key
```

## 开发计划

- [x] UI 设计确认
- [x] 基础架构搭建
- [x] 客户管理模块
- [x] 合同管理模块
- [x] 发票管理模块
- [x] 应收款管理模块
- [x] 产品库存模块
- [x] 项目进度模块
- [x] 数据分析仪表盘
- [x] 用户认证与权限
- [x] 后端 API 测试通过
- [ ] Docker 部署验证
- [ ] 前端页面测试
- [ ] 单元测试
- [ ] 操作日志完善
- [ ] 数据导入/导出
- [ ] 批量操作
- [ ] 移动端适配

## License

MIT
