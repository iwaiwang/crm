<template>
  <div class="docs-page">
    <div class="docs-header">
      <h1>系统架构文档</h1>
      <p>帮助管理者全面理解项目的前端、后端和数据库结构</p>
    </div>

    <!-- 目录 -->
    <el-card class="toc-card">
      <template #header><span>目录</span></template>
      <el-anchor :offset="80">
        <el-anchor-link href="#frontend" title="前端架构" />
        <el-anchor-link href="#backend" title="后端架构" />
        <el-anchor-link href="#database" title="数据库设计" />
        <el-anchor-link href="#deployment" title="部署说明" />
      </el-anchor>
    </el-card>

    <!-- ========== 前端 ========== -->
    <h2 id="frontend" class="section-title">前端架构</h2>

    <el-card class="section-card">
      <template #header><span>技术栈</span></template>
      <el-descriptions border :column="2">
        <el-descriptions-item label="框架">Vue 3 (Composition API)</el-descriptions-item>
        <el-descriptions-item label="构建工具">Vite 5</el-descriptions-item>
        <el-descriptions-item label="UI 组件库">Element Plus 2.5</el-descriptions-item>
        <el-descriptions-item label="图表库">ECharts 5 (vue-echarts)</el-descriptions-item>
        <el-descriptions-item label="路由">Vue Router 4</el-descriptions-item>
        <el-descriptions-item label="状态管理">Pinia 2</el-descriptions-item>
        <el-descriptions-item label="HTTP 客户端">Axios</el-descriptions-item>
        <el-descriptions-item label="Excel 导出">xlsx</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="section-card">
      <template #header><span>目录结构</span></template>
      <el-table :data="frontendFiles" size="small" border>
        <el-table-column prop="path" label="文件/目录" width="280" />
        <el-table-column prop="desc" label="说明" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>页面路由一览</span></template>
      <el-table :data="routes" size="small" border>
        <el-table-column prop="path" label="路由" width="180" />
        <el-table-column prop="name" label="页面名称" width="140" />
        <el-table-column prop="desc" label="功能说明" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>数据流</span></template>
      <div class="flow-steps">
        <div class="flow-item">
          <el-tag type="primary" size="large">1. 用户操作</el-tag>
          <span>页面组件中触发操作</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-item">
          <el-tag type="success" size="large">2. API 调用</el-tag>
          <span>调用 api/ 模块中的函数</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-item">
          <el-tag type="warning" size="large">3. Axios 请求</el-tag>
          <span>api/request.js 拦截器自动携带 JWT Token，过滤 null 参数</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-item">
          <el-tag type="danger" size="large">4. 后端响应</el-tag>
          <span>后端 FastAPI 处理请求，返回 JSON</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-item">
          <el-tag size="large">5. 响应拦截</el-tag>
          <span>request.js 拦截器统一处理错误（401 跳登录，其他弹出提示）</span>
        </div>
      </div>
    </el-card>

    <el-card class="section-card">
      <template #header><span>权限控制</span></template>
      <ul class="text-list">
        <li><strong>路由守卫</strong>（<code>router/index.js</code>）：根据用户 <code>menu_permissions</code> 控制页面访问，非管理员不能访问用户管理和系统设置</li>
        <li><strong>菜单过滤</strong>（<code>Layout.vue</code>）：侧边栏通过 <code>v-if="hasPermission('xxx')"</code> 控制菜单项显示</li>
        <li><strong>管理员后台</strong>：用户管理、系统设置仅 <code>role === 'admin'</code> 可见</li>
        <li><strong>Login 登录</strong>：管理员启用 2FA 后需两步验证，普通用户密码登录即可</li>
      </ul>
    </el-card>

    <!-- ========== 后端 ========== -->
    <h2 id="backend" class="section-title">后端架构</h2>

    <el-card class="section-card">
      <template #header><span>技术栈</span></template>
      <el-descriptions border :column="2">
        <el-descriptions-item label="框架">FastAPI 0.109</el-descriptions-item>
        <el-descriptions-item label="Python 版本">3.11+</el-descriptions-item>
        <el-descriptions-item label="ORM">SQLAlchemy 2.0 (AsyncSession)</el-descriptions-item>
        <el-descriptions-item label="数据库驱动">aiosqlite (异步 SQLite)</el-descriptions-item>
        <el-descriptions-item label="认证">JWT (python-jose + bcrypt)</el-descriptions-item>
        <el-descriptions-item label="数据验证">Pydantic 2.5</el-descriptions-item>
        <el-descriptions-item label="API 文档">自动生成 Swagger (/docs)</el-descriptions-item>
        <el-descriptions-item label="文件格式">PyMuPDF (PDF)、openpyxl (Excel)</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="section-card">
      <template #header><span>目录结构</span></template>
      <el-table :data="backendFiles" size="small" border>
        <el-table-column prop="path" label="文件/目录" width="280" />
        <el-table-column prop="desc" label="说明" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>API 端点一览</span></template>
      <el-table :data="apiEndpoints" size="small" border>
        <el-table-column prop="module" label="模块" width="130" />
        <el-table-column prop="endpoints" label="主要端点" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>认证流程</span></template>
      <ul class="text-list">
        <li><strong>登录</strong>：<code>POST /api/auth/login</code> → 验证用户名/密码，返回 JWT Token</li>
        <li><strong>两步验证（管理员）</strong>：登录后若 <code>totp_enabled=true</code>，返回临时 Token，前端跳转 2FA 页面，输入 TOTP 码后获取正式 Token</li>
        <li><strong>Token 携带</strong>：前端 Axios 拦截器自动在 <code>Authorization: Bearer &lt;token&gt;</code> 头中携带</li>
        <li><strong>权限检查</strong>：<code>get_current_user</code> 依赖验证 Token；<code>require_menu_permission</code> 依赖检查菜单权限</li>
      </ul>
    </el-card>

    <!-- ========== 数据库 ========== -->
    <h2 id="database" class="section-title">数据库设计</h2>

    <el-card class="section-card">
      <template #header><span>数据表一览（17 张表）</span></template>
      <el-table :data="tables" size="small" border>
        <el-table-column prop="name" label="表名" width="160" />
        <el-table-column prop="desc" label="说明" width="200" />
        <el-table-column prop="keyFields" label="关键字段" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>核心表关系图</span></template>
      <div class="er-diagram">
        <pre class="er-text">
                        ┌──────────────┐
                        │    users     │  用户 / 认证
                        └──────┬───────┘
                               │ id
          ┌────────────────────┼──────────────────────────┐
          │ applicant_id       │ created_by               │ approver_id
          ▼                    ▼                          ▼
  ┌───────────────┐   ┌───────────────┐         ┌──────────────┐
  │ certificates  │   │ reimbursements│         │  contracts   │
  │   数字证书     │   │    报销单     │◄────────│   合同       │
  └──────┬────────┘   └──────┬────────┘         └──────┬───────┘
         │ customer_id       │ invoice_id              │ customer_id
         ▼                   ▼                         ▼
  ┌───────────────┐   ┌───────────────┐         ┌──────────────┐
  │   customers   │◄──│   invoices    │◄────────│  receivables │
  │    客户       │   │    发票       │         │   应收款      │
  └──────┬────────┘   └──────┬────────┘         └──────┬───────┘
         │                   │ contract_id             │ id
         │ customer_id       │                         ▼
         ▼                   ▼                 ┌──────────────┐
  ┌───────────────┐   ┌───────────────┐        │payment_records│
  │   projects    │   │   expenses    │        │   收款记录     │
  │    项目       │   │    支出       │        └──────────────┘
  └──────┬────────┘   └──────┬────────┘
         │ contract_id       │ reimbursement_id
         │                   ▼
         │           ┌───────────────┐
         │           │  incomes      │
         │           │    收入       │
         │           └──────┬────────┘
         │                  │ customer_id
         ▼                  ▼
  ┌───────────────────────────────────┐
  │          customers (客户)          │
  └───────────────────────────────────┘
        </pre>
      </div>
    </el-card>

    <el-card class="section-card">
      <template #header><span>表关系详解</span></template>
      <el-collapse>
        <el-collapse-item title="客户域 (customers)" name="1">
          <ul class="text-list">
            <li><code>customers</code> → <code>customer_contacts</code>：一对多，一个客户可有多个联系人</li>
            <li><code>customers</code> → <code>contracts</code>：一对多，一个客户可签多个合同</li>
            <li><code>customers</code> → <code>projects</code>：一对多，一个客户可有多个项目</li>
            <li><code>customers</code> → <code>certificates</code>：一对多，一个客户可申请多个证书</li>
          </ul>
        </el-collapse-item>
        <el-collapse-item title="合同域 (contracts)" name="2">
          <ul class="text-list">
            <li><code>contracts</code> → <code>contract_files</code>：一对多，一个合同可上传多个文件</li>
            <li><code>contracts</code> → <code>invoices</code>：一对多，一个合同可关联多张发票</li>
            <li><code>contracts</code> → <code>receivables</code>：一对多，一个合同可有多笔应收款</li>
            <li><code>contracts</code> → <code>projects</code>：一对一，一个项目可关联一个合同</li>
          </ul>
        </el-collapse-item>
        <el-collapse-item title="财务域 (invoices / receivables / incomes / expenses)" name="3">
          <ul class="text-list">
            <li><code>receivables</code> → <code>payment_records</code>：一对多，一笔应收款可分多次收款</li>
            <li><code>invoices</code> ↔ <code>payment_records</code>：多对多（关联表 invoice_payment_records）</li>
            <li><code>invoices</code> → <code>incomes</code>：一对多，一张发票可产生多笔收入</li>
            <li><code>invoices</code> → <code>expenses</code>：一对多，一张进项发票可关联多笔支出</li>
            <li><code>reimbursements</code> → <code>expenses</code>：一对一，报销支付后自动生成支出记录</li>
          </ul>
        </el-collapse-item>
        <el-collapse-item title="库存域 (products)" name="4">
          <ul class="text-list">
            <li><code>products</code> → <code>stock_moves</code>：一对多，每个产品有出入库流水</li>
          </ul>
        </el-collapse-item>
        <el-collapse-item title="项目域 (projects)" name="5">
          <ul class="text-list">
            <li><code>projects</code> → <code>project_followups</code>：一对多，跟进记录</li>
            <li><code>projects</code> → <code>project_phases</code>：一对多，项目阶段</li>
            <li><code>project_phases</code> → <code>project_tasks</code>：一对多，阶段任务</li>
          </ul>
        </el-collapse-item>
        <el-collapse-item title="设置 & AI (settings / ai_configs)" name="6">
          <ul class="text-list">
            <li><code>settings</code>：系统设置键值对，存储公司信息、业务配置等</li>
            <li><code>ai_configs</code>：AI 服务配置，支持 OpenAI 兼容接口和 Ollama 本地模型</li>
          </ul>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- ========== 部署 ========== -->
    <h2 id="deployment" class="section-title">部署说明</h2>

    <el-card class="section-card">
      <template #header><span>服务器信息</span></template>
      <el-descriptions border :column="2">
        <el-descriptions-item label="服务器 IP">100.124.87.69</el-descriptions-item>
        <el-descriptions-item label="操作系统">macOS (Mac mini)</el-descriptions-item>
        <el-descriptions-item label="部署方式">Docker Compose</el-descriptions-item>
        <el-descriptions-item label="部署路径"><code>/Users/john/deployments/crm/</code></el-descriptions-item>
        <el-descriptions-item label="前端端口">8081 (HTTP)</el-descriptions-item>
        <el-descriptions-item label="后端端口">8002 (内部，不对外暴露)</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="section-card">
      <template #header><span>环境要求</span></template>
      <el-table :data="envRequirements" size="small" border>
        <el-table-column prop="item" label="项目" width="200" />
        <el-table-column prop="local" label="开发机 (本地)" />
        <el-table-column prop="server" label="服务器" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>容器架构</span></template>
      <pre class="code-block">
