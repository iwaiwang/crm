<template>
  <div class="invoices-page">
    <div class="page-header">
      <h2>发票管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增发票
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="类型">
          <el-radio-group v-model="searchForm.invoice_type" @change="handleSearch">
            <el-radio value="all">全部</el-radio>
            <el-radio value="sales">销项发票</el-radio>
            <el-radio value="purchase">进项发票</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="发票号">
          <el-input v-model="searchForm.search" placeholder="发票号码" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable @keyup.enter="handleSearch">
            <el-option label="正常" value="normal" />
            <el-option label="作废" value="void" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 发票列表 -->
    <el-card class="table-card">
      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="selectedInvoices.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedInvoices.length }} 张发票</el-tag>
        <span class="stat-item">合计金额：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="invoice_no" label="发票号码" width="130" />
        <el-table-column prop="buyer_name" label="购买方" width="150" />
        <el-table-column prop="seller_name" label="销售方" width="150" />
        <el-table-column prop="total_amount" label="发票金额（含税）" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'special' ? 'warning' : ''">
              {{ row.type === 'special' ? '专票' : '普票' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发票类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.invoice_type === 'sales' ? 'success' : 'info'">
              {{ row.invoice_type === 'sales' ? '销项' : '进项' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="issue_date" label="开票日期" width="110" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
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
          @current-change="loadInvoices"
          @size-change="loadInvoices"
        />
      </div>
    </el-card>

    <!-- 对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑发票' : '新增发票'" width="700px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="发票号码" prop="invoice_no">
          <el-input v-model="formData.invoice_no" placeholder="请输入发票号码" />
        </el-form-item>
        <el-form-item label="关联合同" prop="contract_id">
          <el-select v-model="formData.contract_id" placeholder="请选择合同（可选）" clearable style="width: 100%">
            <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="含税金额" prop="total_amount">
              <el-input-number v-model="formData.total_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" prop="tax_rate">
              <el-select v-model="formData.tax_rate" style="width: 100%">
                <el-option label="1%" :value="1" />
                <el-option label="3%" :value="3" />
                <el-option label="5%" :value="5" />
                <el-option label="6%" :value="6" />
                <el-option label="11%" :value="11" />
                <el-option label="13%" :value="13" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="type">
              <el-radio-group v-model="formData.type">
                <el-radio value="normal">普票</el-radio>
                <el-radio value="special">专票</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="方向" prop="invoice_type">
              <el-radio-group v-model="formData.invoice_type" @change="fillCompanyInfo">
                <el-radio value="sales">销项发票</el-radio>
                <el-radio value="purchase">进项发票</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="开票日期" prop="issue_date">
          <el-date-picker v-model="formData.issue_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <!-- 状态字段：仅编辑时显示，新增时默认为正常 -->
        <el-form-item v-if="formData.id" label="状态" prop="status">
          <el-select v-model="formData.status" style="width: 100%">
            <el-option label="正常" value="normal" />
            <el-option label="作废" value="void" />
          </el-select>
        </el-form-item>
        <el-form-item label="购买方" prop="buyer_name">
          <el-input v-model="formData.buyer_name" :disabled="formData.invoice_type === 'purchase'" placeholder="购买方名称" />
        </el-form-item>
        <el-form-item label="购买方税号" prop="buyer_tax_id">
          <el-input v-model="formData.buyer_tax_id" :disabled="formData.invoice_type === 'purchase'" placeholder="购买方税号" />
        </el-form-item>
        <el-form-item label="销售方" prop="seller_name">
          <el-input v-model="formData.seller_name" :disabled="formData.invoice_type === 'sales'" placeholder="销售方名称" />
        </el-form-item>
        <el-form-item label="销售方税号" prop="seller_tax_id">
          <el-input v-model="formData.seller_tax_id" :disabled="formData.invoice_type === 'sales'" placeholder="销售方税号" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
        <!-- 发票文件上传和 AI 解析 -->
        <el-form-item label="发票文件">
          <DocumentUploader
            type="invoice"
            :initial-value="fileInfo"
            :refresh-key="documentUploaderKey"
            @change="handleFileChange"
            @ai-result="handleAiResult"
          />
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
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getInvoices, getInvoice, createInvoice, updateInvoice, deleteInvoice, checkInvoiceDuplicate } from '@/api/invoice'
import { getContracts } from '@/api/contract'
import { getCompanyInfo } from '@/api/setting'
import DocumentUploader from '@/components/DocumentUploader.vue'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])
const contracts = ref([])
const companyInfo = ref({
  company_name: '',
  company_tax_id: '',
})
const fileInfo = ref(null)
const documentUploaderKey = ref(0)
const selectedInvoices = ref([])

const searchForm = reactive({ search: '', status: '', invoice_type: 'all' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const formData = reactive({
  id: '', invoice_no: '',
  contract_id: '', total_amount: 0, tax_rate: 6,
  type: 'normal', invoice_type: 'sales', issue_date: '', status: 'normal',
  buyer_name: '', buyer_tax_id: '', seller_name: '', seller_tax_id: '',
  remark: '', file_id: '', file_url: '', ai_parsed: false,
})

const rules = {
  invoice_no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedInvoices.value = selection
}

// 清除选择
const clearSelection = () => {
  if (tableData.value.length > 0) {
    // 使用 nextTick 确保表格渲染完成后清除
    setTimeout(() => {
      const table = document.querySelector('.el-table')
      if (table && table.__vue_app__) {
        table.dispatchEvent(new CustomEvent('clearSelection'))
      }
    }, 0)
  }
  // 直接清空数组
  selectedInvoices.value = []
  // 调用表格的清除选择方法
  loadInvoices()
}

// 计算选中发票的总金额
const selectedTotalAmount = computed(() => {
  return selectedInvoices.value.reduce((sum, invoice) => {
    return sum + (Number(invoice.total_amount) || 0)
  }, 0)
})

// 加载公司信息
const loadCompanyInfo = async () => {
  try {
    const res = await getCompanyInfo()
    companyInfo.value = {
      company_name: res.company_name || '',
      company_tax_id: res.company_tax_id || '',
    }
  } catch (error) {
    console.error('加载公司信息失败:', error)
  }
}

const loadInvoices = async () => {
  loading.value = true
  try {
    const res = await getInvoices({ page: pagination.page, page_size: pagination.page_size, ...searchForm })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const loadContracts = async () => {
  try {
    const res = await getContracts({ page_size: 100 })
    contracts.value = res.items
  } catch (error) {
    console.error('加载合同失败:', error)
  }
}

const handleSearch = () => { pagination.page = 1; loadInvoices() }
const handleReset = () => { searchForm.search = ''; searchForm.status = ''; searchForm.invoice_type = 'all'; handleSearch() }

// 打开新增对话框
const openAddDialog = () => {
  showDialog.value = true
  // 使用 Object.assign 重置 formData，保持响应性
  Object.assign(formData, {
    id: '', invoice_no: '',
    contract_id: '', total_amount: 0, tax_rate: 6,
    type: 'normal', invoice_type: 'sales', issue_date: '', status: 'normal',
    buyer_name: '', buyer_tax_id: '', seller_name: '', seller_tax_id: '',
    remark: '', file_id: '', file_url: '', ai_parsed: false,
  })
  fileInfo.value = null
  documentUploaderKey.value++

  // 手动填充公司信息
  fillCompanyInfo('sales')
}

// 填充公司信息
const fillCompanyInfo = (invoiceType) => {
  if (formData.id) return // 编辑模式不填充
  if (!companyInfo.value.company_name) return // 公司信息未加载

  if (invoiceType === 'sales') {
    formData.seller_name = companyInfo.value.company_name
    formData.seller_tax_id = companyInfo.value.company_tax_id
    formData.buyer_name = ''
    formData.buyer_tax_id = ''
  } else if (invoiceType === 'purchase') {
    formData.buyer_name = companyInfo.value.company_name
    formData.buyer_tax_id = companyInfo.value.company_tax_id
    formData.seller_name = ''
    formData.seller_tax_id = ''
  }
}

// 监听发票类型变化
watch(() => formData.invoice_type, (newType) => {
  fillCompanyInfo(newType)
}, { immediate: true })

const handleEdit = async (row) => {
  showDialog.value = true
  // 获取发票详情，确保字段完整
  try {
    const detail = await getInvoice(row.id)
    // 使用 Object.assign 重置 formData，保持响应性
    Object.assign(formData, {
      id: detail.id || '',
      invoice_no: detail.invoice_no || '',
      contract_id: detail.contract_id || '',
      total_amount: detail.total_amount ? parseFloat(detail.total_amount) : 0,
      tax_rate: detail.tax_rate ? parseFloat(detail.tax_rate) : 6,
      type: detail.type || 'normal',
      invoice_type: detail.invoice_type || 'sales',
      issue_date: detail.issue_date || '',
      status: detail.status || 'normal',
      buyer_name: detail.buyer_name || '',
      buyer_tax_id: detail.buyer_tax_id || '',
      seller_name: detail.seller_name || '',
      seller_tax_id: detail.seller_tax_id || '',
      remark: detail.remark || '',
      file_id: detail.file_id || '',
      file_url: detail.file_url || '',
      ai_parsed: detail.ai_parsed || false,
    })
    // 设置文件信息
    if (detail.file_id && detail.file_url) {
      fileInfo.value = {
        id: detail.file_id,
        name: detail.invoice_no || '发票',
        url: detail.file_url,
        type: 'pdf',
      }
    } else {
      fileInfo.value = null
    }
  } catch (error) {
    console.error('加载发票详情失败:', error)
    ElMessage.error('加载发票详情失败')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定要删除该发票吗？', '提示', { type: 'warning' })
  try {
    await deleteInvoice(row.id)
    ElMessage.success('删除成功')
    loadInvoices()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      // 检查发票号码是否重复（新增时检查，编辑时排除自己）
      if (formData.invoice_no) {
        try {
          const { data } = await checkInvoiceDuplicate(formData.invoice_no, formData.id || null)
          if (data.duplicate) {
            ElMessage.error(data.message || '这张发票已经保存了')
            return
          }
        } catch (error) {
          // 404 表示后端没有这个接口（可能是旧版本），继续提交让后端校验
          if (error.response?.status !== 404) {
            console.error('检查发票号码失败:', error)
          }
          // 其他错误继续提交流程，让后端进行重复校验
        }
      }

      submitting.value = true
      try {
        // 只提交后端需要的字段
        const dataToSubmit = {
          invoice_no: formData.invoice_no || null,
          contract_id: formData.contract_id || null,
          total_amount: formData.total_amount ? String(formData.total_amount) : null,
          tax_rate: String(formData.tax_rate),
          type: formData.type,
          invoice_type: formData.invoice_type,
          issue_date: formData.issue_date || null,
          status: formData.status,
          remark: formData.remark || null,
          // 购买方和销售方信息
          buyer_name: formData.buyer_name || null,
          buyer_tax_id: formData.buyer_tax_id || null,
          seller_name: formData.seller_name || null,
          seller_tax_id: formData.seller_tax_id || null,
        }
        if (fileInfo.value) {
          dataToSubmit.file_id = fileInfo.value.id
          dataToSubmit.file_url = fileInfo.value.url
        }

        // 移除空字符串字段
        Object.keys(dataToSubmit).forEach(key => {
          if (dataToSubmit[key] === '') {
            dataToSubmit[key] = null
          }
        })

        if (formData.id) {
          await updateInvoice(formData.id, dataToSubmit)
          ElMessage.success('更新成功')
        } else {
          await createInvoice(dataToSubmit)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadInvoices()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
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

// 处理 AI 解析结果
const handleAiResult = (result) => {
  console.log('=== AI 解析结果开始 ===')
  console.log('完整 result:', JSON.stringify(result, null, 2))

  if (!result.data) {
    console.error('AI 解析结果中没有 data 字段')
    return
  }

  const data = result.data
  console.log('data 对象内容:', JSON.stringify(data, null, 2))
  console.log('data.invoice_number:', data.invoice_number)
  console.log('data.invoice_code:', data.invoice_code)
  console.log('data.tax_rate:', data.tax_rate, '类型:', typeof data.tax_rate)
  console.log('当前 formData  sebelum:', JSON.stringify(formData, null, 2))

  // 填充表单字段 - 注意字段名映射
  if (data.invoice_number) formData.invoice_no = data.invoice_number
  if (data.invoice_date) formData.issue_date = data.invoice_date
  if (data.total_amount) formData.total_amount = parseFloat(data.total_amount)

  // 处理税率：优先使用 tax_rate，如果没有则通过 amount 和 tax_amount 计算
  if (data.tax_rate) {
    let taxRate = data.tax_rate
    if (typeof taxRate === 'string') {
      taxRate = parseFloat(taxRate.replace('%', ''))
    } else if (taxRate < 1) {
      taxRate = taxRate * 100
    }
    formData.tax_rate = Math.round(taxRate) // 取整为整数
    console.log('使用 data.tax_rate:', taxRate, '->', formData.tax_rate)
  } else if (data.amount && data.tax_amount) {
    // 通过金额和税额计算税率
    const amount = parseFloat(data.amount)
    const taxAmount = parseFloat(data.tax_amount)
    if (amount > 0 && taxAmount > 0) {
      const calculatedRate = (taxAmount / amount) * 100
      // 四舍五入保留 2 位小数，避免浮点数精度问题
      formData.tax_rate = Math.round(calculatedRate * 100) / 100
      console.log('通过 amount 和 tax_amount 计算税率:', calculatedRate, '->', formData.tax_rate)
    } else {
      console.log('没有收到税率数据，使用默认值')
    }
  } else {
    console.log('没有收到税率数据，使用默认值')
  }
  if (data.invoice_type) {
    // 根据发票类型设置专票/普票
    // 后端可能返回：'special'/'normal' 或 '增值税专用发票'/'增值税普通发票' 等
    if (data.invoice_type === 'special' || data.invoice_type.includes('专用')) {
      formData.type = 'special'
    } else if (data.invoice_type === 'normal' || data.invoice_type.includes('普通')) {
      formData.type = 'normal'
    }
  }
  if (data.buyer_name) formData.buyer_name = data.buyer_name
  if (data.buyer_tax_id) formData.buyer_tax_id = data.buyer_tax_id
  if (data.seller_name) formData.seller_name = data.seller_name
  if (data.seller_tax_id) formData.seller_tax_id = data.seller_tax_id
  if (data.remarks) formData.remark = data.remarks

  // 标记为 AI 解析
  formData.ai_parsed = true
  formData.parse_confidence = result.confidence

  console.log('填充后的 formData:', JSON.stringify(formData, null, 2))
  console.log('=== AI 解析结果结束 ===')

  ElMessage.success('识别成功')
}

const getStatusType = (status) => {
  const map = { normal: 'success', void: 'info' }
  return map[status] || ''
}
const getStatusLabel = (status) => {
  const map = { normal: '正常', void: '作废' }
  return map[status] || status
}

onMounted(async () => {
  await loadCompanyInfo()
  loadInvoices()
  loadContracts()
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
  padding: 12px 16px;
  background-color: #f0f9ff;
  border-radius: 6px;
  margin-bottom: 16px;
  border: 1px solid #bae6ff;
}

.stat-item {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-weight: bold;
  color: #409eff;
  font-size: 16px;
}
</style>
