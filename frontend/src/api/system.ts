/**
 * 系统管理 API
 */
import { request, type ApiResponse } from './request'

// 系统健康状态
export interface HealthStatus {
  status: string
  timestamp: string
  services?: {
    database?: { status: string; latency_ms?: number }
    redis?: { status: string; latency_ms?: number }
    zlmediakit?: { status: string; latency_ms?: number }
  }
}

// 系统信息
export interface SystemInfo {
  version: string
  build_time: string
  environment: string
  hostname: string
  os: string
  python_version: string
  uptime_seconds: number
}

// 系统统计
export interface SystemStatistics {
  cameras: {
    total: number
    online: number
    offline: number
  }
  algorithms: {
    total: number
    enabled: number
  }
  models: {
    total: number
    loaded: number
  }
  alarms: {
    total: number
    today: number
    pending: number
  }
  users: {
    total: number
    active: number
  }
}

// 系统日志
export interface SystemLog {
  id: string
  level: 'debug' | 'info' | 'warning' | 'error'
  module: string
  message: string
  user_id: string | null
  username: string | null
  ip_address: string | null
  request_path: string | null
  request_method: string | null
  response_status: number | null
  duration_ms: number | null
  created_at: string
}

// 日志查询参数
export interface LogQueryParams {
  page?: number
  page_size?: number
  level?: string
  module?: string
  user_id?: string
  start_time?: string
  end_time?: string
  keyword?: string
}

/**
 * 获取系统健康状态
 */
export function getHealth() {
  return request.get<HealthStatus>('/system/health')
}

/**
 * 获取系统信息
 */
export function getSystemInfo() {
  return request.get<SystemInfo>('/system/info')
}

/**
 * 获取系统统计（使用后端 /system/dashboard 实时数据）
 */
export function getSystemStatistics() {
  return request.get<SystemStatistics>('/system/dashboard')
}

/**
 * 获取系统日志
 */
export function getSystemLogs(params?: LogQueryParams) {
  return request.get('/system/logs', { params })
}

/**
 * 清理过期数据
 */
export function cleanupData(options: { days: number; types: string[] }) {
  return request.post('/system/cleanup', options)
}

/**
 * 获取系统配置
 */
export function getSystemConfig() {
  return request.get('/system/config')
}

/**
 * 更新系统配置
 */
export function updateSystemConfig(config: Record<string, any>) {
  return request.put('/system/config', config)
}
