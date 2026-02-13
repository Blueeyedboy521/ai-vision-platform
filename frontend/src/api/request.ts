/**
 * API 请求封装
 * 
 * 基于 axios 的 HTTP 请求封装，支持：
 * - 请求/响应拦截
 * - Token 自动添加
 * - Token 过期自动刷新
 * - 统一错误处理
 */
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// API 基础配置
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const API_PREFIX = '/api/v1'

// 统一响应结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
}

// 分页响应
export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 创建 axios 实例
const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL + API_PREFIX,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新 Token
let isRefreshing = false
// 等待刷新的请求队列
let refreshSubscribers: Array<(token: string) => void> = []

// 添加到刷新队列
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

// 通知队列中的请求
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 获取 Token
    const userStore = useUserStore()
    const token = userStore.token
    
    // 添加 Authorization 头
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const data = response.data
    
    // 业务错误
    if (data.code !== 0) {
      // 可以在这里统一处理业务错误
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // 401 未授权，尝试刷新 Token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果是刷新 Token 请求本身失败，直接登出
      if (originalRequest.url?.includes('/auth/refresh')) {
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        return Promise.reject(error)
      }
      
      // 标记已重试
      originalRequest._retry = true
      
      // 如果正在刷新，加入队列等待
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(instance(originalRequest))
          })
        })
      }
      
      // 开始刷新
      isRefreshing = true
      
      try {
        const userStore = useUserStore()
        const newToken = await userStore.refreshToken()
        
        if (newToken) {
          // 刷新成功，通知等待的请求
          onTokenRefreshed(newToken)
          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return instance(originalRequest)
        } else {
          // 刷新失败，登出
          userStore.logout()
          router.push('/login')
          return Promise.reject(error)
        }
      } catch (refreshError) {
        // 刷新异常，登出
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    // 403 禁止访问
    if (error.response?.status === 403) {
      console.error('访问被拒绝')
    }
    
    // 500 服务器错误
    if (error.response?.status >= 500) {
      console.error('服务器错误')
    }
    
    return Promise.reject(error)
  }
)

// 封装请求方法
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return instance.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return instance.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return instance.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return instance.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return instance.patch(url, data, config)
  }
}

export default instance
