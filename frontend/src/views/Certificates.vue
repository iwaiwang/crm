<template>
  <div class="certificates-page">
    <div class="page-header">
      <h2>证书管理</h2>
      <el-button type="primary" @click="openApplyDialog">
        <el-icon><Plus /></el-icon> 申请证书
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable @change="handleSearch">
            <el-option label="待审核" value="pending" />
            <el-option label="已审核" value="approved" />
            <el-option label="已签发" value="active" />
            <el-option label="即将过期" value="expiring_soon" />
            <el-option label="已过期" value="expired" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已吊销" value="revoked" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="searchForm.search" placeholder="医院名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 快速筛选标签 -->
    <div class="filter-tabs">
      <el-radio-group v-model="activeTab" @change="handleTabChange">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="active">已签发</el-radio-button>
        <el-radio-button value="expiring_soon">即将过期</el-radio-button>
        <el-radio-button value="expired">已过期</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 证书列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="cert_serial" label="证书序列号" width="140" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="医院名称" width="160" />
        <el-table-column prop="product_name" label="软件产品" width="160" />
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            <span>{{ row.start_date }}</span>
            <span style="margin: 0 6px; color: #909399">至</span>
            <span>{{ row.end_date }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)" :effect="row.status === 'expired' ? 'dark' : 'light'">
              {{ getStatusLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="applicant_name" label="申请人" width="100" />
        <el-table-column label="剩余天数" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 'active'" :style="{ color: getDaysColor(row) }">
              {{ getDaysRemaining(row) }} 天
            </span>
            <span v-else-if="row.status === 'expired'" style="color: #f56c6c">
              已过期 {{ getDaysOverdue(row) }} 天
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button link type="success" @click="handleApprove(row)">通过</el-button>
              <el-button link type="danger" @click="openRejectDialog(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'approved'">
              <el-button link type="success" @click="handleApprove(row)">签发证书</el-button>
            </template>
            <template v-else-if="row.status === 'active'">
              <el-button link type="primary" @click="handleDownload(row)">下载</el-button>
              <el-button link type="danger" @click="handleRevoke(row)">吊销</el-button>
            </template>
            <template v-else-if="row.status === 'expired'">
              <el-button link type="warning" @click="handleRenew(row)">续期</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-tooltip :content="row.reject_reason" placement="top">
                <el-button link type="info" disabled>已驳回</el-button>
              </el-tooltip>
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
          @current-change="loadCertificates"
          @size-change="loadCertificates"
        />
      </div>
    </el-card>

    <!-- 申请证书抽屉 -->
    <el-drawer
      v-model="showApplyDrawer"
      title="申请数字证书"
      size="520px"
      direction="rtl"
    >
      <el-form :model="applyForm" :rules="applyRules" ref="applyFormRef" label-width="100px">
        <el-form-item label="医院名称" prop="customer_id">
          <el-select v-model="applyForm.customer_id" placeholder="选择医院客户" filterable style="width: 100%">
            <el-option
              v-for="c in customers"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="软件产品" prop="product_name">
          <el-input v-model="applyForm.product_name" placeholder="如：无纸化病案归档系统" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="applyForm.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="有效期" prop="duration_months">
          <el-select v-model="applyForm.duration_months" style="width: 100%">
            <el-option label="3 个月" :value="3" />
            <el-option label="6 个月" :value="6" />
            <el-option label="12 个月" :value="12" />
            <el-option label="24 个月" :value="24" />
            <el-option label="36 个月" :value="36" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-input :model-value="computedEndDate" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDrawer = false">取消</el-button>
        <el-button type="primary" @click="handleApplySubmit" :loading="submitting">提交申请</el-button>
      </template>
    </el-drawer>

    <!-- 驳回对话框 -->
    <el-dialog v-model="showRejectDialog" title="驳回申请" width="450px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef">
        <el-form-item label="驳回原因" prop="reason">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入驳回原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleRejectSubmit">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getCertificates, createCertificate, approveCertificate, rejectCertificate, revokeCertificate, renewCertificate, downloadCertificate } from '@/api/certificate'
import { getCustomers } from '@/api/customer'

const loading = ref(false)
const submitting = ref(false)
const showApplyDrawer = ref(false)
const showRejectDialog = ref(false)
const rejectFormRef = ref(null)
const applyFormRef = ref(null)
const activeTab = ref('all')

const tableData = ref([])
const customers = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const searchForm = reactive({
  status: '',
  search: '',
})

const applyForm = reactive({
  customer_id: '',
  product_name: '',
  start_date: new Date().toISOString().split('T')[0],
  duration_months: 12,
})

const rejectForm = reactive({
  certificateId: '',
  reason: '',
})

const applyRules = {
  customer_id: [{ required: true, message: '请选择医院客户', trigger: 'change' }],
  product_name: [{ required: true, message: '请输入软件产品名称', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
}

const rejectRules = {
  reason: [{ required: true, message: '请输入驳回原因', trigger: 'blur' }],
}

const computedEndDate = computed(() => {
  if (!applyForm.start_date) return ''
  const d = new Date(applyForm.start_date)
  d.setMonth(d.getMonth() + applyForm.duration_months)
  return d.toISOString().split('T')[0]
})

const loadCertificates = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    const tabStatus = activeTab.value
    if (tabStatus !== 'all') params.status = tabStatus
    if (searchForm.status) params.status = searchForm.status
    if (searchForm.search) params.search = searchForm.search
    const res = await getCertificates(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (e) {
    console.error('加载证书列表失败:', e)
    ElMessage.error('加载证书列表失败')
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    const res = await getCustomers({ page: 1, page_size: 100 })
    customers.value = res.items || []
  } catch { /* ignore */ }
}

const getDaysRemaining = (row) => {
  const end = new Date(row.end_date)
  const now = new Date()
  return Math.max(0, Math.ceil((end - now) / (1000 * 60 * 60 * 24)))
}

const getDaysOverdue = (row) => {
  const end = new Date(row.end_date)
  const now = new Date()
  return Math.max(0, Math.ceil((now - end) / (1000 * 60 * 60 * 24)))
}

const getDaysColor = (row) => {
  const remaining = getDaysRemaining(row)
  if (remaining <= 30) return '#e6a23c'
  return '#67c23a'
}

const getStatusType = (row) => {
  if (row.status === 'active' && getDaysRemaining(row) <= 30 && getDaysRemaining(row) > 0) return 'warning'
  const map = {
    pending: 'warning', approved: 'primary', active: 'success',
    expired: 'danger', rejected: 'info', revoked: 'info',
  }
  return map[row.status] || 'info'
}

const getStatusLabel = (row) => {
  if (row.status === 'active' && getDaysRemaining(row) <= 30 && getDaysRemaining(row) > 0) return '即将过期'
  const map = {
    pending: '待审核', approved: '已审核', active: '已签发',
    expired: '已过期', rejected: '已驳回', revoked: '已吊销',
  }
  return map[row.status] || row.status
}

const handleTabChange = () => {
  searchForm.status = ''
  searchForm.search = ''
  pagination.page = 1
  loadCertificates()
}

const handleSearch = () => {
  pagination.page = 1
  loadCertificates()
}

const handleReset = () => {
  searchForm.status = ''
  searchForm.search = ''
  activeTab.value = 'all'
  handleSearch()
}

const openApplyDialog = () => {
  showApplyDrawer.value = true
  applyForm.customer_id = ''
  applyForm.product_name = ''
  applyForm.start_date = new Date().toISOString().split('T')[0]
  applyForm.duration_months = 12
}

const handleApplySubmit = async () => {
  if (!applyFormRef.value) return
  await applyFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await createCertificate({ ...applyForm })
      ElMessage.success('证书申请已提交')
      showApplyDrawer.value = false
      loadCertificates()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '提交失败')
    } finally {
      submitting.value = false
    }
  })
}

