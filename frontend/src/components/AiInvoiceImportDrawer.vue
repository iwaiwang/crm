<template>
  <el-drawer
    :model-value="modelValue"
    title="AI录入发票"
    size="74%"
    destroy-on-close
    class="ai-invoice-drawer"
    @close="handleClose"
  >
    <div class="ai-import-shell">
      <section class="hero-panel">
        <div class="hero-copy">
          <span class="hero-kicker">SMART BILLING</span>
          <h3>把发票拖进来，系统会先识别票面信息，再帮你串上合同、应收和收支动作。</h3>
          <p>销项发票会优先推荐合同与应收，进项发票会自动带出支出草稿，确认后再统一入账。</p>
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
            <div class="summary-item">
              <span>文件地址</span>
              <strong>{{ fileInfo.url }}</strong>
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
            <span>发票信息</span>
            <div class="header-tags">
              <el-tag v-if="form.parse_confidence" effect="dark">
                置信度 {{ Math.round(form.parse_confidence * 100) }}%
              </el-tag>
              <el-tag :type="form.invoice_type === 'sales' ? 'success' : 'warning'" effect="plain">
                {{ form.invoice_type === 'sales' ? '销项发票' : '进项发票' }}
              </el-tag>
            </div>
          </div>

          <el-form :model="form" label-width="96px" class="invoice-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="发票号码" required>
                  <el-input v-model="form.invoice_no" placeholder="请输入发票号码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="发票代码">
                  <el-input v-model="form.invoice_code" placeholder="请输入发票代码" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
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
              <el-col :span="8">
                <el-form-item label="发票类型">
                  <el-radio-group v-model="form.type">
                    <el-radio value="normal">普票</el-radio>
                    <el-radio value="special">专票</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="发票方向">
                  <el-radio-group v-model="form.invoice_type" @change="handleDirectionChange">
                    <el-radio value="sales">销项</el-radio>
                    <el-radio value="purchase">进项</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="不含税金额">
                  <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="税额">
                  <el-input-number v-model="form.tax_amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="价税合计">
                  <el-input-number v-model="form.total_amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item :label="form.invoice_type === 'sales' ? '购买方' : '我方购买方'">
                  <el-input v-model="form.buyer_name" placeholder="购买方名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="购买方税号">
                  <el-input v-model="form.buyer_tax_id" placeholder="购买方税号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="form.invoice_type === 'sales' ? '销售方' : '供应商'">
                  <el-input v-model="form.seller_name" placeholder="销售方名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="销售方税号">
                  <el-input v-model="form.seller_tax_id" placeholder="销售方税号" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="补充说明" />
            </el-form-item>
          </el-form>

          <div class="linkage-panel" v-if="form.invoice_type === 'sales'">
            <div class="panel-heading">
              <span>合同与应收关联</span>
              <el-tag v-if="contractMatches.length" effect="plain">已匹配 {{ contractMatches.length }} 份合同</el-tag>
            </div>
            <el-form label-width="96px">
              <el-form-item label="推荐合同">
                <el-select v-model="form.contract_id" clearable placeholder="选择合同" style="width: 100%">
                  <el-option
                    v-for="item in contractMatches"
                    :key="item.contract_id"
                    :label="`${item.contract_no} / ${item.contract_name}`"
                    :value="item.contract_id"
                  >
                    <div class="option-line">
                      <span>{{ item.contract_no }} / {{ item.contract_name }}</span>
                      <small>{{ item.reason }}</small>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="推荐应收">
                <el-select v-model="payment.receivable_id" clearable placeholder="选择应收" style="width: 100%">
                  <el-option
                    v-for="item in receivableMatches"
                    :key="item.receivable_id"
                    :label="`${formatMoney(item.unpaid_amount)} / ${item.due_date || '未设置日期'}`"
                    :value="item.receivable_id"
                  >
                    <div class="option-line">
                      <span>未收 {{ formatMoney(item.unpaid_amount) }} / 到期 {{ item.due_date || '未设置' }}</span>
                      <small>{{ item.reason }}</small>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-form>

            <div class="payment-switch">
              <div>
                <strong>开票时同步登记收款</strong>
                <p>如果这张销项发票对应的款项已经收到，可以顺手把收款记录也落进去。</p>
              </div>
              <el-switch v-model="createPayment" />
            </div>

            <el-form v-if="createPayment" :model="payment" label-width="96px">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="收款金额">
                    <el-input-number v-model="payment.amount" :min="0" :precision="2" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="收款日期">
                    <el-date-picker
                      v-model="payment.payment_date"
                      type="date"
                      value-format="YYYY-MM-DD"
                      placeholder="选择日期"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="收款方式">
                    <el-select v-model="payment.payment_method" style="width: 100%">
                      <el-option v-for="item in paymentMethods" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="收款备注">
                <el-input v-model="payment.remark" placeholder="收款说明" />
              </el-form-item>
            </el-form>

            <div class="payment-switch">
              <div>
                <strong>自动创建收入</strong>
                <p>销项发票确认后会自动生成一条收入记录，备注里会带上发票号。</p>
              </div>
              <el-switch v-model="createIncome" />
            </div>

            <el-form v-if="createIncome" :model="income" label-width="96px">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="收入金额">
                    <el-input-number v-model="income.amount" :min="0" :precision="2" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="收入日期">
                    <el-date-picker
                      v-model="income.income_date"
                      type="date"
                      value-format="YYYY-MM-DD"
                      placeholder="选择日期"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="收款方式">
                    <el-select v-model="income.payment_method" clearable style="width: 100%">
                      <el-option v-for="item in paymentMethods" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="收入备注">
                <el-input v-model="income.remark" placeholder="收入备注" />
              </el-form-item>
            </el-form>
          </div>

          <div class="linkage-panel" v-else>
            <div class="panel-heading">
              <span>支出草稿</span>
              <el-tag effect="plain">AI 已推荐分类</el-tag>
            </div>
            <div class="payment-switch">
              <div>
                <strong>自动创建支出</strong>
                <p>进项发票确认后会自动生成一条支出，分类默认取 AI 推荐值，你也可以改。</p>
              </div>
              <el-switch v-model="createExpense" />
            </div>

            <el-form v-if="createExpense" :model="expense" label-width="96px">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="支出金额">
                    <el-input-number v-model="expense.amount" :min="0" :precision="2" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="价税合计">
                    <el-input-number v-model="expense.total_amount" :min="0" :precision="2" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="支出日期">
                    <el-date-picker
                      v-model="expense.expense_date"
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
                  <el-form-item label="支出分类">
                    <el-select v-model="expense.expense_category" style="width: 100%">
                      <el-option v-for="item in expenseCategories" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="支付方式">
                    <el-select v-model="expense.payment_method" clearable style="width: 100%">
                      <el-option v-for="item in paymentMethods" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="支出备注">
                <el-input v-model="expense.remark" placeholder="支出备注" />
              </el-form-item>
            </el-form>
          </div>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <div class="footer-summary">
          <span>{{ summaryActions.join(' / ') || '将创建 1 张发票' }}</span>
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
import { parseDocumentWithAI } from '@/api/document'
import { confirmAiInvoiceImport, previewAiInvoiceImport } from '@/api/invoice'

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
const contractMatches = ref([])
const receivableMatches = ref([])
const summaryActions = ref([])

