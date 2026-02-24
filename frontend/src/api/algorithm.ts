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

// 创建算法请求（与后端一致：model_id、target_classes、default_confidence、alert_config）
export interface CreateAlgorithmRequest {
  name: string
  code: string
  description?: string
  model_id: string
  target_classes: string[]
  default_confidence?: number
  alert_config?: Record<string, unknown>
  is_enabled?: boolean
}

// 更新算法请求
export interface UpdateAlgorithmRequest {
  name?: string
  description?: string
  model_id?: string
  target_classes?: string[]
  default_confidence?: number
  alert_config?: Record<string, unknown>
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

// ==================== 摄像头-算法配置 ====================

export interface CameraAlgorithmConfig {
  id: string
  camera_id: string
  algorithm_id: string
  algorithm_name?: string
  model_id: string
  confidence: number | null
  effective_confidence: number
  is_enabled: boolean
}

export interface AddCameraAlgorithmRequest {
  camera_id: string
  algorithm_id: string
  model_id: string
  confidence?: number
  is_enabled?: boolean
}

/** 获取某摄像头的算法配置列表 */
export function getCameraAlgorithmConfigs(cameraId: string) {
  return request.get<CameraAlgorithmConfig[]>(`/algorithms/camera/${cameraId}/configs`)
}

/** 为摄像头添加算法配置 */
export function addCameraAlgorithmConfig(cameraId: string, data: AddCameraAlgorithmRequest) {
  return request.post<{ id: string }>(`/algorithms/camera/${cameraId}/configs`, data)
}

/** 删除摄像头某条算法配置 */
export function deleteCameraAlgorithmConfig(cameraId: string, configId: string) {
  return request.delete(`/algorithms/camera/${cameraId}/configs/${configId}`)
}
