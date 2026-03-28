<template>
  <el-drawer
    :model-value="modelValue"
    title="AI录入合同"
    size="72%"
    destroy-on-close
    class="ai-contract-drawer"
    @close="handleClose"
  >
    <div class="ai-import-shell">
      <section class="hero-panel">
        <div class="hero-copy">
          <span class="hero-kicker">SMART INTAKE</span>
          <h3>拖入合同，系统先帮你拆字段，再自动生成应收计划。</h3>
          <p>你只需要确认关键字段，必要时改一下付款节点，最后一键录入。</p>
        </div>
        <el-steps :active="activeStep" simple class="hero-steps">
          <el-step title="上传合同" />
          <el-step title="AI解析" />
          <el-step title="确认录入" />
        </el-steps>
      </section>

      <div class="content-grid">
        <section class="upload-column">
          <div class="panel-heading">
            <span>合同文件</span>
            <el-tag v-if="fileInfo?.name" type="success" effect="plain">已上传</el-tag>
          </div>
          <DocumentUploader
            type="contract"
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
                重新解析
              </el-button>
            </div>
            <p class="analysis-status">{{ previewStatus }}</p>
            <el-alert
              v-if="matchingCustomerNames.length"
              type="info"
              :closable="false"
              show-icon
              title="已为你找到相近客户"
            >
              <div class="candidate-line">{{ matchingCustomerNames.join(' / ') }}</div>
            </el-alert>
            <el-alert
              v-else-if="previewReady && !form.customer_id"
              type="warning"
              :closable="false"
              show-icon
              title="没有匹配到现有客户，确认录入时会自动创建"
            />
          </div>
        </section>

        <section class="form-column">
          <div class="panel-heading">
            <span>合同信息</span>
            <el-tag v-if="form.parse_confidence" effect="dark" class="confidence-tag">
              置信度 {{ Math.round(form.parse_confidence * 100) }}%
            </el-tag>
          </div>

          <el-form :model="form" label-width="96px" class="contract-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="合同编号" required>
                  <el-input v-model="form.contract_no" placeholder="请输入合同编号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="合同名称" required>
                  <el-input v-model="form.name" placeholder="请输入合同名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="客户" required>
                  <el-select v-model="form.customer_id" filterable placeholder="请选择现有客户" style="width: 100%">
                    <el-option
                      v-for="customer in customers"
                      :key="customer.id"
                      :label="customer.name"
                      :value="customer.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="识别客户名">
                  <el-input v-model="form.customer_name" placeholder="AI识别出的客户名称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="合同金额" required>
                  <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="开始日期">
                  <el-date-picker
                    v-model="form.start_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择开始日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="结束日期">
                  <el-date-picker
                    v-model="form.end_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择结束日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="付款条款">
              <el-input v-model="form.payment_terms" type="textarea" :rows="3" placeholder="AI会优先识别首付、验收款、尾款等节点" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="合同补充说明" />
            </el-form-item>
          </el-form>

          <div class="receivable-panel">
            <div class="panel-heading">
              <span>应收计划</span>
              <div class="receivable-actions">
                <el-tag effect="plain">共 {{ receivableRows.length }} 条</el-tag>
                <el-button size="small" @click="addReceivableRow">新增一条</el-button>
              </div>
            </div>
            <div v-if="receivableRows.length" class="receivable-list">
              <div v-for="(item, index) in receivableRows" :key="item.key" class="receivable-card">
                <div class="receivable-card-head">
                  <strong>节点 {{ index + 1 }}</strong>
                  <el-button text type="danger" @click="removeReceivableRow(index)">删除</el-button>
                </div>
                <el-row :gutter="12">
                  <el-col :span="8">
                    <label>比例 (%)</label>
                    <el-input-number v-model="item.percent" :min="0" :max="100" :precision="2" style="width: 100%" @change="syncAmountFromPercent(item)" />
                  </el-col>
                  <el-col :span="8">
                    <label>应收金额</label>
                    <el-input-number v-model="item.amount" :min="0" :precision="2" style="width: 100%" @change="syncPercentFromAmount(item)" />
                  </el-col>
                  <el-col :span="8">
                    <label>应收日期</label>
                    <el-date-picker
                      v-model="item.due_date"
                      type="date"
                      value-format="YYYY-MM-DD"
                      placeholder="可留空"
                      style="width: 100%"
                    />
                  </el-col>
                </el-row>
                <label>节点说明</label>
                <el-input v-model="item.remark" placeholder="例如：首付、验收后、尾款" />
              </div>
            </div>
            <el-empty v-else description="暂未生成应收计划，可手动新增" />
          </div>
        </section>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <div class="footer-summary">
          <span>预计创建 {{ receivableRows.length }} 条应收</span>
          <strong>合计 ￥{{ totalReceivableAmount }}</strong>
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
import { useRouter } from 'vue-router'
import DocumentUploader from '@/components/DocumentUploader.vue'
import { createCustomer, getCustomers } from '@/api/customer'
import { parseDocumentWithAI } from '@/api/document'
import { createReceivable } from '@/api/receivable'
import { previewAiContractImport, confirmAiContractImport, createContract } from '@/api/contract'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'success'])

