import { onMounted, onUnmounted } from 'vue'
import { createAlarmWebSocket, type WebSocketClient } from '@/utils/websocket'
import { useAlarmNotification } from '@/composables/useAlarmNotification'

let client: WebSocketClient | null = null
let inited = false

export function useAppWebSocket() {
  const { pushAlarmToast } = useAlarmNotification()

  function ensureClient() {
    if (client) return
    client = createAlarmWebSocket((data: any) => {
      // 统一处理告警消息
      if (data?.type === 'alarm') {
        const payload = (data as any).data || data
        pushAlarmToast(payload)
      }
    })
    client.connect()
  }

  onMounted(() => {
    if (!inited) {
      ensureClient()
      inited = true
    }
  })

  onUnmounted(() => {
    // 保持全局长连，不在组件卸载时主动断开
  })

  return {}
}

