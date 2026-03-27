import request from './request'

// 获取合同列表
export function getContracts(params) {
  return request.get('/contracts', { params })
}

// 获取合同详情
export function getContract(id) {
  return request.get(`/contracts/${id}`)
}

// 创建合同
export function createContract(data) {
  return request.post('/contracts', data)
}

// 更新合同
export function updateContract(id, data) {
  return request.put(`/contracts/${id}`, data)
}

// 删除合同
export function deleteContract(id) {
  return request.delete(`/contracts/${id}`)
}

// 上传合同文件
export function uploadContractFile(id, file, isPrimary = false) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/contracts/${id}/files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    params: { is_primary: isPrimary }
  })
}

// 获取合同文件列表
export function getContractFiles(id) {
  return request.get(`/contracts/${id}/files`)
}

// 删除合同文件
export function deleteContractFile(contractId, fileId) {
  return request.delete(`/contracts/${contractId}/files/${fileId}`)
}
