<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>仪表盘</h2>
      <div class="year-selector">
        <el-select v-model="selectedYear" @change="loadStats" style="width: 120px">
          <el-option label="2026 年" value="2026" />
          <el-option label="2025 年" value="2025" />
          <el-option label="2024 年" value="2024" />
          <el-option label="2023 年" value="2023" />
          <el-option label="2022 年" value="2022" />
        </el-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card customer-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.customers?.total || 0 }}</div>
              <div class="stat-label">客户总数</div>
            </div>
          </div>
          <div class="stat-detail">
            本月新增：{{ stats.customers?.new_this_month || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card contract-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ formatNumber(stats.contracts?.total_amount) }}</div>
              <div class="stat-label">合同总金额</div>
            </div>
          </div>
          <div class="stat-detail">
            执行中：{{ stats.contracts?.in_progress || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card receivable-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ formatNumber(stats.receivables?.unpaid_amount) }}</div>
              <div class="stat-label">未收款金额</div>
            </div>
          </div>
          <div class="stat-detail">
            逾期：{{ stats.receivables?.overdue_count || 0 }} 笔
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card project-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Finished /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.projects?.total || 0 }}</div>
              <div class="stat-label">项目总数</div>
            </div>
          </div>
          <div class="stat-detail">
            进行中：{{ stats.projects?.implementation || 0 }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 现金流统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card income-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="color: #f56c6c">¥{{ formatNumber(stats.cashflow?.total_income) }}</div>
              <div class="stat-label">现金流入</div>
            </div>
          </div>
          <div class="stat-detail">
            收入笔数：{{ stats.cashflow?.income_count || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stat-card expense-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="color: #67c23a">¥{{ formatNumber(stats.cashflow?.total_expense) }}</div>
              <div class="stat-label">现金流出</div>
            </div>
          </div>
          <div class="stat-detail">
            支出笔数：{{ stats.cashflow?.expense_count || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stat-card cashflow-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" :style="{ color: Number(stats.cashflow?.net_cashflow) >= 0 ? '#409EFF' : '#F56C6C' }">
                ¥{{ formatNumber(stats.cashflow?.net_cashflow) }}
              </div>
              <div class="stat-label">净现金流</div>
            </div>
          </div>
          <div class="stat-detail">
            年份：{{ selectedYear }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 证书统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card cert-card" @click="$router.push('/certificates')">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.certificates?.active_count || 0 }}</div>
              <div class="stat-label">已签发证书</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card cert-warning-card" @click="$router.push('/certificates')">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="color: #e6a23c">{{ stats.certificates?.expiring_soon_count || 0 }}</div>
              <div class="stat-label">即将过期</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card cert-danger-card" @click="$router.push('/certificates')">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="color: #f56c6c">{{ stats.certificates?.expired_count || 0 }}</div>
              <div class="stat-label">已过期证书</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 逾期应收款提醒 -->
    <el-row :gutter="20" class="stats-row" v-if="overdueItems.length > 0">
      <el-col :span="24">
        <el-card class="overdue-card">
          <template #header>
            <div class="card-header overdue-header">
              <span class="overdue-title">
                <el-icon :size="20"><WarningFilled /></el-icon>
                逾期应收款提醒
              </span>
              <el-tag type="danger" effect="dark">共 {{ overdueItems.length }} 笔，¥{{ formatNumber(stats.receivables?.overdue_amount) }}</el-tag>
            </div>
          </template>
          <el-table :data="overdueItems" stripe size="small" @row-click="(row) => $router.push('/receivables')">
            <el-table-column prop="contract_no" label="合同编号" width="160" />
            <el-table-column prop="contract_name" label="合同名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="customer_name" label="客户" width="140" show-overflow-tooltip />
            <el-table-column label="未收金额" width="140" align="right">
              <template #default="{ row }">
                <strong class="overdue-amount">¥{{ formatNumber(row.unpaid_amount) }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="到期日" width="120" align="center" />
            <el-table-column label="逾期天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.days_overdue > 90 ? 'danger' : row.days_overdue > 30 ? 'warning' : 'info'" effect="dark">
                  {{ row.days_overdue }} 天
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'partial' ? 'warning' : 'danger'" size="small">
                  {{ row.status === 'partial' ? '部分收款' : '未收款' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 证书到期提醒 -->
    <el-row :gutter="20" class="stats-row" v-if="(stats.certificates?.expiring_soon_items?.length || 0) > 0">
      <el-col :span="24">
        <el-card class="cert-warning-section">
          <template #header>
            <div class="card-header cert-alert-header">
              <span class="cert-alert-title warning-title">
                <el-icon :size="20"><WarningFilled /></el-icon>
                即将过期证书
              </span>
              <el-tag type="warning" effect="dark">共 {{ stats.certificates?.expiring_soon_count || 0 }} 张</el-tag>
            </div>
          </template>
          <el-table :data="stats.certificates?.expiring_soon_items || []" stripe size="small"
            @row-click="(row) => $router.push('/certificates')">
            <el-table-column prop="customer_name" label="医院名称" min-width="160" />
            <el-table-column prop="product_name" label="软件产品" min-width="160" />
            <el-table-column prop="end_date" label="截止日期" width="120" align="center" />
            <el-table-column label="剩余天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="warning" effect="dark">{{ row.days_remaining }} 天</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row" v-if="(stats.certificates?.expired_items?.length || 0) > 0">
      <el-col :span="24">
        <el-card class="cert-danger-section">
          <template #header>
            <div class="card-header cert-alert-header">
              <span class="cert-alert-title danger-title">
                <el-icon :size="20"><WarningFilled /></el-icon>
                已过期证书
              </span>
              <el-tag type="danger" effect="dark">共 {{ stats.certificates?.expired_count || 0 }} 张</el-tag>
            </div>
          </template>
          <el-table :data="stats.certificates?.expired_items || []" stripe size="small"
            @row-click="(row) => $router.push('/certificates')">
            <el-table-column prop="customer_name" label="医院名称" min-width="160" />
            <el-table-column prop="product_name" label="软件产品" min-width="160" />
            <el-table-column prop="end_date" label="截止日期" width="120" align="center" />
            <el-table-column label="过期天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="danger" effect="dark">{{ row.days_overdue }} 天</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>客户增长趋势</span>
            </div>
          </template>
          <div ref="customerTrendRef" class="chart"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>月度收支趋势</span>
            </div>
          </template>
          <div ref="cashflowTrendRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 销售漏斗 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>销售漏斗</span>
            </div>
          </template>
          <div class="funnel-row">
            <div class="funnel-stage" v-for="s in funnelData" :key="s.status">
              <div class="funnel-label">{{ s.label }}</div>
              <div class="funnel-bar-wrap">
                <div class="funnel-bar" :style="{ height: funnelHeight(s.total_amount) + 'px', background: funnelColor(s.status) }" />
              </div>
              <div class="funnel-amount">¥ {{ formatFunnelAmount(s.total_amount) }}</div>
              <div class="funnel-count">{{ s.count }} 个项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <el-space>
            <el-button type="info" class="ai-entry-button" @click="aiImportVisible = true">
              <el-icon><Plus /></el-icon> AI录入合同
            </el-button>
            <el-button type="primary" @click="$router.push('/customers')">
              <el-icon><Plus /></el-icon> 新增客户
            </el-button>
            <el-button type="success" @click="$router.push('/contracts')">
              <el-icon><Plus /></el-icon> 新增合同
            </el-button>
            <el-button type="warning" @click="$router.push('/invoices')">
              <el-icon><Plus /></el-icon> 创建发票
            </el-button>
            <el-button type="danger" @click="$router.push('/receivables')">
              <el-icon><Plus /></el-icon> 登记收款
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
    <AiContractImportDrawer v-model="aiImportVisible" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { User, Document, Coin, Finished, TrendCharts, Money, Plus, WarningFilled, Key, Warning, CircleClose } from '@element-plus/icons-vue'
import { getDashboardStats } from '@/api/dashboard'
import { getFunnelStats } from '@/api/project'
import AiContractImportDrawer from '@/components/AiContractImportDrawer.vue'

const stats = ref({})
const customerTrendRef = ref(null)
const cashflowTrendRef = ref(null)
const funnelData = ref([])
const selectedYear = ref(new Date().getFullYear().toString())
const aiImportVisible = ref(false)

const overdueItems = computed(() => {
  return stats.value.receivables?.overdue_items || []
})

const formatNumber = (num) => {
  if (!num) return '0'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const loadStats = async () => {
  try {
    stats.value = await getDashboardStats({ year: selectedYear.value })
    nextTick(() => {
      initCustomerTrendChart()
      initCashflowTrendChart()
      loadFunnel()
    })
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const initCustomerTrendChart = () => {
  if (!customerTrendRef.value) return

  const chart = echarts.init(customerTrendRef.value)
  const trend = stats.value.customers?.trend || []

  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trend.map((item) => item.month),
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '新增客户',
        type: 'line',
        data: trend.map((item) => item.count),
        smooth: true,
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.5)' },
            { offset: 1, color: 'rgba(64,158,255,0.1)' },
          ]),
        },
      },
    ],
  })

  window.addEventListener('resize', () => chart.resize())
}

const initCashflowTrendChart = () => {
  if (!cashflowTrendRef.value) return

  const chart = echarts.init(cashflowTrendRef.value)
  const cashflow = stats.value.cashflow || {}

  // 构建 12 个月的数据
  const months = Array.from({ length: 12 }, (_, i) => i + 1)
  const incomeData = months.map((m) => {
    const found = cashflow.income_by_month?.find((item) => item.month === m)
    return found ? found.amount : 0
  })
  const expenseData = months.map((m) => {
    const found = cashflow.expense_by_month?.find((item) => item.month === m)
    return found ? found.amount : 0
  })
  const netData = months.map((_, i) => incomeData[i] - expenseData[i])

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['现金流入', '现金流出', '净现金流'] },
    xAxis: {
      type: 'category',
      data: ['1 月', '2 月', '3 月', '4 月', '5 月', '6 月', '7 月', '8 月', '9 月', '10 月', '11 月', '12 月'],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '现金流入',
        type: 'bar',
        data: incomeData,
        itemStyle: { color: '#f56c6c' },
      },
      {
        name: '现金流出',
        type: 'bar',
        data: expenseData,
        itemStyle: { color: '#67c23a' },
      },
      {
        name: '净现金流',
        type: 'line',
        data: netData,
        itemStyle: { color: '#409EFF' },
        smooth: true,
      },
    ],
  })

  window.addEventListener('resize', () => chart.resize())
}

