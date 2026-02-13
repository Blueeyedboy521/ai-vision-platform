/**
 * 模型管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 模型状态
export type ModelStatus = 'uploaded' | 'loading' | 'loaded' | 'error'

// 模型信息
export interface Model {
  id: string
  name: string
  code: string | null
  description: string | null
  file_path: string
  file_size: number
  model_type: string
  framework: string | null
  version: string | null
  input_shape: any | null
  output_shape: any | null
  classes: string[] | null
  class_count: number
  status: ModelStatus
  is_enabled: boolean
  created_at: string
  updated_at: string
}

// 创建模型请求
export interface CreateModelRequest {
  name: string
  code?: string
  description?: string
  file_path: string
  file_size?: number
  model_type: string
  framework?: string
  version?: string
  input_shape?: any
  output_shape?: any
  classes?: string[]
  class_count?: number
  is_enabled?: boolean
}

// 更新模型请求
export interface UpdateModelRequest {
  name?: string
  code?: string
  description?: string
  file_path?: string
  file_size?: number
  model_type?: string
  framework?: string
  version?: string
  input_shape?: any
  output_shape?: any
  classes?: string[]
  class_count?: number
  is_enabled?: boolean
}

// 模型列表查询参数
export interface ModelQueryParams {
  page?: number
  page_size?: number
  model_type?: string
  framework?: string
  status?: ModelStatus
  is_enabled?: boolean
  keyword?: string
}

/**
 * 获取模型列表
 */
export function getModelList(params?: ModelQueryParams) {
  return request.get<PageResponse<Model>>('/models', { params })
}

/**
 * 获取模型详情
 */
export function getModel(id: string) {
  return request.get<Model>(`/models/${id}`)
}

/**
 * 创建模型
 */
export function createModel(data: CreateModelRequest) {
  return request.post<Model>('/models', data)
}

/**
 * 更新模型
 */
export function updateModel(id: string, data: UpdateModelRequest) {
  return request.put<Model>(`/models/${id}`, data)
}

/**
 * 删除模型
 */
export function deleteModel(id: string) {
  return request.delete(`/models/${id}`)
}

/**
 * 加载模型到推理引擎
 */
export function loadModel(id: string) {
  return request.post(`/models/${id}/load`)
}

/**
 * 卸载模型
 */
export function unloadModel(id: string) {
  return request.post(`/models/${id}/unload`)
}

/**
 * 获取模型支持的类别列表
 */
export function getModelClasses(id: string) {
  return request.get<string[]>(`/models/${id}/classes`)
}
