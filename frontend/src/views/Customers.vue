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
        <el-form-item label="省份">
          <el-select v-model="searchForm.province" placeholder="全部省份" clearable filterable>
            <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.customer_type" placeholder="全部类型" clearable>
            <el-option label="医院" value="hospital" />
            <el-option label="代理商" value="agent" />
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
      <div class="statistics-bar" v-if="selectedItems.length > 0">
        <el-tag type="primary" size="large">已选择 {{ selectedItems.length }} 项</el-tag>
        <el-button link type="primary" @click="clearSelection">清除选择</el-button>
        <el-button type="danger" size="small" @click="handleBatchDelete">批量删除</el-button>
      </div>

      <el-table :data="displayData" v-loading="loading" border stripe @selection-change="handleSelectionChange" @sort-change="handleSortChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="客户名称" min-width="150" sortable="custom" />
        <el-table-column label="联系人" min-width="180">
          <template #default="{ row }">
            <div v-if="row.contacts && row.contacts.length > 0">
              <div v-for="c in row.contacts" :key="c.id" class="contact-line">
                <span>{{ c.name }}</span>
                <el-tag v-if="c.is_primary" size="small" type="primary" effect="plain">主要</el-tag>
                <span v-if="c.position" class="contact-position">{{ c.position }}</span>
              </div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="电话" width="130">
          <template #default="{ row }">
            <div v-if="row.contacts && row.contacts.length > 0">
              <div v-for="c in row.contacts" :key="c.id">{{ c.phone || '-' }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="province" label="省份" width="80" sortable="custom">
          <template #default="{ row }">
            <span>{{ row.province || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_type" label="类型" width="80" sortable="custom">
          <template #default="{ row }">
            <el-tag v-if="row.customer_type === 'hospital'" type="primary" effect="plain">医院</el-tag>
            <el-tag v-else-if="row.customer_type === 'agent'" effect="plain">代理商</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="80" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" sortable="custom">
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
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadCustomers"
          @size-change="loadCustomers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-drawer
      v-model="showDialog"
      :title="formData.id ? '编辑客户' : '新增客户'"
      size="600px"
      direction="rtl"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="formData.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="省份" prop="province">
          <el-select v-model="formData.province" placeholder="请选择省份" clearable filterable>
            <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" prop="customer_type">
          <el-radio-group v-model="formData.customer_type">
            <el-radio label="hospital">医院（终端用户）</el-radio>
            <el-radio label="agent">代理商</el-radio>
          </el-radio-group>
          <el-button v-if="formData.customer_type" link size="small" @click="formData.customer_type = null">清除</el-button>
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

        <!-- 联系人列表 -->
        <el-divider content-position="left">联系人</el-divider>
        <div v-for="(contact, index) in formData.contacts" :key="index" class="contact-card">
          <div class="contact-header">
            <span>联系人 {{ index + 1 }}</span>
            <el-button link type="danger" size="small" @click="removeContact(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="姓名" :prop="`contacts.${index}.name`" label-width="50px"
                :rules="{ required: true, message: '请输入姓名', trigger: 'blur' }">
                <el-input v-model="contact.name" size="small" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="职位" :prop="`contacts.${index}.position`" label-width="50px">
                <el-input v-model="contact.position" size="small" placeholder="如：销售经理" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="电话" :prop="`contacts.${index}.phone`" label-width="50px">
                <el-input v-model="contact.phone" size="small" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱" :prop="`contacts.${index}.email`" label-width="50px">
                <el-input v-model="contact.email" size="small" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-checkbox v-model="contact.is_primary" size="small">设为主要联系人</el-checkbox>
        </div>
        <el-button type="primary" link @click="addContact">
          <el-icon><Plus /></el-icon> 添加联系人
        </el-button>

        <el-divider content-position="left">其他信息</el-divider>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCustomers, createCustomer, updateCustomer, deleteCustomer, batchDeleteCustomers } from '@/api/customer'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const formRef = ref(null)
const tableData = ref([])
const displayData = ref([])
const selectedItems = ref([])

const collator = new Intl.Collator('zh-Hans-CN', { sensitivity: 'base', numeric: true })
const sortState = ref({ prop: null, order: null })

function applySort() {
  const { prop, order } = sortState.value
  if (!prop || !order) {
    displayData.value = [...tableData.value]
    return
  }
  const arr = [...displayData.value]
  arr.sort((a, b) => {
    let va = a[prop] ?? ''
    let vb = b[prop] ?? ''
    let cmp = collator.compare(String(va), String(vb))
    return order === 'ascending' ? cmp : -cmp
  })
  displayData.value = arr
}

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古',
  '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东',
  '河南', '湖北', '湖南', '广东', '广西', '海南',
  '重庆', '四川', '贵州', '云南', '西藏',
  '陕西', '甘肃', '青海', '宁夏', '新疆',
  '台湾', '香港', '澳门',
]

const searchForm = reactive({
  search: '',
  category: '',
  status: '',
  province: '',
  customer_type: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const emptyContact = () => ({
  id: '',
  name: '',
  phone: '',
  email: '',
  position: '',
  is_primary: false,
  remark: '',
})

const formData = reactive({
  id: '',
  name: '',
  address: '',
  province: null,
  customer_type: null,
  category: 'normal',
  status: 'active',
  remark: '',
  contacts: [],
})

const rules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
}

const addContact = () => {
  formData.contacts.push(emptyContact())
}

const removeContact = (index) => {
  formData.contacts.splice(index, 1)
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
    displayData.value = [...res.items]
    sortState.value = { prop: null, order: null }
    pagination.total = res.total
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSortChange = ({ prop, order }) => {
  sortState.value = { prop, order }
  applySort()
}

const handleSearch = () => {
  pagination.page = 1
  loadCustomers()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.category = ''
  searchForm.status = ''
  searchForm.province = ''
  searchForm.customer_type = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    name: '',
    address: '',
    province: null,
    customer_type: null,
    category: 'normal',
    status: 'active',
    remark: '',
    contacts: [emptyContact()],
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  const contacts = (row.contacts && row.contacts.length > 0)
    ? row.contacts.map(c => ({ ...c }))
    : [emptyContact()]
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    address: row.address,
    province: row.province || null,
    customer_type: row.customer_type || null,
    category: row.category,
    status: row.status,
    remark: row.remark,
    contacts,
  })
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

const handleSelectionChange = (selection) => {
  selectedItems.value = selection
}

const clearSelection = () => {
  selectedItems.value = []
  loadCustomers()
}

const handleBatchDelete = async () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请选择要删除的客户')
    return
  }
  await ElMessageBox.confirm(`确定要删除选中的 ${selectedItems.value.length} 个客户吗？`, '提示', { type: 'warning' })
  try {
    const ids = selectedItems.value.map(item => item.id)
    await batchDeleteCustomers(ids)
    ElMessage.success('批量删除成功')
    selectedItems.value = []
    loadCustomers()
  } catch (error) {
    console.error('批量删除失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  // 校验联系人姓名
  if (formData.contacts.length === 0) {
    ElMessage.warning('请至少添加一个联系人')
    return
  }
  for (const c of formData.contacts) {
    if (!c.name || !c.name.trim()) {
      ElMessage.warning('请填写所有联系人姓名')
      return
    }
  }

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const payload = {
          name: formData.name,
          address: formData.address,
          province: formData.province || null,
          customer_type: formData.customer_type || null,
          category: formData.category,
          status: formData.status,
          remark: formData.remark,
          contacts: formData.contacts.map(c => ({
            name: c.name,
            phone: c.phone || null,
            email: c.email || null,
            position: c.position || null,
            is_primary: c.is_primary || false,
            remark: c.remark || null,
          })),
        }

        if (formData.id) {
          // 更新客户基本信息 + 同步联系人
          await updateCustomer(formData.id, {
            name: payload.name,
            address: payload.address,
            province: payload.province,
            category: payload.category,
            customer_type: payload.customer_type,
            status: payload.status,
            remark: payload.remark,
          })

          // 删除旧联系人，重新创建
          const { getContacts, deleteContact, createContact } = await import('@/api/customer')
          const existingContacts = await getContacts(formData.id)
          for (const c of existingContacts) {
            await deleteContact(formData.id, c.id)
          }
          for (const c of payload.contacts) {
            await createContact(formData.id, c)
          }

          ElMessage.success('更新成功')
        } else {
          await createCustomer(payload)
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
  const map = { potential: 'info', normal: 'primary', vip: 'warning' }
  return map[category] || 'info'
}

const getCategoryLabel = (category) => {
  const map = { potential: '潜在', normal: '普通', vip: 'VIP' }
  return map[category] || category
}

const getStatusType = (status) => {
  const map = { active: 'success', suspended: 'warning', lost: 'danger' }
  return map[status] || 'info'
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

.contact-card {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.contact-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.contact-line {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
}

.contact-position {
  font-size: 12px;
  color: #999;
}

.text-muted {
  color: #ccc;
}
</style>