docker-compose.yml
├── backend (crm-backend)
│   ├── 镜像：python:3.11-slim + 依赖
│   ├── 端口：8002（仅内网，不映射宿主机）
│   ├── Volume：./backend/app → /app/app（代码热更新）
│   ├── Volume：./data → /data（数据库 + 上传文件）
│   └── 环境变量：DATABASE_URL, UPLOAD_DIR, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
│
├── frontend (crm-frontend)
│   ├── 镜像：nginx:alpine + 构建后的静态文件
│   ├── 端口：8081 → 80
│   ├── Nginx 反向代理 /api/* → backend:8002
│   └── 依赖：depends_on backend
      </pre>
    </el-card>

    <el-card class="section-card">
      <template #header><span>服务器连接方式</span></template>
      <pre class="code-block">
# 使用 sshpass + SSH 密码认证连接服务器
sshpass -p '&lt;password&gt;' ssh -o StrictHostKeyChecking=no \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  john@100.124.87.69

# Docker 命令需要指定 PATH
export PATH=/usr/local/bin:$PATH</pre>
    </el-card>

    <el-card class="section-card">
      <template #header><span>部署步骤（完整流程）</span></template>
      <el-steps direction="vertical" :active="7">
        <el-step title="1. 本地构建前端" description="npm run build（在 frontend/ 目录下执行）">
          <pre class="code-block">cd frontend
npm run build
# 输出到 dist/ 目录</pre>
        </el-step>
        <el-step title="2. 同步代码到服务器" description="使用 rsync 将本地代码同步到服务器（排除不需要的文件）">
          <pre class="code-block">sshpass -p '&lt;password&gt;' rsync -avz \
  --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='venv' --exclude='data/' --exclude='.DS_Store' \
  --exclude='node_modules' --exclude='backups/' \
  --exclude='.claude/' --exclude='dist/' \
  --exclude='*.png' --exclude='*.txt' --exclude='mockups/' \
  -e 'ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no' \
  /path/to/local/crm/ \
  john@100.124.87.69:/Users/john/deployments/crm/</pre>
        </el-step>
        <el-step title="3. 同步前端 dist 到服务器" description="前端的 dist 需要单独同步（因为 .gitignore 排除了 dist）">
          <pre class="code-block">sshpass -p '&lt;password&gt;' rsync -avz \
  -e 'ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no' \
  frontend/dist/ \
  john@100.124.87.69:/Users/john/deployments/crm/frontend/dist/</pre>
        </el-step>
        <el-step title="4. 安装后端新依赖（如有新增）" description="如果 requirements.txt 有变动，先在容器中临时安装，同时也要更新 requirements.txt 以备后续构建">
          <pre class="code-block"># 临时安装到运行中的容器
sshpass -p '&lt;password&gt;' ssh ... john@100.124.87.69 \
  "export PATH=/usr/local/bin:\$PATH && cd /Users/john/deployments/crm && \
   docker compose exec -T backend pip install &lt;package&gt;"

# 同时更新 requirements.txt（本地文件会被 rsync 同步）</pre>
        </el-step>
        <el-step title="5. 执行数据库迁移（如有新增字段）" description="SQLite 不支持直接 ALTER TABLE，需手动添加列">
          <pre class="code-block">sshpass -p '&lt;password&gt;' ssh ... john@100.124.87.69 \
  "export PATH=/usr/local/bin:\$PATH && cd /Users/john/deployments/crm && \
   docker compose exec -T backend python3 -c \"
import sqlite3
conn = sqlite3.connect('/data/crm.db')
conn.execute('ALTER TABLE xxx ADD COLUMN xxx TYPE DEFAULT ...')
conn.commit()
conn.close()
\""</pre>
        </el-step>
        <el-step title="6. 构建镜像并重启容器" description="使用 deploy 脚本自动备份 + 构建 + 重启">
          <pre class="code-block"># 完整部署（前后端都更新）
sshpass -p '&lt;password&gt;' ssh ... john@100.124.87.69 \
  "export PATH=/usr/local/bin:\$PATH && cd /Users/john/deployments/crm && \
   bash scripts/safe-deploy.sh all"

# 仅部署前端
bash scripts/safe-deploy.sh frontend

# 仅部署后端
bash scripts/safe-deploy.sh backend</pre>
        </el-step>
        <el-step title="7. 验证部署" description="确保容器正常运行，API 可访问">
          <pre class="code-block"># 查看容器状态
docker compose ps

# 查看后端日志
docker compose logs backend --tail 50

# 测试 API
curl -s --noproxy '*' http://100.124.87.69:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"&lt;password&gt;"}'

# 浏览器访问
open http://100.124.87.69:8081</pre>
        </el-step>
      </el-steps>
    </el-card>

    <el-card class="section-card">
      <template #header><span>部署脚本说明</span></template>
      <el-table :data="deployScripts" size="small" border>
        <el-table-column prop="script" label="脚本" width="220" />
        <el-table-column prop="desc" label="功能" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><span>数据备份策略</span></template>
      <el-descriptions border :column="1">
        <el-descriptions-item label="自动备份">
          <code>scripts/safe-deploy.sh</code> 在每次部署前自动调用 <code>scripts/backup.sh</code>，将 <code>data/crm.db</code> 和 <code>data/uploads/</code> 备份到 <code>backups/YYYYMMDD_HHMMSS/</code>
        </el-descriptions-item>
        <el-descriptions-item label="保留策略">自动保留最近 7 天的备份，超过 7 天的自动清理</el-descriptions-item>
        <el-descriptions-item label="手动备份">
          可随时执行：<code>bash scripts/backup.sh</code>
        </el-descriptions-item>
        <el-descriptions-item label="恢复方法">
          将备份的 <code>crm.db</code> 复制回 <code>data/</code> 目录，重启容器即可
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="section-card">
      <template #header><span>最新部署注意事项</span></template>
      <ul class="text-list">
        <li><strong>前端构建</strong>：服务器上 Docker 构建前端时遇到 Vite 兼容问题，目前采用<strong>本地构建 dist + rsync 到服务器</strong>的方式。服务器上的 <code>frontend/Dockerfile</code> 已简化为直接 COPY 预构建的 dist</li>
        <li><strong>后端依赖</strong>：新增 Python 包需同时更新 <code>backend/requirements.txt</code>，并在服务器容器中 <code>pip install</code>。容器重建时会从 requirements.txt 安装</li>
        <li><strong>后端代码更新</strong>：后端代码通过 volume 挂载，rsync 同步后<strong>无需重建镜像</strong>，只需 <code>docker compose restart backend</code></li>
        <li><strong>前端代码更新</strong>：前端没有 volume 挂载，每次需本地构建 + rsync dist + docker compose build frontend + up -d</li>
        <li><strong>数据安全</strong>：rsync 时必须 <code>--exclude='data/'</code>，避免覆盖服务器上的生产数据库</li>
        <li><strong>端口检查</strong>：确保 8081 端口未被占用。如有冲突，修改 <code>docker-compose.yml</code> 中 frontend 的 ports 映射</li>
      </ul>
    </el-card>

    <el-card class="section-card">
      <template #header><span>故障排查</span></template>
      <el-collapse>
        <el-collapse-item title="502 Bad Gateway" name="1">
          <p>前端 Nginx 无法连接后端。检查后端容器是否运行：</p>
          <pre class="code-block">docker compose ps backend
docker compose logs backend --tail 30</pre>
          <p>常见原因：后端容器崩溃（Python 导入错误、缺少依赖）、端口冲突</p>
        </el-collapse-item>
        <el-collapse-item title="前端页面空白或 JS 报错" name="2">
          <p>通常是因为浏览器缓存了旧的 JS 文件。强制刷新（Ctrl+Shift+R 或 Cmd+Shift+R），或清除浏览器缓存后重试</p>
        </el-collapse-item>
        <el-collapse-item title="API 返回 401 Unauthorized" name="3">
          <p>Token 过期或无效。退出重新登录即可获取新 Token。Token 过期时间由 <code>ACCESS_TOKEN_EXPIRE_MINUTES</code> 环境变量控制（默认 1440 分钟 = 24 小时）</p>
        </el-collapse-item>
        <el-collapse-item title="数据库锁定 (database is locked)" name="4">
          <p>SQLite 不支持高并发写入。如果多个请求同时写入，可能出现锁定。重启后端容器临时解决：</p>
          <pre class="code-block">docker compose restart backend</pre>
          <p>长期方案：考虑迁移到 PostgreSQL</p>
        </el-collapse-item>
        <el-collapse-item title="Docker 构建失败" name="5">
          <p>检查 Docker 是否在运行：<code>docker info</code></p>
          <p>清理构建缓存：<code>docker builder prune</code></p>
          <p>查看详细错误：<code>docker compose build --progress=plain</code></p>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const frontendFiles = ref([
  { path: 'src/main.js', desc: '入口文件，挂载 Vue 应用' },
  { path: 'src/App.vue', desc: '根组件' },
  { path: 'src/router/index.js', desc: '路由配置 + 权限守卫（token 检查、菜单权限过滤）' },
  { path: 'src/store/user.js', desc: 'Pinia 用户状态（token、用户信息、权限判断）' },
  { path: 'src/api/request.js', desc: 'Axios 实例：baseURL、JWT 拦截器、错误统一处理、参数过滤' },
  { path: 'src/api/*.js', desc: '各业务模块 API 封装（auth、customer、contract、invoice 等）' },
  { path: 'src/views/Layout.vue', desc: '主布局：侧边栏菜单 + 顶部导航 + 内容区' },
  { path: 'src/views/Login.vue', desc: '登录页：品牌展示 + 密码登录 + 两步验证' },
  { path: 'src/views/Dashboard.vue', desc: '仪表盘：全局统计图表' },
  { path: 'src/views/*.vue', desc: '各业务页面（客户、合同、发票、应收款、报销、产品、项目、现金流、证书等）' },
  { path: 'src/components/*.vue', desc: '公共组件：DocumentUploader（文件上传+AI解析）、AI导入抽屉等' },
])

const backendFiles = ref([
  { path: 'backend/app/main.py', desc: 'FastAPI 应用入口，注册所有路由，配置 CORS' },
  { path: 'backend/app/config.py', desc: 'Settings 配置类（密钥、Token 过期时间等）' },
  { path: 'backend/app/database.py', desc: 'AsyncSession 工厂 + get_db 依赖' },
  { path: 'backend/app/models/*.py', desc: 'SQLAlchemy ORM 模型定义（17 张表）' },
  { path: 'backend/app/schemas/*.py', desc: 'Pydantic 请求/响应 Schema，数据验证' },
  { path: 'backend/app/api/auth.py', desc: '认证路由：登录、注册、Token、两步验证' },
  { path: 'backend/app/api/*.py', desc: '各业务模块 API 路由（CRUD + 审批流 + AI 解析）' },
  { path: 'backend/app/utils/auth.py', desc: 'JWT 工具 + TOTP 生成/验证 + 密码哈希' },
])

const routes = ref([
  { path: '/login', name: '登录', desc: '用户登录（支持两步验证）' },
  { path: '/dashboard', name: '仪表盘', desc: '全局数据概览：收入、应收款、项目进度、库存等统计图表' },
  { path: '/customers', name: '客户管理', desc: '客户 CRUD + 联系人管理 + 批量操作' },
  { path: '/contracts', name: '合同管理', desc: '合同 CRUD + 文件上传 + AI 智能导入 + 批量操作' },
  { path: '/invoices', name: '发票管理', desc: '发票 CRUD + AI 智能导入 + 扫码/OCR 识别 + 销项/进项分类' },
  { path: '/receivables', name: '应收款管理', desc: '应收款跟踪 + 收款登记 + 状态管理' },
  { path: '/reimbursements', name: '报销管理', desc: '报销单申请/审批/支付流程 + AI 发票识别 + 批量支付导出' },
  { path: '/suppliers', name: '收款方管理', desc: '供应商/收款方信息管理 + 银行账户信息' },
  { path: '/incomes', name: '收入管理', desc: '收入记录 + 分类统计' },
  { path: '/expenses', name: '支出管理', desc: '支出记录 + 分类统计 + 关联发票/合同' },
  { path: '/products', name: '产品库存', desc: '产品管理 + 出入库流水 + 库存预警' },
  { path: '/projects', name: '项目进度', desc: '项目管理 + 销售漏斗 + 进度跟踪 + 阶段/任务分解' },
  { path: '/certificates', name: '证书管理', desc: '数字证书申请/审批/签发/下载/吊销 + RSA X.509 签名' },
  { path: '/certificates/guide', name: '证书使用指南', desc: '医院端集成证书的代码示例（Python/C#/Java）' },
  { path: '/profile', name: '个人中心', desc: '个人资料修改 + 密码修改 + 两步验证设置' },
  { path: '/users', name: '用户管理', desc: '用户 CRUD + 角色分配 + 菜单权限配置（仅管理员）' },
  { path: '/settings', name: '系统设置', desc: '公司信息 + AI 配置 + 报销类别 + 文件清理等（仅管理员）' },
])

const apiEndpoints = ref([
  { module: 'auth', endpoints: 'POST /login, /logout, /register, GET /me, POST /2fa/setup, /2fa/verify-setup, /2fa/verify, /2fa/disable' },
  { module: 'users', endpoints: 'GET/POST/PUT/DELETE /users, POST /users/change-password, /users/avatar' },
  { module: 'customers', endpoints: 'GET/POST/PUT/DELETE /customers, /customers/{id}/contacts' },
  { module: 'contracts', endpoints: 'CRUD /contracts, /contracts/{id}/files, /contracts/ai/* (AI 导入)' },
  { module: 'invoices', endpoints: 'CRUD /invoices, /invoices/ai/* (AI 导入), /invoices/check-duplicate' },
  { module: 'receivables', endpoints: 'CRUD /receivables, /receivables/{id}/payments' },
  { module: 'reimbursements', endpoints: 'CRUD + 审批流程, /reimbursements/ai/*, /reimbursements/statistics, /export-batch-payment' },
  { module: 'suppliers', endpoints: 'CRUD /suppliers, GET /suppliers/search' },
  { module: 'incomes', endpoints: 'CRUD /incomes, GET /incomes/stats' },
  { module: 'expenses', endpoints: 'CRUD /expenses, GET /expenses/stats, /expenses/categories' },
  { module: 'products', endpoints: 'CRUD /products, /products/{id}/stock-moves' },
  { module: 'projects', endpoints: 'CRUD /projects, /projects/{id}/phases, /projects/{id}/tasks, /projects/funnel' },
  { module: 'certificates', endpoints: 'CRUD + 审批 + 签发 + 吊销 + 续期 + 下载 /certificates' },
  { module: 'settings', endpoints: 'CRUD /settings, GET /settings/public, /settings/company-info, /settings/init' },
  { module: 'dashboard', endpoints: 'GET /dashboard/stats (全局统计)' },
  { module: 'document', endpoints: 'POST /document/upload, /document/parse, /document/scan-invoice-qr, GET /document/ai-status' },
  { module: 'webhooks', endpoints: 'POST /webhooks/github (GitHub 自动化)' },
])

const tables = ref([
  { name: 'users', desc: '用户', keyFields: 'id, username, email, role, is_active, menu_permissions, totp_secret, totp_enabled' },
  { name: 'customers', desc: '客户', keyFields: 'id, name, address, category, status' },
  { name: 'customer_contacts', desc: '客户联系人', keyFields: 'id, customer_id (FK), name, phone, email, is_primary' },
  { name: 'contracts', desc: '合同', keyFields: 'id, contract_no, name, customer_id (FK), amount, status, payment_terms' },
  { name: 'contract_files', desc: '合同文件', keyFields: 'id, contract_id (FK), file_name, file_path, source, is_primary' },
  { name: 'invoices', desc: '发票', keyFields: 'id, invoice_no, contract_id (FK), amount, tax_rate, type, status' },
  { name: 'receivables', desc: '应收款', keyFields: 'id, contract_id (FK), amount, due_date, received_amount, status' },
  { name: 'payment_records', desc: '收款记录', keyFields: 'id, receivable_id (FK), amount, payment_date, payment_method' },
  { name: 'reimbursements', desc: '报销单', keyFields: 'id, supplier_name, amount, expense_category, status, created_by (FK)' },
  { name: 'expenses', desc: '支出记录', keyFields: 'id, supplier_id (FK), invoice_id (FK), amount, expense_category, source_type' },
  { name: 'incomes', desc: '收入记录', keyFields: 'id, invoice_id (FK), customer_id (FK), amount, income_category, source_type' },
  { name: 'suppliers', desc: '收款方', keyFields: 'id, name, supplier_type, bank_name, bank_account, status' },
  { name: 'products', desc: '产品', keyFields: 'id, name, spec, price, stock_qty, min_stock, category' },
  { name: 'stock_moves', desc: '库存流水', keyFields: 'id, product_id (FK), type (in/out), qty, ref_type, ref_id' },
  { name: 'projects', desc: '项目', keyFields: 'id, name, customer_id (FK), contract_id (FK), progress, status, bid_amount' },
  { name: 'project_followups', desc: '项目跟进', keyFields: 'id, project_id (FK), followup_date, followup_method' },
  { name: 'project_phases', desc: '项目阶段', keyFields: 'id, project_id (FK), name, status, start_date, end_date' },
  { name: 'project_tasks', desc: '阶段任务', keyFields: 'id, phase_id (FK), name, status, assignee' },
  { name: 'certificates', desc: '数字证书', keyFields: 'id, cert_serial, customer_id (FK), product_name, status, certificate_pem' },
  { name: 'settings', desc: '系统设置', keyFields: 'key (PK), value, value_type, is_public' },
  { name: 'ai_configs', desc: 'AI 配置', keyFields: 'id, service_type, api_base_url, model, enabled, health_status' },
])
</script>

<style scoped>
.docs-page {
  padding: 20px;
  max-width: 1100px;
}

.docs-header {
  margin-bottom: 24px;
}

.docs-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}

.docs-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.toc-card {
  margin-bottom: 24px;
}

.section-title {
  margin: 32px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
  font-size: 20px;
  color: #303133;
}

.section-card {
  margin-bottom: 16px;
}

.text-list {
  margin: 0;
  padding-left: 20px;
  line-height: 2;
  color: #606266;
}

.flow-steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.flow-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
  max-width: 160px;
}

.flow-item span {
  font-size: 12px;
  color: #909399;
}

.flow-arrow {
  font-size: 24px;
  color: #c0c4cc;
  margin: 0 4px;
}

.er-diagram {
  overflow-x: auto;
}

.er-text {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.35;
  color: #303133;
  white-space: pre;
  background: #f8f9fb;
  padding: 16px;
  border-radius: 8px;
}
</style>
