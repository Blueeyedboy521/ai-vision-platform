/**
 * 认证相关 API
 */
import { request, type ApiResponse } from './request'

// 用户信息
export interface UserInfo {
  id: string
  username: string
  nickname: string | null
  email: string | null
  phone: string | null
  avatar: string | null
  role: string
  is_admin: boolean
}

// Token 信息
export interface TokenInfo {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// 登录响应数据
export interface LoginData {
  token: TokenInfo
  user: UserInfo
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 刷新 Token 请求
export interface RefreshTokenRequest {
  refresh_token: string
}

// 修改密码请求
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 用户登录
 */
export function login(data: LoginRequest) {
  return request.post<LoginData>('/auth/login', data)
}

/**
 * 刷新 Token
 */
export function refreshToken(data: RefreshTokenRequest) {
  return request.post<TokenInfo>('/auth/refresh', data)
}

/**
 * 用户登出
 */
export function logout() {
  return request.post('/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request.get<UserInfo>('/auth/me')
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest) {
  return request.post('/auth/change-password', data)
}
