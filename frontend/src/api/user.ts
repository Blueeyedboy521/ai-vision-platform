/**
 * 用户管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 用户角色
export type UserRole = 'admin' | 'operator' | 'viewer'

// 用户信息
export interface User {
  id: string
  username: string
  nickname: string | null
  email: string | null
  phone: string | null
  avatar: string | null
  role: UserRole
  is_active: boolean
  is_admin: boolean
  remark: string | null
  last_login_at: string | null
  created_at: string
  updated_at: string
}

// 创建用户请求
export interface CreateUserRequest {
  username: string
  password: string
  nickname?: string
  email?: string
  phone?: string
  role?: UserRole
  is_active?: boolean
  remark?: string
}

// 更新用户请求
export interface UpdateUserRequest {
  nickname?: string
  email?: string
  phone?: string
  avatar?: string
  role?: UserRole
  is_active?: boolean
  remark?: string
}

// 用户列表查询参数
export interface UserQueryParams {
  page?: number
  page_size?: number
  role?: UserRole
  is_active?: boolean
  keyword?: string
}

/**
 * 获取用户列表
 */
export function getUserList(params?: UserQueryParams) {
  return request.get<PageResponse<User>>('/users', { params })
}

/**
 * 获取用户详情
 */
export function getUser(id: string) {
  return request.get<User>(`/users/${id}`)
}

/**
 * 创建用户
 */
export function createUser(data: CreateUserRequest) {
  return request.post<User>('/users', data)
}

/**
 * 更新用户
 */
export function updateUser(id: string, data: UpdateUserRequest) {
  return request.put<User>(`/users/${id}`, data)
}

/**
 * 删除用户
 */
export function deleteUser(id: string) {
  return request.delete(`/users/${id}`)
}

/**
 * 重置用户密码
 */
export function resetUserPassword(id: string, newPassword: string) {
  return request.post(`/users/${id}/reset-password`, { new_password: newPassword })
}

/**
 * 启用用户
 */
export function enableUser(id: string) {
  return request.post(`/users/${id}/enable`)
}

/**
 * 禁用用户
 */
export function disableUser(id: string) {
  return request.post(`/users/${id}/disable`)
}
