import request from './request'

// 获取收款方列表
export function getSuppliers(params) {
  return request.get('/suppliers', { params })
}

// 搜索收款方（自动补全）
export function searchSuppliers(keyword, limit = 10) {
  return request.get('/suppliers/search', { params: { keyword, limit } })
}

// 获取收款方详情
export function getSupplier(id) {
  return request.get(`/suppliers/${id}`)
}

// 创建收款方
export function createSupplier(data) {
  return request.post('/suppliers', data)
}

// 更新收款方
export function updateSupplier(id, data) {
  return request.put(`/suppliers/${id}`, data)
}

// 删除收款方
export function deleteSupplier(id) {
  return request.delete(`/suppliers/${id}`)
}