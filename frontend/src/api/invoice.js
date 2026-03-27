import request from './request'

// 获取发票列表
export function getInvoices(params) {
  return request.get('/invoices', { params })
}

// 获取发票详情
export function getInvoice(id) {
  return request.get(`/invoices/${id}`)
}

// 创建发票
export function createInvoice(data) {
  return request.post('/invoices', data)
}

// 更新发票
export function updateInvoice(id, data) {
  return request.put(`/invoices/${id}`, data)
}

// 删除发票
export function deleteInvoice(id) {
  return request.delete(`/invoices/${id}`)
}

// 检查发票号码是否重复
export function checkInvoiceDuplicate(invoiceNo, excludeId = null) {
  return request.get('/invoices/actions/check-duplicate', {
    params: { invoice_no: invoiceNo, exclude_id: excludeId }
  })
}

// 获取发票可关联的应收款列表
export function getInvoiceReceivables(id) {
  return request.get(`/invoices/${id}/receivables`)
}

// 从发票创建收款记录
export function registerPaymentFromInvoice(id, data) {
  return request.post(`/invoices/${id}/register-payment`, data)
}
