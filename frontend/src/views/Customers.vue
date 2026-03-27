<template>
  <div class="customers-page">
    <div class="page-header">
      <h2>客户管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增客户
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="客户名称/联系人/电话"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="searchForm.category" placeholder="全部分类" clearable>
            <el-option label="潜在" value="potential" />
            <el-option label="普通" value="normal" />
            <el-option label="VIP" value="vip" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="suspended" />
            <el-option label="流失" value="lost" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 客户列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="客户名称" min-width="150" />
        <el-table-column prop="contact" label="联系人" width="100" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column label="分类" width="80">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
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

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadCustomers"
          @size-change="loadCustomers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="formData.id ? '编辑客户' : '新增客户'"
      width="500px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact">
          <el-input v-model="formData.contact" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="formData.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-radio-group v-model="formData.category">
            <el-radio label="potential">潜在</el-radio>
            <el-radio label="normal">普通</el-radio>
            <el-radio label="vip">VIP</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="active">活跃</el-radio>
            <el-radio label="suspended">暂停</el-radio>
            <el-radio label="lost">流失</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/customer'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])

const searchForm = reactive({
  search: '',
  category: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const formData = reactive({
  id: '',
  name: '',
  contact: '',
  phone: '',
  email: '',
  address: '',
  category: 'normal',
  status: 'active',
  remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
}

const loadCustomers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm,
    }
    const res = await getCustomers(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadCustomers()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.category = ''
  searchForm.status = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  // 使用 Object.assign 重置 formData，保持响应性
  Object.assign(formData, {
    id: '',
    name: '',
    contact: '',
    phone: '',
    email: '',
    address: '',
    category: 'normal',
    status: 'active',
    remark: '',
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, row)
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定要删除该客户吗？', '提示', {
    type: 'warning',
  })
  try {
    await deleteCustomer(row.id)
    ElMessage.success('删除成功')
    loadCustomers()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (formData.id) {
          await updateCustomer(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await createCustomer(formData)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadCustomers()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

const getCategoryType = (category) => {
  const map = { potential: 'info', normal: '', vip: 'warning' }
  return map[category] || ''
}

const getCategoryLabel = (category) => {
  const map = { potential: '潜在', normal: '普通', vip: 'VIP' }
  return map[category] || category
}

const getStatusType = (status) => {
  const map = { active: 'success', suspended: 'warning', lost: 'danger' }
  return map[status] || ''
}

const getStatusLabel = (status) => {
  const map = { active: '活跃', suspended: '暂停', lost: '流失' }
  return map[status] || status
}

onMounted(() => {
  loadCustomers()
})
</script>

<style scoped>
.customers-page {
  height: 100%;
}

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