const router = useRouter()
const uploaderRefreshKey = ref(0)
const customers = ref([])
const fileInfo = ref(null)
const previewLoading = ref(false)
const previewReady = ref(false)
const submitting = ref(false)
const matchingCustomerNames = ref([])

const form = reactive({
  contract_no: '',
  name: '',
  customer_id: '',
  customer_name: '',
  amount: 0,
  start_date: '',
  end_date: '',
  status: 'signed',
  payment_terms: '',
  remark: '',
  file_id: '',
  file_url: '',
  ai_parsed: true,
  parse_confidence: null,
})

const receivableRows = ref([])

const normalizeText = (value) => {
  return typeof value === 'string' ? value.trim() : ''
}

const nullableText = (value) => {
  const normalized = normalizeText(value)
  return normalized || null
}

const resolveReceivableDueDate = (dueDate) => {
  return dueDate || form.start_date || new Date().toISOString().slice(0, 10)
}

const buildReceivablePlan = (paymentTerms, totalAmount) => {
  const amount = Number(totalAmount || 0)
  if (!amount) return []

  const text = normalizeText(paymentTerms)
  if (!text) {
    return [{
      amount,
      percent: 100,
      due_date: '',
      remark: '未识别付款条款，按合同总金额生成',
    }]
  }

  const percentMatches = [...text.matchAll(/(\d+(?:\.\d+)?)\s*%/g)].map((match) => Number(match[1]))
  if (!percentMatches.length) {
    return [{
      amount,
      percent: 100,
      due_date: '',
      remark: '未识别清晰付款比例，按合同总金额生成',
    }]
  }

  const segments = text.split(/[；;\n。]+/).map((item) => item.trim()).filter(Boolean)
  const rows = percentMatches.map((percent, index) => {
    const matchedSegment = segments.find((segment) => segment.includes(`${percent}%`))
    return {
      amount: Number(((amount * percent) / 100).toFixed(2)),
      percent,
      due_date: '',
      remark: matchedSegment || `付款节点 ${index + 1}`,
    }
  })

  const currentTotal = rows.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const diff = Number((amount - currentTotal).toFixed(2))
  if (Math.abs(diff) >= 0.01) {
    rows.push({
      amount: diff > 0 ? diff : 0,
      percent: Number((100 - rows.reduce((sum, item) => sum + Number(item.percent || 0), 0)).toFixed(2)),
      due_date: '',
      remark: '剩余尾款',
    })
  }

  return rows
}

const buildLegacyPreview = (aiResult) => {
  const data = aiResult?.data || {}
  const customerName = normalizeText(data.customer_name)
  const matchedCustomers = customers.value.filter((customer) => {
    return customerName && (customer.name.includes(customerName) || customerName.includes(customer.name))
  })
  const contractAmount = Number(data.amount || 0)

  return {
    contract: {
      contract_no: normalizeText(data.contract_no) || `AI-${Date.now()}`,
      name: normalizeText(data.contract_name) || 'AI 导入合同',
      customer_id: matchedCustomers[0]?.id || '',
      customer_name: customerName,
      amount: contractAmount,
      start_date: data.start_date || data.sign_date || '',
      end_date: data.end_date || '',
      status: 'signed',
      payment_terms: normalizeText(data.payment_terms),
      remark: normalizeText(data.remarks),
      file_id: fileInfo.value?.id || '',
      file_url: fileInfo.value?.url || '',
      ai_parsed: true,
      parse_confidence: aiResult?.confidence ?? null,
    },
    receivables: buildReceivablePlan(data.payment_terms, contractAmount),
    matching_customer_names: matchedCustomers.map((customer) => customer.name),
  }
}

const previewStatus = computed(() => {
  if (previewLoading.value) return 'AI 正在分析合同内容并生成应收计划，请稍候...'
  if (previewReady.value) return 'AI 草案已准备好，你可以直接确认，也可以先修改。'
  if (fileInfo.value) return '文件已上传，正在等待或准备解析。'
  return '先上传合同文件，系统会自动开始解析。'
})

const activeStep = computed(() => {
  if (!fileInfo.value) return 0
  if (!previewReady.value) return 1
  return 2
})

