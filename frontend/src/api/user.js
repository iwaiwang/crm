import request from './request'

// 获取当前用户信息
export function getCurrentUser() {
  return request.get('/users/profile')
}

// 更新个人信息
export function updateProfile(data) {
  return request.put('/users/profile', null, { params: data })
}

// 修改密码
export function changePassword(data) {
  return request.post('/users/change-password', null, { params: data })
}

// 上传头像
export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/users/upload-avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

// 获取所有用户列表（管理员）
export function getUserList() {
  return request.get('/users')
}

// 获取用户详情（管理员）
export function getUserDetail(id) {
  return request.get(`/users/${id}`)
}

// 创建用户（管理员）
export function createUser(data) {
  return request.post('/users', {
    username: data.username,
    password: data.password,
    email: data.email || '',
    role: data.role || 'user',
    is_active: data.is_active !== undefined ? data.is_active : true,
    menu_permissions: data.menu_permissions || [],
  })
}

// 更新用户信息（管理员）
export function updateUser(id, data) {
  return request.put(`/users/${id}`, {
    username: data.username,
    email: data.email,
    role: data.role,
    is_active: data.is_active,
    menu_permissions: data.menu_permissions || [],
  })
}

// 删除用户（管理员）
export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

// 重置用户密码（管理员）
export function resetPassword(id, newPassword) {
  return request.post(`/users/${id}/reset-password`, null, { params: { new_password: newPassword } })
}
