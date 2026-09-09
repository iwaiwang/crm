<template>
  <div class="attachment-uploader">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :multiple="true"
      :show-file-list="false"
      :accept="acceptTypes"
      :on-change="handleFileChange"
      class="attachment-upload-trigger"
    >
      <el-button type="primary" plain>
        <el-icon><UploadFilled /></el-icon> 添加票据
      </el-button>
      <span class="upload-hint">
        支持 {{ acceptTypes.replace(/\./g, '').toUpperCase() }}，可多选，单个 ≤ 50MB
      </span>
    </el-upload>

    <div class="attachment-list" v-if="files.length">
      <div class="attachment-item" v-for="(f, idx) in files" :key="f.file_id">
        <div class="attachment-icon">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="attachment-info">
          <div class="attachment-name">{{ f.file_name || '票据附件' }}</div>
          <div class="attachment-size">{{ formatFileSize(f.file_size) }}</div>
        </div>
        <div class="attachment-actions">
          <el-button link type="primary" @click="openFile(f.file_url)">查看</el-button>
          <el-button link type="danger" @click="removeFile(idx)">删除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import { uploadFile } from '@/api/document'

const props = defineProps({
  initialValue: {
    type: Array,
    default: () => [],
  },
  acceptTypes: {
    type: String,
    default: '.pdf,.jpg,.jpeg,.png',
  },
  refreshKey: {
    type: [Number, String],
    default: 0,
  },
})

const emit = defineEmits(['change'])

const uploadRef = ref(null)
const files = ref([])

watch(
  () => props.initialValue,
  (val) => {
    files.value = val ? [...val] : []
  },
  { deep: true, immediate: true }
)

watch(
  () => props.refreshKey,
  () => {
    files.value = []
    emit('change', [])
  }
)

const handleFileChange = async (file) => {
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小超过 50MB 限制')
    uploadRef.value?.clearFiles()
    return
  }
  try {
    const result = await uploadFile(file.raw, 'invoice')
    const item = {
      file_id: result.file_id,
      file_name: result.file_name,
      file_url: result.file_url,
      file_type: result.file_type,
      file_size: result.file_size,
    }
    files.value.push(item)
    emit('change', [...files.value])
    ElMessage.success('上传成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploadRef.value?.clearFiles()
  }
}

const removeFile = (idx) => {
  files.value.splice(idx, 1)
  emit('change', [...files.value])
}

const openFile = (url) => {
  if (!url) return
  window.open(url, '_blank')
}

const formatFileSize = (bytes) => {
  if (!Number.isFinite(Number(bytes)) || Number(bytes) <= 0) return '未知大小'
  bytes = Number(bytes)
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}
</script>

<style scoped>
.attachment-uploader {
  width: 100%;
}

.attachment-upload-trigger {
  width: 100%;
}

.upload-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.attachment-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.attachment-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: #e4e7ed;
  border-radius: 6px;
  color: #606266;
  flex-shrink: 0;
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-size {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.attachment-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
</style>
