<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="brand-glow" />
      <div class="brand-content">
        <div class="brand-logo">
          <img v-if="companyLogo" :src="companyLogo" class="logo-img" />
          <img v-else src="/pyxis-logo.svg" class="logo-img" />
        </div>
        <p class="brand-name">{{ companyName }}</p>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="form-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>请登录您的账号以继续</p>
        </div>

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              class="form-input"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              class="form-input"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="form-footer">
        <span>{{ companyName }} &copy; {{ currentYear }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { normalizeUser, useUserStore } from '@/store/user'
import { login } from '@/api/auth'
import { getPublicSettings } from '@/api/setting'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const companyName = ref('菲克希斯科技')
const companyLogo = ref('')
const currentYear = new Date().getFullYear()

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const loadBranding = async () => {
  try {
    const res = await getPublicSettings()
    if (res.items) {
      for (const item of res.items) {
        if (item.key === 'company_name' && item.value) {
          companyName.value = item.value
        }
        if (item.key === 'company_logo_url' && item.value) {
          companyLogo.value = item.value
        }
      }
    }
  } catch {
    // use defaults
  }
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(loginForm)
        userStore.setToken(res.access_token)
        userStore.setUser(res.user)
        ElMessage.success('登录成功')
        redirectToAllowedPage(res.user)
      } catch (error) {
        ElMessage.error('登录失败：' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }
  })
}

const redirectToAllowedPage = (user) => {
  const normalizedUser = normalizeUser(user)
  if (normalizedUser?.role === 'admin') {
    router.push('/dashboard')
    return
  }

  const menuPermissions = normalizedUser?.menu_permissions || []
  const permissionToPath = {
    'dashboard': '/dashboard',
    'customers': '/customers',
    'contracts': '/contracts',
    'invoices': '/invoices',
    'receivables': '/receivables',
    'reimbursements': '/reimbursements',
    'suppliers': '/suppliers',
    'products': '/products',
    'projects': '/projects',
    'cashflow': '/incomes',
  }

  for (const permission of menuPermissions) {
    const path = permissionToPath[permission]
    if (path) {
      router.push(path)
      return
    }
  }
  router.push('/profile')
}

onMounted(() => {
  loadBranding()
})
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ---- 左侧品牌区 ---- */

.brand-panel {
  flex: 0 0 520px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #071126;
  overflow: hidden;
}

.brand-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(33,79,175,0.18) 0%, transparent 70%);
  pointer-events: none;
}

.brand-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px;
}

.brand-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
}

.logo-img {
  width: 260px;
  height: 260px;
  object-fit: contain;
}

.brand-name {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
}

/* ---- 右侧表单 ---- */

.form-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8fafc;
}

.form-wrapper {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  margin: auto;
}

.form-header {
  margin-bottom: 36px;
}

.form-header h2 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.form-header p {
  margin: 0;
  font-size: 15px;
  color: #64748b;
}

.login-form {
  margin-top: 0;
}

.form-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}

.form-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.form-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(33, 79, 175, 0.15);
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, #163f9e, #214faf);
  border: none;
  box-shadow: 0 4px 16px rgba(22, 63, 158, 0.35);
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(22, 63, 158, 0.5);
}

.login-btn:active {
  transform: translateY(0);
}

.form-footer {
  margin-top: auto;
  padding: 16px;
  font-size: 13px;
  color: #94a3b8;
}

/* ---- 响应式 ---- */

@media (max-width: 900px) {
  .brand-panel {
    display: none;
  }

  .form-wrapper {
    padding: 24px;
  }
}
</style>
