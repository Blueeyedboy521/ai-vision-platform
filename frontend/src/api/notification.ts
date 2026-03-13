/**
 * 消息推送配置 API（通道 / 模板）
 * 对应后端 /api/v1/notifications
 */
import { request, type ApiResponse, type PageResponse } from './request'

export type ProviderType = 'dingtalk_bot' | 'wecom_bot'
export type TemplateType = 'text' | 'rich'

export interface NotificationEndpoint {
  id: string
  name: string
  provider: ProviderType
  is_enabled: boolean
  config_masked?: Record<string, unknown>
  created_at: string | null
  updated_at: string | null
}

export interface NotificationTemplate {
  id: string
  name: string
  type: TemplateType
  is_enabled: boolean
  content: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

export interface NotificationPolicy {
  id: string
  name: string
  priority: number
  is_enabled: boolean
  match: Record<string, unknown>
  actions: Record<string, unknown>[]
  match_desc?: string
  actions_desc?: string
  created_at?: string | null
  updated_at?: string | null
}

export interface CreateEndpointRequest {
  name: string
  provider: ProviderType
  is_enabled?: boolean
  config?: Record<string, unknown>
}

export interface UpdateEndpointRequest {
  name?: string
  is_enabled?: boolean
  config?: Record<string, unknown>
}

export interface CreateTemplateRequest {
  name: string
  type: TemplateType
  is_enabled?: boolean
  content?: Record<string, unknown>
}

export interface UpdateTemplateRequest {
  name?: string
  is_enabled?: boolean
  content?: Record<string, unknown>
}

export interface CreatePolicyRequest {
  name: string
  priority?: number
  is_enabled?: boolean
  match: Record<string, unknown>
  actions: Record<string, unknown>[]
}

export interface UpdatePolicyRequest {
  name?: string
  priority?: number
  is_enabled?: boolean
  match?: Record<string, unknown>
  actions?: Record<string, unknown>[]
}

/** 获取推送通道列表 */
export function getNotificationEndpoints() {
  return request.get<ApiResponse<NotificationEndpoint[]>>('/notifications/endpoints')
}

/** 创建推送通道 */
export function createNotificationEndpoint(data: CreateEndpointRequest) {
  return request.post<ApiResponse<{ id: string }>>('/notifications/endpoints', data)
}

/** 更新推送通道 */
export function updateNotificationEndpoint(id: string, data: UpdateEndpointRequest) {
  return request.put<ApiResponse<{ updated: boolean }>>(`/notifications/endpoints/${id}`, data)
}

/** 删除推送通道 */
export function deleteNotificationEndpoint(id: string) {
  return request.delete<ApiResponse<{ deleted: boolean }>>(`/notifications/endpoints/${id}`)
}

/** 获取推送模板列表 */
export function getNotificationTemplates() {
  return request.get<ApiResponse<NotificationTemplate[]>>('/notifications/templates')
}

/** 创建推送模板 */
export function createNotificationTemplate(data: CreateTemplateRequest) {
  return request.post<ApiResponse<{ id: string }>>('/notifications/templates', data)
}

/** 更新推送模板 */
export function updateNotificationTemplate(id: string, data: UpdateTemplateRequest) {
  return request.put<ApiResponse<{ updated: boolean }>>(`/notifications/templates/${id}`, data)
}

/** 删除推送模板 */
export function deleteNotificationTemplate(id: string) {
  return request.delete<ApiResponse<{ deleted: boolean }>>(`/notifications/templates/${id}`)
}

/** 获取推送策略列表 */
export function getNotificationPolicies() {
  return request.get<ApiResponse<NotificationPolicy[]>>('/notifications/policies')
}

/** 获取推送策略详情 */
export function getNotificationPolicy(id: string) {
  return request.get<ApiResponse<NotificationPolicy>>(`/notifications/policies/${id}`)
}

/** 创建推送策略 */
export function createNotificationPolicy(data: CreatePolicyRequest) {
  return request.post<ApiResponse<{ id: string }>>('/notifications/policies', data)
}

/** 更新推送策略 */
export function updateNotificationPolicy(id: string, data: UpdatePolicyRequest) {
  return request.put<ApiResponse<{ updated: boolean }>>(`/notifications/policies/${id}`, data)
}

/** 删除推送策略 */
export function deleteNotificationPolicy(id: string) {
  return request.delete<ApiResponse<{ deleted: boolean }>>(`/notifications/policies/${id}`)
}
