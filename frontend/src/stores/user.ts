/**
 * 用户状态管理
 * 
 * 管理用户登录状态、Token、用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, refreshToken as refreshTokenApi, getCurrentUser } from '@/api/auth'
import type { UserInfo, LoginRequest, TokenInfo } from '@/api/auth'

// localStorage 存储键名
const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user_info'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshTokenValue = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const userInfo = ref<UserInfo | null>(
    localStorage.getItem(USER_KEY) ? JSON.parse(localStorage.getItem(USER_KEY)!) : null
  )
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const isAdmin = computed(() => userInfo.value?.is_admin || false)
  const username = computed(() => userInfo.value?.username || '')
  const nickname = computed(() => userInfo.value?.nickname || userInfo.value?.username || '')
  const avatar = computed(() => userInfo.value?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${username.value}`)
  
  /**
   * 用户登录
   */
  async function login(credentials: LoginRequest): Promise<boolean> {
    try {
      const response = await loginApi(credentials)
      const data = response.data.data
      
      if (data) {
        // 保存 Token
        setToken(data.token.access_token, data.token.refresh_token)
        // 保存用户信息
        setUserInfo(data.user)
        return true
      }
      return false
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }
  
  /**
   * 用户登出
   */
  async function logout(): Promise<void> {
    try {
      // 调用后端登出接口（将 Token 加入黑名单）
      if (token.value) {
        await logoutApi()
      }
    } catch (error) {
      // 忽略登出错误
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地状态
      clearAuth()
    }
  }
  
  /**
   * 刷新 Token
   */
  async function refreshToken(): Promise<string | null> {
    if (!refreshTokenValue.value) {
      return null
    }
    
    try {
      const response = await refreshTokenApi({ refresh_token: refreshTokenValue.value })
      const data = response.data.data
      
      if (data) {
        setToken(data.access_token, data.refresh_token)
        return data.access_token
      }
      return null
    } catch (error) {
      console.error('刷新 Token 失败:', error)
      clearAuth()
      return null
    }
  }
  
  /**
   * 获取并更新用户信息
   */
  async function fetchUserInfo(): Promise<UserInfo | null> {
    if (!token.value) {
      return null
    }
    
    try {
      const response = await getCurrentUser()
      const data = response.data.data
      
      if (data) {
        setUserInfo(data)
        return data
      }
      return null
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    }
  }
  
  /**
   * 设置 Token
   */
  function setToken(accessToken: string, refreshTokenStr: string): void {
    token.value = accessToken
    refreshTokenValue.value = refreshTokenStr
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshTokenStr)
  }
  
  /**
   * 设置用户信息
   */
  function setUserInfo(info: UserInfo): void {
    userInfo.value = info
    localStorage.setItem(USER_KEY, JSON.stringify(info))
  }
  
  /**
   * 清除认证信息
   */
  function clearAuth(): void {
    token.value = null
    refreshTokenValue.value = null
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
  
  /**
   * 检查是否已登录（用于路由守卫）
   */
  function checkAuth(): boolean {
    return !!token.value
  }
  
  return {
    // 状态
    token,
    userInfo,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    username,
    nickname,
    avatar,
    
    // 方法
    login,
    logout,
    refreshToken,
    fetchUserInfo,
    checkAuth,
    clearAuth
  }
})