const paymentMethods = [
  { label: '银行转账', value: 'bank_transfer' },
  { label: '支票', value: 'check' },
  { label: '现金', value: 'cash' },
  { label: '支付宝', value: 'alipay' },
  { label: '微信', value: 'wechat' },
]

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
  invoice_code: '',
  invoice_number: '',
  check_code: '',
  invoice_no: '',
  contract_id: '',
  amount: 0,
  tax_rate: 0,
  tax_amount: 0,
  total_amount: 0,
  type: 'normal',
  invoice_type: 'sales',
  buyer_name: '',
  buyer_tax_id: '',
  seller_name: '',
  seller_tax_id: '',
  issue_date: '',
  due_date: '',
  status: 'normal',
  remark: '',
  file_id: '',
  file_url: '',
  ai_parsed: true,
  parse_confidence: null,
})

const payment = reactive({
  receivable_id: '',
  amount: 0,
  payment_date: '',
  payment_method: 'bank_transfer',
  remark: '',
})

const income = reactive({
  amount: 0,
  income_date: '',
  income_category: 'sales',
  payment_method: 'bank_transfer',
  remark: '',
})

const expense = reactive({
  supplier_id: '',
  supplier_name: '',
  contract_id: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_date: '',
  expense_category: 'other',
  payment_method: 'bank_transfer',
  remark: '',
})

