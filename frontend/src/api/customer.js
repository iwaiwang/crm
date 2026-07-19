import request from './request'

// 获取客户列表
export function getCustomers(params) {
  return request.get('/customers', { params })
}

// 获取客户详情
export function getCustomer(id) {
  return request.get(`/customers/${id}`)
}

// 创建客户
export function createCustomer(data) {
  return request.post('/customers', data)
}

// 更新客户
export function updateCustomer(id, data) {
  return request.put(`/customers/${id}`, data)
}

// 删除客户
export function deleteCustomer(id) {
  return request.delete(`/customers/${id}`)
}

// 批量删除客户
export function batchDeleteCustomers(ids) {
  return request.post('/customers/batch-delete', ids)
}

// ── 联系人 API ──────────────────────────────────────

// 获取客户联系人列表
export function getContacts(customerId) {
  return request.get(`/customers/${customerId}/contacts`)
}

// 添加联系人
export function createContact(customerId, data) {
  return request.post(`/customers/${customerId}/contacts`, data)
}

// 更新联系人
export function updateContact(customerId, contactId, data) {
  return request.put(`/customers/${customerId}/contacts/${contactId}`, data)
}

// 删除联系人
export function deleteContact(customerId, contactId) {
  return request.delete(`/customers/${customerId}/contacts/${contactId}`)
}