const canConfirm = computed(() => {
  return Boolean(
    fileInfo.value &&
    form.contract_no &&
    form.name &&
    (form.customer_id || normalizeText(form.customer_name)) &&
    Number(form.amount) >= 0
  )
})

const totalReceivableAmount = computed(() => {
  return receivableRows.value
    .reduce((sum, item) => sum + Number(item.amount || 0), 0)
    .toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})

const loadCustomers = async () => {
  const res = await getCustomers({ page_size: 100 })
  customers.value = res.items || []
}

const resetState = () => {
  fileInfo.value = null
  previewLoading.value = false
  previewReady.value = false
  submitting.value = false
  matchingCustomerNames.value = []
  uploaderRefreshKey.value += 1
  Object.assign(form, {
    contract_no: '',
    name: '',
    customer_id: '',
    customer_name: '',
    amount: 0,
    start_date: '',
    end_date: '',
    status: 'signed',
    payment_terms: '',
    remark: '',
    file_id: '',
    file_url: '',
    ai_parsed: true,
    parse_confidence: null,
  })
  receivableRows.value = []
}

const mapPreviewToForm = (preview) => {
  const contract = preview.contract || {}
  Object.assign(form, {
    contract_no: contract.contract_no || '',
    name: contract.name || '',
    customer_id: contract.customer_id || '',
    customer_name: contract.customer_name || '',
    amount: Number(contract.amount || 0),
    start_date: contract.start_date || '',
    end_date: contract.end_date || '',
    status: contract.status || 'signed',
    payment_terms: contract.payment_terms || '',
    remark: contract.remark || '',
    file_id: contract.file_id || fileInfo.value?.id || '',
    file_url: contract.file_url || fileInfo.value?.url || '',
    ai_parsed: true,
    parse_confidence: contract.parse_confidence ?? null,
  })

  receivableRows.value = (preview.receivables || []).map((item, index) => ({
    key: `${Date.now()}-${index}`,
    amount: Number(item.amount || 0),
    percent: item.percent == null ? null : Number(item.percent),
    due_date: item.due_date || '',
    remark: item.remark || '',
  }))
  matchingCustomerNames.value = preview.matching_customer_names || []
  previewReady.value = true
}

const runPreview = async () => {
  if (!fileInfo.value?.id) return
  previewLoading.value = true
  previewReady.value = false
  try {
    let preview
    try {
      preview = await previewAiContractImport(fileInfo.value.id)
    } catch (error) {
      if (error.response?.status !== 404) {
        throw error
      }
      const aiResult = await parseDocumentWithAI(fileInfo.value.id, 'contract')
      preview = buildLegacyPreview(aiResult)
      ElMessage.warning('当前后端未升级到 AI 导入新接口，已自动切换兼容模式')
    }
    mapPreviewToForm(preview)
    ElMessage.success('合同解析完成')
  } catch (error) {
    console.error('AI 解析合同失败:', error)
    if (error.response?.status === 503) {
      ElMessage.error('AI 服务未配置或未启用，请先到系统设置中保存 AI 配置后再试')
    } else {
      ElMessage.error(error.response?.data?.detail || '合同解析失败')
    }
  } finally {
    previewLoading.value = false
  }
}

const handleFileChange = async (file) => {
  fileInfo.value = file
  previewReady.value = false
  matchingCustomerNames.value = []
  if (!file) {
    form.file_id = ''
    form.file_url = ''
    receivableRows.value = []
    return
  }
  form.file_id = file.id
  form.file_url = file.url
  await runPreview()
}

const addReceivableRow = () => {
  receivableRows.value.push({
    key: `${Date.now()}-${Math.random()}`,
    amount: 0,
    percent: null,
    due_date: '',
    remark: '',
  })
}

const removeReceivableRow = (index) => {
  receivableRows.value.splice(index, 1)
}

const syncAmountFromPercent = (item) => {
  const contractAmount = Number(form.amount || 0)
  if (!contractAmount || item.percent == null) return
  item.amount = Number(((contractAmount * Number(item.percent)) / 100).toFixed(2))
}

const syncPercentFromAmount = (item) => {
  const contractAmount = Number(form.amount || 0)
  if (!contractAmount) {
    item.percent = null
    return
  }
  item.percent = Number(((Number(item.amount || 0) / contractAmount) * 100).toFixed(2))
}