const createPayment = ref(false)
const createIncome = ref(false)
const createExpense = ref(false)

const normalizeText = (value) => (typeof value === 'string' ? value.trim() : '')
const toNumber = (value) => Number(value || 0)
const formatMoney = (value) => Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const activeStep = computed(() => {
  if (!fileInfo.value) return 0
  if (!previewReady.value) return 1
  return 2
})

const previewStatus = computed(() => {
  if (previewLoading.value) return 'AI 正在识别发票字段并生成业务建议，请稍候...'
  if (previewReady.value) return 'AI 草稿已准备好，你可以直接确认，也可以先调整合同、应收和收支动作。'
  if (fileInfo.value) return '文件已上传，准备开始识别。'
  return '先上传发票文件，系统会自动进入识别流程。'
})

const canConfirm = computed(() => {
  if (!fileInfo.value || !normalizeText(form.invoice_no)) return false
  if (createPayment.value && !payment.receivable_id) return false
  return true
})

const resetState = () => {
  fileInfo.value = null
  previewLoading.value = false
  previewReady.value = false
  submitting.value = false
  contractMatches.value = []
  receivableMatches.value = []
  summaryActions.value = []
  uploaderRefreshKey.value += 1
  Object.assign(form, {
    invoice_code: '',
    invoice_number: '',
    check_code: '',
    invoice_no: '',
    contract_id: '',
    amount: 0,
    tax_rate: 0,
    tax_amount: 0,
    total_amount: 0,
    type: 'normal',
    invoice_type: 'sales',
    buyer_name: '',
    buyer_tax_id: '',
    seller_name: '',
    seller_tax_id: '',
    issue_date: '',
    due_date: '',
    status: 'normal',
    remark: '',
    file_id: '',
    file_url: '',
    ai_parsed: true,
    parse_confidence: null,
  })
  Object.assign(payment, {
    receivable_id: '',
    amount: 0,
    payment_date: '',
    payment_method: 'bank_transfer',
    remark: '',
  })
  Object.assign(income, {
    amount: 0,
    income_date: '',
    income_category: 'sales',
    payment_method: 'bank_transfer',
    remark: '',
  })
  Object.assign(expense, {
    supplier_id: '',
    supplier_name: '',
    contract_id: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_date: '',
    expense_category: 'other',
    payment_method: 'bank_transfer',
    remark: '',
  })
  createPayment.value = false
  createIncome.value = false
  createExpense.value = false
}

