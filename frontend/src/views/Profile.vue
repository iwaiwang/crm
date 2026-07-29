<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <span>个人信息</span>
      </template>

      <el-form :model="userForm" label-width="100px" style="max-width: 500px">
        <el-form-item label="头像">
          <div class="avatar-section">
            <el-avatar :size="80" :src="userForm.avatar || ''" :icon="!userForm.avatar ? User : undefined" />
            <el-button size="small" style="margin-left: 20px" @click="showAvatarDlg = true">
              更换头像
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>

        <el-form-item label="角色">
          <el-tag>{{ userForm.role === 'admin' ? '管理员' : '普通用户' }}</el-tag>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="updateProfileHandler">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>修改密码</span>
      </template>

      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px" style="max-width: 500px">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="changePasswordHandler">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 两步验证（仅管理员可见） -->
    <el-card v-if="userForm.role === 'admin'" style="margin-top: 20px">
      <template #header>
        <span>两步验证</span>
      </template>

      <div v-if="!totpInfo.enabled && !totpInfo.settingUp">
        <p style="color: #909399; margin-bottom: 12px">开启后登录时需额外输入验证器 App 中的 6 位动态码</p>
        <el-button type="primary" @click="start2faSetup" :loading="totpInfo.loading">开启两步验证</el-button>
      </div>

      <div v-if="totpInfo.settingUp" class="twofa-setup">
        <el-steps :active="2" align-center style="margin-bottom: 24px">
          <el-step title="扫码" description="用验证器 App 扫描二维码" />
          <el-step title="验证" description="输入动态码确认" />
        </el-steps>
        <div class="qr-section">
          <img v-if="totpInfo.qrCode" :src="'data:image/png;base64,' + totpInfo.qrCode" class="qr-image" />
          <p class="secret-text">密钥：<code>{{ totpInfo.secret }}</code></p>
          <p style="font-size: 12px; color: #909399">如果无法扫码，可手动输入上方密钥到验证器 App</p>
        </div>
        <el-form :model="totpInfo.setupForm" label-width="120px" style="max-width: 400px; margin-top: 20px">
          <el-form-item label="验证码">
            <el-input v-model="totpInfo.setupForm.code" placeholder="输入6位验证码" maxlength="6" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="confirm2faSetup" :loading="totpInfo.loading">确认开启</el-button>
            <el-button @click="cancel2faSetup">取消</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="totpInfo.enabled && !totpInfo.settingUp">
        <el-alert type="success" title="两步验证已启用" :closable="false" show-icon style="margin-bottom: 16px">
          <template #default>
            登录时需要输入验证器 App 中的 6 位动态码
          </template>
        </el-alert>
        <div v-if="totpInfo.showDisableInput">
          <el-form :model="totpInfo.disableForm" label-width="120px" style="max-width: 400px">
            <el-form-item label="验证码">
              <el-input v-model="totpInfo.disableForm.code" placeholder="输入6位验证码确认关闭" maxlength="6" />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" @click="confirmDisable2fa" :loading="totpInfo.loading">确认关闭</el-button>
              <el-button @click="totpInfo.showDisableInput = false">取消</el-button>
            </el-form-item>
          </el-form>
        </div>
        <el-button v-else type="danger" plain @click="totpInfo.showDisableInput = true">关闭两步验证</el-button>
      </div>
    </el-card>

    <!-- 更换头像对话框 -->
    <el-dialog v-model="showAvatarDlg" title="更换头像" width="400px">
      <div class="avatar-upload">
        <el-avatar :size="100" :src="avatarPreview || userForm.avatar || ''" :icon="!avatarPreview && !userForm.avatar ? User : undefined" />
        <el-button size="small" @click="selectFile" style="margin-top: 15px">
          选择图片
        </el-button>
        <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" style="display: none" />
        <p style="font-size: 12px; color: #999; margin-top: 10px">支持 JPG、PNG 格式，大小不超过 2MB</p>
      </div>
      <template #footer>
        <el-button @click="showAvatarDlg = false">取消</el-button>
        <el-button type="primary" @click="showAvatarDlg = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { updateProfile, changePassword, uploadAvatar } from '@/api/user'
