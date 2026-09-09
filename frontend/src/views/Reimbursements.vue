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
        <el-button
          type="success"
          :disabled="selectedReimbursements.length === 0"
          @click="exportToExcel"
        >
          <el-icon><Download /></el-icon> 导出 Excel ({{ selectedReimbursements.length }})
        </el-button>
        <el-button
          type="warning"
          :disabled="selectedReimbursements.length === 0"
          @click="handleBatchPaymentExport"
        >
          <el-icon><Download /></el-icon> 导出批量支付 ({{ selectedReimbursements.length }})
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
            <el-option v-for="c in expenseCategories" :key="c.value" :label="c.label" :value="c.value" />
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
        <el-form-item label="支付方">
          <el-select
            v-model="searchForm.payer_company"
            placeholder="全部支付方"
            clearable
            filterable
            @change="handleSearch"
            style="width: 180px"
          >
            <el-option v-for="name in payerCompanies" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="种类">
          <el-select v-model="searchForm.reimbursement_kind" placeholder="全部种类" clearable @change="handleSearch" style="width: 180px">
            <el-option v-for="k in kindOptions" :key="k.value" :label="k.label" :value="k.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报销单列表 -->
    <el-card class="table-card">
      <div class="statistics-bar" v-if="selectedReimbursements.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedReimbursements.length }} 张报销单</el-tag>
        <span class="stat-item">合计金额：<span class="stat-value">¥{{ selectedTotalAmount.toLocaleString() }}</span></span>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" border stripe @selection-change="handleSelectionChange" ref="tableRef">
        <el-table-column type="selection" width="55" />
        <el-table-column label="种类" width="120">
          <template #default="{ row }">
            <el-tag :type="row.reimbursement_kind === 'allowance_travel' ? 'warning' : (row.reimbursement_kind === 'invoice_personal' ? 'success' : '')" size="small">
              {{ getKindLabel(row.reimbursement_kind) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="编号" width="120">
          <template #default="{ row }">
            <span class="reim-id" @click="openDetail(row)">{{ formatId(row.id) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商/收款方" width="150" />
        <el-table-column prop="payer_company" label="支付方" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.payer_company" type="info" effect="plain">{{ row.payer_company }}</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="isAdmin && (row.status === 'approved' || row.status === 'paid')"
              link
              type="warning"
              @click="openAdminEdit(row)"
            >补充修改</el-button>
            <template v-if="row.status === 'draft'">
              <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="success" @click="handleSubmit(row)">提交</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
            <template v-else-if="row.status === 'pending' && row.can_approve">
              <el-button link type="success" @click="openApproveDialog(row)">审核通过</el-button>
              <el-button link type="danger" @click="openRejectDialog(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'approved' && row.can_pay">
              <el-button link type="success" @click="handlePay(row)">确认支付</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button link type="primary" @click="handleEdit(row)">修改重提</el-button>
              <el-button link type="info" @click="showRejectReason(row)">查看原因</el-button>
            </template>
            <template v-else-if="row.status === 'paid'">
              <el-button link type="info" @click="openDetail(row)">查看</el-button>
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
        <!-- 报销种类 -->
        <el-divider content-position="left">报销种类</el-divider>
        <el-form-item label="种类" prop="reimbursement_kind">
          <el-radio-group v-model="formData.reimbursement_kind">
            <el-radio v-for="k in kindOptions" :key="k.value" :label="k.value">{{ k.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出差信息" v-if="formData.reimbursement_kind === 'allowance_travel'">
          <el-row :gutter="12" style="width: 100%">
            <el-col :span="8">
              <el-date-picker
                v-model="formData.travel_start_date"
                type="date"
                placeholder="开始日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="8">
              <el-date-picker
                v-model="formData.travel_end_date"
                type="date"
                placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="8">
              <el-input v-model="formData.travel_destination" placeholder="出差地点（可选）" />
            </el-col>
          </el-row>
        </el-form-item>

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
            <el-form-item label="支行">
              <el-input v-model="formData.supplier_bank_branch" placeholder="支行名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="开户行省份">
              <el-input v-model="formData.supplier_bank_province" placeholder="开户行所在省份" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开户行城市">
              <el-input v-model="formData.supplier_bank_city" placeholder="开户行所在城市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联行号">
              <el-input v-model="formData.supplier_bank_code" placeholder="12位联行号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
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
            <el-form-item :label="formData.reimbursement_kind === 'allowance_travel' ? '津贴金额' : '报销金额(不含税)'" prop="amount">
              <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="formData.reimbursement_kind !== 'allowance_travel'">
            <el-form-item label="税额">
              <el-input-number v-model="formData.tax_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="formData.reimbursement_kind === 'allowance_travel' ? '合计' : '价税合计'">
          <el-input-number v-model="formData.total_amount" :min="0" :precision="2" style="width: 100%" disabled />
        </el-form-item>

        <!-- 分类和关联 -->
        <el-divider content-position="left">分类与关联</el-divider>
        <el-row :gutter="16">
          <el-col :span="12" v-if="formData.reimbursement_kind !== 'allowance_travel'">
            <el-form-item label="费用分类" prop="expense_category">
              <el-select v-model="formData.expense_category" style="width: 100%" filterable allow-create>
                <el-option v-for="c in expenseCategories" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="支付方" prop="payer_company">
              <el-select
                v-model="formData.payer_company"
                placeholder="选择支付方公司"
                clearable
                filterable
                allow-create
                style="width: 100%"
              >
                <el-option v-for="name in payerCompanies" :key="name" :label="name" :value="name" />
              </el-select>
              <div class="form-tip" v-if="!payerCompanies.length">尚未配置支付方，请到 系统设置 → 报销设置 中维护。</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16" v-if="formData.reimbursement_kind !== 'allowance_travel'">
          <el-col :span="12">
            <el-form-item label="关联发票">
              <el-select v-model="formData.invoice_id" placeholder="选择进项发票（可选）" clearable style="width: 100%">
                <el-option v-for="inv in purchaseInvoices" :key="inv.id" :label="inv.invoice_no" :value="inv.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联合同">
              <el-select v-model="formData.contract_id" placeholder="选择合同（可选）" clearable style="width: 100%">
                <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <div class="form-tip" v-if="formData.reimbursement_kind === 'allowance_travel'">出差津贴无需税额/费用分类（自动归入"差旅"），无需关联发票。可上传 Excel 出差明细作为附件（可选）。</div>

        <!-- 附件上传 -->
        <el-divider content-position="left">附件</el-divider>
        <el-form-item label="发票/票据文件">
          <AttachmentUploader
            :initial-value="formData.files"
            :refresh-key="attachmentUploaderKey"
            accept-types=".pdf,.jpg,.jpeg,.png"
            @change="handleAttachmentChange"
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
            <el-option v-for="c in expenseCategories" :key="c.value" :label="c.label" :value="c.value" />
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

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" direction="rtl" size="520px" :with-header="false">
      <div class="detail-drawer" v-loading="detailLoading">
        <template v-if="detailData">
          <div class="detail-header">
            <div class="detail-title">
              <span class="detail-id">{{ formatId(detailData.id) }}</span>
              <el-tag :type="getStatusType(detailData.status)">{{ getStatusLabel(detailData.status) }}</el-tag>
              <el-tag size="small" effect="plain">{{ getKindLabel(detailData.reimbursement_kind) }}</el-tag>
            </div>
            <div class="detail-id-full">{{ detailData.id }}</div>
          </div>

          <el-divider content-position="left">基本信息</el-divider>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="供应商/收款方">{{ detailData.supplier_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="支付方">{{ detailData.payer_company || '—' }}</el-descriptions-item>
            <el-descriptions-item label="报销金额(不含税)">¥{{ Number(detailData.amount || 0).toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item v-if="detailData.reimbursement_kind !== 'allowance_travel'" label="税额">¥{{ Number(detailData.tax_amount || 0).toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="价税合计">¥{{ Number(detailData.total_amount || 0).toLocaleString() }}</el-descriptions-item>
            <el-descriptions-item label="费用分类">{{ getCategoryLabel(detailData.expense_category) }}</el-descriptions-item>
            <template v-if="detailData.reimbursement_kind === 'allowance_travel'">
              <el-descriptions-item label="出差开始">{{ detailData.travel_start_date || '—' }}</el-descriptions-item>
              <el-descriptions-item label="出差结束">{{ detailData.travel_end_date || '—' }}</el-descriptions-item>
              <el-descriptions-item label="出差地点">{{ detailData.travel_destination || '—' }}</el-descriptions-item>
            </template>
            <el-descriptions-item label="备注">{{ detailData.remark || '—' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">收款账号</el-divider>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="税号">{{ detailData.supplier_tax_id || '—' }}</el-descriptions-item>
            <el-descriptions-item label="开户行">{{ detailData.supplier_bank_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="支行">{{ detailData.supplier_bank_branch || '—' }}</el-descriptions-item>
            <el-descriptions-item label="开户行省份">{{ detailData.supplier_bank_province || '—' }}</el-descriptions-item>
            <el-descriptions-item label="开户行城市">{{ detailData.supplier_bank_city || '—' }}</el-descriptions-item>
            <el-descriptions-item label="联行号">{{ detailData.supplier_bank_code || '—' }}</el-descriptions-item>
            <el-descriptions-item label="银行账号">{{ detailData.supplier_bank_account || '—' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">发票附件</el-divider>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="关联发票号">{{ detailData.invoice_no || '—' }}</el-descriptions-item>
            <el-descriptions-item label="发票代码">{{ detailData.invoice_code || '—' }}</el-descriptions-item>
          </el-descriptions>
          <div class="detail-files" v-if="detailData.files && detailData.files.length">
            <div class="detail-file-item" v-for="f in detailData.files" :key="f.file_id">
              <span class="detail-file-name">{{ f.file_name || '票据附件' }}</span>
              <el-button link type="primary" @click="openFile(f.file_url)">
                <el-icon><Document /></el-icon> 查看
              </el-button>
            </div>
          </div>
          <div v-else class="detail-empty">未上传附件</div>

          <el-divider content-position="left">操作信息</el-divider>
          <el-timeline>
            <el-timeline-item :timestamp="formatDate(detailData.created_at)" type="primary">
              录入 — {{ detailData.creator_name || '—' }}
            </el-timeline-item>
            <el-timeline-item
              v-if="detailData.status === 'rejected'"
              :timestamp="detailData.approved_at ? formatDate(detailData.approved_at) : ''"
              type="danger"
            >
              已驳回 — {{ detailData.approver_name || '—' }}
              <div v-if="detailData.reject_reason" class="reject-reason">原因：{{ detailData.reject_reason }}</div>
            </el-timeline-item>
            <el-timeline-item
              v-else-if="detailData.approved_at"
              :timestamp="formatDate(detailData.approved_at)"
              type="success"
            >
              审核通过 — {{ detailData.approver_name || '—' }}
            </el-timeline-item>
            <el-timeline-item
              v-if="detailData.paid_at"
              :timestamp="formatDate(detailData.paid_at)"
              type="success"
            >
              确认支付 — {{ detailData.payer_name || '—' }}
            </el-timeline-item>
          </el-timeline>
        </template>
      </div>
      <template #footer>
        <el-button
          v-if="isAdmin && detailData && (detailData.status === 'approved' || detailData.status === 'paid')"
          type="warning"
          @click="editFromDetail"
        >补充修改</el-button>
        <el-button @click="showDetailDrawer = false">关闭</el-button>
      </template>
    </el-drawer>

    <!-- 管理员补充修改抽屉（已审核/已支付） -->
    <el-drawer v-model="showAdminEdit" direction="rtl" size="520px" title="补充修改报销单">
      <el-form :model="adminEditForm" label-width="120px">
        <el-divider content-position="left">关联信息</el-divider>
        <el-form-item label="关联发票">
          <el-select v-model="adminEditForm.invoice_id" placeholder="选择进项发票（可选）" clearable style="width: 100%">
            <el-option v-for="inv in purchaseInvoices" :key="inv.id" :label="inv.invoice_no" :value="inv.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="adminEditForm.remark" type="textarea" :rows="2" />
        </el-form-item>

        <el-divider content-position="left">银行信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开户行">
              <el-input v-model="adminEditForm.supplier_bank_name" placeholder="开户银行名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="支行">
              <el-input v-model="adminEditForm.supplier_bank_branch" placeholder="支行名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开户行省份">
              <el-input v-model="adminEditForm.supplier_bank_province" placeholder="省份" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户行城市">
              <el-input v-model="adminEditForm.supplier_bank_city" placeholder="城市" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联行号">
              <el-input v-model="adminEditForm.supplier_bank_code" placeholder="12位联行号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="银行账号">
          <el-input v-model="adminEditForm.supplier_bank_account" placeholder="银行账号" />
        </el-form-item>

        <el-divider content-position="left">附件</el-divider>
        <el-form-item label="票据附件">
          <AttachmentUploader
            :initial-value="adminFiles"
            :refresh-key="adminUploaderKey"
            accept-types=".pdf,.jpg,.jpeg,.png"
            @change="handleAdminFilesChange"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdminEdit = false">取消</el-button>
        <el-button type="primary" :loading="adminSubmitting" @click="saveAdminEdit">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick, Download, Document } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import * as XLSX from 'xlsx'
import {
  getReimbursements,
  getReimbursement,
  createReimbursement,
  updateReimbursement,
  deleteReimbursement,
  submitReimbursement,
  approveReimbursement,
  rejectReimbursement,
  payReimbursement,
  getReimbursementStatistics,
  getReimbursementPayerCompanies,
  getReimbursementExpenseCategories,
  exportBatchPayment,
} from '@/api/reimbursement'
import { getInvoices } from '@/api/invoice'
import { getContracts } from '@/api/contract'
import { searchSuppliers } from '@/api/supplier'
import AttachmentUploader from '@/components/AttachmentUploader.vue'
import AiReimbursementImportDrawer from '@/components/AiReimbursementImportDrawer.vue'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const showAiImportDrawer = ref(false)
const showApproveDialog = ref(false)
const showRejectDialog = ref(false)
const showDetailDrawer = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const formRef = ref(null)
const rejectFormRef = ref(null)
const tableRef = ref(null)
const tableData = ref([])
const purchaseInvoices = ref([])
const contracts = ref([])
const payerCompanies = ref([])
const expenseCategories = ref([])
const selectedReimbursements = ref([])

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const showAdminEdit = ref(false)
const adminSubmitting = ref(false)
const adminUploaderKey = ref(0)
const adminFiles = ref([])
const adminEditForm = reactive({
  id: '',
  remark: '',
  invoice_id: '',
  supplier_bank_name: '',
  supplier_bank_branch: '',
  supplier_bank_province: '',
  supplier_bank_city: '',
  supplier_bank_code: '',
  supplier_bank_account: '',
})

const selectedTotalAmount = computed(() => {
  return selectedReimbursements.value.reduce((sum, r) => sum + Number(r.total_amount || 0), 0)
})

const handleSelectionChange = (selection) => {
  selectedReimbursements.value = selection
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
  selectedReimbursements.value = []
}

const exportToExcel = () => {
  if (selectedReimbursements.value.length === 0) {
    ElMessage.warning('请先选择要导出的报销单')
    return
  }
  const rows = selectedReimbursements.value.map((r, idx) => ({
    '序号': idx + 1,
    '编号': formatId(r.id),
    '完整编号': r.id,
    '种类': getKindLabel(r.reimbursement_kind),
    '供应商/收款方': r.supplier_name || '',
    '税号': r.supplier_tax_id || '',
    '开户行': r.supplier_bank_name || '',
    '支行': r.supplier_bank_branch || '',
    '开户行省份': r.supplier_bank_province || '',
    '开户行城市': r.supplier_bank_city || '',
    '联行号': r.supplier_bank_code || '',
    '银行账号': r.supplier_bank_account || '',
    '报销金额(不含税)': Number(r.amount || 0),
    '税额': Number(r.tax_amount || 0),
    '价税合计': Number(r.total_amount || 0),
    '费用分类': getCategoryLabel(r.expense_category),
    '支付方': r.payer_company || '',
    '出差开始': r.travel_start_date || '',
    '出差结束': r.travel_end_date || '',
    '出差地点': r.travel_destination || '',
    '状态': getStatusLabel(r.status),
    '录入人': r.creator_name || '',
    '审核人': r.approver_name || '',
    '支付确认人': r.payer_name || '',
    '创建时间': formatDate(r.created_at),
    '审核时间': r.approved_at ? formatDate(r.approved_at) : '',
    '支付时间': r.paid_at ? formatDate(r.paid_at) : '',
    '驳回原因': r.reject_reason || '',
    '备注': r.remark || '',
  }))
  const ws = XLSX.utils.json_to_sheet(rows)
  // 设置列宽
  ws['!cols'] = [
    { wch: 6 },   // 序号
    { wch: 14 },  // 编号
    { wch: 36 },  // 完整编号
    { wch: 14 },  // 种类
    { wch: 20 },  // 供应商
    { wch: 18 },  // 税号
    { wch: 20 },  // 开户行
    { wch: 18 },  // 支行
    { wch: 14 },  // 开户行省份
    { wch: 14 },  // 开户行城市
    { wch: 14 },  // 联行号
    { wch: 22 },  // 银行账号
    { wch: 14 },  // 报销金额
    { wch: 12 },  // 税额
    { wch: 14 },  // 价税合计
    { wch: 12 },  // 费用分类
    { wch: 18 },  // 支付方
    { wch: 14 },  // 出差开始
    { wch: 14 },  // 出差结束
    { wch: 18 },  // 出差地点
    { wch: 10 },  // 状态
    { wch: 12 },  // 录入人
    { wch: 12 },  // 审核人
    { wch: 12 },  // 支付确认人
    { wch: 20 },  // 创建时间
    { wch: 20 },  // 审核时间
    { wch: 20 },  // 支付时间
    { wch: 24 },  // 驳回原因
    { wch: 30 },  // 备注
  ]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '报销单')
  const dateStr = new Date().toISOString().slice(0, 10)
  XLSX.writeFile(wb, `报销单导出_${dateStr}.xlsx`)
  ElMessage.success(`已导出 ${rows.length} 张报销单`)
}

const handleBatchPaymentExport = async () => {
  if (selectedReimbursements.value.length === 0) {
    ElMessage.warning('请先选择要导出的报销单')
    return
  }
  try {
    const ids = selectedReimbursements.value.map(r => r.id)
    const response = await exportBatchPayment(ids)
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    const dateStr = new Date().toISOString().slice(0, 10)
    link.setAttribute('download', `批量支付_${dateStr}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success(`已导出 ${ids.length} 张报销单为批量支付格式`)
  } catch (error) {
    ElMessage.error('导出批量支付失败')
  }
}
const attachmentUploaderKey = ref(0)
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
  payer_company: '',
  reimbursement_kind: '',
  year: null,
  search: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const kindOptions = [
  { value: 'invoice_company', label: '发票·公司直付' },
  { value: 'invoice_personal', label: '发票·个人垫付' },
  { value: 'allowance_travel', label: '出差津贴' },
]

const getKindLabel = (kind) => {
  const found = kindOptions.find(o => o.value === kind)
  return found ? found.label : (kind || '-')
}

const formData = reactive({
  id: '',
  supplier_name: '',
  supplier_tax_id: '',
  supplier_bank_name: '',
  supplier_bank_branch: '',
  supplier_bank_province: '',
  supplier_bank_city: '',
  supplier_bank_code: '',
  supplier_bank_account: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_category: 'other',
  payer_company: '',
  invoice_id: '',
  contract_id: '',
  remark: '',
  file_id: '',
  file_url: '',
  files: [],
  reimbursement_kind: 'invoice_company',
  travel_start_date: null,
  travel_end_date: null,
  travel_destination: '',
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

const getCategoryLabel = (category) => {
  const found = expenseCategories.value.find(c => c.value === category)
  if (found) return found.label
  return categoryLabels[category] || category
}
const getStatusLabel = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || 'info'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

// 报销单编号显示用：BX + UUID 前 8 位（便于区分）
const formatId = (id) => {
  if (!id) return ''
  const short = id.replace(/-/g, '').slice(0, 8).toUpperCase()
  return `BX-${short}`
}

const openDetail = async (row) => {
  showDetailDrawer.value = true
  detailData.value = row
  detailLoading.value = true
  try {
    const res = await getReimbursement(row.id)
    detailData.value = res
  } catch (error) {
    ElMessage.error('加载报销单详情失败')
  } finally {
    detailLoading.value = false
  }
}

const openFile = (url) => {
  if (!url) return
  window.open(url, '_blank')
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
  formData.supplier_bank_branch = item.bank_branch || ''
  formData.supplier_bank_province = item.bank_province || ''
  formData.supplier_bank_city = item.city || ''
  formData.supplier_bank_code = item.bank_code || ''
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
      payer_company: searchForm.payer_company,
      reimbursement_kind: searchForm.reimbursement_kind,
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

const loadPayerCompanies = async () => {
  try {
    const res = await getReimbursementPayerCompanies()
    payerCompanies.value = res.items || []
  } catch (error) {
    console.error('加载支付方列表失败:', error)
    payerCompanies.value = []
  }
}

const loadExpenseCategories = async () => {
  try {
    const res = await getReimbursementExpenseCategories()
    expenseCategories.value = res.items || []
  } catch (error) {
    console.error('加载费用分类失败:', error)
    expenseCategories.value = []
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
  searchForm.payer_company = ''
  searchForm.reimbursement_kind = ''
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
    supplier_bank_branch: '',
    supplier_bank_province: '',
    supplier_bank_city: '',
    supplier_bank_code: '',
    supplier_bank_account: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_category: 'other',
    payer_company: '',
    invoice_id: '',
    contract_id: '',
    remark: '',
    file_id: '',
    file_url: '',
    files: [],
    reimbursement_kind: 'invoice_company',
    travel_start_date: null,
    travel_end_date: null,
    travel_destination: '',
  })
  attachmentUploaderKey.value++
  // 在打开对话框时加载发票和合同列表
  loadPurchaseInvoices()
  loadContracts()
  loadPayerCompanies()
  loadExpenseCategories()
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, {
    id: row.id,
    supplier_name: row.supplier_name,
    supplier_tax_id: row.supplier_tax_id || '',
    supplier_bank_name: row.supplier_bank_name || '',
    supplier_bank_branch: row.supplier_bank_branch || '',
    supplier_bank_province: row.supplier_bank_province || '',
    supplier_bank_city: row.supplier_bank_city || '',
    supplier_bank_code: row.supplier_bank_code || '',
    supplier_bank_account: row.supplier_bank_account || '',
    amount: Number(row.amount),
    tax_amount: Number(row.tax_amount || 0),
    total_amount: Number(row.total_amount),
    expense_category: row.expense_category,
    payer_company: row.payer_company || '',
    invoice_id: row.invoice_id || '',
    contract_id: row.contract_id || '',
    remark: row.remark || '',
    file_id: row.file_id || '',
    file_url: row.file_url || '',
    files: (row.files || []).map((f) => ({
      file_id: f.file_id,
      file_name: f.file_name,
      file_url: f.file_url,
      file_type: f.file_type,
      file_size: f.file_size,
    })),
    reimbursement_kind: row.reimbursement_kind || 'invoice_company',
    travel_start_date: row.travel_start_date || null,
    travel_end_date: row.travel_end_date || null,
    travel_destination: row.travel_destination || '',
  })
  attachmentUploaderKey.value++
  // 在打开对话框时加载发票和合同列表
  loadPurchaseInvoices()
  loadContracts()
  loadPayerCompanies()
  loadExpenseCategories()
}

// 处理附件变化（多文件）
const handleAttachmentChange = (files) => {
  formData.files = files || []
  if (formData.files.length) {
    formData.file_id = formData.files[0].file_id
    formData.file_url = formData.files[0].file_url
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
        const isAllowance = formData.reimbursement_kind === 'allowance_travel'
        const data = {
          ...formData,
          // 津贴场景：无税，分类强制差旅
          ...(isAllowance ? {
            tax_amount: 0,
            total_amount: Number(formData.amount),
            expense_category: 'travel',
            supplier_tax_id: null,
          } : {
            total_amount: Number(formData.amount) + Number(formData.tax_amount),
          }),
        }
        // 移除空字符串字段
        Object.keys(data).forEach(key => {
          if (data[key] === '') {
            data[key] = null
          }
        })
        // 日期空串转 null
        if (data.travel_start_date === '') data.travel_start_date = null
        if (data.travel_end_date === '') data.travel_end_date = null
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

const showRejectReason = (row) => {
  ElMessageBox.alert(row.reject_reason || '无驳回原因', '驳回原因', { type: 'warning' })
}

const editFromDetail = () => {
  const row = detailData.value
  showDetailDrawer.value = false
  if (row) openAdminEdit(row)
}

const openAdminEdit = (row) => {
  Object.assign(adminEditForm, {
    id: row.id,
    remark: row.remark || '',
    invoice_id: row.invoice_id || '',
    supplier_bank_name: row.supplier_bank_name || '',
    supplier_bank_branch: row.supplier_bank_branch || '',
    supplier_bank_province: row.supplier_bank_province || '',
    supplier_bank_city: row.supplier_bank_city || '',
    supplier_bank_code: row.supplier_bank_code || '',
    supplier_bank_account: row.supplier_bank_account || '',
  })
  adminFiles.value = (row.files || []).map((f) => ({
    file_id: f.file_id,
    file_name: f.file_name,
    file_url: f.file_url,
    file_type: f.file_type,
    file_size: f.file_size,
  }))
  adminUploaderKey.value++
  loadPurchaseInvoices()
  showAdminEdit.value = true
}

const handleAdminFilesChange = (files) => {
  adminFiles.value = files || []
}

const saveAdminEdit = async () => {
  adminSubmitting.value = true
  try {
    const data = {
      remark: adminEditForm.remark || null,
      invoice_id: adminEditForm.invoice_id || null,
      supplier_bank_name: adminEditForm.supplier_bank_name || null,
      supplier_bank_branch: adminEditForm.supplier_bank_branch || null,
      supplier_bank_province: adminEditForm.supplier_bank_province || null,
      supplier_bank_city: adminEditForm.supplier_bank_city || null,
      supplier_bank_code: adminEditForm.supplier_bank_code || null,
      supplier_bank_account: adminEditForm.supplier_bank_account || null,
      files: adminFiles.value,
    }
    await updateReimbursement(adminEditForm.id, data)
    ElMessage.success('保存成功')
    showAdminEdit.value = false
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    adminSubmitting.value = false
  }
}

const handleAiImportSuccess = () => {
  showAiImportDrawer.value = false
  loadReimbursements()
  loadStatistics()
}

onMounted(() => {
  loadReimbursements()
  loadStatistics()
  loadPayerCompanies()
  loadExpenseCategories()
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

.text-muted {
  color: #c0c4cc;
}

.reim-id {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
  user-select: none;
}

.reim-id:hover {
  text-decoration: underline;
}

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

.statistics-bar .stat-item {
  font-size: 14px;
  color: #606266;
}

.statistics-bar .stat-value {
  font-weight: bold;
  color: #409eff;
  font-size: 16px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 4px;
}

.detail-drawer {
  padding: 0 8px;
}

.detail-header {
  margin-bottom: 8px;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.detail-id {
  font-family: monospace;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.detail-id-full {
  font-family: monospace;
  font-size: 12px;
  color: #909399;
  word-break: break-all;
}

.detail-files {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.detail-file-name {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-empty {
  margin-top: 12px;
  font-size: 13px;
  color: #c0c4cc;
}

.reject-reason {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
}
</style>
