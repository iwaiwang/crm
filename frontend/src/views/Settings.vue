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

        <!-- AI 配置 -->
        <el-tab-pane label="AI 配置" name="ai">
          <el-form :model="aiForm" label-width="150px" size="large">
            <el-form-item label="服务状态">
              <el-tag :type="aiHealthStatus === 'healthy' ? 'success' : (aiHealthStatus === 'unhealthy' ? 'danger' : 'info')">
                {{ aiHealthStatus === 'healthy' ? '正常' : (aiHealthStatus === 'unhealthy' ? '异常' : '未检查') }}
              </el-tag>
              <span v-if="aiLastHealthCheck" style="margin-left: 10px; font-size: 12px; color: #909399">
                最后检查：{{ formatHealthTime(aiLastHealthCheck) }}
              </span>
              <el-button link type="primary" @click="checkAiService" style="margin-left: 10px">
                <el-icon><Refresh /></el-icon> 刷新状态
              </el-button>
            </el-form-item>
            <el-form-item label="启用 AI">
              <el-switch v-model="aiForm.enabled" active-text="开启" inactive-text="关闭" />
              <div class="form-tip">开启后可使用 AI 智能解析功能</div>
            </el-form-item>
            <el-form-item label="API 地址">
              <el-input v-model="aiForm.api_base_url" placeholder="https://coding.dashscope.aliyuncs.com/v1" />
              <div class="form-tip">阿里云 DashScope API 地址</div>
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="aiForm.api_key" type="password" placeholder="sk-..." show-password />
              <div class="form-tip">从阿里云 DashScope 控制台获取 API Key</div>
            </el-form-item>
            <el-form-item label="模型名称">
              <el-input v-model="aiForm.model" placeholder="qwen3.5-plus" />
              <div class="form-tip">推荐使用 qwen3.5-plus 或 qwen-vl-plus</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveAiConfig" :loading="savingAi">保存设置</el-button>
            </el-form-item>
          </el-form>
          <div class="ai-help">
            <h4>使用说明：</h4>
            <ol>
              <li>开通阿里云百炼服务：<a href="https://dashscope.console.aliyun.com/" target="_blank">https://dashscope.console.aliyun.com/</a></li>
              <li>创建 API Key 并复制保存</li>
              <li>在上方填写 API 地址和 API Key</li>
              <li>选择支持视觉的模型（推荐 qwen-vl-plus）</li>
            </ol>
            <p class="ai-help-tip">提示：新注册用户通常有免费额度可用于测试</p>
          </div>
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
            <el-form-item>
              <el-button type="primary" @click="saveFeatures" :loading="saving">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 高级设置 -->
        <el-tab-pane label="高级设置" name="advanced">
          <el-form :model="advancedForm" label-width="150px" size="large">
            <el-form-item label="文件上传目录">
              <el-input v-model="advancedForm.upload_directory" placeholder="文件上传存储目录" />
              <div class="form-tip">
                实际目录：<code class="dir-path">{{ actualUploadDir }}</code>
                <el-button link type="primary" @click="loadUploadDir" style="margin-left: 10px">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
              </div>
            </el-form-item>
            <el-form-item label="头像目录">
              <el-input :model-value="actualUploadDir + '/avatars'" disabled />
            </el-form-item>
            <el-form-item label="合同目录">
              <el-input :model-value="actualUploadDir + '/contracts'" disabled />
            </el-form-item>
            <el-form-item label="发票目录">
              <el-input :model-value="actualUploadDir + '/invoices'" disabled />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveAdvancedConfig" :loading="saving">保存设置</el-button>
              <el-button type="warning" @click="showCleanupDialog = true" :loading="cleaning">
                <el-icon><Delete /></el-icon> 清理未使用文件
              </el-button>
            </el-form-item>
          </el-form>
          <el-divider />
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

    <!-- 清理文件确认对话框 -->
    <el-dialog v-model="showCleanupDialog" title="清理未使用文件" width="500px">
      <div class="cleanup-info">
        <p>系统将清理以下未使用的文件：</p>
        <ul>
          <li>未关联用户的头像文件</li>
          <li>未关联合同的上传文件</li>
        </ul>
        <p class="cleanup-tip">注意：发票文件不会被清理（因为发票可独立存在）</p>
        <p class="cleanup-tip">注意：此操作不可恢复，请确认后再执行！</p>
      </div>
      <template #footer>
        <el-button @click="showCleanupDialog = false">取消</el-button>
        <el-button type="danger" @click="handleCleanup" :loading="cleaning">确定清理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { getSettings, getCompanyInfo, updateSetting, initSettings, cleanupUnusedFiles } from '@/api/setting'
import { getAIServiceStatus, saveAiConfig as apiSaveAiConfig } from '@/api/document'

const activeTab = ref('company')
const saving = ref(false)
const settingsList = ref([])
const editDialogVisible = ref(false)
const editingSetting = ref({})
const savingAi = ref(false)
const aiHealthStatus = ref('unknown')
const aiLastHealthCheck = ref(null)
const actualUploadDir = ref('')
const showCleanupDialog = ref(false)
const cleaning = ref(false)

const isAuthError = (error) => {
  const status = error?.response?.status
  return status === 401 || status === 403
}

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

// AI 配置表单
const aiForm = reactive({
  enabled: true,
  api_base_url: '',
  api_key: '',
  model: '',
})

