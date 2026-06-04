<template>
  <div class="reimbursements-page">
    <div class="page-header">
      <h2>报销管理</h2>
      <div class="header-actions">
        <el-button @click="showAiImportDrawer = true">
          <el-icon><MagicStick /></el-icon> AI录入报销
        </el-button>
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon> 新增报销单
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="statistics-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">待审核</div>
            <div class="stat-value warning">¥{{ Number(statistics.total_pending_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.pending_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">待支付</div>
            <div class="stat-value primary">¥{{ Number(statistics.total_approved_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.approved_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">已支付</div>
            <div class="stat-value success">¥{{ Number(statistics.total_paid_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.paid_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable @change="handleSearch">
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="pending" />
            <el-option label="已审核" value="approved" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已支付" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用分类">
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
        <el-form-item label="年份">
          <el-select v-model="searchForm.year" placeholder="全部年份" clearable @change="handleSearch">
            <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
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

    <!-- 报销单列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="supplier_name" label="供应商/收款方" width="150" />
        <el-table-column prop="total_amount" label="报销金额" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="费用分类" width="100">
          <template #default="{ row }">
            <el-tag>{{ getCategoryLabel(row.expense_category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="录入人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'draft'">
              <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="success" @click="handleSubmit(row)">提交</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
            <template v-else-if="row.status === 'pending' && isAdmin">
              <el-button link type="success" @click="openApproveDialog(row)">审核通过</el-button>
              <el-button link type="danger" @click="openRejectDialog(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'approved' && isAdmin">
              <el-button link type="success" @click="handlePay(row)">确认支付</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button link type="primary" @click="handleEdit(row)">修改重提</el-button>
              <el-button link type="info" @click="showRejectReason(row)">查看原因</el-button>
            </template>
            <template v-else-if="row.status === 'paid'">
              <el-button link type="info" @click="handleView(row)">查看</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="loadReimbursements"
          @size-change="loadReimbursements"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-drawer
      v-model="showDialog"
      :title="formData.id ? '编辑报销单' : '新增报销单'"
      size="720px"
      direction="rtl"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
        <!-- 收款方信息 -->
        <el-divider content-position="left">收款方信息</el-divider>
        <el-form-item label="供应商/收款方" prop="supplier_name">
          <el-autocomplete
            v-model="formData.supplier_name"
            :fetch-suggestions="fetchSupplierSuggestions"
            placeholder="输入名称自动补全"
            @select="handleSupplierSelect"
            style="width: 100%"
            clearable
          >
            <template #default="{ item }">
              <div class="supplier-suggestion">
                <span class="supplier-name">{{ item.name }}</span>
                <span class="supplier-bank" v-if="item.bank_name">{{ item.bank_name }}</span>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="税号">
              <el-input v-model="formData.supplier_tax_id" placeholder="收款方税号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开户行">
              <el-input v-model="formData.supplier_bank_name" placeholder="开户银行名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号">
              <el-input v-model="formData.supplier_bank_account" placeholder="银行账号" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 金额信息 -->
        <el-divider content-position="left">金额信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="报销金额(不含税)" prop="amount">
              <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税额">
              <el-input-number v-model="formData.tax_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="价税合计">
          <el-input-number v-model="formData.total_amount" :min="0" :precision="2" style="width: 100%" disabled />
        </el-form-item>

        <!-- 分类和关联 -->
        <el-divider content-position="left">分类与关联</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="费用分类" prop="expense_category">
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联发票">
              <el-select v-model="formData.invoice_id" placeholder="选择进项发票（可选）" clearable style="width: 100%">
                <el-option v-for="inv in purchaseInvoices" :key="inv.id" :label="inv.invoice_no" :value="inv.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="关联合同">
          <el-select v-model="formData.contract_id" placeholder="选择合同（可选）" clearable style="width: 100%">
            <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no" :value="c.id" />
          </el-select>
        </el-form-item>

        <!-- 附件上传 -->
        <el-divider content-position="left">附件</el-divider>
        <el-form-item label="发票/票据文件">
          <DocumentUploader
            type="invoice"
            :initial-value="fileInfo"
            :refresh-key="documentUploaderKey"
            :show-ai-parse="false"
            accept-types=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            @change="handleFileChange"
          />
        </el-form-item>

        <!-- 备注 -->
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>

    <!-- 审核通过对话框（可修改金额） -->
    <el-dialog v-model="showApproveDialog" title="审核通过" width="400px">
      <el-form :model="approveForm" label-width="100px">
        <el-form-item label="修改金额">
          <el-input-number v-model="approveForm.amount" :min="0" :precision="2" style="width: 100%" placeholder="不修改则保持原金额" />
        </el-form-item>
        <el-form-item label="修改分类">
          <el-select v-model="approveForm.expense_category" style="width: 100%" placeholder="不修改则保持原分类" clearable>
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleApprove">确认通过</el-button>
      </template>
    </el-dialog>

    <!-- 驳回对话框 -->
    <el-dialog v-model="showRejectDialog" title="驳回报销单" width="400px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="驳回原因" prop="reason">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请填写驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认驳回</el-button>
      </template>
    </el-dialog>
    <AiReimbursementImportDrawer v-model="showAiImportDrawer" @success="handleAiImportSuccess" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import {
  getReimbursements,
  createReimbursement,
  updateReimbursement,
  deleteReimbursement,
  submitReimbursement,
  approveReimbursement,
  rejectReimbursement,
  payReimbursement,
  getReimbursementStatistics,
} from '@/api/reimbursement'
import { getInvoices } from '@/api/invoice'
import { getContracts } from '@/api/contract'
import { searchSuppliers } from '@/api/supplier'
import DocumentUploader from '@/components/DocumentUploader.vue'
import AiReimbursementImportDrawer from '@/components/AiReimbursementImportDrawer.vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const showAiImportDrawer = ref(false)
const showApproveDialog = ref(false)
const showRejectDialog = ref(false)
const formRef = ref(null)
const rejectFormRef = ref(null)
const tableData = ref([])
const purchaseInvoices = ref([])
const contracts = ref([])
const fileInfo = ref(null)
const documentUploaderKey = ref(0)
const statistics = ref({
  total_pending_amount: 0,
  total_approved_amount: 0,
  total_paid_amount: 0,
  pending_count: 0,
  approved_count: 0,
  paid_count: 0,
})

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i)

const searchForm = reactive({
  status: '',
  expense_category: '',
  year: null,
  search: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  supplier_name: '',
  supplier_tax_id: '',
  supplier_bank_name: '',
  supplier_bank_account: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_category: 'other',
  invoice_id: '',
  contract_id: '',
  remark: '',
  file_id: '',
  file_url: '',
})

const approveForm = reactive({
  id: '',
  amount: null,
  expense_category: '',
})

const rejectForm = reactive({
  id: '',
  reason: '',
})

const rules = {
  supplier_name: [{ required: true, message: '请输入供应商/收款方名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入报销金额', trigger: 'blur' }],
}

const rejectRules = {
  reason: [{ required: true, message: '请填写驳回原因', trigger: 'blur' }],
}

// 分类标签映射
const categoryLabels = {
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

// 状态标签映射
const statusLabels = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  rejected: '已驳回',
  paid: '已支付',
}

// 状态颜色映射
const statusTypes = {
  draft: 'info',
  pending: 'warning',
  approved: 'primary',
  rejected: 'danger',
  paid: 'success',
}

const getCategoryLabel = (category) => categoryLabels[category] || category
const getStatusLabel = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || 'info'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

// 收款方自动补全
const fetchSupplierSuggestions = async (queryString, cb) => {
  if (!queryString) {
    cb([])
    return
  }
  try {
    const results = await searchSuppliers(queryString, 10)
    cb(results)
  } catch (error) {
    cb([])
  }
}

// 选择收款方后自动填充信息
const handleSupplierSelect = (item) => {
  formData.supplier_name = item.name
  formData.supplier_tax_id = item.tax_id || ''
  formData.supplier_bank_name = item.bank_name || ''
  formData.supplier_bank_account = item.bank_account || ''
}

// 监听金额变化自动计算合计
watch([() => formData.amount, () => formData.tax_amount], ([amount, tax]) => {
  formData.total_amount = Number(amount || 0) + Number(tax || 0)
}, { immediate: true })

const loadReimbursements = async () => {
  loading.value = true
  try {
    const res = await getReimbursements({
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status,
      expense_category: searchForm.expense_category,
      year: searchForm.year,
      search: searchForm.search,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error('加载报销单列表失败')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const res = await getReimbursementStatistics({ year: searchForm.year })
    statistics.value = res
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadPurchaseInvoices = async () => {
  try {
    const res = await getInvoices({ page_size: 100, invoice_type: 'purchase' })
    purchaseInvoices.value = res.items || []
  } catch (error) {
    console.error('加载发票失败:', error)
  }
}

const loadContracts = async () => {
  try {
    const res = await getContracts({ page_size: 100 })
    contracts.value = res.items || []
  } catch (error) {
    console.error('加载合同失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadReimbursements()
  loadStatistics()
}

const handleReset = () => {
  searchForm.status = ''
  searchForm.expense_category = ''
  searchForm.year = null
  searchForm.search = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    supplier_name: '',
    supplier_tax_id: '',
    supplier_bank_name: '',
    supplier_bank_account: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_category: 'other',
    invoice_id: '',
    contract_id: '',
    remark: '',
    file_id: '',
    file_url: '',
  })
  fileInfo.value = null
  documentUploaderKey.value++
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, {
    id: row.id,
    supplier_name: row.supplier_name,
    supplier_tax_id: row.supplier_tax_id || '',
    supplier_bank_name: row.supplier_bank_name || '',
    supplier_bank_account: row.supplier_bank_account || '',
    amount: Number(row.amount),
    tax_amount: Number(row.tax_amount || 0),
    total_amount: Number(row.total_amount),
    expense_category: row.expense_category,
    invoice_id: row.invoice_id || '',
    contract_id: row.contract_id || '',
    remark: row.remark || '',
    file_id: row.file_id || '',
    file_url: row.file_url || '',
  })
  // 设置文件信息
  if (row.file_id && row.file_url) {
    fileInfo.value = {
      id: row.file_id,
      name: row.supplier_name || '报销单',
      url: row.file_url,
      type: 'pdf',
    }
  } else {
    fileInfo.value = null
  }
  documentUploaderKey.value++
}

// 处理文件变化
const handleFileChange = (file) => {
  fileInfo.value = file
  if (file) {
    formData.file_id = file.id
    formData.file_url = file.url
  } else {
    formData.file_id = ''
    formData.file_url = ''
  }
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          ...formData,
          total_amount: Number(formData.amount) + Number(formData.tax_amount),
        }
        // 移除空字符串字段
        Object.keys(data).forEach(key => {
          if (data[key] === '') {
            data[key] = null
          }
        })
        if (formData.id) {
          await updateReimbursement(formData.id, data)
          ElMessage.success('更新成功')
        } else {
          await createReimbursement(data)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadReimbursements()
        loadStatistics()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleSubmit = async (row) => {
  try {
    await ElMessageBox.confirm('确认提交此报销单进行审核？', '提示', { type: 'info' })
    await submitReimbursement(row.id)
    ElMessage.success('提交成功')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '提交失败')
    }
  }
}

const openApproveDialog = (row) => {
  approveForm.id = row.id
  approveForm.amount = null
  approveForm.expense_category = ''
  showApproveDialog.value = true
}

const handleApprove = async () => {
  try {
    const data = {}
    if (approveForm.amount !== null) data.amount = approveForm.amount
    if (approveForm.expense_category) data.expense_category = approveForm.expense_category
    await approveReimbursement(approveForm.id, data)
    ElMessage.success('审核通过')
    showApproveDialog.value = false
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '审核失败')
  }
}

const openRejectDialog = (row) => {
  rejectForm.id = row.id
  rejectForm.reason = ''
  showRejectDialog.value = true
}

const handleReject = async () => {
  if (!rejectFormRef.value) return
  await rejectFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await rejectReimbursement(rejectForm.id, rejectForm.reason)
        ElMessage.success('已驳回')
        showRejectDialog.value = false
        loadReimbursements()
        loadStatistics()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '驳回失败')
      }
    }
  })
}

const handlePay = async (row) => {
  try {
    await ElMessageBox.confirm('确认支付此报销单？', '提示', { type: 'success' })
    await payReimbursement(row.id)
    ElMessage.success('已确认支付')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '支付确认失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除此报销单？', '提示', { type: 'warning' })
    await deleteReimbursement(row.id)
    ElMessage.success('删除成功')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleView = (row) => {
  ElMessageBox.alert(`
    供应商：${row.supplier_name}
    税号：${row.supplier_tax_id || '未填写'}
    开户行：${row.supplier_bank_name || '未填写'}
    银行账号：${row.supplier_bank_account || '未填写'}
    金额：¥${row.total_amount}
  `, '报销单详情', { type: 'info' })
}

const showRejectReason = (row) => {
  ElMessageBox.alert(row.reject_reason || '无驳回原因', '驳回原因', { type: 'warning' })
}

const handleAiImportSuccess = () => {
  showAiImportDrawer.value = false
  loadReimbursements()
  loadStatistics()
}

onMounted(() => {
  loadReimbursements()
  loadStatistics()
  loadPurchaseInvoices()
  loadContracts()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.statistics-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-value.primary {
  color: #409eff;
}

.stat-value.success {
  color: #67c23a;
}

.stat-count {
  font-size: 12px;
  color: #909399;
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

.supplier-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.supplier-name {
  font-weight: 500;
}

.supplier-bank {
  font-size: 12px;
  color: #909399;
}
</style>