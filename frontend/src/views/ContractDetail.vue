<template>
  <div class="contract-detail-page">
    <!-- 头部工具栏 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon> {{ isCreateMode ? '取消' : '返回' }}
        </el-button>
        <h2>{{ pageTitle }}</h2>
      </div>
      <div class="header-right">
        <!-- 查看模式：显示编辑按钮 -->
        <el-button v-if="isViewMode" type="primary" size="small" @click="enterEditMode">
          <el-icon><Edit /></el-icon> 编辑
        </el-button>
        <!-- 编辑模式：显示保存/取消按钮 -->
        <template v-else-if="isEditMode">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="saveContract" :loading="saving">保存</el-button>
        </template>
        <!-- 新建模式：显示保存/取消按钮 -->
        <template v-else-if="isCreateMode">
          <el-button @click="handleBack">取消</el-button>
          <el-button type="primary" @click="saveContract" :loading="saving">保存</el-button>
        </template>
        <!-- 关闭按钮（仅查看模式） -->
        <el-button v-if="isViewMode" link @click="handleBack">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 基本信息卡片（查看/编辑模式） -->
    <el-card class="info-card">
      <!-- 查看模式：显示详情 -->
      <el-descriptions v-if="isViewMode" :column="4" border size="large">
        <el-descriptions-item label="合同名称" :span="2">
          <span class="info-value">{{ contract.name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="合同编号">
          <span class="info-value">{{ contract.contract_no }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户名称">
          <span class="info-value">{{ customerName }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="合同金额">
          <span class="amount">¥{{ Number(contract.amount).toLocaleString() }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(contract.status)">{{ getStatusLabel(contract.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始日期">
          {{ contract.start_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束日期">
          {{ contract.end_date || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 编辑/新建模式：显示表单 -->
      <el-form v-else :model="formData" :rules="rules" ref="formRef" label-width="100px" size="large">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="合同编号" prop="contract_no">
              <el-input v-model="formData.contract_no" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="合同名称" prop="name">
              <el-input v-model="formData.name" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户" prop="customer_id">
              <el-select v-model="formData.customer_id" placeholder="请选择客户" style="width: 100%">
                <el-option
                  v-for="c in customers"
                  :key="c.id"
                  :label="c.name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="合同金额" prop="amount">
              <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker
                v-model="formData.start_date"
                type="date"
                placeholder="选择开始日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker
                v-model="formData.end_date"
                type="date"
                placeholder="选择结束日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formData.status" style="width: 100%">
                <el-option label="签约" value="signed" />
                <el-option label="执行中" value="in_progress" />
                <el-option label="完毕" value="completed" />
                <el-option label="终止" value="terminated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="付款条款" prop="payment_terms">
              <el-input v-model="formData.payment_terms" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="formData.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="合同文件">
              <DocumentUploader
                type="contract"
                :show-ai-parse="true"
                :initial-value="fileInfo"
                :refresh-key="documentUploaderKey"
                @change="handleFileChange"
                @ai-result="handleAiResult"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- Tabs 内容区（仅查看模式显示） -->
    <el-card v-if="isViewMode" class="tabs-card">
      <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
        <!-- 基本信息 Tab -->
        <el-tab-pane label="基本信息" name="basic">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="付款条款" :span="2">
              {{ contract.payment_terms || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">
              {{ contract.remark || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(contract.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDate(contract.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 回款管理 Tab -->
        <el-tab-pane label="回款管理" name="receivables">
          <div class="tab-toolbar">
            <el-button type="primary" size="small" @click="showAddReceivableDlg = true">
              <el-icon><Plus /></el-icon> 新增应收
            </el-button>
          </div>
          <el-table :data="receivables" v-loading="receivablesLoading" border stripe>
            <el-table-column prop="due_date" label="应收日期" width="110" />
            <el-table-column prop="amount" label="应收金额" width="120" align="right">
              <template #default="{ row }">¥{{ Number(row.amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="received_amount" label="已收金额" width="120" align="right">
              <template #default="{ row }">¥{{ Number(row.received_amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="unpaid_amount" label="未收金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ overdue: row.due_date < today }">
                  ¥{{ (Number(row.amount) - Number(row.received_amount)).toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getReceivableStatusType(row.status)">{{ getReceivableStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button link type="success" @click="showPaymentDlg(row)">登记收款</el-button>
                <el-button link type="danger" @click="deleteReceivable(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 收款统计 -->
          <div class="receivable-summary">
            <el-descriptions :column="4" border size="small">
              <el-descriptions-item label="应收总额">
                ¥{{ receivableSummary.total.toLocaleString() }}
              </el-descriptions-item>
              <el-descriptions-item label="已收总额">
                <span class="received">¥{{ receivableSummary.received.toLocaleString() }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="未收总额">
                <span class="unpaid">¥{{ receivableSummary.unpaid.toLocaleString() }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="回款率">
                <el-progress :percentage="receivableSummary.rate" :stroke-width="15" />
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 开票历史 Tab -->
        <el-tab-pane label="开票历史" name="invoices">
          <div class="tab-toolbar">
            <el-button type="primary" size="small" @click="showAddInvoiceDlg = true">
              <el-icon><Plus /></el-icon> 新增发票
            </el-button>
          </div>

          <!-- 开票统计 -->
          <div class="invoice-summary">
            <el-descriptions :column="4" border size="small">
              <el-descriptions-item label="销项发票总额">
                <span class="sales">¥{{ invoiceSummary.salesTotal.toLocaleString() }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="进项发票总额">
                <span class="purchase">¥{{ invoiceSummary.purchaseTotal.toLocaleString() }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="净开票额">
                <span :class="{ 'net-positive': invoiceSummary.net >= 0, 'net-negative': invoiceSummary.net < 0 }">
                  ¥{{ invoiceSummary.net.toLocaleString() }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="开票完成率">
                <el-progress :percentage="invoiceSummary.rate" :stroke-width="15" />
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <el-table :data="invoices" v-loading="invoicesLoading" border stripe>
            <el-table-column prop="invoice_no" label="发票号码" width="150" />
            <el-table-column prop="type" label="发票类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ getInvoiceTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="方向" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.invoice_type === 'sales' ? 'success' : 'info'">
                  {{ row.invoice_type === 'sales' ? '销项' : '进项' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" label="开票金额" width="120" align="right">
              <template #default="{ row }">¥{{ Number(row.total_amount || row.amount || 0).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="issue_date" label="开票日期" width="110">
              <template #default="{ row }">
                {{ row.issue_date || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="getInvoiceStatusType(row.status)">
                  {{ getInvoiceStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="buyer_name" label="购买方" min-width="150" />
            <el-table-column prop="remark" label="备注" min-width="120" />
          </el-table>
        </el-tab-pane>

        <!-- 文件柜 Tab -->
        <el-tab-pane label="文件柜" name="files">
          <div class="file-section">
            <!-- 文件列表 -->
            <div class="file-list" v-loading="filesLoading">
              <div v-if="attachments.length === 0" class="no-file">暂无文件</div>
              <div v-else>
                <div class="file-item" v-for="file in attachments" :key="file.id">
                  <el-icon class="file-icon" :class="getFileIconClass(file.file_type)">
                    <component :is="getFileIcon(file.file_type)" />
                  </el-icon>
                  <div class="file-info">
                    <span class="file-name">{{ file.file_name }}</span>
                    <span class="file-meta">
                      {{ formatFileSize(file.file_size) }} · {{ formatDate(file.created_at) }}
                      <el-tag v-if="file.is_primary" size="small" type="warning">主文件</el-tag>
                    </span>
                  </div>
                  <div class="file-actions">
                    <el-button link type="primary" @click="previewFile(file)">
                      <el-icon><View /></el-icon> 预览
                    </el-button>
                    <el-button link type="primary" @click="downloadFile(file.file_url)">
                      <el-icon><Download /></el-icon> 下载
                    </el-button>
                    <el-button
                      v-if="!file.is_primary"
                      link
                      type="danger"
                      @click="deleteFile(file)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <el-divider />

            <!-- 上传文件 -->
            <h4>上传文件</h4>
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :on-success="handleFileUploadSuccess"
              :on-error="handleFileUploadError"
              :show-file-list="false"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              multiple
            >
              <el-button type="primary" :loading="uploading">
                <el-icon><Upload /></el-icon> 选择文件
              </el-button>
            </el-upload>
            <p class="upload-tip">支持 PDF、JPG、PNG、DOC、DOCX 格式，可多选</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- PDF 预览对话框 -->
    <el-dialog v-model="showPreview" title="文件预览" width="80%" top="5vh">
      <div class="preview-container">
        <iframe v-if="previewUrl" :src="previewUrl" width="100%" height="600px" frameborder="0"></iframe>
        <img v-else-if="isImagePreview" :src="previewUrl" alt="预览" class="preview-image" />
        <div v-else class="no-preview">
          <el-icon :size="60"><Document /></el-icon>
          <p>该文件格式不支持预览</p>
        </div>
      </div>
    </el-dialog>

    <!-- 新增应收款对话框 -->
    <el-dialog v-model="showAddReceivableDlg" title="新增应收款" width="550px">
      <el-form :model="receivableForm" :rules="receivableRules" ref="receivableFormRef" label-width="100px">
        <!-- 合同参考信息 -->
        <el-alert
          v-if="contractReference.amount > 0"
          title="合同参考信息"
          type="info"
          :closable="false"
          show-icon
          class="contract-ref-info"
        >
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="合同金额">
              ¥{{ contractReference.amount.toLocaleString() }}
            </el-descriptions-item>
            <el-descriptions-item label="已收金额">
              <span class="received">¥{{ contractReference.received.toLocaleString() }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="未收金额">
              <span class="unpaid">¥{{ contractReference.unpaid.toLocaleString() }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-alert>

        <el-form-item label="应收金额" prop="amount">
          <el-input-number v-model="receivableForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>

        <el-form-item label="百分比" prop="percent">
          <el-input-number
            v-model="receivableForm.percent"
            :min="0"
            :max="100"
            :precision="2"
            :step="0.01"
            style="width: 100%"
            placeholder="按合同金额百分比"
          />
          <span class="form-tip">按合同金额的百分比计算金额</span>
        </el-form-item>

        <el-form-item label="应收日期" prop="due_date">
          <el-date-picker
            v-model="receivableForm.due_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="receivableForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddReceivableDlg = false">取消</el-button>
        <el-button type="primary" @click="submitReceivable" :loading="receivableSubmitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 登记收款对话框 -->
    <el-dialog v-model="showPaymentDlgFlag" title="登记收款" width="450px">
      <el-form :model="paymentForm" ref="paymentFormRef" label-width="80px">
        <el-form-item label="收款金额">
          <el-input-number v-model="paymentForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收款日期">
          <el-date-picker
            v-model="paymentForm.payment_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
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
        <el-button @click="showPaymentDlgFlag = false">取消</el-button>
        <el-button type="primary" @click="submitPayment" :loading="paymentLoading">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 新增发票对话框 -->
    <el-dialog v-model="showAddInvoiceDlg" title="新增发票" width="600px">
      <el-form :model="invoiceForm" :rules="invoiceRules" ref="invoiceFormRef" label-width="100px">
        <el-form-item label="发票号码" prop="invoice_no">
          <el-input v-model="invoiceForm.invoice_no" placeholder="请输入发票号码" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="发票类型" prop="type">
              <el-radio-group v-model="invoiceForm.type">
                <el-radio value="normal">增值税普通发票</el-radio>
                <el-radio value="special">增值税专用发票</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发票方向" prop="invoice_type">
              <el-radio-group v-model="invoiceForm.invoice_type">
                <el-radio value="sales">销项发票</el-radio>
                <el-radio value="purchase">进项发票</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="开票金额" prop="amount">
          <el-input-number v-model="invoiceForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开票日期" prop="issue_date">
          <el-date-picker
            v-model="invoiceForm.issue_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <!-- 销项发票：显示销售方（本公司）信息 - 自动填充 -->
        <el-divider content-position="left" v-if="invoiceForm.invoice_type === 'sales'">销售方信息（本公司）</el-divider>
        <el-form-item label="销售方名称" v-if="invoiceForm.invoice_type === 'sales'">
          <el-input v-model="invoiceForm.seller_name" placeholder="销售方名称" disabled />
        </el-form-item>
        <el-form-item label="销售方税号" v-if="invoiceForm.invoice_type === 'sales'">
          <el-input v-model="invoiceForm.seller_tax_id" placeholder="销售方税号" disabled />
        </el-form-item>

        <!-- 销项发票：显示购买方输入框 -->
        <el-divider content-position="left" v-if="invoiceForm.invoice_type === 'sales'">购买方信息</el-divider>
        <el-form-item label="购买方名称" v-if="invoiceForm.invoice_type === 'sales'" prop="buyer_name">
          <el-input v-model="invoiceForm.buyer_name" placeholder="购买方名称" />
        </el-form-item>
        <el-form-item label="购买方税号" v-if="invoiceForm.invoice_type === 'sales'" prop="buyer_tax_id">
          <el-input v-model="invoiceForm.buyer_tax_id" placeholder="购买方税号" />
        </el-form-item>

        <!-- 进项发票：显示购买方（本公司）信息 - 自动填充 -->
        <el-divider content-position="left" v-if="invoiceForm.invoice_type === 'purchase'">购买方信息（本公司）</el-divider>
        <el-form-item label="购买方名称" v-if="invoiceForm.invoice_type === 'purchase'">
          <el-input v-model="invoiceForm.buyer_name" placeholder="购买方名称" disabled />
        </el-form-item>
        <el-form-item label="购买方税号" v-if="invoiceForm.invoice_type === 'purchase'">
          <el-input v-model="invoiceForm.buyer_tax_id" placeholder="购买方税号" disabled />
        </el-form-item>

        <!-- 进项发票：显示销售方输入框 -->
        <el-divider content-position="left" v-if="invoiceForm.invoice_type === 'purchase'">销售方信息</el-divider>
        <el-form-item label="销售方名称" v-if="invoiceForm.invoice_type === 'purchase'" prop="seller_name">
          <el-input v-model="invoiceForm.seller_name" placeholder="销售方名称" />
        </el-form-item>
        <el-form-item label="销售方税号" v-if="invoiceForm.invoice_type === 'purchase'" prop="seller_tax_id">
          <el-input v-model="invoiceForm.seller_tax_id" placeholder="销售方税号" />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input v-model="invoiceForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddInvoiceDlg = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice" :loading="invoiceSubmitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Close, Plus, Document, Upload, Edit, View, Download, Delete, Picture } from '@element-plus/icons-vue'
import { getContract, createContract, updateContract, uploadContractFile, getContractFiles, deleteContractFile } from '@/api/contract'
import { getCustomers } from '@/api/customer'
import { getReceivables, createReceivable, addPayment, deleteReceivable as apiDeleteReceivable } from '@/api/receivable'
import { getInvoices, createInvoice } from '@/api/invoice'
import { getCompanyInfo } from '@/api/setting'
import { useUserStore } from '@/store/user'
import DocumentUploader from '@/components/DocumentUploader.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 页面模式：'view' | 'edit' | 'create'
const mode = ref('view')
const formRef = ref(null)
const customers = ref([])
const fileInfo = ref(null)
const documentUploaderKey = ref(0)
const saving = ref(false)
const uploading = ref(false)

// 根据路由判断模式
const isViewMode = computed(() => mode.value === 'view')
const isEditMode = computed(() => mode.value === 'edit')
const isCreateMode = computed(() => mode.value === 'create')

const pageTitle = computed(() => {
  if (isCreateMode.value) return '新增合同'
  if (isEditMode.value) return '编辑合同'
  return '合同详情'
})

const contract = ref({})
const activeTab = ref('basic')
const receivables = ref([])
const invoices = ref([])
const receivablesLoading = ref(false)
const invoicesLoading = ref(false)
const showAddReceivableDlg = ref(false)
const showPaymentDlgFlag = ref(false)
const showAddInvoiceDlg = ref(false)
const receivableSubmitting = ref(false)
const paymentLoading = ref(false)
const invoiceSubmitting = ref(false)

// 文件相关
const attachments = ref([])
const filesLoading = ref(false)
const showPreview = ref(false)
const previewUrl = ref('')
const isImagePreview = ref(false)

const today = new Date().toISOString().split('T')[0]

// 表单数据
const formData = reactive({
  contract_no: '',
  name: '',
  customer_id: '',
  amount: 0,
  start_date: '',
  end_date: '',
  status: 'signed',
  payment_terms: '',
  remark: '',
  file_id: '',
  file_url: '',
})

const rules = {
  contract_no: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
}

const receivableForm = reactive({
  amount: 0,
  percent: 0,
  due_date: '',
  remark: '',
})

const receivableRules = {
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
}

const paymentForm = reactive({
  receivable_id: '',
  amount: 0,
  payment_date: new Date().toISOString().split('T')[0],
  payment_method: 'bank',
  remark: '',
})

const companyInfo = ref({
  company_name: '',
  company_tax_id: '',
})

const invoiceForm = reactive({
  invoice_no: '',
  type: 'normal',
  invoice_type: 'sales',
  amount: 0,
  issue_date: new Date().toISOString().split('T')[0],
  buyer_name: '',
  buyer_tax_id: '',
  seller_name: '',
  seller_tax_id: '',
  remark: '',
})

const invoiceRules = {
  invoice_no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  buyer_name: [{ required: true, message: '请输入购买方名称', trigger: 'blur' }],
  buyer_tax_id: [{ required: true, message: '请输入购买方税号', trigger: 'blur' }],
  seller_name: [{ required: true, message: '请输入销售方名称', trigger: 'blur' }],
  seller_tax_id: [{ required: true, message: '请输入销售方税号', trigger: 'blur' }],
}

// 客户名称（兼容 contract.customer_name 和关联查询）
const customerName = computed(() => {
  if (contract.value.customer_name) return contract.value.customer_name
  const customer = customers.value.find(c => c.id === contract.value.customer_id)
  return customer ? customer.name : '-'
})

const receivableSummary = computed(() => {
  const total = receivables.value.reduce((sum, r) => sum + Number(r.amount), 0)
  const received = receivables.value.reduce((sum, r) => sum + Number(r.received_amount), 0)
  const unpaid = total - received
  const rate = total > 0 ? Math.round((received / total) * 100) : 0
  return { total, received, unpaid, rate }
})

// 合同参考信息（用于新增应收款时显示）
const contractReference = computed(() => {
  const contractAmount = Number(contract.value.amount || 0)
  const received = receivables.value.reduce((sum, r) => sum + Number(r.received_amount || 0), 0)
  const totalReceivable = receivables.value.reduce((sum, r) => sum + Number(r.amount || 0), 0)
  const unpaid = contractAmount - received - totalReceivable > 0 ? contractAmount - received - totalReceivable : 0
  return { amount: contractAmount, received, unpaid }
})

const invoiceSummary = computed(() => {
  const salesTotal = invoices.value
    .filter(i => i.invoice_type === 'sales')
    .reduce((sum, i) => sum + Number(i.total_amount || i.amount || 0), 0)
  const purchaseTotal = invoices.value
    .filter(i => i.invoice_type === 'purchase')
    .reduce((sum, i) => sum + Number(i.total_amount || i.amount || 0), 0)
  const net = salesTotal - purchaseTotal
  const contractAmount = Number(contract.value.amount || 0)
  const rate = contractAmount > 0 ? Math.round(((salesTotal + purchaseTotal) / contractAmount) * 100) : 0
  return { salesTotal, purchaseTotal, net, rate }
})

const uploadUrl = computed(() => {
  if (isCreateMode.value || !route.params.id) return null
  return `/api/contracts/${route.params.id}/files`
})

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return {
    Authorization: `Bearer ${token}`,
  }
})

// 加载客户列表
const loadCustomers = async () => {
  try {
    const res = await getCustomers({ page_size: 100 })
    customers.value = res.items
  } catch (error) {
    console.error('加载客户列表失败:', error)
  }
}

// 加载合同详情
const loadContract = async () => {
  if (isCreateMode.value) {
    // 新建模式：初始化空数据
    resetForm()
    return
  }

  try {
    const res = await getContract(route.params.id)
    contract.value = res
    // 同步表单数据
    syncFormFromContract()
  } catch (error) {
    console.error('加载合同详情失败:', error)
    ElMessage.error('加载合同详情失败')
  }
}

// 同步合同数据到表单
const syncFormFromContract = () => {
  formData.contract_no = contract.value.contract_no || ''
  formData.name = contract.value.name || ''
  formData.customer_id = contract.value.customer_id || ''
  formData.amount = Number(contract.value.amount) || 0
  formData.start_date = contract.value.start_date || ''
  formData.end_date = contract.value.end_date || ''
  formData.status = contract.value.status || 'signed'
  formData.payment_terms = contract.value.payment_terms || ''
  formData.remark = contract.value.remark || ''
  formData.file_id = contract.value.file_id || ''
  formData.file_url = contract.value.file_url || ''

  // 设置文件信息
  if (contract.value.file_id && contract.value.file_url) {
    fileInfo.value = {
      id: contract.value.file_id,
      name: contract.value.file_path || contract.value.contract_no,
      url: contract.value.file_url,
      type: 'pdf',
    }
  } else {
    fileInfo.value = null
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    contract_no: '',
    name: '',
    customer_id: '',
    amount: 0,
    start_date: '',
    end_date: '',
    status: 'signed',
    payment_terms: '',
    remark: '',
    file_id: '',
    file_url: '',
  })
  fileInfo.value = null
  documentUploaderKey.value++
}

const loadReceivables = async () => {
  receivablesLoading.value = true
  try {
    const res = await getReceivables({ contract_id: route.params.id, page_size: 100 })
    receivables.value = res.items
  } catch (error) {
    console.error('加载应收款失败:', error)
  } finally {
    receivablesLoading.value = false
  }
}

const loadInvoices = async () => {
  invoicesLoading.value = true
  try {
    const res = await getInvoices({ contract_id: route.params.id, page_size: 100 })
    invoices.value = res.items
  } catch (error) {
    console.error('加载发票失败:', error)
  } finally {
    invoicesLoading.value = false
  }
}

const handleBack = () => {
  router.push('/contracts')
}

// 进入编辑模式
const enterEditMode = () => {
  mode.value = 'edit'
  syncFormFromContract()
}

// 取消编辑
const cancelEdit = () => {
  mode.value = 'view'
  syncFormFromContract()
}

// 保存合同
const saveContract = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const dataToSubmit = { ...formData }

      // 将空字符串转换为 null
      Object.keys(dataToSubmit).forEach(key => {
        if (dataToSubmit[key] === '') {
          dataToSubmit[key] = null
        }
      })

      if (isCreateMode.value) {
        await createContract(dataToSubmit)
        ElMessage.success('创建成功')
      } else {
        await updateContract(route.params.id, dataToSubmit)
        ElMessage.success('更新成功')
        // 重新加载详情
        await loadContract()
      }

      // 编辑成功后返回查看模式或列表
      if (isCreateMode.value) {
        router.push('/contracts')
      } else {
        mode.value = 'view'
        await loadContract()
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

const getStatusType = (status) => {
  const map = { signed: '', in_progress: 'warning', completed: 'success', terminated: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { signed: '签约', in_progress: '执行中', completed: '完毕', terminated: '终止' }
  return map[status] || status
}

const getReceivableStatusType = (status) => {
  const map = { unpaid: 'warning', partial: 'info', paid: 'success', overdue: 'danger' }
  return map[status] || 'info'
}

const getReceivableStatusLabel = (status) => {
  const map = { unpaid: '未收款', partial: '部分收款', paid: '已结清', overdue: '逾期' }
  return map[status] || status
}

const getInvoiceTypeLabel = (type) => {
  const map = {
    normal: '普票',
    special: '专票',
  }
  return map[type] || type
}

const getInvoiceStatusType = (status) => {
  const map = {
    pending: 'info',
    issued: 'success',
    sent: 'warning',
    received: 'success',
    normal: 'success',
    void: 'danger',
  }
  return map[status] || 'info'
}

const getInvoiceStatusLabel = (status) => {
  const map = {
    pending: '待开票',
    issued: '已开具',
    sent: '已寄送',
    received: '已收到',
    normal: '正常',
    void: '作废',
  }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const showPaymentDlg = (row) => {
  paymentForm.receivable_id = row.id
  paymentForm.amount = Number(row.amount) - Number(row.received_amount)
  showPaymentDlgFlag.value = true
}

const submitReceivable = async () => {
  receivableSubmitting.value = true
  try {
    await createReceivable({
      contract_id: route.params.id,
      amount: receivableForm.amount,
      due_date: receivableForm.due_date,
      status: 'unpaid',
      remark: receivableForm.remark || undefined,
    })
    ElMessage.success('创建成功')
    showAddReceivableDlg.value = false
    loadReceivables()
  } catch (error) {
    console.error('创建失败:', error)
    ElMessage.error('创建失败')
  } finally {
    receivableSubmitting.value = false
  }
}

const submitPayment = async () => {
  paymentLoading.value = true
  try {
    await addPayment(paymentForm.receivable_id, {
      amount: paymentForm.amount,
      payment_date: paymentForm.payment_date,
      payment_method: paymentForm.payment_method,
      remark: paymentForm.remark,
    })
    ElMessage.success('收款登记成功')
    showPaymentDlgFlag.value = false
    loadReceivables()
  } catch (error) {
    console.error('登记失败:', error)
    ElMessage.error('登记失败')
  } finally {
    paymentLoading.value = false
  }
}

const submitInvoice = async () => {
  invoiceSubmitting.value = true
  try {
    await createInvoice({
      contract_id: route.params.id,
      invoice_no: invoiceForm.invoice_no,
      type: invoiceForm.type,
      invoice_type: invoiceForm.invoice_type,
      total_amount: invoiceForm.amount,
      issue_date: invoiceForm.issue_date,
      buyer_name: invoiceForm.buyer_name,
      buyer_tax_id: invoiceForm.buyer_tax_id,
      seller_name: invoiceForm.seller_name,
      seller_tax_id: invoiceForm.seller_tax_id,
      status: 'issued',
      remark: invoiceForm.remark || undefined,
    })
    ElMessage.success('创建成功')
    showAddInvoiceDlg.value = false
    loadInvoices()
  } catch (error) {
    console.error('创建失败:', error)
    ElMessage.error('创建失败')
  } finally {
    invoiceSubmitting.value = false
  }
}

const deleteReceivable = async (row) => {
  await ElMessageBox.confirm(`确定要删除该应收款吗？`, '提示', { type: 'warning' })
  try {
    await apiDeleteReceivable(row.id)
    ElMessage.success('删除成功')
    loadReceivables()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const downloadFile = (fileUrl) => {
  window.open(fileUrl, '_blank')
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
  if (!result.data) return

  const data = result.data

  // 填充表单字段
  if (data.contract_no) formData.contract_no = data.contract_no
  if (data.contract_name) formData.name = data.contract_name
  if (data.customer_name) {
    const matchedCustomer = customers.value.find(c => c.name.includes(data.customer_name) || data.customer_name.includes(c.name))
    if (matchedCustomer) {
      formData.customer_id = matchedCustomer.id
    }
  }
  if (data.amount) formData.amount = parseFloat(data.amount)
  if (data.sign_date) formData.start_date = data.sign_date
  if (data.start_date) formData.start_date = data.start_date
  if (data.end_date) formData.end_date = data.end_date
  if (data.payment_terms) formData.payment_terms = data.payment_terms
  if (data.remarks) formData.remark = data.remarks

  ElMessage.success(`AI 解析成功，置信度：${Math.round((result.confidence || 0) * 100)}%`)
}

// 监听 tab 切换，lazy-load 数据
const handleTabChange = (tabName) => {
  if (tabName === 'receivables') {
    loadReceivables()
  } else if (tabName === 'invoices') {
    loadInvoices()
  } else if (tabName === 'files') {
    loadAttachments()
  }
}

// 加载附件列表
const loadAttachments = async () => {
  if (!route.params.id) return
  filesLoading.value = true
  try {
    const res = await getContractFiles(route.params.id)
    attachments.value = res.items || []
  } catch (error) {
    console.error('加载附件失败:', error)
  } finally {
    filesLoading.value = false
  }
}

// 预览文件
const previewFile = (file) => {
  // 使用完整 URL，因为 iframe 不走 Vite 代理
  const baseUrl = window.location.origin
  previewUrl.value = `${baseUrl}${file.file_url}`
  const ext = file.file_type?.toLowerCase()
  isImagePreview.value = ['jpg', 'jpeg', 'png', 'gif'].includes(ext)
  showPreview.value = true
}

// 删除文件
const deleteFile = async (file) => {
  await ElMessageBox.confirm(`确定要删除文件 "${file.file_name}" 吗？`, '提示', { type: 'warning' })
  try {
    await deleteContractFile(route.params.id, file.id)
    ElMessage.success('删除成功')
    loadAttachments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 获取文件图标
const getFileIcon = (fileType) => {
  const type = fileType?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(type)) return 'Picture'
  return 'Document'
}

// 获取文件图标 class
const getFileIconClass = (fileType) => {
  const type = fileType?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(type)) return 'image-icon'
  if (type === 'pdf') return 'pdf-icon'
  if (['doc', 'docx'].includes(type)) return 'word-icon'
  return ''
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return ''
  const bytes = parseInt(size)
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 处理文件上传成功
const handleFileUploadSuccess = (response) => {
  uploading.value = false
  if (response.id) {
    ElMessage.success('上传成功')
    loadAttachments()
  }
}

// 处理文件上传失败
const handleFileUploadError = (error) => {
  uploading.value = false
  console.error('上传失败:', error)
  ElMessage.error('上传失败')
}

// 监听路由变化（支持浏览器后退）
watch(() => route.params.id, () => {
  if (route.path === '/contracts/new') {
    mode.value = 'create'
  } else if (route.params.id) {
    mode.value = 'view'
    loadContract()
  }
})

// 监听发票类型变化，自动填充购买方或销售方信息
watch([() => invoiceForm.invoice_type, () => companyInfo.value.company_name, () => companyInfo.value.company_tax_id], ([newType, companyName, companyTaxId]) => {
  if (newType === 'sales') {
    // 销项发票：销售方是本公司
    invoiceForm.seller_name = companyName || ''
    invoiceForm.seller_tax_id = companyTaxId || ''
    // 购买方留空，由用户填写
    invoiceForm.buyer_name = ''
    invoiceForm.buyer_tax_id = ''
  } else if (newType === 'purchase') {
    // 进项发票：购买方是本公司
    invoiceForm.buyer_name = companyName || ''
    invoiceForm.buyer_tax_id = companyTaxId || ''
    // 销售方留空，由用户填写
    invoiceForm.seller_name = ''
    invoiceForm.seller_tax_id = ''
  }
}, { immediate: true })

// 监听应收款表单百分比/金额联动
watch([() => receivableForm.percent, () => contractReference.value.amount], ([newPercent, contractAmount]) => {
  if (contractAmount > 0 && newPercent > 0) {
    // 根据百分比计算金额
    const calculatedAmount = Math.round((contractAmount * newPercent) / 100 * 100) / 100
    if (Math.abs(calculatedAmount - receivableForm.amount) > 0.01) {
      receivableForm.amount = calculatedAmount
    }
  }
})

watch(() => receivableForm.amount, (newAmount) => {
  const contractAmount = contractReference.value.amount
  if (contractAmount > 0 && newAmount >= 0) {
    // 根据金额计算百分比
    const calculatedPercent = Math.round((newAmount / contractAmount) * 100 * 100) / 100
    if (Math.abs(calculatedPercent - receivableForm.percent) > 0.01) {
      receivableForm.percent = calculatedPercent
    }
  }
})

// 监听新增应收款对话框显示，自动填充默认值
watch(showAddReceivableDlg, async (newVal) => {
  if (newVal) {
    // 打开对话框时，自动填充未收金额
    const unpaid = contractReference.value.unpaid
    if (unpaid > 0) {
      receivableForm.amount = unpaid
      // 自动计算对应的百分比
      const contractAmount = contractReference.value.amount
      if (contractAmount > 0) {
        receivableForm.percent = Math.round((unpaid / contractAmount) * 100 * 100) / 100
      }
    } else {
      receivableForm.amount = 0
      receivableForm.percent = 0
    }
    receivableForm.due_date = new Date().toISOString().split('T')[0]
    receivableForm.remark = ''
  }
})

onMounted(async () => {
  await loadCustomers()
  await loadCompanyInfo()

  // 根据路由判断模式
  if (route.path === '/contracts/new') {
    mode.value = 'create'
  } else if (route.params.id) {
    mode.value = 'view'
    await loadContract()
  }
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
</script>

<style scoped>
.contract-detail-page {
  padding: 20px;
  height: 100%;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-card {
  margin-bottom: 20px;
}

.info-card :deep(.el-descriptions__label) {
  width: 120px;
  font-weight: 500;
}

.info-value {
  font-weight: 500;
}

.amount {
  color: #f56c6c;
  font-weight: 600;
  font-size: 16px;
}

.tabs-card {
  flex: 1;
  overflow: hidden;
}

.tabs-card :deep(.el-tabs__content) {
  padding: 20px;
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}

.tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

.overdue {
  color: #f56c6c;
  font-weight: 500;
}

.received {
  color: #67c23a;
  font-weight: 500;
}

.unpaid {
  color: #f56c6c;
  font-weight: 500;
}

.receivable-summary {
  margin-top: 20px;
}

.invoice-summary {
  margin-top: 20px;
  margin-bottom: 15px;
}

.invoice-summary .sales {
  color: #67c23a;
  font-weight: 500;
}

.invoice-summary .purchase {
  color: #909399;
  font-weight: 500;
}

.invoice-summary .net-positive {
  color: #67c23a;
  font-weight: 500;
}

.invoice-summary .net-negative {
  color: #f56c6c;
  font-weight: 500;
}

.contract-ref-info {
  margin-bottom: 15px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

.file-section h4 {
  margin: 15px 0 10px;
  color: #303133;
  font-size: 14px;
}

.file-list {
  margin-bottom: 15px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 10px;
}

.file-item:hover {
  background: #ecf5ff;
}

.file-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.file-icon.image-icon {
  color: #67c23a;
}

.file-icon.pdf-icon {
  color: #f56c6c;
}

.file-icon.word-icon {
  color: #409eff;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.no-file {
  color: #909399;
  font-size: 14px;
  padding: 20px;
  text-align: center;
}

.upload-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.preview-container {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
}

.no-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
}

.no-preview .el-icon {
  margin-bottom: 16px;
}

.no-preview p {
  margin: 0;
  font-size: 14px;
}
</style>
