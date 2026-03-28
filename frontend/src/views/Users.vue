<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showAddDlg = true">
        <el-icon><Plus /></el-icon> 新增用户
      </el-button>
    </div>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table :data="users" v-loading="loading" border stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : ''">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="菜单权限" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="menu in row.menu_permissions" :key="menu" size="small" style="margin-right: 5px">
              {{ getMenuLabel(menu) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="handleResetPwd(row)">重置密码</el-button>
            <el-button link type="danger" @click="handleDelete(row)" :disabled="row.username === 'admin'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑用户对话框 -->
    <el-drawer
      v-model="showAddDlg"
      :title="isEdit ? '编辑用户' : '新增用户'"
      size="520px"
      direction="rtl"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="userForm.role">
            <el-radio value="user">普通用户</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="userForm.is_active">
            <el-radio :value="true">启用</el-radio>
            <el-radio :value="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="菜单权限" prop="menu_permissions">
          <el-checkbox-group v-model="userForm.menu_permissions">
            <el-checkbox value="dashboard">仪表盘</el-checkbox>
            <el-checkbox value="customers">客户管理</el-checkbox>
            <el-checkbox value="contracts">合同管理</el-checkbox>
            <el-checkbox value="invoices">发票管理</el-checkbox>
            <el-checkbox value="receivables">应收款管理</el-checkbox>
            <el-checkbox value="products">产品库存</el-checkbox>
            <el-checkbox value="projects">项目进度</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDlg = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showResetPwdDlg" title="重置密码" width="400px">
      <el-form :model="resetPwdForm" :rules="resetPwdRules" ref="resetPwdFormRef">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetPwdForm.newPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetPwdDlg = false">取消</el-button>
        <el-button type="primary" @click="handleResetPwdConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getUserList, updateUser, deleteUser, resetPassword, createUser } from '@/api/user'

const loading = ref(false)
const submitting = ref(false)
const showAddDlg = ref(false)
const showResetPwdDlg = ref(false)
const isEdit = ref(false)
const users = ref([])
const userFormRef = ref(null)
const resetPwdFormRef = ref(null)
const currentUser = ref(null)

const userForm = reactive({
  id: '',
  username: '',
  password: '',
  email: '',
  role: 'user',
  is_active: true,
  menu_permissions: [],
})

const resetPwdForm = reactive({
  newPassword: '',
})

const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, message: '用户名至少 3 个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }],
}

const resetPwdRules = {
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }],
}

const menuMap = {
  dashboard: '仪表盘',
  customers: '客户管理',
  contracts: '合同管理',
  invoices: '发票管理',
  receivables: '应收款管理',
  products: '产品库存',
  projects: '项目进度',
}

const getMenuLabel = (key) => menuMap[key] || key

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUserList()
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = (row) => {
  isEdit.value = true
  showAddDlg.value = true
  currentUser.value = row
  userForm.id = row.id
  userForm.username = row.username
  userForm.email = row.email || ''
  userForm.role = row.role
  userForm.is_active = row.is_active
  userForm.menu_permissions = row.menu_permissions || []
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' })
  try {
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const handleResetPwd = (row) => {
  currentUser.value = row
  showResetPwdDlg.value = true
  resetPwdForm.newPassword = ''
}

const handleResetPwdConfirm = async () => {
  if (!resetPwdFormRef.value) return
  await resetPwdFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await resetPassword(currentUser.value.id, resetPwdForm.newPassword)
        ElMessage.success('密码重置成功')
        showResetPwdDlg.value = false
      } catch (error) {
        console.error('重置密码失败:', error)
        ElMessage.error('重置密码失败')
      }
    }
  })
}

const handleSubmit = async () => {
  if (!userFormRef.value) return
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await updateUser(currentUser.value.id, {
            username: userForm.username,
            email: userForm.email,
            role: userForm.role,
            is_active: userForm.is_active,
            menu_permissions: userForm.menu_permissions,
          })
          ElMessage.success('更新成功')
        } else {
          await createUser({
            username: userForm.username,
            password: userForm.password,
            email: userForm.email,
            role: userForm.role,
            is_active: userForm.is_active,
            menu_permissions: userForm.menu_permissions,
          })
          ElMessage.success('用户创建成功')
        }
        showAddDlg.value = false
        loadUsers()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-card {
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
