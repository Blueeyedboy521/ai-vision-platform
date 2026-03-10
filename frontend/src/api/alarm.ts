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