const buildLegacyPreview = (aiResult) => {
  const data = aiResult?.data || {}
  const invoiceTypeText = normalizeText(data.invoice_type)
  const normalizedKind = invoiceTypeText.includes('专') ? 'special' : 'normal'
  return {
    invoice: {
      invoice_code: data.invoice_code || '',
      invoice_number: data.invoice_number || '',
      check_code: data.check_code || '',
      invoice_no: data.invoice_no || data.invoice_number || '',
      contract_id: '',
      amount: toNumber(data.amount),
      tax_rate: toNumber(data.tax_rate),
      tax_amount: toNumber(data.tax_amount),
      total_amount: toNumber(data.total_amount || data.amount),
      type: normalizedKind,
      invoice_type: 'sales',
      buyer_name: data.buyer_name || '',
      buyer_tax_id: data.buyer_tax_id || '',
      seller_name: data.seller_name || '',
      seller_tax_id: data.seller_tax_id || '',
      issue_date: data.invoice_date || '',
      due_date: data.invoice_date || '',
      status: 'normal',
      remark: data.remarks || '',
      file_id: fileInfo.value?.id || '',
      file_url: fileInfo.value?.url || '',
      ai_parsed: true,
      parse_confidence: aiResult?.confidence ?? null,
    },
    matching_contracts: [],
    matching_receivables: [],
    payment: null,
    income: {
      amount: toNumber(data.total_amount || data.amount),
      income_date: data.invoice_date || new Date().toISOString().slice(0, 10),
      income_category: 'sales',
      payment_method: 'bank_transfer',
      remark: `AI录入销项发票自动创建收入，发票号：${data.invoice_no || data.invoice_number || ''}`,
    },
    expense: null,
    suggested_actions: ['将创建 1 张发票', '将创建 1 条收入'],
  }
}

const mapPreviewToState = (preview) => {
  const invoiceData = preview.invoice || {}
  Object.assign(form, {
    invoice_code: invoiceData.invoice_code || '',
    invoice_number: invoiceData.invoice_number || '',
    check_code: invoiceData.check_code || '',
    invoice_no: invoiceData.invoice_no || '',
    contract_id: invoiceData.contract_id || '',
    amount: toNumber(invoiceData.amount),
    tax_rate: toNumber(invoiceData.tax_rate),
    tax_amount: toNumber(invoiceData.tax_amount),
    total_amount: toNumber(invoiceData.total_amount),
    type: invoiceData.type || 'normal',
    invoice_type: invoiceData.invoice_type || 'sales',
    buyer_name: invoiceData.buyer_name || '',
    buyer_tax_id: invoiceData.buyer_tax_id || '',
    seller_name: invoiceData.seller_name || '',
    seller_tax_id: invoiceData.seller_tax_id || '',
    issue_date: invoiceData.issue_date || '',
    due_date: invoiceData.due_date || invoiceData.issue_date || '',
    status: invoiceData.status || 'normal',
    remark: invoiceData.remark || '',
    file_id: invoiceData.file_id || fileInfo.value?.id || '',
    file_url: invoiceData.file_url || fileInfo.value?.url || '',
    ai_parsed: invoiceData.ai_parsed !== false,
    parse_confidence: invoiceData.parse_confidence ?? null,
  })

  contractMatches.value = preview.matching_contracts || []
  receivableMatches.value = preview.matching_receivables || []
  summaryActions.value = preview.suggested_actions || []

  Object.assign(payment, {
    receivable_id: preview.payment?.receivable_id || '',
    amount: toNumber(preview.payment?.amount),
    payment_date: preview.payment?.payment_date || form.issue_date || new Date().toISOString().slice(0, 10),
    payment_method: preview.payment?.payment_method || 'bank_transfer',
    remark: preview.payment?.remark || '',
  })

  Object.assign(income, {
    amount: toNumber(preview.income?.amount || form.total_amount),
    income_date: preview.income?.income_date || form.issue_date || new Date().toISOString().slice(0, 10),
    income_category: preview.income?.income_category || 'sales',
    payment_method: preview.income?.payment_method || 'bank_transfer',
    remark: preview.income?.remark || '',
  })

  Object.assign(expense, {
    supplier_id: preview.expense?.supplier_id || '',
    supplier_name: preview.expense?.supplier_name || form.seller_name || '',
    contract_id: preview.expense?.contract_id || '',
    amount: toNumber(preview.expense?.amount || form.amount),
    tax_amount: toNumber(preview.expense?.tax_amount || form.tax_amount),
    total_amount: toNumber(preview.expense?.total_amount || form.total_amount),
    expense_date: preview.expense?.expense_date || form.issue_date || new Date().toISOString().slice(0, 10),
    expense_category: preview.expense?.expense_category || 'other',
    payment_method: preview.expense?.payment_method || 'bank_transfer',
    remark: preview.expense?.remark || '',
  })

  createPayment.value = Boolean(preview.payment?.receivable_id)
  createIncome.value = form.invoice_type === 'sales'
  createExpense.value = form.invoice_type === 'purchase'
  previewReady.value = true
}

