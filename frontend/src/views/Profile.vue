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
</style>
