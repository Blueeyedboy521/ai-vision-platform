/**
 * 告警管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 告警级别
export type AlarmLevel = 'info' | 'warning' | 'critical'

// 告警状态
export type AlarmStatus = 'pending' | 'confirmed' | 'resolved' | 'ignored'

// 告警信息
export interface Alarm {
  id: string
  camera_id: string
  camera_name?: string
  algorithm_id: string
  algorithm_name?: string
  alarm_type: string
  alarm_level: AlarmLevel
  title: string
  content: string | null
  image_path: string | null
  video_path: string | null
  detection_data: any | null
  status: AlarmStatus
  confirmed_by: string | null
  confirmed_at: string | null
  resolved_by: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
}

// 告警列表查询参数
export interface AlarmQueryParams {
  page?: number
  page_size?: number
  camera_id?: string
  algorithm_id?: string
  alarm_type?: string
  alarm_level?: AlarmLevel
  status?: AlarmStatus
  start_time?: string
  end_time?: string
  keyword?: string
}

// 告警统计
export interface AlarmStatistics {
  total: number
  pending: number
  confirmed: number
  resolved: number
  ignored: number
  by_level: {
    info: number
    warning: number
    critical: number
  }
  by_type: Record<string, number>
  today_count: number
  week_count: number
}

/**
 * 获取告警列表
 */
export function getAlarmList(params?: AlarmQueryParams) {
  return request.get<PageResponse<Alarm>>('/alarms', { params })
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
 * 获取告警统计
 */
export function getAlarmStatistics(params?: { camera_id?: string; start_time?: string; end_time?: string }) {
  return request.get<AlarmStatistics>('/alarms/statistics', { params })
}

/**
 * 导出告警记录
 */
export function exportAlarms(params?: AlarmQueryParams) {
  return request.get('/alarms/export', { params, responseType: 'blob' as any })
}
