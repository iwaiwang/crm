<template>
  <div class="suppliers-page">
    <div class="page-header">
      <h2>收款方管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增收款方
      </el-button>
    </div>

    <!-- 搜索 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="名称">
          <el-input v-model="searchForm.search" placeholder="收款方名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.supplier_type" placeholder="全部类型" clearable style="width: 120px">
            <el-option label="企业" value="company" />
            <el-option label="个人" value="individual" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="活跃" value="active" />
            <el-option label="暂停合作" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 收款方列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="收款方名称" min-width="150" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.supplier_type === 'company' ? 'primary' : 'info'" size="small">
              {{ getSupplierTypeLabel(row.supplier_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tax_id" label="税号/身份证" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.supplier_type === 'individual' ? row.id_card : row.tax_id }}
          </template>
        </el-table-column>
        <el-table-column label="银行账户" min-width="200">
          <template #default="{ row }">
            <div v-if="row.bank_name">
              <div>{{ row.bank_name }} {{ row.bank_branch }}</div>
              <div class="text-muted">{{ row.bank_province }} | {{ row.bank_account }}</div>
              <div v-if="row.bank_code" class="text-muted">联行号: {{ row.bank_code }}</div>
            </div>
            <span v-else class="text-muted">未填写</span>
          </template>
        </el-table-column>
        <el-table-column label="账户类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.account_type === 'corporate' ? 'success' : 'warning'" size="small">
              {{ getAccountTypeLabel(row.account_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="电话" width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_term" label="账期" width="80">
          <template #default="{ row }">
            {{ row.payment_term }}天
          </template>
        </el-table-column>
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
          @current-change="loadSuppliers"
          @size-change="loadSuppliers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-drawer
      v-model="showDialog"
      :title="formData.id ? '编辑收款方' : '新增收款方'"
      size="600px"
      direction="rtl"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="110px">
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="收款方名称" prop="name">
          <el-input v-model="formData.name" placeholder="公司/个人名称" />
        </el-form-item>
        <el-form-item label="收款方类型" prop="supplier_type">
          <el-radio-group v-model="formData.supplier_type">
            <el-radio label="company">企业</el-radio>
            <el-radio label="individual">个人</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="税号" v-if="formData.supplier_type === 'company'">
          <el-input v-model="formData.tax_id" placeholder="统一社会信用代码" />
        </el-form-item>
        <el-form-item label="身份证号" v-if="formData.supplier_type === 'individual'">
          <el-input v-model="formData.id_card" placeholder="身份证号码" />
        </el-form-item>

        <!-- 银行账户信息 -->
        <el-divider content-position="left">银行账户信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开户行">
              <el-input v-model="formData.bank_name" placeholder="如: 中国工商银行" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户行省份">
              <el-input v-model="formData.bank_province" placeholder="如: 北京市" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="支行名称">
              <el-input v-model="formData.bank_branch" placeholder="如: 朝阳支行" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联行号">
              <el-input v-model="formData.bank_code" placeholder="12位联行号" maxlength="12" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="银行账号">
              <el-input v-model="formData.bank_account" placeholder="银行账号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账户类型">
              <el-radio-group v-model="formData.account_type">
                <el-radio label="corporate">对公账户</el-radio>
                <el-radio label="personal">个人账户</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 地址信息 -->
        <el-divider content-position="left">地址信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="省份">
              <el-input v-model="formData.province" placeholder="省份" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="城市">
              <el-input v-model="formData.city" placeholder="城市" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="详细地址">
          <el-input v-model="formData.address" placeholder="详细地址" />
        </el-form-item>

        <!-- 联系信息 -->
        <el-divider content-position="left">联系信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="formData.contact_person" placeholder="联系人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="formData.contact_phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="邮箱">
          <el-input v-model="formData.email" placeholder="用于发送付款通知" />
        </el-form-item>

        <!-- 业务信息 -->
        <el-divider content-position="left">业务信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合作状态">
              <el-radio-group v-model="formData.status">
                <el-radio label="active">活跃</el-radio>
                <el-radio label="inactive">暂停合作</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="付款账期">
              <el-input-number v-model="formData.payment_term" :min="0" :max="365" placeholder="天数" />
              <span style="margin-left: 8px">天</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="付款方式">
          <el-radio-group v-model="formData.payment_method">
            <el-radio label="transfer">电汇</el-radio>
            <el-radio label="check">支票</el-radio>
            <el-radio label="cash">现金</el-radio>
            <el-radio label="other">其他</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 备注 -->
        <el-divider content-position="left">备注</el-divider>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getSuppliers, createSupplier, updateSupplier, deleteSupplier } from '@/api/supplier'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])

const searchForm = reactive({
  search: '',
  supplier_type: '',
  status: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  name: '',
  supplier_type: 'company',
  tax_id: '',
  id_card: '',
  bank_name: '',
  bank_province: '',
  bank_branch: '',
  bank_account: '',
  bank_code: '',
  account_type: 'corporate',
  province: '',
  city: '',
  address: '',
  contact_person: '',
  contact_phone: '',
  email: '',
  status: 'active',
  payment_term: 30,
  payment_method: 'transfer',
  remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入收款方名称', trigger: 'blur' }],
}

const loadSuppliers = async () => {
  loading.value = true
  try {
    const res = await getSuppliers({
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchForm.search,
      supplier_type: searchForm.supplier_type,
      status: searchForm.status,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error('加载收款方列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadSuppliers()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.supplier_type = ''
  searchForm.status = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    name: '',
    supplier_type: 'company',
    tax_id: '',
    id_card: '',
    bank_name: '',
    bank_province: '',
    bank_branch: '',
    bank_account: '',
    bank_code: '',
    account_type: 'corporate',
    province: '',
    city: '',
    address: '',
    contact_person: '',
    contact_phone: '',
    email: '',
    status: 'active',
    payment_term: 30,
    payment_method: 'transfer',
    remark: '',
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    supplier_type: row.supplier_type || 'company',
    tax_id: row.tax_id || '',
    id_card: row.id_card || '',
    bank_name: row.bank_name || '',
    bank_province: row.bank_province || '',
    bank_branch: row.bank_branch || '',
    bank_account: row.bank_account || '',
    bank_code: row.bank_code || '',
    account_type: row.account_type || 'corporate',
    province: row.province || '',
    city: row.city || '',
    address: row.address || '',
    contact_person: row.contact_person || '',
    contact_phone: row.contact_phone || '',
    email: row.email || '',
    status: row.status || 'active',
    payment_term: row.payment_term || 30,
    payment_method: row.payment_method || 'transfer',
    remark: row.remark || '',
  })
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = { ...formData }
        // 移除空字符串字段
        Object.keys(data).forEach(key => {
          if (data[key] === '') {
            data[key] = null
          }
        })
        if (formData.id) {
          await updateSupplier(formData.id, data)
          ElMessage.success('更新成功')
        } else {
          await createSupplier(data)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadSuppliers()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除此收款方？', '提示', { type: 'warning' })
    await deleteSupplier(row.id)
    ElMessage.success('删除成功')
    loadSuppliers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 类型映射
const getSupplierTypeLabel = (type) => {
  const map = { company: '企业', individual: '个人' }
  return map[type] || type
}

const getAccountTypeLabel = (type) => {
  const map = { corporate: '对公', personal: '个人' }
  return map[type] || type
}

const getStatusLabel = (status) => {
  const map = { active: '活跃', inactive: '暂停' }
  return map[status] || status
}

onMounted(() => {
  loadSuppliers()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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

.text-muted {
  color: #909399;
  font-size: 12px;
}

.el-divider {
  margin: 16px 0;
}
</style>