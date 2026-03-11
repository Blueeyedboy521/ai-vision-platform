/**
 * 告警管理 API
 */
import { request } from './request'

// 告警级别（后端: info/warning/danger/critical）
export type AlarmLevel = 'info' | 'warning' | 'danger' | 'critical'

// 告警状态（后端: unconfirmed/confirmed/ignored/processed）
export type AlarmStatus = 'unconfirmed' | 'confirmed' | 'ignored' | 'processed'

// 告警信息
export interface Alarm {
  id: string
  camera_id: string
  camera_name?: string
  area_name?: string | null
  algorithm_id: string
  algorithm_name?: string
  alarm_type: string
  level: AlarmLevel
  title: string | null
  description: string | null
  alarm_time: string
  snapshot_url: string | null
  video_url: string | null
  detection_data: any | null
  status: AlarmStatus
  confirmed_by: string | null
  confirmed_at: string | null
  confirm_remark?: string | null
  is_pushed?: boolean
  created_at: string
}

// 告警列表查询参数
export interface AlarmQueryParams {
  page?: number
  page_size?: number
  camera_id?: string
  algorithm_id?: string
  level?: AlarmLevel
  status?: AlarmStatus
  area_id?: string
  start_time?: string
  end_time?: string
  keyword?: string
}

// 告警统计（对接后端 /alarms/stats 返回结构）
export interface AlarmStatistics {
  total: number
  unconfirmed: number
  confirmed: number
  ignored: number
  processed: number
  by_level: { label: string; value: number }[]
  by_camera: { label: string; value: number }[]
  by_algorithm: { label: string; value: number }[]
  trend: { date: string; count: number }[]
}

/**
 * 获取告警列表
 */
export function getAlarmList(params?: AlarmQueryParams) {
  // 后端分页结构为 {code,message,data,page_info}
  return request.get<any>('/alarms', { params })
}

/**
 * 获取告警详情
 */
export function getAlarm(id: string) {
  return request.get<Alarm>(`/alarms/${id}`)
}

/**
 * 确认告警
 */
export function confirmAlarm(id: string) {
  return request.post(`/alarms/${id}/confirm`)
}

/**
 * 解决告警
 */
export function resolveAlarm(id: string, remark?: string) {
  return request.post(`/alarms/${id}/resolve`, { remark })
}

/**
 * 忽略告警
 */
export function ignoreAlarm(id: string, reason?: string) {
  return request.post(`/alarms/${id}/ignore`, { reason })
}

/**
 * 批量确认告警
 */
export function batchConfirmAlarms(ids: string[]) {
  return request.post('/alarms/batch/confirm', { ids })
}

/**
 * 批量忽略告警
 */
export function batchIgnoreAlarms(ids: string[], reason?: string) {
  return request.post('/alarms/batch/ignore', { ids, reason })
}

/**
 * 获取告警统计（封装 /alarms/stats）
 */
export function getAlarmStatistics(params?: { days?: number }) {
  return request.get<AlarmStatistics>('/alarms/stats', { params })
}

/**
 * 导出告警记录
 */
export function exportAlarms(params?: AlarmQueryParams) {
  return request.get('/alarms/export', { params, responseType: 'blob' as any })
}

// 告警概览统计
export interface AlarmOverviewStats {
  total: number
  total_trend: number
  total_new: number
  unconfirmed: number
  unconfirmed_trend: number
  urgent_count: number
  confirmed: number
  confirmed_trend: number
  avg_handle_time: number
  completion_rate: number
  completion_trend: number
  site_rank_percent: number
}

// 高频告警设备项
export interface AlarmDeviceTopItem {
  camera_id: string
  camera_name: string
  area_name: string | null
  count: number
}

// 高频告警区域项
export interface AlarmAreaTopItem {
  area_name: string
  count: number
  percentage: number
}

// 告警类型统计项
export interface AlarmTypeStatsItem {
  algorithm_id: string
  algorithm_name: string
  count: number
  percentage: number
}

// 告警等级统计项
export interface AlarmLevelStatsItem {
  level: string
  label: string
  count: number
  percentage: number
}

// 告警仪表盘统计数据
export interface AlarmDashboardStats {
  overview: AlarmOverviewStats
  trend: { date: string; count: number }[]
  trend_range: string
  device_top: AlarmDeviceTopItem[]
  area_top: AlarmAreaTopItem[]
  type_stats: AlarmTypeStatsItem[]
  level_stats: AlarmLevelStatsItem[]
}

export interface AlarmTrendResponse {
  trend: { date: string; count: number }[]
  trend_range: string
}

/**
 * 获取告警仪表盘统计数据
 * @param trendDays 趋势统计天数，1=今日，7=7日，14=14日，30=30日
 */
export function getAlarmDashboard(trendDays: number = 1) {
  return request.get<AlarmDashboardStats>('/alarms/dashboard', {
    params: { trend_days: trendDays }
  })
}

/**
 * 获取告警趋势（仅趋势，用于按需切换）
 * @param days 1=今日，7/14/30=近N天
 */
export function getAlarmTrend(days: number = 1) {
  return request.get<AlarmTrendResponse>('/alarms/trend', {
    params: { days }
  })
}
