<template>
  <div class="receivables-page">
    <div class="page-header">
      <h2>应收款管理</h2>
      <el-button type="primary" @click="showDialog = true; formData = {}">
        <el-icon><Plus /></el-icon> 新增应收
      </el-button>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="未收款" value="unpaid" />
            <el-option label="部分收款" value="partial" />
            <el-option label="已结清" value="paid" />
            <el-option label="逾期" value="overdue" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="selectedReceivables.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedReceivables.length }} 条应收</el-tag>
        <span class="stat-item">应收合计：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <span class="stat-item">已收合计：<span class="stat-value">¥{{ selectedReceivedAmount.toLocaleString() }}</span></span>
        <span class="stat-item">未收合计：<span class="stat-value">¥{{ selectedUnpaidAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="contract_no" label="关联合同" width="120" />
        <el-table-column prop="amount" label="应收金额" width="110" align="right">
          <template #default="{ row }">¥{{ Number(row.amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="received_amount" label="已收金额" width="110" align="right">
          <template #default="{ row }">¥{{ Number(row.received_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="unpaid_amount" label="未收金额" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.due_date < new Date().toISOString().split('T')[0] ? 'red' : '' }">
              ¥{{ (Number(row.amount) - Number(row.received_amount)).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="应收日期" width="110" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="showPaymentDlg = true; currentReceivable = row">登记收款</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :total="pagination.total" layout="total, sizes, prev, pager, next"
          @current-change="loadReceivables" @size-change="loadReceivables" />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑应收' : '新增应收'" width="500px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="关联合同" prop="contract_id">
          <el-select v-model="formData.contract_id" placeholder="请选择合同" style="width: 100%" @change="handleContractChange">
            <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="应收金额" prop="amount">
          <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="应收日期" prop="due_date">
          <el-date-picker v-model="formData.due_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
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

    <!-- 登记收款对话框 -->
    <el-dialog v-model="showPaymentDlg" title="登记收款" width="450px">
      <el-form :model="paymentForm" ref="paymentFormRef" label-width="80px">
        <el-form-item label="收款金额">
          <el-input-number v-model="paymentForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收款日期">
          <el-date-picker v-model="paymentForm.payment_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="收款方式">
          <el-select v-model="paymentForm.payment_method" style="width: 100%">
            <el-option label="银行转账" value="bank" />
            <el-option label="支票" value="check" />
            <el-option label="现金" value="cash" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="paymentForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPaymentDlg = false">取消</el-button>
        <el-button type="primary" @click="handlePayment" :loading="paymentLoading">确认收款</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getReceivables, createReceivable, updateReceivable, addPayment } from '@/api/receivable'
import { getContracts, getContract } from '@/api/contract'

const loading = ref(false)
const submitting = ref(false)
const paymentLoading = ref(false)
const showDialog = ref(false)
const showPaymentDlg = ref(false)
const formRef = ref(null)
const tableData = ref([])
const contracts = ref([])
const currentReceivable = ref(null)
const selectedReceivables = ref([])

const searchForm = reactive({ status: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const formData = ref({ id: '', contract_id: '', amount: 0, due_date: '', remark: '' })
const paymentForm = ref({ amount: 0, payment_date: new Date().toISOString().split('T')[0], payment_method: 'bank', remark: '' })

const rules = { contract_id: [{ required: true, message: '请选择合同', trigger: 'change' }], amount: [{ required: true, message: '请输入金额', trigger: 'blur' }] }

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedReceivables.value = selection
}

// 清除选择
const clearSelection = () => {
  selectedReceivables.value = []
  loadReceivables()
}

// 计算选中应收款的各项金额
const selectedTotalAmount = computed(() => {
  return selectedReceivables.value.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const selectedReceivedAmount = computed(() => {
  return selectedReceivables.value.reduce((sum, item) => sum + (Number(item.received_amount) || 0), 0)
})

const selectedUnpaidAmount = computed(() => {
  return selectedReceivables.value.reduce((sum, item) => sum + ((Number(item.amount) - Number(item.received_amount)) || 0), 0)
})

const loadReceivables = async () => {
  loading.value = true
  try {
    const res = await getReceivables({ page: pagination.page, page_size: pagination.page_size, ...searchForm })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) { console.error('加载失败:', error) } finally { loading.value = false }
}

const loadContracts = async () => {
  try { const res = await getContracts({ page_size: 100 }); contracts.value = res.items } catch (error) { console.error('加载合同失败:', error) }
}

const handleSearch = () => { pagination.page = 1; loadReceivables() }
const handleReset = () => { searchForm.status = ''; handleSearch() }
const handleEdit = (row) => { showDialog.value = true; formData.value = { ...formData.value, ...row } }

const handleContractChange = async (contractId) => {
  if (!contractId) return
  try {
    const contract = await getContract(contractId)
    if (contract && contract.amount) {
      formData.value.amount = Number(contract.amount)
      await nextTick()
    }
  } catch (error) {
    console.error('获取合同详情失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 过滤空值字段，转换为 null（特别是日期字段）
        const submitData = { ...formData.value }
        if (submitData.due_date === '') { submitData.due_date = null }
        if (submitData.remark === '') { delete submitData.remark }

        if (submitData.id) { await updateReceivable(formData.value.id, submitData); ElMessage.success('更新成功') }
        else { await createReceivable(submitData); ElMessage.success('创建成功') }
        showDialog.value = false; loadReceivables()
      } catch (error) { console.error('提交失败:', error) } finally { submitting.value = false }
    }
  })
}

const handlePayment = async () => {
  if (!currentReceivable.value) return
  paymentLoading.value = true
  try {
    await addPayment(currentReceivable.value.id, paymentForm.value)
    ElMessage.success('收款登记成功')
    showPaymentDlg.value = false; loadReceivables()
  } catch (error) { console.error('登记失败:', error) } finally { paymentLoading.value = false }
}

const getStatusType = (status) => {
  const map = { unpaid: 'warning', partial: 'info', paid: 'success', overdue: 'danger' }
  return map[status] || 'info'
}
const getStatusLabel = (status) => {
  const map = { unpaid: '未收款', partial: '部分收款', paid: '已结清', overdue: '逾期' }
  return map[status] || status
}

onMounted(() => { loadReceivables(); loadContracts() })
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
