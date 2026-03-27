<template>
  <div class="document-uploader">
    <!-- 上传区域 -->
    <div class="upload-area" v-if="!fileInfo">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :accept="acceptTypes"
        :limit="1"
        class="upload-trigger"
      >
        <div class="upload-placeholder">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            拖拽文件到此处 或 <span class="upload-link">点击上传</span>
          </div>
          <div class="upload-hint">
            支持格式：{{ acceptTypes.replace(/\./g, '').toUpperCase() }} (最大 10MB)
          </div>
        </div>
      </el-upload>
    </div>

    <!-- 已上传文件预览 -->
    <div class="file-preview" v-else>
      <div class="file-info-card">
        <div class="file-icon">
          <el-icon :size="40"><Document /></el-icon>
        </div>
        <div class="file-details">
          <div class="file-name">{{ fileInfo.name }}</div>
          <div class="file-size">{{ formatFileSize(fileInfo.size) }}</div>
        </div>
        <div class="file-actions">
          <el-button link type="primary" @click="handlePreview">
            <el-icon><View /></el-icon> 预览
          </el-button>
          <el-button link type="primary" @click="handleDownload">
            <el-icon><Download /></el-icon> 下载
          </el-button>
          <el-button link type="danger" @click="handleRemove">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 自动识别按钮 -->
    <div class="ai-parse-section" v-if="fileInfo && showAiParse && type === 'invoice'">
      <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
        <!-- 自动识别按钮（仅发票类型，支持图片和 PDF） -->
        <el-button
          v-if="isImageFile || isPdf"
          type="primary"
          :loading="parsing"
          @click="handleAutoParse"
        >
          <el-icon><Aim /></el-icon>
          {{ parsing ? '识别中...' : '自动识别' }}
        </el-button>
      </div>
      <div class="parse-hint" style="margin-top: 8px;">
        <el-icon><InfoFilled /></el-icon>
        提示：自动识别会优先尝试二维码识别（速度快、准确率高），失败时自动切换到 OCR 识别
      </div>
    </div>

    <!-- 解析进度 -->
    <div class="parse-progress" v-if="parsing">
      <el-progress :percentage="100" :indeterminate="true" :duration="2" status="active" />
      <div class="parse-status">
        <el-icon class="pulsing"><Loading /></el-icon>
        正在解析文档内容，请稍候...
      </div>
      <div class="parse-hint">
        提示：AI 正在分析文档并提取关键信息，通常需要 10-30 秒
      </div>
    </div>

    <!-- PDF 预览对话框 -->
    <el-dialog v-model="previewVisible" title="文件预览" width="80%" top="5vh">
      <div class="preview-container">
        <iframe v-if="isPdf" :src="previewUrl" class="pdf-preview" />
        <img v-else :src="previewUrl" class="image-preview" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, View, Download, Delete, Aim, InfoFilled } from '@element-plus/icons-vue'
import { uploadFile, parseInvoiceByQr, parseInvoiceByOcr, getFileDocument } from '@/api/document'

const props = defineProps({
  // 文档类型：contract | invoice
  type: {
    type: String,
    required: true,
    validator: (v) => ['contract', 'invoice'].includes(v),
  },
  // 是否显示 AI 解析按钮
  showAiParse: {
    type: Boolean,
    default: true,
  },
  // 初始文件信息
  initialValue: {
    type: Object,
    default: null,
  },
  // 允许的文件类型
  acceptTypes: {
    type: String,
    default: '.pdf,.doc,.docx',
  },
  // 刷新 key，用于强制重置组件
  refreshKey: {
    type: [Number, String],
    default: 0,
  },
})

const emit = defineEmits(['change', 'ai-result'])

const uploadRef = ref(null)
const fileInfo = ref(null)
const parsing = ref(false)
const previewVisible = ref(false)

