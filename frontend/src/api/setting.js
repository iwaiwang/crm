import request from './request'

// 获取设置列表
export function getSettings(params) {
  return request.get('/settings', { params })
}

// 获取公开设置
export function getPublicSettings() {
  return request.get('/settings/public')
}

// 获取单个设置
export function getSetting(key) {
  return request.get(`/settings/${key}`)
}

// 创建设置
export function createSetting(data) {
  return request.post('/settings', data)
}

// 更新设置
export function updateSetting(key, data) {
  return request.put(`/settings/${key}`, data)
}

// 删除设置
export function deleteSetting(key) {
  return request.delete(`/settings/${key}`)
}

// 获取公司信息
export function getCompanyInfo() {
  return request.get('/settings/company/info')
}

// 初始化默认设置
export function initSettings() {
  return request.post('/settings/init')
}

// 获取实际的文件上传目录
export function getUploadDirectory() {
  return request.get('/settings/system/upload-dir')
}

// 清理未使用的上传文件
export function cleanupUnusedFiles() {
  return request.post('/settings/cleanup-files')
}
