import request from './request'

// 获取项目列表
export function getProjects(params) {
  return request.get('/projects', { params })
}

// 获取项目详情
export function getProject(id) {
  return request.get(`/projects/${id}`)
}

// 创建项目
export function createProject(data) {
  return request.post('/projects', data)
}

// 更新项目
export function updateProject(id, data) {
  return request.put(`/projects/${id}`, data)
}

// 删除项目
export function deleteProject(id) {
  return request.delete(`/projects/${id}`)
}

// 添加跟进记录
export function createFollowup(projectId, data) {
  return request.post(`/projects/${projectId}/followups`, data)
}

// 获取跟进记录
export function getProjectFollowups(projectId) {
  return request.get(`/projects/${projectId}/followups`)
}

// 添加项目阶段
export function createPhase(projectId, data) {
  return request.post(`/projects/${projectId}/phases`, data)
}

// 获取项目阶段
export function getProjectPhases(projectId) {
  return request.get(`/projects/${projectId}/phases`)
}

// 更新项目阶段
export function updatePhase(projectId, phaseId, data) {
  return request.put(`/projects/${projectId}/phases/${phaseId}`, data)
}

// 添加项目任务
export function createTask(projectId, data) {
  return request.post(`/projects/${projectId}/tasks`, data)
}

// 获取项目任务
export function getProjectTasks(projectId) {
  return request.get(`/projects/${projectId}/tasks`)
}

// 更新项目任务
export function updateTask(projectId, taskId, data) {
  return request.put(`/projects/${projectId}/tasks/${taskId}`, data)
}