// 功能开关表单
const featureForm = reactive({
  ocr_enabled: true,
})

// 高级设置表单
const advancedForm = reactive({
  upload_directory: '',
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
    let runtimeDirectories = null
    try {
      runtimeDirectories = await getUploadDirectory()
    } catch (error) {
      runtimeDirectories = null
    }
    settingsList.value = response.items || []

    // 查找数据库目录设置
    const dbSetting = response.items?.find(item => item.key === 'database_directory')
    if (dbSetting) {
      databaseForm.database_directory = dbSetting.value || runtimeDirectories?.database_directory || ''
    } else {
      databaseForm.database_directory = runtimeDirectories?.database_directory || ''
    }

    // 查找功能开关设置
    const ocrSetting = response.items?.find(item => item.key === 'ocr_enabled')
    if (ocrSetting) {
      featureForm.ocr_enabled = ocrSetting.value === 'true'
    }

    // 查找文件目录设置
    const uploadSetting = response.items?.find(item => item.key === 'upload_directory')
    if (uploadSetting) {
      advancedForm.upload_directory = uploadSetting.value || runtimeDirectories?.upload_directory || ''
    } else {
      advancedForm.upload_directory = runtimeDirectories?.upload_directory || ''
    }

    actualUploadDir.value = runtimeDirectories?.upload_directory || advancedForm.upload_directory || ''
  } catch (error) {
    console.error('加载设置失败:', error)
    if (!isAuthError(error)) {
      ElMessage.error('加载设置失败：' + (error.message || '未知错误'))
    }
  }
}

// 加载实际上传目录
const loadUploadDirLegacy = async () => {
  try {
    const data = await getUploadDirectory()
    actualUploadDir.value = data.upload_directory || ''
    if (!databaseForm.database_directory) {
      databaseForm.database_directory = data.database_directory || ''
    }
    if (!advancedForm.upload_directory) {
      advancedForm.upload_directory = data.upload_directory || ''
    }
  } catch (error) {
    // API 可能不存在（后端未重启），使用设置中的值
    actualUploadDir.value = advancedForm.upload_directory || ''
  }
}

// 清理未使用的文件
const loadUploadDir = () => {
  actualUploadDir.value = advancedForm.upload_directory || ''
}

const handleCleanup = async () => {
  try {
    await ElMessageBox.confirm('确定要清理未使用的文件吗？此操作不可恢复！', '警告', {
      type: 'warning'
    })
    cleaning.value = true
    const result = await cleanupUnusedFiles()
    ElMessage.success(`清理完成！共删除 ${result.deleted_count} 个文件，释放 ${formatFileSize(result.deleted_size)} 空间`)
    showCleanupDialog.value = false
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理文件失败:', error)
      ElMessage.error(error.response?.data?.detail || '清理失败')
    }
  } finally {
    cleaning.value = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 检查 AI 服务状态
const checkAiService = async () => {
  try {
    const status = await getAIServiceStatus()
    aiHealthStatus.value = status.health_status || 'unknown'
    aiLastHealthCheck.value = status.last_health_check
    aiForm.enabled = status.enabled
    aiForm.api_base_url = status.api_base_url || ''
    aiForm.model = status.model || ''
    aiForm.api_key = status.has_api_key ? 'saved-but-hidden' : ''
  } catch (error) {
    console.error('检查 AI 服务失败:', error)
    if (isAuthError(error)) {
      return
    }
    aiHealthStatus.value = 'unhealthy'
  }
}

// 格式化健康检查时间
const formatHealthTime = (isoString) => {
  if (!isoString) return '从未'
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 保存 AI 配置
const saveAiConfig = async () => {
  savingAi.value = true
  try {
    const config = {
      service_type: 'openai_compatible',
      api_base_url: aiForm.api_base_url,
      api_key: aiForm.api_key === 'saved-but-hidden' ? '' : aiForm.api_key,
      model: aiForm.model,
      enabled: aiForm.enabled,
    }
    await apiSaveAiConfig(config)
    ElMessage.success('AI 配置保存成功')
    await checkAiService()
  } catch (error) {
    console.error('保存 AI 配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingAi.value = false
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
    ElMessage.success('功能开关保存成功')
  } catch (error) {
    console.error('保存功能开关失败:', error)
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 保存高级配置
const saveAdvancedConfig = async () => {
  saving.value = true
  try {
    await updateSetting('upload_directory', {
      value: advancedForm.upload_directory,
      description: '文件上传目录',
      is_public: false,
    })
    ElMessage.success('文件目录配置保存成功')
  } catch (error) {
    console.error('保存文件目录配置失败:', error)
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
  checkAiService()
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

.ai-help {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-top: 10px;
}

.ai-help h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.ai-help ol {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
}

.ai-help li {
  margin-bottom: 6px;
}

.ai-help a {
  color: #409eff;
}

.ai-help-tip {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 13px;
}

.dir-path {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

.cleanup-info {
  color: #606266;
  font-size: 14px;
}

.cleanup-info ul {
  margin: 10px 0;
  padding-left: 20px;
}

.cleanup-info li {
  margin-bottom: 6px;
}

.cleanup-tip {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #fef0f0;
  border-radius: 4px;
  color: #f56c6c;
  font-size: 13px;
}
</style>
