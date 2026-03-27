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
              <span>合同状态分布</span>
            </div>
          </template>
          <div ref="contractStatusRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 现金流图表 -->
    <el-row :gutter="20" class="charts-row">
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

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>支出分类占比</span>
            </div>
          </template>
          <div ref="expenseCategoryRef" class="chart"></div>
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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { User, Document, Coin, Finished, TrendCharts, Money, Plus } from '@element-plus/icons-vue'
import { getDashboardStats } from '@/api/dashboard'

const stats = ref({})
const customerTrendRef = ref(null)
const contractStatusRef = ref(null)
const cashflowTrendRef = ref(null)
const expenseCategoryRef = ref(null)
const selectedYear = ref(new Date().getFullYear().toString())

const formatNumber = (num) => {
  if (!num) return '0'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const loadStats = async () => {
  try {
    stats.value = await getDashboardStats({ year: selectedYear.value })
    nextTick(() => {
      initCustomerTrendChart()
      initContractStatusChart()
      initCashflowTrendChart()
      initExpenseCategoryChart()
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

const initContractStatusChart = () => {
  if (!contractStatusRef.value) return

  const chart = echarts.init(contractStatusRef.value)
  const c = stats.value.contracts || {}

  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center' },
    series: [
      {
        name: '合同状态',
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: c.draft || 0, name: '草拟' },
          { value: c.pending_review || 0, name: '待审核' },
          { value: c.in_progress || 0, name: '执行中' },
          { value: c.completed || 0, name: '已完成' },
          { value: c.terminated || 0, name: '已终止' },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
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

const initExpenseCategoryChart = () => {
  if (!expenseCategoryRef.value) return

  const chart = echarts.init(expenseCategoryRef.value)
  const cashflow = stats.value.cashflow || {}

  const categoryData = Object.entries(cashflow.expense_by_category || {}).map(([name, data]) => ({
    value: data.amount,
    name,
  }))

  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center' },
    series: [
      {
        name: '支出分类',
        type: 'pie',
        radius: ['40%', '70%'],
        data: categoryData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  })

  window.addEventListener('resize', () => chart.resize())
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
</style>