const loadFunnel = async () => {
  try {
    const res = await getFunnelStats()
    funnelData.value = res.stages
  } catch (e) {
    console.error('加载漏斗统计失败:', e)
  }
}

const funnelHeight = (amount) => {
  const max = Math.max(...funnelData.value.map(s => s.total_amount), 1)
  return Math.max(4, (amount / max) * 28)
}

const funnelColor = (status) => {
  const colors = { contact: '#409EFF', bidding: '#409EFF', signing: '#409EFF', implementation: '#67C23A', acceptance: '#67C23A', after_sales: '#E6A23C' }
  return colors[status] || '#409EFF'
}

const formatFunnelAmount = (val) => {
  const n = Number(val)
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h2 {
  margin: 0;
}

.year-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dashboard h2 {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.customer-card .stat-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.contract-card .stat-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.receivable-card .stat-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.project-card .stat-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.income-card .stat-icon {
  background: linear-gradient(135deg, #f56c6c, #f5a877);
}

.expense-card .stat-icon {
  background: linear-gradient(135deg, #67c23a, #43e97b);
}

.cashflow-card .stat-icon {
  background: linear-gradient(135deg, #409EFF, #67c23a);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.stat-detail {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  font-size: 13px;
  color: #606266;
}

.charts-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart {
  height: 300px;
}

.quick-actions {
  margin-top: 20px;
}

.ai-entry-button {
  background: linear-gradient(135deg, #0f766e, #1d4ed8);
  border: none;
  color: #fff;
  box-shadow: 0 10px 24px rgba(29, 78, 216, 0.22);
}

/* 销售漏斗 */
.funnel-row { display: flex; gap: 12px; align-items: flex-end; }
.funnel-stage { flex: 1; text-align: center; padding: 8px; border-radius: 8px; transition: background .2s; }
.funnel-stage:hover { background: #f5f7fa; }
.funnel-label { font-size: 13px; color: #666; margin-bottom: 4px; }
.funnel-bar-wrap { height: 32px; display: flex; align-items: flex-end; justify-content: center; margin-bottom: 6px; }
.funnel-bar { width: 85%; border-radius: 4px; min-height: 4px; transition: height .3s; }
.funnel-amount { font-size: 16px; font-weight: 700; color: #303133; }
.funnel-count { font-size: 12px; color: #909399; }

.overdue-card {
  border: 2px solid #f56c6c;
  border-radius: 12px;
}

.overdue-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #fef0f0, #fdf6f6);
  border-bottom: 1px solid #fde2e2;
  border-radius: 12px 12px 0 0;
  padding: 14px 20px;
}

.overdue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overdue-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.overdue-amount {
  color: #f56c6c;
}

.overdue-card :deep(.el-table__row) {
  cursor: pointer;
}

.overdue-card :deep(.el-table__row:hover) {
  background: #fef0f0 !important;
}

/* Certificate stat cards */
.cert-card .stat-icon { background: linear-gradient(135deg, #409EFF, #67c23a); }
.cert-warning-card .stat-icon { background: linear-gradient(135deg, #f5a623, #e6a23c); }
.cert-danger-card .stat-icon { background: linear-gradient(135deg, #f56c6c, #e63946); }

.cert-warning-section { border: 2px solid #e6a23c; border-radius: 12px; }
.cert-warning-section :deep(.el-card__header) {
  background: linear-gradient(135deg, #fdf6ec, #fef9f0);
  border-bottom: 1px solid #fae3c4;
  border-radius: 12px 12px 0 0; padding: 14px 20px;
}

.cert-danger-section { border: 2px solid #f56c6c; border-radius: 12px; }
.cert-danger-section :deep(.el-card__header) {
  background: linear-gradient(135deg, #fef0f0, #fdf6f6);
  border-bottom: 1px solid #fde2e2;
  border-radius: 12px 12px 0 0; padding: 14px 20px;
}

.cert-alert-header { display: flex; justify-content: space-between; align-items: center; }
.cert-alert-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 700; }
.warning-title { color: #e6a23c; }
.danger-title { color: #f56c6c; }

.cert-warning-section :deep(.el-table__row), .cert-danger-section :deep(.el-table__row) { cursor: pointer; }
.cert-warning-section :deep(.el-table__row:hover) { background: #fdf6ec !important; }
.cert-danger-section :deep(.el-table__row:hover) { background: #fef0f0 !important; }
</style>
