import request from './request'

// 获取报销单列表
export function getReimbursements(params) {
  return request.get('/reimbursements', { params })
}

// 获取报销单详情
export function getReimbursement(id) {
  return request.get(`/reimbursements/${id}`)
}

// 创建报销单
export function createReimbursement(data) {
  return request.post('/reimbursements', data)
}

// 更新报销单
export function updateReimbursement(id, data) {
  return request.put(`/reimbursements/${id}`, data)
}

// 删除报销单
export function deleteReimbursement(id) {
  return request.delete(`/reimbursements/${id}`)
}

// 提交审核
export function submitReimbursement(id) {
  return request.post(`/reimbursements/${id}/submit`)
}

// 审核通过
export function approveReimbursement(id, data) {
  return request.post(`/reimbursements/${id}/approve`, data)
}

// 驳回报销单
export function rejectReimbursement(id, reason) {
  return request.post(`/reimbursements/${id}/reject`, { reason })
}

// 确认支付
export function payReimbursement(id) {
  return request.post(`/reimbursements/${id}/pay`)
}

// 获取报销统计
export function getReimbursementStatistics(params) {
  return request.get('/reimbursements/statistics', { params })
}

// AI 录入报销单预览
export function previewAiReimbursementImport(fileId) {
  return request.post('/reimbursements/ai-import/preview', { file_id: fileId })
}

// AI 录入报销单确认
export function confirmAiReimbursementImport(data) {
  return request.post('/reimbursements/ai-import/confirm', data)
}