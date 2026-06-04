<template>
  <el-drawer
    :model-value="modelValue"
    title="AI录入报销单"
    size="60%"
    destroy-on-close
    class="ai-reimbursement-drawer"
    @close="handleClose"
  >
    <div class="ai-import-shell">
      <section class="hero-panel">
        <div class="hero-copy">
          <span class="hero-kicker">SMART EXPENSE</span>
          <h3>把进项发票拖进来，系统会自动识别票面信息，帮你生成报销单草稿。</h3>
          <p>识别后可直接确认录入，也可以同时创建收款方信息方便后续打款。</p>
        </div>
        <el-steps :active="activeStep" simple class="hero-steps">
          <el-step title="上传发票" />
          <el-step title="AI识别" />
          <el-step title="确认录入" />
        </el-steps>
      </section>

      <div class="content-grid">
        <section class="upload-column">
          <div class="panel-heading">
            <span>发票文件</span>
            <el-tag v-if="fileInfo?.name" type="success" effect="plain">已上传</el-tag>
          </div>
          <DocumentUploader
            type="invoice"
            :show-ai-parse="false"
            :initial-value="fileInfo"
            :refresh-key="uploaderRefreshKey"
            @change="handleFileChange"
          />

          <div class="file-summary" v-if="fileInfo">
            <div class="summary-item">
              <span>文件名</span>
              <strong>{{ fileInfo.name }}</strong>
            </div>
          </div>

          <div class="analysis-box" v-loading="previewLoading">
            <div class="analysis-head">
              <span>AI分析状态</span>
              <el-button text type="primary" :disabled="!fileInfo || previewLoading" @click="runPreview">
                重新识别
              </el-button>
            </div>
            <p class="analysis-status">{{ previewStatus }}</p>
            <el-alert
              v-if="summaryActions.length"
              type="info"
              :closable="false"
              show-icon
              title="本次建议动作"
            >
              <div class="candidate-line">{{ summaryActions.join(' / ') }}</div>
            </el-alert>
          </div>
        </section>

        <section class="form-column">
          <div class="panel-heading">
            <span>报销单信息</span>
            <div class="header-tags">
              <el-tag v-if="form.parse_confidence" effect="dark">
                置信度 {{ Math.round(form.parse_confidence * 100) }}%
              </el-tag>
            </div>
          </div>

          <el-form :model="form" label-width="100px" class="reimbursement-form">
            <!-- 收款方信息 -->
            <el-divider content-position="left">收款方信息</el-divider>
            <el-form-item label="供应商名称" required>
              <el-input v-model="form.supplier_name" placeholder="供应商/收款方名称" />
            </el-form-item>
            <el-form-item label="税号">
              <el-input v-model="form.supplier_tax_id" placeholder="收款方税号" />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="开户行">
                  <el-input v-model="form.supplier_bank_name" placeholder="开户银行名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="银行账号">
                  <el-input v-model="form.supplier_bank_account" placeholder="银行账号" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 金额信息 -->
            <el-divider content-position="left">金额信息</el-divider>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="发票号码">
                  <el-input v-model="form.invoice_no" placeholder="发票号码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="开票日期">
                  <el-date-picker
                    v-model="form.issue_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="费用分类">
                  <el-select v-model="form.expense_category" style="width: 100%">
                    <el-option v-for="item in expenseCategories" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="不含税金额">
                  <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="税额">
                  <el-input-number v-model="form.tax_amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="价税合计">
                  <el-input-number v-model="form.total_amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="补充说明" />
            </el-form-item>
          </el-form>

          <!-- 创建收款方选项 -->
          <div class="linkage-panel">
            <div class="payment-switch">
              <div>
                <strong>同时创建收款方</strong>
                <p>如果勾选，系统会在确认录入报销单的同时，把收款方信息保存下来，方便后续打款时直接选择。</p>
              </div>
              <el-switch v-model="createSupplier" />
            </div>
          </div>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <div class="footer-summary">
          <span>{{ summaryActions.join(' / ') || '将创建 1 张报销单' }}</span>
        </div>
        <div class="footer-actions">
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" :loading="submitting" :disabled="!canConfirm" @click="confirmImport">
            确认录入
          </el-button>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import DocumentUploader from '@/components/DocumentUploader.vue'
import { previewAiReimbursementImport, confirmAiReimbursementImport } from '@/api/reimbursement'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'success'])

const uploaderRefreshKey = ref(0)
const fileInfo = ref(null)
const previewLoading = ref(false)
const previewReady = ref(false)
const submitting = ref(false)
const summaryActions = ref([])

const expenseCategories = [
  { label: '餐饮', value: 'catering' },
  { label: '差旅', value: 'travel' },
  { label: '采购', value: 'procurement' },
  { label: '办公', value: 'office' },
  { label: '房租', value: 'rent' },
  { label: '水电', value: 'utilities' },
  { label: '工资', value: 'salary' },
  { label: '市场推广', value: 'marketing' },
  { label: '软件服务', value: 'software' },
  { label: '维修维护', value: 'maintenance' },
  { label: '培训', value: 'training' },
  { label: '业务招待', value: 'entertainment' },
  { label: '物流快递', value: 'logistics' },
  { label: '其他', value: 'other' },
]

const form = reactive({
  invoice_no: '',
  invoice_code: '',
  invoice_number: '',
  supplier_name: '',
  supplier_tax_id: '',
  supplier_bank_name: '',
  supplier_bank_account: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_category: 'other',
  issue_date: '',
  remark: '',
  file_id: '',
  file_url: '',
  ai_parsed: true,
  parse_confidence: null,
})

