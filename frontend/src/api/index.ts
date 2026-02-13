/**
 * API 统一入口
 * 
 * 导出所有 API 模块
 */

// 基础请求
export { request, type ApiResponse, type PageResponse } from './request'

// 认证相关
export * from './auth'

// 区域管理
export * from './area'

// 摄像头管理
export * from './camera'

// 模型管理
export * from './model'

// 算法管理
export * from './algorithm'

// 告警管理
export * from './alarm'

// 推送配置
export * from './push'

// 用户管理
export * from './user'

// 系统管理
export * from './system'
