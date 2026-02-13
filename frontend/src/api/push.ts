/**
 * 推送配置 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 推送类型
export type PushType = 'dingtalk' | 'wechat' | 'email' | 'sms' | 'webhook'

// 推送配置状态
export type PushConfigStatus = 'enabled' | 'disabled' | 'testing'

// 推送配置
export interface PushConfig {
  id: string
  name: string
  description: string | null
  push_type: PushType
  config: PushTypeConfig
  alarm_levels: string[]
  alarm_types: string[]
  camera_ids: string[]
  is_enabled: boolean
  status: PushConfigStatus
  last_push_at: string | null
  success_count: number
  fail_count: number
  created_at: string
  updated_at: string
}

// 推送类型配置
export interface PushTypeConfig {
  // 钉钉
  webhook_url?: string
  secret?: string
  at_mobiles?: string[]
  at_all?: boolean
  
  // 邮件
  smtp_host?: string
  smtp_port?: number
  smtp_username?: string
  smtp_password?: string
  smtp_ssl?: boolean
  from_email?: string
  to_emails?: string[]
  
  // 企业微信
  corp_id?: string
  agent_id?: string
  corp_secret?: string
  to_users?: string[]
  to_parties?: string[]
  to_tags?: string[]
  
  // Webhook
  url?: string
  method?: 'GET' | 'POST'
  headers?: Record<string, string>
  body_template?: string
  
  // 短信
  sms_provider?: string
  sms_access_key?: string
  sms_secret_key?: string
  sms_sign_name?: string
  sms_template_code?: string
  phone_numbers?: string[]
}

// 创建推送配置请求
export interface CreatePushConfigRequest {
  name: string
  description?: string
  push_type: PushType
  config: PushTypeConfig
  alarm_levels?: string[]
  alarm_types?: string[]
  camera_ids?: string[]
  is_enabled?: boolean
}

// 更新推送配置请求
export interface UpdatePushConfigRequest {
  name?: string
  description?: string
  push_type?: PushType
  config?: PushTypeConfig
  alarm_levels?: string[]
  alarm_types?: string[]
  camera_ids?: string[]
  is_enabled?: boolean
}

// 推送记录
export interface PushRecord {
  id: string
  config_id: string
  config_name?: string
  alarm_id: string
  alarm_title?: string
  push_type: PushType
  status: 'success' | 'failed'
  error_message: string | null
  request_data: any | null
  response_data: any | null
  push_at: string
}

// 推送记录查询参数
export interface PushRecordQueryParams {
  page?: number
  page_size?: number
  config_id?: string
  alarm_id?: string
  push_type?: PushType
  status?: 'success' | 'failed'
  start_time?: string
  end_time?: string
}

/**
 * 获取推送配置列表
 */
export function getPushConfigList(params?: { page?: number; page_size?: number; push_type?: PushType; is_enabled?: boolean }) {
  return request.get<PageResponse<PushConfig>>('/push-configs', { params })
}

/**
 * 获取推送配置详情
 */
export function getPushConfig(id: string) {
  return request.get<PushConfig>(`/push-configs/${id}`)
}

/**
 * 创建推送配置
 */
export function createPushConfig(data: CreatePushConfigRequest) {
  return request.post<PushConfig>('/push-configs', data)
}

/**
 * 更新推送配置
 */
export function updatePushConfig(id: string, data: UpdatePushConfigRequest) {
  return request.put<PushConfig>(`/push-configs/${id}`, data)
}

/**
 * 删除推送配置
 */
export function deletePushConfig(id: string) {
  return request.delete(`/push-configs/${id}`)
}

/**
 * 测试推送配置
 */
export function testPushConfig(id: string) {
  return request.post(`/push-configs/${id}/test`)
}

/**
 * 启用推送配置
 */
export function enablePushConfig(id: string) {
  return request.post(`/push-configs/${id}/enable`)
}

/**
 * 禁用推送配置
 */
export function disablePushConfig(id: string) {
  return request.post(`/push-configs/${id}/disable`)
}

/**
 * 获取推送记录列表
 */
export function getPushRecordList(params?: PushRecordQueryParams) {
  return request.get<PageResponse<PushRecord>>('/push-records', { params })
}