// 监听 initialValue 变化，同步更新文件信息
watch(() => props.initialValue, (newVal) => {
  if (newVal === null) {
    fileInfo.value = null
  } else if (newVal) {
    // 当 initialValue 变为新对象时，同步更新
    fileInfo.value = newVal
  }
}, { deep: true })

// 监听 refreshKey 变化，强制重置组件
watch(() => props.refreshKey, () => {
  fileInfo.value = null
  emit('change', null)
})

const isPdf = computed(() => {
  return fileInfo.value && fileInfo.value.type === 'pdf'
})

const isImageFile = computed(() => {
  return fileInfo.value && ['jpg', 'jpeg', 'png'].includes(fileInfo.value.type)
})

const previewUrl = computed(() => {
  if (fileInfo.value?.url) {
    return fileInfo.value.url
  }
  return ''
})

// 检查 AI 服务状态（已移除）

// 处理文件变化
const handleFileChange = async (file) => {
  // 验证文件大小
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小超过 10MB 限制')
    return
  }

  try {
    // 上传文件
    const result = await uploadFile(file.raw, props.type)
    fileInfo.value = {
      id: result.file_id,
      name: result.file_name,
      url: result.file_url,
      size: result.file_size,
      type: result.file_type,
    }

    emit('change', fileInfo.value)
    ElMessage.success('上传成功')
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  }
}

// 处理自动识别（二维码 + OCR，合并结果）
const handleAutoParse = async () => {
  if (!fileInfo.value?.id) {
    console.error('[Auto] 没有文件 ID')
    return
  }

  console.log('[Auto] 开始自动识别，fileId:', fileInfo.value.id)
  parsing.value = true

  try {
    // 同时识别二维码和 OCR
    console.log('[Auto] 识别二维码...')
    let qrResult = null
    try {
      qrResult = await parseInvoiceByQr(fileInfo.value.id)
      console.log('[Auto] 二维码识别返回:', qrResult)
    } catch (e) {
      console.log('[Auto] 二维码识别异常:', e.message)
    }

    console.log('[Auto] 识别 OCR...')
    let ocrResult = null
    try {
      ocrResult = await parseInvoiceByOcr(fileInfo.value.id)
      console.log('[Auto] OCR 识别返回:', ocrResult)
    } catch (e) {
      console.log('[Auto] OCR 识别异常:', e.message)
    }

    // 合并结果：二维码提供发票基本信息，OCR 提供购买方/销售方
    // 发票类型优先使用二维码的结果（更准确）
    const mergedData = {
      ...(ocrResult?.data || {}),
      ...(qrResult?.data || {}),  // 二维码的结果会覆盖 OCR 的 invoice_type
    }

    console.log('[Auto] 合并后的数据:', mergedData)
    console.log('[Auto] 税率字段 (tax_rate):', mergedData.tax_rate)
    console.log('[Auto] OCR 税率:', ocrResult?.data?.tax_rate)
    console.log('[Auto] 二维码税率:', qrResult?.data?.tax_rate)

    // 检查是否有有效数据
    const hasData = Object.values(mergedData).some(v => v !== null && v !== undefined && v !== '')

    if (hasData) {
      emit('ai-result', { data: mergedData, confidence: 0.9 })
      ElMessage.success('识别成功')
    } else {
      ElMessage.warning('未识别到有效信息')
    }
  } catch (error) {
    console.error('[Auto] 识别过程异常:', error)
    ElMessage.error('识别失败：' + error.message)
  } finally {
    parsing.value = false
  }
}