const runPreview = async () => {
  if (!fileInfo.value?.id) return
  previewLoading.value = true
  try {
    const preview = await previewAiInvoiceImport(fileInfo.value.id)
    mapPreviewToState(preview)
  } catch (error) {
    if (error.response?.status === 404) {
      try {
        const aiResult = await parseDocumentWithAI(fileInfo.value.id, 'invoice')
        mapPreviewToState(buildLegacyPreview(aiResult))
        ElMessage.warning('当前后端尚未升级 AI 发票编排接口，已切换到基础识别模式。')
      } catch (fallbackError) {
        console.error('AI 解析发票失败:', fallbackError)
        ElMessage.error(fallbackError.response?.data?.detail || 'AI 解析发票失败')
      }
    } else {
      console.error('AI 解析发票失败:', error)
      ElMessage.error(error.response?.data?.detail || 'AI 解析发票失败')
    }
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

const handleDirectionChange = (value) => {
  if (value === 'sales') {
    createIncome.value = true
    createExpense.value = false
  } else {
    createIncome.value = false
    createPayment.value = false
    createExpense.value = true
  }
}

watch(() => createPayment.value, (enabled) => {
  if (enabled && !payment.amount) {
    payment.amount = receivableMatches.value[0]?.unpaid_amount ? toNumber(receivableMatches.value[0].unpaid_amount) : toNumber(form.total_amount)
  }
  if (enabled && !payment.payment_date) {
    payment.payment_date = form.issue_date || new Date().toISOString().slice(0, 10)
  }
})

const confirmImport = async () => {
  submitting.value = true
  try {
    const payload = {
      invoice: {
        ...form,
        amount: String(toNumber(form.amount).toFixed(2)),
        tax_rate: String(toNumber(form.tax_rate)),
        tax_amount: String(toNumber(form.tax_amount).toFixed(2)),
        total_amount: String(toNumber(form.total_amount).toFixed(2)),
      },
      create_payment: createPayment.value,
      payment: createPayment.value
        ? {
            ...payment,
            amount: String(toNumber(payment.amount).toFixed(2)),
          }
        : null,
      create_income: createIncome.value,
      income: createIncome.value
        ? {
            ...income,
            amount: String(toNumber(income.amount).toFixed(2)),
          }
        : null,
      create_expense: createExpense.value,
      expense: createExpense.value
        ? {
            ...expense,
            amount: String(toNumber(expense.amount).toFixed(2)),
            tax_amount: String(toNumber(expense.tax_amount).toFixed(2)),
            total_amount: String(toNumber(expense.total_amount).toFixed(2)),
          }
        : null,
    }
    const result = await confirmAiInvoiceImport(payload)
    ElMessage.success('AI录入发票成功')
    emit('success', result)
    emit('update:modelValue', false)
    resetState()
  } catch (error) {
    console.error('确认录入发票失败:', error)
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
  font-size: 28px;
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

.invoice-form,
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
  margin: 16px 0;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f7fafc 0%, #eef6ff 100%);
}

.payment-switch p {
  margin: 6px 0 0;
  color: #66788a;
  line-height: 1.6;
}

.option-line {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-line small {
  color: #7b8a9a;
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

@media (max-width: 1100px) {
  .hero-panel,
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
