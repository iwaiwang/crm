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
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 收款方列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="收款方名称" width="180" />
        <el-table-column prop="tax_id" label="税号" width="150" />
        <el-table-column prop="bank_name" label="开户行" width="180" />
        <el-table-column prop="bank_account" label="银行账号" width="150" />
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="120" />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
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
      size="500px"
      direction="rtl"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="收款方名称" prop="name">
          <el-input v-model="formData.name" placeholder="公司/个人名称" />
        </el-form-item>
        <el-form-item label="税号">
          <el-input v-model="formData.tax_id" placeholder="纳税人识别号" />
        </el-form-item>
        <el-form-item label="开户行">
          <el-input v-model="formData.bank_name" placeholder="银行名称" />
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="formData.bank_account" placeholder="银行账号" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="formData.contact_person" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="formData.contact_phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="formData.address" placeholder="地址" />
        </el-form-item>
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
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  name: '',
  tax_id: '',
  bank_name: '',
  bank_account: '',
  contact_person: '',
  contact_phone: '',
  address: '',
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
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    name: '',
    tax_id: '',
    bank_name: '',
    bank_account: '',
    contact_person: '',
    contact_phone: '',
    address: '',
    remark: '',
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    tax_id: row.tax_id || '',
    bank_name: row.bank_name || '',
    bank_account: row.bank_account || '',
    contact_person: row.contact_person || '',
    contact_phone: row.contact_phone || '',
    address: row.address || '',
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
</style>