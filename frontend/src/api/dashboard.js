import request from './request'

// 获取仪表盘统计数据
export function getDashboardStats(params) {
  return request.get('/dashboard', { params })
}

// 获取客户统计
export function getCustomerStats() {
  return request.get('/dashboard/customers')
}

// 获取合同统计
export function getContractStats() {
  return request.get('/dashboard/contracts')
}

// 获取应收款统计
export function getReceivableStats() {
  return request.get('/dashboard/receivables')
}

// 获取库存统计
export function getInventoryStats() {
  return request.get('/dashboard/inventory')
}

// 获取项目统计
export function getProjectStats() {
  return request.get('/dashboard/projects')
}
