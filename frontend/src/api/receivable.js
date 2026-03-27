import request from './request'

// 获取应收款列表
export function getReceivables(params) {
  return request.get('/receivables', { params })
}

// 获取应收款详情
export function getReceivable(id) {
  return request.get(`/receivables/${id}`)
}

// 创建应收款
export function createReceivable(data) {
  return request.post('/receivables', data)
}

// 更新应收款
export function updateReceivable(id, data) {
  return request.put(`/receivables/${id}`, data)
}

// 删除应收款
export function deleteReceivable(id) {
  return request.delete(`/receivables/${id}`)
}

// 登记收款
export function addPayment(id, data) {
  return request.post(`/receivables/${id}/payment`, data)
}
