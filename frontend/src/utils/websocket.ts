/**
 * WebSocket 客户端封装
 * 
 * 支持自动重连、心跳检测、消息解析
 */

export interface WebSocketOptions {
  url: string
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (error: Event) => void
  onMessage?: (data: any) => void
}

export type MessageHandler = (data: any) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private options: Required<WebSocketOptions>
  private reconnectAttempts = 0
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private messageHandlers: Map<string, MessageHandler[]> = new Map()
  private isManualClose = false

  constructor(options: WebSocketOptions) {
    this.options = {
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      onOpen: () => {},
      onClose: () => {},
      onError: () => {},
      onMessage: () => {},
      ...options
    }
  }

  /**
   * 连接 WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket 已连接')
      return
    }

    this.isManualClose = false
    
    try {
      this.ws = new WebSocket(this.options.url)
      this.setupEventHandlers()
    } catch (error) {
      console.error('WebSocket 连接失败:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()
    this.clearReconnectTimer()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 发送消息
   */
  send(data: any): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法发送消息')
      return
    }

    const message = typeof data === 'string' ? data : JSON.stringify(data)
    this.ws.send(message)
  }

  /**
   * 订阅消息类型
   */
  on(type: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)!.push(handler)
  }

  /**
   * 取消订阅
   */
  off(type: string, handler?: MessageHandler): void {
    if (!handler) {
      this.messageHandlers.delete(type)
      return
    }
    
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket 已连接')
      this.reconnectAttempts = 0
      this.startHeartbeat()
      this.options.onOpen()
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket 已断开:', event.code, event.reason)
      this.stopHeartbeat()
      this.options.onClose(event)
      
      if (!this.isManualClose) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      this.options.onError(error)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.options.onMessage(data)
        
        // 分发消息到订阅者
        if (data.type) {
          const handlers = this.messageHandlers.get(data.type)
          if (handlers) {
            handlers.forEach(handler => handler(data))
          }
        }
        
        // 处理心跳响应
        if (data.type === 'pong') {
          console.debug('收到心跳响应')
        }
      } catch (error) {
        // 非 JSON 消息
        this.options.onMessage(event.data)
      }
    }
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() })
      }
    }, this.options.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    if (!this.options.reconnect) return
    
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('WebSocket 重连次数已达上限')
      return
    }
    
    this.clearReconnectTimer()
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      console.log(`WebSocket 重连中... (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`)
      this.connect()
    }, this.options.reconnectInterval)
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

// 检测结果 WebSocket 连接
export function createDetectionWebSocket(cameraId: string, onMessage: MessageHandler): WebSocketClient {
  const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000'
  const client = new WebSocketClient({
    url: `${baseUrl}/ws/detections/${cameraId}`,
    onMessage
  })
  return client
}

// 告警 WebSocket 连接
export function createAlarmWebSocket(onMessage: MessageHandler): WebSocketClient {
  const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000'
  const client = new WebSocketClient({
    url: `${baseUrl}/ws/alarms`,
    onMessage
  })
  return client
}

export default WebSocketClient