const confirmImport = async () => {
  if (!canConfirm.value) {
    ElMessage.warning('请先补全合同编号、合同名称、客户信息和金额')
    return
  }

  submitting.value = true
  try {
    let result
    const payload = {
      contract: {
        ...form,
        customer_id: nullableText(form.customer_id),
        customer_name: nullableText(form.customer_name),
        amount: Number(form.amount || 0),
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        payment_terms: nullableText(form.payment_terms),
        remark: nullableText(form.remark),
        file_id: nullableText(form.file_id),
        file_url: nullableText(form.file_url),
      },
      receivables: receivableRows.value.map((item) => ({
        amount: Number(item.amount || 0),
        percent: item.percent == null ? null : Number(item.percent),
        due_date: item.due_date || null,
        remark: item.remark || null,
      })),
    }
    try {
      result = await confirmAiContractImport(payload)
    } catch (error) {
      if (error.response?.status !== 404) {
        throw error
      }
      const createdContract = await createContract({
        contract_no: form.contract_no,
        name: form.name,
        customer_id: form.customer_id || (await createCustomer({
          name: normalizeText(form.customer_name),
          category: 'normal',
          status: 'active',
          remark: 'AI录入合同时自动创建',
        })).id,
        amount: Number(form.amount || 0),
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        status: form.status || 'signed',
        payment_terms: nullableText(form.payment_terms),
        remark: nullableText(form.remark),
        file_id: nullableText(form.file_id),
        file_url: nullableText(form.file_url),
        ai_parsed: true,
        parse_confidence: form.parse_confidence,
      })
      const receivablePayloads = payload.receivables.length
        ? payload.receivables
        : buildReceivablePlan(form.payment_terms, form.amount)
      const createdReceivables = []
      for (const item of receivablePayloads) {
        if (!Number(item.amount || 0)) continue
        const createdReceivable = await createReceivable({
          contract_id: createdContract.id,
          amount: Number(item.amount || 0),
          due_date: resolveReceivableDueDate(item.due_date),
          status: 'unpaid',
          remark: item.remark || null,
        })
        createdReceivables.push(createdReceivable)
      }
      result = {
        contract: createdContract,
        receivables: createdReceivables,
      }
      ElMessage.warning('当前后端未升级到 AI 导入新接口，已自动切换兼容录入模式')
    }
    ElMessage.success('合同已录入')
    emit('success', result)
    emit('update:modelValue', false)
    resetState()
    if (result?.contract?.id) {
      router.push(`/contracts/${result.contract.id}`)
    }
  } catch (error) {
    console.error('确认录入失败:', error)
    ElMessage.error(error.response?.data?.detail || '录入失败')
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
  async (visible) => {
    if (visible) {
      try {
        await loadCustomers()
      } catch (error) {
        console.error('加载客户失败:', error)
        ElMessage.error('加载客户失败')
      }
    }
  }
)

watch(
  () => form.amount,
  () => {
    receivableRows.value.forEach((item) => {
      if (item.percent != null && item.percent !== '') {
        syncAmountFromPercent(item)
      }
    })
  }
)
</script>

<style scoped>
.ai-import-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(254, 240, 138, 0.35), transparent 30%),
    radial-gradient(circle at top right, rgba(125, 211, 252, 0.22), transparent 32%),
    linear-gradient(180deg, #fffef8 0%, #f7f9fc 100%);
}

.hero-panel {
  padding: 22px 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, #102542 0%, #1d4e89 55%, #c2410c 100%);
  color: #fffdf6;
  box-shadow: 0 18px 36px rgba(16, 37, 66, 0.22);
}

.hero-copy h3 {
  margin: 8px 0 10px;
  font-size: 28px;
  line-height: 1.25;
}

.hero-copy p {
  margin: 0;
  max-width: 720px;
  color: rgba(255, 253, 246, 0.8);
}

.hero-kicker {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 253, 246, 0.14);
  font-size: 12px;
  letter-spacing: 0.16em;
}

.hero-steps {
  margin-top: 18px;
  border-radius: 18px;
  overflow: hidden;
}

.content-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 20px;
}

.upload-column,
.form-column {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.file-summary {
  margin-top: 16px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-item span {
  font-size: 12px;
  color: #64748b;
}

.summary-item strong {
  color: #0f172a;
  word-break: break-all;
}

.analysis-box {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #fff7ed 0%, #fff1f2 100%);
}

.analysis-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.analysis-status {
  margin: 0 0 12px;
  color: #7c2d12;
  line-height: 1.6;
}

.candidate-line {
  color: #0f172a;
  font-weight: 600;
}

.confidence-tag {
  background: linear-gradient(135deg, #0f766e, #0891b2);
  border: 0;
}

.contract-form {
  margin-bottom: 12px;
}

.receivable-panel {
  padding-top: 8px;
}

.receivable-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.receivable-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.receivable-card {
  padding: 16px;
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(251, 191, 36, 0.12), transparent 35%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(251, 191, 36, 0.22);
}

.receivable-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.receivable-card label {
  display: block;
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #475569;
}

.footer-summary strong {
  color: #c2410c;
  font-size: 18px;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
