<template>
  <div class="expenses-page">
    <div class="page-header">
      <h2>支出管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增支出
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
        <el-form-item label="支出分类">
          <el-select v-model="searchForm.expense_category" placeholder="全部分类" clearable @change="handleSearch">
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="房租" value="rent" />
            <el-option label="水电" value="utilities" />
            <el-option label="工资" value="salary" />
            <el-option label="市场推广" value="marketing" />
            <el-option label="软件服务" value="software" />
            <el-option label="维修维护" value="maintenance" />
            <el-option label="培训" value="training" />
            <el-option label="业务招待" value="entertainment" />
            <el-option label="物流快递" value="logistics" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="searchForm.search" placeholder="供应商名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 支出列表 -->
    <el-card class="table-card">
      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="selectedExpenses.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedExpenses.length }} 条支出</el-tag>
        <span class="stat-item">支出合计：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="expense_date" label="支出日期" width="110" />
        <el-table-column prop="supplier_name" label="供应商/收款方" width="150" />
        <el-table-column prop="total_amount" label="支出金额" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="支出分类" width="100">
          <template #default="{ row }">
            <el-tag>{{ getExpenseCategoryLabel(row.expense_category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
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
          @current-change="loadExpenses"
          @size-change="loadExpenses"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑支出' : '新增支出'" width="600px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="支出日期" prop="expense_date">
          <el-date-picker v-model="formData.expense_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="供应商/收款方" prop="supplier_name">
          <el-input v-model="formData.supplier_name" placeholder="供应商/收款方名称" />
        </el-form-item>
        <el-form-item label="支出金额" prop="amount">
          <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" placeholder="不含税金额" />
        </el-form-item>
        <el-form-item label="税额" prop="tax_amount">
          <el-input-number v-model="formData.tax_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="价税合计" prop="total_amount">
          <el-input-number v-model="formData.total_amount" :min="0" :precision="2" style="width: 100%" disabled />
        </el-form-item>
        <el-form-item label="支出分类" prop="expense_category">
          <el-select v-model="formData.expense_category" style="width: 100%">
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="房租" value="rent" />
            <el-option label="水电" value="utilities" />
            <el-option label="工资" value="salary" />
            <el-option label="市场推广" value="marketing" />
            <el-option label="软件服务" value="software" />
            <el-option label="维修维护" value="maintenance" />
            <el-option label="培训" value="training" />
            <el-option label="业务招待" value="entertainment" />
            <el-option label="物流快递" value="logistics" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式" prop="payment_method">
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
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getExpenses, createExpense, updateExpense, deleteExpense } from '@/api/expense'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])
const selectedExpenses = ref([])

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i)

const searchForm = reactive({
  year: currentYear,
  expense_category: '',
  search: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  supplier_name: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_date: new Date().toISOString().split('T')[0],
  expense_year: String(currentYear),
  expense_category: 'other',
  payment_method: '',
  remark: '',
})

const rules = {
  expense_date: [{ required: true, message: '请选择支出日期', trigger: 'change' }],
  supplier_name: [{ required: true, message: '请输入供应商/收款方名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入支出金额', trigger: 'blur' }],
}

// 支出分类标签映射
const expenseCategoryLabels = {
  catering: '餐饮',
  travel: '差旅',
  procurement: '采购',
  office: '办公',
  rent: '房租',
  utilities: '水电',
  salary: '工资',
  marketing: '市场推广',
  software: '软件服务',
  maintenance: '维修维护',
  training: '培训',
  entertainment: '业务招待',
  logistics: '物流快递',
  other: '其他',
}

const getExpenseCategoryLabel = (category) => {
  return expenseCategoryLabels[category] || category
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedExpenses.value = selection
}

// 清除选择
const clearSelection = () => {
  selectedExpenses.value = []
  loadExpenses()
}

// 计算选中支出合计
const selectedTotalAmount = computed(() => {
  return selectedExpenses.value.reduce((sum, item) => sum + (Number(item.total_amount) || 0), 0)
})

// 监听金额变化，自动计算价税合计
watch([() => formData.amount, () => formData.tax_amount], ([amount, taxAmount]) => {
  formData.total_amount = Number(amount) + Number(taxAmount)
}, { immediate: true })

const loadExpenses = async () => {
  loading.value = true
  try {
    const res = await getExpenses({
      page: pagination.page,
      page_size: pagination.page_size,
      year: searchForm.year,
      expense_category: searchForm.expense_category,
      search: searchForm.search,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载支出列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadExpenses()
}

const handleReset = () => {
  searchForm.year = currentYear
  searchForm.expense_category = ''
  searchForm.search = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    supplier_name: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_date: new Date().toISOString().split('T')[0],
    expense_year: String(currentYear),
    expense_category: 'other',
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
    await ElMessageBox.confirm('确认删除该支出记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteExpense(row.id)
    ElMessage.success('删除成功')
    loadExpenses()
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
          expense_year: String(new Date(formData.expense_date).getFullYear()),
          total_amount: Number(formData.amount) + Number(formData.tax_amount)
        }
        if (formData.id) {
          await updateExpense(formData.id, dataToSubmit)
          ElMessage.success('更新成功')
        } else {
          await createExpense(dataToSubmit)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadExpenses()
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
  loadExpenses()
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
