/**
 * 摄像头管理 API
 */
import { request, type ApiResponse, type PageResponse } from './request'

// 摄像头状态
export type CameraStatus = 'online' | 'offline' | 'error'

// 摄像头信息
export interface Camera {
  id: string
  name: string
  code: string | null
  description: string | null
  area_id: string | null
  area_name?: string
  rtsp_url: string
  manufacturer: string | null
  device_model: string | null
  ip_address: string | null
  location: string | null
  longitude: number | null
  latitude: number | null
  is_enabled: boolean
  status: CameraStatus
  /** 在线状态（来自 Redis camera:online:{id}） */
  online?: boolean
  fps: number
  resolution: string | null
  /** 识别间隔(秒)，控制该摄像头推理抽帧频率 */
  inference_interval_sec: number
  algorithm_count?: number
  inference_started?: boolean
  snapshot_url?: string | null
  created_at: string
  updated_at: string
}

// 创建摄像头请求
export interface CreateCameraRequest {
  name: string
  code?: string
  description?: string
  area_id?: string
  rtsp_url: string
  manufacturer?: string
  device_model?: string
  ip_address?: string
  location?: string
  longitude?: number
  latitude?: number
  is_enabled?: boolean
  fps?: number
  resolution?: string
  inference_interval_sec?: number
}

// 更新摄像头请求
export interface UpdateCameraRequest {
  name?: string
  code?: string
  description?: string
  area_id?: string
  rtsp_url?: string
  manufacturer?: string
  device_model?: string
  ip_address?: string
  location?: string
  longitude?: number
  latitude?: number
  is_enabled?: boolean
  fps?: number
  resolution?: string
  inference_interval_sec?: number
}

// 摄像头列表查询参数
export interface CameraQueryParams {
  page?: number
  page_size?: number
  area_id?: string
  status?: CameraStatus
  is_enabled?: boolean
  keyword?: string
}

// 播放 URL
export interface PlayUrls {
  rtsp: string | null
  rtmp: string | null
  http_flv: string | null
  hls: string | null
  ws_flv: string | null
}

/**
 * 获取摄像头列表
 */
export function getCameraList(params?: CameraQueryParams) {
  return request.get<PageResponse<Camera>>('/cameras', { params })
}

/**
 * 获取摄像头详情
 */
export function getCamera(id: string) {
  return request.get<Camera>(`/cameras/${id}`)
}

/**
 * 创建摄像头
 */
export function createCamera(data: CreateCameraRequest) {
  return request.post<Camera>('/cameras', data)
}

/**
 * 更新摄像头
 */
export function updateCamera(id: string, data: UpdateCameraRequest) {
  return request.put<Camera>(`/cameras/${id}`, data)
}

/**
 * 删除摄像头
 */
export function deleteCamera(id: string) {
  return request.delete(`/cameras/${id}`)
}

/**
 * 启动摄像头
 */
export function startCamera(id: string) {
  return request.post(`/cameras/${id}/start`)
}

/**
 * 停止摄像头
 */
export function stopCamera(id: string) {
  return request.post(`/cameras/${id}/stop`)
}

/**
 * 启动摄像头推理（后台推理）
 */
export function startCameraInference(id: string) {
  return request.post(`/cameras/${id}/start-inference`)
}

/**
 * 停止摄像头推理（后台推理）
 */
export function stopCameraInference(id: string) {
  return request.post(`/cameras/${id}/stop-inference`)
}

/**
 * 摄像头直播心跳（播放时每 60 秒调用一次）
 */
export function cameraLiveHeartbeat(id: string) {
  return request.post(`/cameras/${id}/live-heartbeat`)
}

/**
 * 获取播放地址
 */
export function getCameraPlayUrls(id: string) {
  return request.get<PlayUrls>(`/cameras/${id}/play-url`)
}

/** 流通性测试请求 */
export interface ProbeStreamRequest {
  rtsp_url: string
}

/** 流通性测试响应 */
export interface ProbeStreamResult {
  width: number
  height: number
  fps: number | null
  resolution: string | null
}

/**
 * 流通性测试（后端用 OpenCV/ffprobe 获取宽高、帧率）
 */
export function probeStream(data: ProbeStreamRequest) {
  return request.post<ProbeStreamResult>('/cameras/probe-stream', data)
}

/**
 * 抓拍并保存为最新缩略图
 */
export function snapshotCamera(id: string) {
  return request.post<{ snapshot_url: string }>(`/cameras/${id}/snapshot`)
}
