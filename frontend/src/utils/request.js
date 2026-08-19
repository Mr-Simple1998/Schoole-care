import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

function cleanParams(params) {
  if (!params || typeof params !== 'object') return params
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  )
}

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截器：自动带上 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (config.params) config.params = cleanParams(config.params)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 401) {
      ElMessage.error(detail || '登录已过期，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
    } else if (status === 403) {
      ElMessage.error(detail || '没有权限执行此操作')
    } else if (status === 400) {
      ElMessage.error(detail || '请求参数有误')
    } else {
      ElMessage.error(detail || '服务器错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default request
