<template>
  <div class="contracts-page">
    <div class="page-header">
      <h2>合同管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增合同
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="合同名称/编号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="searchForm.year" placeholder="全部年份" clearable style="width: 100px">
            <el-option label="2026" value="2026" />
            <el-option label="2025" value="2025" />
            <el-option label="2024" value="2024" />
            <el-option label="2023" value="2023" />
            <el-option label="2022" value="2022" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="签约" value="signed" />
            <el-option label="执行中" value="in_progress" />
            <el-option label="完毕" value="completed" />
            <el-option label="终止" value="terminated" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 合同列表 -->
    <el-card class="table-card">
      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="selectedContracts.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedContracts.length }} 条合同</el-tag>
        <span class="stat-item">合同金额合计：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="contract_no" label="合同编号" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">
              {{ row.contract_no }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="合同名称" min-width="200" />
        <el-table-column prop="customer_name" label="客户" width="150" />
        <el-table-column prop="amount" label="合同金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ Number(row.amount).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始日期" width="110" />
        <el-table-column prop="end_date" label="结束日期" width="110" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadContracts"
          @size-change="loadContracts"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getContracts, deleteContract } from '@/api/contract'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const selectedContracts = ref([])

const searchForm = reactive({
  search: '',
  year: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const loadContracts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm,
    }
    const res = await getContracts(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载合同列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedContracts.value = selection
}

// 清除选择
const clearSelection = () => {
  selectedContracts.value = []
  loadContracts()
}

// 计算选中合同金额合计
const selectedTotalAmount = computed(() => {
  return selectedContracts.value.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const handleSearch = () => {
  pagination.page = 1
  loadContracts()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.status = ''
  handleSearch()
}

// 打开新增合同页面
const openAddDialog = () => {
  router.push('/contracts/new')
}

// 编辑合同 - 打开详情页进入编辑模式
const handleEdit = (row) => {
  router.push(`/contracts/${row.id}`)
}

const handleViewDetail = (row) => {
  router.push(`/contracts/${row.id}`)
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定要删除该合同吗？', '提示', { type: 'warning' })
  try {
    await deleteContract(row.id)
    ElMessage.success('删除成功')
    loadContracts()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const getStatusType = (status) => {
  const map = { signed: '', in_progress: 'warning', completed: 'success', terminated: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { signed: '签约', in_progress: '执行中', completed: '完毕', terminated: '终止' }
  return map[status] || status
}

onMounted(() => {
  loadContracts()
})
</script>

<style scoped>
.contracts-page {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>

<style scoped>
.statistics-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
.stat-item {
  font-size: 14px;
  color: #606266;
}
.stat-value {
  font-weight: bold;
  color: #409eff;
}
</style>
