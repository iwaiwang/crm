import request from './request'

// 获取支出列表
export function getExpenses(params) {
  return request.get('/expenses', { params })
}

// 获取支出详情
export function getExpense(id) {
  return request.get(`/expenses/${id}`)
}

// 创建支出
export function createExpense(data) {
  return request.post('/expenses', data)
}

// 更新支出
export function updateExpense(id, data) {
  return request.put(`/expenses/${id}`, data)
}

// 删除支出
export function deleteExpense(id) {
  return request.delete(`/expenses/${id}`)
}

// 获取支出统计
export function getExpenseStats(params) {
  return request.get('/expenses/stats/overview', { params })
}
