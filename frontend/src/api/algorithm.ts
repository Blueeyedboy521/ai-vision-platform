/**
 * 算法管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 算法类型
export type AlgorithmType = 'detection' | 'classification' | 'segmentation' | 'tracking' | 'other'

// 算法信息
export interface Algorithm {
  id: string
  name: string
  code: string | null
  description: string | null
  algorithm_type: AlgorithmType
  model_id: string | null
  model_name?: string
  config: AlgorithmConfig | null
  default_threshold: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

// 算法配置
export interface AlgorithmConfig {
  classes?: string[]
  confidence_threshold?: number
  nms_threshold?: number
  max_detections?: number
  min_box_size?: number
  custom?: Record<string, any>
}

// 创建算法请求
export interface CreateAlgorithmRequest {
  name: string
  code?: string
  description?: string
  algorithm_type: AlgorithmType
  model_id?: string
  config?: AlgorithmConfig
  default_threshold?: number
  is_enabled?: boolean
}

// 更新算法请求
export interface UpdateAlgorithmRequest {
  name?: string
  code?: string
  description?: string
  algorithm_type?: AlgorithmType
  model_id?: string
  config?: AlgorithmConfig
  default_threshold?: number
  is_enabled?: boolean
}

// 算法列表查询参数
export interface AlgorithmQueryParams {
  page?: number
  page_size?: number
  algorithm_type?: AlgorithmType
  model_id?: string
  is_enabled?: boolean
  keyword?: string
}

/**
 * 获取算法列表
 */
export function getAlgorithmList(params?: AlgorithmQueryParams) {
  return request.get<PageResponse<Algorithm>>('/algorithms', { params })
}

/**
 * 获取算法详情
 */
export function getAlgorithm(id: string) {
  return request.get<Algorithm>(`/algorithms/${id}`)
}

/**
 * 创建算法
 */
export function createAlgorithm(data: CreateAlgorithmRequest) {
  return request.post<Algorithm>('/algorithms', data)
}

/**
 * 更新算法
 */
export function updateAlgorithm(id: string, data: UpdateAlgorithmRequest) {
  return request.put<Algorithm>(`/algorithms/${id}`, data)
}

/**
 * 删除算法
 */
export function deleteAlgorithm(id: string) {
  return request.delete(`/algorithms/${id}`)
}

/**
 * 获取算法可用类别
 */
export function getAlgorithmClasses(id: string) {
  return request.get<string[]>(`/algorithms/${id}/classes`)
}
