import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 120000,  // 120 秒超时，给 AI 解析足够的时间
})

const getTokenExpiry = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

const isTokenExpired = (token) => {
  const exp = getTokenExpiry(token)
  return exp ? Date.now() >= exp : false
}

const redirectToLogin = (message) => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  if (router.currentRoute.value.path !== '/login') {
    router.push('/login')
    ElMessage.error(message || '登录已过期，请重新登录')
  }
}

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      if (isTokenExpired(token)) {
        redirectToLogin('登录已过期，请重新登录')
        return Promise.reject(new Error('Token expired'))
      }
      config.headers.Authorization = `Bearer ${token}`
    }
    // 过滤掉空值参数
    if (config.params) {
      Object.keys(config.params).forEach(key => {
        if (config.params[key] === '' || config.params[key] === null || config.params[key] === undefined) {
          delete config.params[key]
        }
      })
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      if (status === 401) {
        if (error.config.url.includes('/auth/login')) {
          ElMessage.error(data.detail || '用户名或密码错误')
        } else {
          redirectToLogin('登录已过期，请重新登录')
        }
      } else if (status === 403) {
        ElMessage.error('没有权限访问此资源')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status === 500) {
        ElMessage.error(data.detail || '服务器错误')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