// 处理二维码识别（仅发票）
const handleQrParse = async () => {
  if (!fileInfo.value?.id) {
    console.error('[QR] 没有文件 ID')
    return
  }

  console.log('[QR] 开始识别二维码，fileId:', fileInfo.value.id)
  parsing.value = true
  try {
    const result = await parseInvoiceByQr(fileInfo.value.id)
    console.log('[QR] 后端返回结果:', JSON.stringify(result, null, 2))

    if (result.success && result.data) {
      console.log('[QR] 发送 ai-result 事件，data:', JSON.stringify(result.data, null, 2))
      emit('ai-result', { data: result.data, confidence: result.confidence })
      ElMessage.success('二维码识别成功')
    } else {
      console.log('[QR] 结果中没有 success 或 data')
      ElMessage.warning('二维码识别失败，请尝试 AI 智能识别')
    }
  } catch (error) {
    console.error('二维码识别失败:', error)
    console.error('错误响应:', error.response)
    console.error('错误数据:', error.response?.data)
    ElMessage.error(error.response?.data?.detail || error.response?.data?.message || '二维码识别失败')
  } finally {
    parsing.value = false
  }
}

// 处理 OCR 识别（仅发票）
const handleOcrParse = async () => {
  if (!fileInfo.value?.id) {
    console.error('[OCR] 没有文件 ID')
    return
  }

  console.log('[OCR] 开始 OCR 识别，fileId:', fileInfo.value.id)
  parsing.value = true
  try {
    const result = await parseInvoiceByOcr(fileInfo.value.id)
    console.log('[OCR] 后端返回结果:', JSON.stringify(result, null, 2))

    if (result.success && result.data) {
      console.log('[OCR] 发送 ai-result 事件，data:', JSON.stringify(result.data, null, 2))
      emit('ai-result', { data: result.data, confidence: result.confidence || 0.85 })
      ElMessage.success('OCR 识别成功')
    } else {
      console.log('[OCR] 结果中没有 success 或 data')
      ElMessage.warning('OCR 识别失败，请尝试 AI 智能识别')
    }
  } catch (error) {
    console.error('OCR 识别失败:', error)
    console.error('错误响应:', error.response)
    console.error('错误数据:', error.response?.data)
    ElMessage.error(error.response?.data?.detail || error.response?.data?.message || 'OCR 识别失败')
  } finally {
    parsing.value = false
  }
}

// 处理预览
const handlePreview = () => {
  previewVisible.value = true
}

// 处理下载
const handleDownload = () => {
  if (fileInfo.value?.url) {
    const a = document.createElement('a')
    a.href = fileInfo.value.url
    a.download = fileInfo.value.name
    a.click()
  }
}

// 处理删除
const handleRemove = () => {
  fileInfo.value = null
  emit('change', null)
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 初始化
onMounted(() => {
  if (props.initialValue) {
    fileInfo.value = props.initialValue
  }
})
</script>

<style scoped>
.document-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  background-color: #fafafa;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
}

.upload-trigger {
  width: 100%;
}

.upload-trigger :deep(.el-upload) {
  width: 100%;
}

.upload-placeholder {
  padding: 20px 16px;
  text-align: center;
  color: #8c939d;
}

.upload-icon {
  font-size: 32px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 13px;
  margin-bottom: 4px;
}

.upload-link {
  color: #409eff;
  cursor: pointer;
}

.upload-hint {
  font-size: 11px;
  color: #a8abb2;
}

.file-preview {
  margin-top: 12px;
}

.file-info-card {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  gap: 12px;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: #e4e7ed;
  border-radius: 6px;
  color: #606266;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.file-actions {
  display: flex;
  gap: 6px;
}

.file-actions :deep(.el-button) {
  padding: 4px 8px;
  font-size: 12px;
}

.ai-parse-section {
  margin-top: 12px;
  padding: 10px 12px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border: 1px solid #d0e8ff;
}

.parse-progress {
  margin-top: 16px;
  padding: 16px;
  background-color: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.parse-status {
  text-align: center;
  font-size: 14px;
  color: #303133;
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
}

.parse-hint {
  text-align: center;
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.pulsing {
  animation: pulse 1.5s ease-in-out infinite;
  color: #409eff;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.9);
  }
}

.preview-container {
  height: 70vh;
  display: flex;
  justify-content: center;
}

.pdf-preview {
  width: 100%;
  height: 100%;
  border: none;
}

.image-preview {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
</style>