const openRejectDialog = (row) => {
  rejectForm.certificateId = row.id
  rejectForm.reason = ''
  showRejectDialog.value = true
}

const handleRejectSubmit = async () => {
  if (!rejectFormRef.value) return
  await rejectFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await rejectCertificate(rejectForm.certificateId, rejectForm.reason)
      ElMessage.success('已驳回')
      showRejectDialog.value = false
      loadCertificates()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '驳回失败')
    }
  })
}

const handleApprove = async (row) => {
  const level = row.status === 'approved' ? '签发证书' : '通过申请'
  const msg = row.status === 'approved'
    ? '确认签发该证书吗？将生成 RSA 密钥对和 X.509 数字证书。'
    : '确认通过该申请吗？'
  try {
    await ElMessageBox.confirm(msg, '确认操作', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'success'
    })
    await approveCertificate(row.id)
    ElMessage.success(row.status === 'approved' ? '证书已签发' : '已通过，等待二级审批')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认吊销 ${row.customer_name} 的证书吗？吊销后医院端软件将无法通过验证。`,
      '确认吊销',
      { confirmButtonText: '确定吊销', cancelButtonText: '取消', type: 'warning' }
    )
    await revokeCertificate(row.id)
    ElMessage.success('证书已吊销')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const handleDownload = async (row) => {
  try {
    const blob = await downloadCertificate(row.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `certificate_${row.cert_serial}.zip`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

const handleRenew = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认为 ${row.customer_name} 的证书申请续期吗？将创建新的申请记录。`,
      '确认续期',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' }
    )
    await renewCertificate(row.id)
    ElMessage.success('续期申请已提交')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(() => {
  loadCertificates()
  loadCustomers()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.search-card { margin-bottom: 16px; }
.filter-tabs { margin-bottom: 16px; }
.table-card { margin-bottom: 20px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
