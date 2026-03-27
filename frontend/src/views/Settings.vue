<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 公司信息设置 -->
        <el-tab-pane label="公司信息" name="company">
          <el-form :model="companyForm" label-width="150px" size="large">
            <el-form-item label="公司名称">
              <el-input v-model="companyForm.company_name" placeholder="请输入公司名称" />
            </el-form-item>
            <el-form-item label="公司税号">
              <el-input v-model="companyForm.company_tax_id" placeholder="请输入公司税号" />
            </el-form-item>
            <el-form-item label="银行账号">
              <el-input v-model="companyForm.company_bank_account" placeholder="请输入银行账号" />
            </el-form-item>
            <el-form-item label="公司地址">
              <el-input v-model="companyForm.company_address" placeholder="请输入公司地址" />
            </el-form-item>
            <el-form-item label="公司电话">
              <el-input v-model="companyForm.company_phone" placeholder="请输入公司电话" />
            </el-form-item>
            <el-form-item label="公司邮箱">
              <el-input v-model="companyForm.company_email" type="email" placeholder="请输入公司邮箱" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveCompanyInfo" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 数据库配置 -->
        <el-tab-pane label="数据库配置" name="database">
          <el-form :model="databaseForm" label-width="150px" size="large">
            <el-form-item label="数据库目录">
              <el-input v-model="databaseForm.database_directory" placeholder="请输入数据库目录路径" />
              <div class="form-tip">数据库文件存储目录，修改后需要重启服务生效</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveDatabaseConfig" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 功能开关 -->
        <el-tab-pane label="功能开关" name="features">
          <el-form :model="featureForm" label-width="150px" size="large">
            <el-form-item label="OCR 功能">
              <el-switch v-model="featureForm.ocr_enabled" active-text="开启" inactive-text="关闭" />
              <div class="form-tip">开启后可使用发票 OCR 识别功能</div>
            </el-form-item>
            <el-form-item label="AI 功能">
              <el-switch v-model="featureForm.ai_enabled" active-text="开启" inactive-text="关闭" />
              <div class="form-tip">开启后可使用 AI 智能解析功能</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveFeatures" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 高级设置 -->
        <el-tab-pane label="高级设置" name="advanced">
          <el-table :data="settingsList" style="width: 100%" border>
            <el-table-column prop="key" label="设置键" width="200" />
            <el-table-column prop="value" label="设置值" />
            <el-table-column prop="value_type" label="类型" width="100" />
            <el-table-column prop="description" label="描述" width="200" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="editSetting(scope.row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 编辑设置对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑设置" width="500px">
      <el-form :model="editingSetting" label-width="100px">
        <el-form-item label="设置键">
          <el-input v-model="editingSetting.key" disabled />
        </el-form-item>
        <el-form-item label="设置值">
          <el-input v-model="editingSetting.value" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editingSetting.description" :rows="2" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEditSetting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, getCompanyInfo, updateSetting, initSettings } from '@/api/setting'

const activeTab = ref('company')
const saving = ref(false)
const settingsList = ref([])
const editDialogVisible = ref(false)
const editingSetting = ref({})

// 公司信息表单
const companyForm = reactive({
  company_name: '',
  company_tax_id: '',
  company_bank_account: '',
  company_address: '',
  company_phone: '',
  company_email: '',
})

// 数据库配置表单
const databaseForm = reactive({
  database_directory: '',
})

// 功能开关表单
const featureForm = reactive({
  ocr_enabled: true,
  ai_enabled: true,
})

// 加载设置
const loadSettings = async () => {
  try {
    // 加载公司信息
    const companyData = await getCompanyInfo()
    if (companyData) {
      Object.assign(companyForm, companyData)
    }

    // 加载所有设置
    const response = await getSettings({ page: 1, page_size: 100 })
    settingsList.value = response.items || []

    // 查找数据库目录设置
    const dbSetting = response.items?.find(item => item.key === 'database_directory')
    if (dbSetting) {
      databaseForm.database_directory = dbSetting.value
    }

    // 查找功能开关设置
    const ocrSetting = response.items?.find(item => item.key === 'ocr_enabled')
    const aiSetting = response.items?.find(item => item.key === 'ai_enabled')
    if (ocrSetting) {
      featureForm.ocr_enabled = ocrSetting.value === 'true'
    }
    if (aiSetting) {
      featureForm.ai_enabled = aiSetting.value === 'true'
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败：' + (error.message || '未知错误'))
  }
}

// 保存公司信息
const saveCompanyInfo = async () => {
  saving.value = true
  try {
    const settingsToUpdate = [
      { key: 'company_name', value: companyForm.company_name, description: '公司名称', is_public: true },
      { key: 'company_tax_id', value: companyForm.company_tax_id, description: '公司税号', is_public: true },
      { key: 'company_bank_account', value: companyForm.company_bank_account, description: '公司银行账号', is_public: true },
      { key: 'company_address', value: companyForm.company_address, description: '公司地址', is_public: true },
      { key: 'company_phone', value: companyForm.company_phone, description: '公司电话', is_public: true },
      { key: 'company_email', value: companyForm.company_email, description: '公司邮箱', is_public: true },
    ]

    for (const setting of settingsToUpdate) {
      try {
        await updateSetting(setting.key, setting)
      } catch {
        // 如果设置不存在则创建
        await initSettings()
        await updateSetting(setting.key, setting)
      }
    }

    ElMessage.success('公司信息保存成功')
  } catch (error) {
    console.error('保存公司信息失败:', error)
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 保存数据库配置
const saveDatabaseConfig = async () => {
  saving.value = true
  try {
    await updateSetting('database_directory', {
      value: databaseForm.database_directory,
      description: '数据库目录',
      is_public: false,
    })
    ElMessage.success('数据库配置保存成功')
  } catch (error) {
    console.error('保存数据库配置失败:', error)
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 保存功能开关
const saveFeatures = async () => {
  saving.value = true
  try {
    await updateSetting('ocr_enabled', {
      value: featureForm.ocr_enabled ? 'true' : 'false',
      description: '是否启用 OCR 功能',
      is_public: false,
      value_type: 'boolean',
    })
    await updateSetting('ai_enabled', {
      value: featureForm.ai_enabled ? 'true' : 'false',
      description: '是否启用 AI 功能',
      is_public: false,
      value_type: 'boolean',
    })
    ElMessage.success('功能开关保存成功')
  } catch (error) {
    console.error('保存功能开关失败:', error)
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 编辑设置
const editSetting = (setting) => {
  editingSetting.value = { ...setting }
  editDialogVisible.value = true
}

// 保存编辑的设置
const saveEditSetting = async () => {
  try {
    await updateSetting(editingSetting.value.key, editingSetting.value)
    ElMessage.success('设置更新成功')
    editDialogVisible.value = false
    loadSettings()
  } catch (error) {
    console.error('更新设置失败:', error)
    ElMessage.error('更新失败：' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.settings-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

:deep(.el-tabs__content) {
  padding: 20px;
}
</style>
