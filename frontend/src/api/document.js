import request from './request'

// 上传文件
export function uploadFile(file, type) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  return request.post('/document/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

// 获取文件信息
export function getFileDocument(fileId, type) {
  return request.get(`/document/${fileId}/info`, {
    params: { type },
  })
}

// AI 解析文档
export function parseDocumentWithAI(fileId, type) {
  return request.post('/document/parse-with-ai', {
    file_id: fileId,
    type,
  })
}

// 通过二维码识别发票
export function parseInvoiceByQr(fileId) {
  return request.post('/document/parse-invoice-qr', {
    file_id: fileId,
  }, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

// 通过 OCR 识别发票
export function parseInvoiceByOcr(fileId) {
  return request.post('/document/parse-invoice-ocr', {
    file_id: fileId,
  }, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

// 获取 AI 服务状态（从数据库读取，不实时检查）
export function getAIServiceStatus() {
  return request.get('/document/ai-service/status')
}

// 保存 AI 服务配置（会进行健康检查）
export function saveAiConfig(config) {
  return request.post('/document/ai-service/config', config)
}
