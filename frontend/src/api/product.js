import request from './request'

// 获取产品列表
export function getProducts(params) {
  return request.get('/products', { params })
}

// 获取产品详情
export function getProduct(id) {
  return request.get(`/products/${id}`)
}

// 创建产品
export function createProduct(data) {
  return request.post('/products', data)
}

// 更新产品
export function updateProduct(id, data) {
  return request.put(`/products/${id}`, data)
}

// 删除产品
export function deleteProduct(id) {
  return request.delete(`/products/${id}`)
}

// 出入库操作
export function createStockMove(data) {
  return request.post('/products/stock-move', data)
}

// 获取出入库记录
export function getProductStockMoves(id) {
  return request.get(`/products/${id}/stock-moves`)
}
