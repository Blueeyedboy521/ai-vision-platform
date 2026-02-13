/**
 * 区域管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 区域信息
export interface Area {
  id: string
  name: string
  code: string | null
  description: string | null
  parent_id: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

// 区域树节点
export interface AreaTreeNode extends Area {
  children?: AreaTreeNode[]
}

// 创建区域请求
export interface CreateAreaRequest {
  name: string
  code?: string
  description?: string
  parent_id?: string
  sort_order?: number
}

// 更新区域请求
export interface UpdateAreaRequest {
  name?: string
  code?: string
  description?: string
  parent_id?: string
  sort_order?: number
}

/**
 * 获取区域列表
 */
export function getAreaList() {
  return request.get<Area[]>('/areas')
}

/**
 * 获取区域树
 */
export function getAreaTree() {
  return request.get<AreaTreeNode[]>('/areas/tree')
}

/**
 * 获取区域详情
 */
export function getArea(id: string) {
  return request.get<Area>(`/areas/${id}`)
}

/**
 * 创建区域
 */
export function createArea(data: CreateAreaRequest) {
  return request.post<Area>('/areas', data)
}

/**
 * 更新区域
 */
export function updateArea(id: string, data: UpdateAreaRequest) {
  return request.put<Area>(`/areas/${id}`, data)
}

/**
 * 删除区域
 */
export function deleteArea(id: string) {
  return request.delete(`/areas/${id}`)
}