const createSupplier = ref(false)

const normalizeText = (value) => (typeof value === 'string' ? value.trim() : '')
const toNumber = (value) => Number(value || 0)

const activeStep = computed(() => {
  if (!fileInfo.value) return 0
  if (!previewReady.value) return 1
  return 2
})

const previewStatus = computed(() => {
  if (previewLoading.value) return 'AI 正在识别发票字段，请稍候...'
  if (previewReady.value) return 'AI 草稿已准备好，你可以直接确认，也可以先调整金额和收款方信息。'
  if (fileInfo.value) return '文件已上传，准备开始识别。'
  return '先上传发票文件，系统会自动进入识别流程。'
})

const canConfirm = computed(() => {
  if (!fileInfo.value || !normalizeText(form.supplier_name)) return false
  return true
})

const resetState = () => {
  fileInfo.value = null
  previewLoading.value = false
  previewReady.value = false
  submitting.value = false
  summaryActions.value = []
  uploaderRefreshKey.value += 1
  Object.assign(form, {
    invoice_no: '',
    invoice_code: '',
    invoice_number: '',
    supplier_name: '',
    supplier_tax_id: '',
    supplier_bank_name: '',
    supplier_bank_account: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_category: 'other',
    issue_date: '',
    remark: '',
    file_id: '',
    file_url: '',
    ai_parsed: true,
    parse_confidence: null,
  })
  createSupplier.value = false
}

const mapPreviewToState = (preview) => {
  const reimbursementData = preview.reimbursement || {}
  Object.assign(form, {
    invoice_no: reimbursementData.invoice_no || '',
    invoice_code: reimbursementData.invoice_code || '',
    invoice_number: reimbursementData.invoice_number || '',
    supplier_name: reimbursementData.supplier_name || '',
    supplier_tax_id: reimbursementData.supplier_tax_id || '',
    supplier_bank_name: reimbursementData.supplier_bank_name || '',
    supplier_bank_account: reimbursementData.supplier_bank_account || '',
    amount: toNumber(reimbursementData.amount),
    tax_amount: toNumber(reimbursementData.tax_amount),
    total_amount: toNumber(reimbursementData.total_amount),
    expense_category: reimbursementData.expense_category || 'other',
    issue_date: reimbursementData.issue_date || '',
    remark: reimbursementData.remark || '',
    file_id: reimbursementData.file_id || fileInfo.value?.id || '',
    file_url: reimbursementData.file_url || fileInfo.value?.url || '',
    ai_parsed: reimbursementData.ai_parsed !== false,
    parse_confidence: reimbursementData.parse_confidence ?? null,
  })

  summaryActions.value = preview.suggested_actions || []
  previewReady.value = true
}

const runPreview = async () => {
  if (!fileInfo.value?.id) return
  previewLoading.value = true
  try {
    const preview = await previewAiReimbursementImport(fileInfo.value.id)
    mapPreviewToState(preview)
  } catch (error) {
    console.error('AI 解析发票失败:', error)
    ElMessage.error(error.response?.data?.detail || 'AI 解析发票失败')
  } finally {
    previewLoading.value = false
  }
}

const handleFileChange = async (file) => {
  fileInfo.value = file
  if (!file) {
    resetState()
    return
  }
  form.file_id = file.id
  form.file_url = file.url
  previewReady.value = false
  await runPreview()
}

const confirmImport = async () => {
  submitting.value = true
  try {
    const payload = {
      reimbursement: {
        ...form,
        amount: String(toNumber(form.amount).toFixed(2)),
        tax_amount: String(toNumber(form.tax_amount).toFixed(2)),
        total_amount: String(toNumber(form.total_amount).toFixed(2)),
      },
      create_supplier: createSupplier.value,
    }
    const result = await confirmAiReimbursementImport(payload)
    ElMessage.success('AI录入报销单成功')
    emit('success', result)
    emit('update:modelValue', false)
    resetState()
  } catch (error) {
    console.error('确认录入报销单失败:', error)
    ElMessage.error(error.response?.data?.detail || '确认录入失败')
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  resetState()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      resetState()
    }
  }
)
</script>

<style scoped>
.ai-import-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-panel {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 42%),
    linear-gradient(135deg, #f5fbfa 0%, #eef6ff 100%);
}

.hero-kicker {
  display: inline-block;
  margin-bottom: 10px;
  letter-spacing: 0.16em;
  font-size: 12px;
  color: #0f766e;
}

.hero-copy h3 {
  margin: 0 0 10px;
  font-size: 24px;
  line-height: 1.3;
}

.hero-copy p {
  margin: 0;
  color: #526071;
  line-height: 1.7;
}

.hero-steps {
  align-self: end;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.content-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
}

.upload-column,
.form-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-heading,
.analysis-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-tags,
.panel-heading {
  gap: 12px;
}

.analysis-box,
.linkage-panel,
.file-summary {
  padding: 18px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid #dce7f2;
}

.reimbursement-form,
.linkage-panel {
  padding: 20px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid #dce7f2;
}

.analysis-status {
  margin: 12px 0 0;
  color: #526071;
  line-height: 1.7;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-item + .summary-item {
  margin-top: 12px;
}

.summary-item span {
  font-size: 12px;
  color: #6a7a90;
}

.summary-item strong,
.candidate-line {
  word-break: break-all;
}

.payment-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f7fafc 0%, #eef6ff 100%);
}

.payment-switch p {
  margin: 6px 0 0;
  color: #66788a;
  line-height: 1.6;
}

.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.footer-summary {
  color: #526071;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 900px) {
  .hero-panel,
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>