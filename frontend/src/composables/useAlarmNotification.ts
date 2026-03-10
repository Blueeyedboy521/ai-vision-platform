import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { appendToken } from '@/utils/auth_url'

export interface AlarmToast {
  id: string
  level: string
  title: string
  subtitle: string
  cameraName?: string
  areaName?: string
  fullTime?: string
  thumb?: string | null
  alarmTime?: string
  raw: any
}

const toasts = ref<AlarmToast[]>([])
const showDetailModal = ref(false)
const currentAlarmDetail = ref<any | null>(null)

function formatHHMMSS(input: any): string {
  try {
    if (input == null || input === '') return ''
    const d = input instanceof Date ? input : new Date(input)
    if (Number.isNaN(d.getTime())) return ''
    // 统一 24 小时制
    return d.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return ''
  }
}

function formatFullDateTime(input: any): string {
  try {
    if (input == null || input === '') return ''
    const d = input instanceof Date ? input : new Date(input)
    if (Number.isNaN(d.getTime())) return ''
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return ''
  }
}

export function useAlarmNotification() {
  const userStore = useUserStore()

  function pushAlarmToast(data: any) {
    const level = (data.level || data.alert_level || 'info').toLowerCase()
    const cameraName = data.camera_name || data.camera_id
    const areaName = data.area_name || data.region_name || ''
    const algoName = data.algorithm_name || data.alarm_type || '告警'
    const ts = data.timestamp || data.alarm_time || data.created_at
    const time = formatHHMMSS(ts)
    const fullTime = formatFullDateTime(ts)
    const rawSnapshot = data.snapshot_url || data.snapshotUrl || data.snapshot_path || data.snapshot_path
    const token = userStore.token
    const thumb = appendToken(rawSnapshot, token)

    // 详情弹框/图片预览复用同一份对象时，确保 snapshot_url 已携带 token
    const raw = { ...(data || {}) }
    if (!raw.snapshot_url && rawSnapshot) {
      raw.snapshot_url = rawSnapshot
    }
    raw.snapshot_url = appendToken(raw.snapshot_url, token) || raw.snapshot_url

    const toast: AlarmToast = {
      id: data.alarm_id || `${Date.now()}-${Math.random()}`,
      level,
      title: algoName,
      subtitle: [cameraName, areaName, fullTime].filter(Boolean).join(' · '),
      cameraName,
      areaName,
      fullTime,
      thumb,
      alarmTime: time,
      raw,
    }

    toasts.value.unshift(toast)
    if (toasts.value.length > 3) {
      toasts.value = toasts.value.slice(0, 3)
    }

    const timeout = level === 'critical' || level === 'danger' ? 8000 : 4000
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== toast.id)
    }, timeout)
  }

  function openDetailFromToast(toast: AlarmToast) {
    currentAlarmDetail.value = toast.raw
    showDetailModal.value = true
  }

  function closeDetail() {
    showDetailModal.value = false
  }

  return {
    toasts,
    showDetailModal,
    currentAlarmDetail,
    pushAlarmToast,
    openDetailFromToast,
    closeDetail,
  }
}