import { setup2fa, verify2faSetup, disable2fa } from '@/api/auth'

const userStore = useUserStore()
const passwordFormRef = ref(null)
const showAvatarDlg = ref(false)
const fileInput = ref(null)
const avatarPreview = ref(null)
const uploading = ref(false)

const userForm = reactive({
  username: '',
  email: '',
  avatar: '',
  role: '',
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const totpInfo = reactive({
  enabled: false,
  settingUp: false,
  loading: false,
  secret: '',
  qrCode: '',
  showDisableInput: false,
  setupForm: { code: '' },
  disableForm: { code: '' },
})

const start2faSetup = async () => {
  totpInfo.loading = true
  try {
    const res = await setup2fa()
    totpInfo.secret = res.secret
    totpInfo.qrCode = res.qr_code_base64
    totpInfo.settingUp = true
    totpInfo.setupForm.code = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取密钥失败')
  } finally {
    totpInfo.loading = false
  }
}

const confirm2faSetup = async () => {
  if (!totpInfo.setupForm.code || totpInfo.setupForm.code.length !== 6) {
    ElMessage.warning('请输入6位验证码')
    return
  }
  totpInfo.loading = true
  try {
    await verify2faSetup({ token: '', code: totpInfo.setupForm.code })
    totpInfo.enabled = true
    totpInfo.settingUp = false
    ElMessage.success('两步验证已开启')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证失败')
  } finally {
    totpInfo.loading = false
  }
}

const cancel2faSetup = () => {
  totpInfo.settingUp = false
  totpInfo.secret = ''
  totpInfo.qrCode = ''
}

const confirmDisable2fa = async () => {
  if (!totpInfo.disableForm.code || totpInfo.disableForm.code.length !== 6) {
    ElMessage.warning('请输入6位验证码')
    return
  }
  totpInfo.loading = true
  try {
    await disable2fa({ code: totpInfo.disableForm.code })
    totpInfo.enabled = false
    totpInfo.showDisableInput = false
    totpInfo.disableForm.code = ''
    ElMessage.success('两步验证已关闭')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '关闭失败')
  } finally {
    totpInfo.loading = false
  }
}

const loadUserInfo = () => {
  const user = userStore.user
  if (user) {
    userForm.username = user.username
    userForm.email = user.email || ''
    userForm.avatar = user.avatar || ''
    userForm.role = user.role
  }
}

const updateProfileHandler = async () => {
  try {
    await updateProfile({
      username: userForm.username,
      email: userForm.email,
      avatar: userForm.avatar,
    })
    ElMessage.success('个人信息已更新')
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  }
}

const saveAvatar = () => {
  updateProfileHandler()
  showAvatarDlg.value = false
}

const selectFile = () => {
  fileInput.value.click()
}

const onFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    avatarPreview.value = URL.createObjectURL(file)
    uploadFile(file)
  }
}

const uploadFile = async (file) => {
  uploading.value = true
  try {
    const result = await uploadAvatar(file)
    userForm.avatar = result.avatar
    // 使用 setUser 方法触发响应式更新
    const updatedUser = { ...userStore.user, avatar: result.avatar }
    userStore.setUser(updatedUser)
    ElMessage.success('头像上传成功')
    showAvatarDlg.value = false
    avatarPreview.value = null
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
  } finally {
    uploading.value = false
  }
}

const changePasswordHandler = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await changePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword,
        })
        ElMessage.success('密码修改成功')
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
      } catch (error) {
        console.error('修改密码失败:', error)
        ElMessage.error(error.response?.data?.detail || '修改密码失败')
      }
    }
  })
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile-page {
  padding: 20px;
  max-width: 800px;
}

.avatar-section {
  display: flex;
  align-items: center;
}

.twofa-setup {
  padding: 10px 0;
}

.qr-section {
  text-align: center;
}

.qr-image {
  width: 200px;
  height: 200px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 8px;
}

.secret-text {
  margin-top: 12px;
  font-size: 14px;
}

.secret-text code {
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 16px;
  letter-spacing: 2px;
}
</style>
