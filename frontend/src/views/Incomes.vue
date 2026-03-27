<template>
  <div class="incomes-page">
    <div class="page-header">
      <h2>收入管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增收入
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="年份">
          <el-select v-model="searchForm.year" placeholder="选择年份" @change="handleSearch">
            <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="收入分类">
          <el-select v-model="searchForm.income_category" placeholder="全部分类" clearable @change="handleSearch">
            <el-option label="销售收入" value="sales" />
            <el-option label="服务收入" value="service" />
            <el-option label="退税/返还" value="refund" />
            <el-option label="其他收入" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="searchForm.search" placeholder="客户名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 收入列表 -->
    <el-card class="table-card">
      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="selectedIncomes.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedIncomes.length }} 条收入</el-tag>
        <span class="stat-item">收入合计：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="income_date" label="收入日期" width="110" />
        <el-table-column prop="customer_name" label="付款方" width="150" />
        <el-table-column prop="amount" label="收入金额" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="收入分类" width="100">
          <template #default="{ row }">
            <el-tag>{{ getIncomeCategoryLabel(row.income_category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收入来源" width="100">
          <template #default="{ row }">
            <span v-if="row.source_type === 'invoice'">发票</span>
            <span v-else-if="row.source_type === 'contract'">合同</span>
            <span v-else>其他</span>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="收款方式" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="loadIncomes"
          @size-change="loadIncomes"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑收入' : '新增收入'" width="600px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="收入日期" prop="income_date">
          <el-date-picker v-model="formData.income_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="付款方名称" prop="customer_name">
          <el-input v-model="formData.customer_name" placeholder="付款方名称" />
        </el-form-item>
        <el-form-item label="收入金额" prop="amount">
          <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收入分类" prop="income_category">
          <el-select v-model="formData.income_category" style="width: 100%">
            <el-option label="销售收入" value="sales" />
            <el-option label="服务收入" value="service" />
            <el-option label="退税/返还" value="refund" />
            <el-option label="其他收入" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="收入来源" prop="source_type">
          <el-select v-model="formData.source_type" style="width: 100%">
            <el-option label="发票收入" value="invoice" />
            <el-option label="合同收入" value="contract" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款方式" prop="payment_method">
          <el-select v-model="formData.payment_method" style="width: 100%">
            <el-option label="银行转账" value="bank_transfer" />
            <el-option label="支票" value="check" />
            <el-option label="现金" value="cash" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getIncomes, createIncome, updateIncome, deleteIncome } from '@/api/income'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])
const selectedIncomes = ref([])

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i)

const searchForm = reactive({
  year: currentYear,
  income_category: '',
  search: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  source_type: 'invoice',
  customer_name: '',
  amount: 0,
  income_date: new Date().toISOString().split('T')[0],
  income_year: String(currentYear),
  income_category: 'sales',
  payment_method: '',
  remark: '',
})

const rules = {
  income_date: [{ required: true, message: '请选择收入日期', trigger: 'change' }],
  customer_name: [{ required: true, message: '请输入付款方名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入收入金额', trigger: 'blur' }],
}

const getIncomeCategoryLabel = (category) => {
  const map = {
    sales: '销售收入',
    service: '服务收入',
    refund: '退税/返还',
    other: '其他收入',
  }
  return map[category] || category
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedIncomes.value = selection
}

// 清除选择
const clearSelection = () => {
  selectedIncomes.value = []
  loadIncomes()
}

// 计算选中收入合计
const selectedTotalAmount = computed(() => {
  return selectedIncomes.value.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const loadIncomes = async () => {
  loading.value = true
  try {
    const res = await getIncomes({
      page: pagination.page,
      page_size: pagination.page_size,
      year: searchForm.year,
      income_category: searchForm.income_category,
      search: searchForm.search,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载收入列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadIncomes()
}

const handleReset = () => {
  searchForm.year = currentYear
  searchForm.income_category = ''
  searchForm.search = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    source_type: 'invoice',
    customer_name: '',
    amount: 0,
    income_date: new Date().toISOString().split('T')[0],
    income_year: String(currentYear),
    income_category: 'sales',
    payment_method: '',
    remark: '',
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, { ...row })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除该收入记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteIncome(row.id)
    ElMessage.success('删除成功')
    loadIncomes()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const dataToSubmit = {
          ...formData,
          income_year: String(new Date(formData.income_date).getFullYear())
        }
        if (formData.id) {
          await updateIncome(formData.id, dataToSubmit)
          ElMessage.success('更新成功')
        } else {
          await createIncome(dataToSubmit)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadIncomes()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  loadIncomes()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.search-card { margin-bottom: 20px; }
.table-card { margin-bottom: 20px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
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
