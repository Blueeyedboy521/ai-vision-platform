<template>
  <div v-if="alarm" class="alarm-detail">
    <div class="alarm-detail__header">
      <span class="alarm-detail__level" :class="`alarm-detail__level--${level}`">
        {{ levelText }}
      </span>
      <span class="alarm-detail__type">{{ titleText }}</span>
      <span class="alarm-detail__time">{{ fullTime }}</span>
    </div>

    <div class="alarm-detail__body">
      <div class="alarm-detail__info">
        <div class="info-row">
          <span class="info-label">摄像头</span>
          <span class="info-value">{{ alarm.camera_name || alarm.camera_id || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">区域</span>
          <span class="info-value">{{ alarm.area_name || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">算法</span>
          <span class="info-value">{{ alarm.algorithm_name || alarm.algorithm_id || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">告警描述</span>
          <span class="info-value">{{ alarm.title || alarm.description || '检测到异常事件' }}</span>
        </div>
      </div>

      <div class="alarm-detail__snapshot" v-if="snapshotUrl">
        <div class="snapshot-title-row">
          <h4 class="snapshot-title">告警截图</h4>
          <span class="snapshot-tip">点击图片可缩放查看</span>
        </div>
        <div
          class="alarm-detail__snapshot-clickable"
          role="button"
          tabindex="0"
          @click="openViewer"
          @keydown.enter="openViewer"
        >
          <img :src="snapshotUrl" alt="告警截图" />
        </div>
      </div>
    </div>

    <ImageViewer
      v-model:show="showViewer"
      :src="snapshotUrl"
      :detections="detections"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ImageViewer from '@/components/ImageViewer.vue'
import { useUserStore } from '@/stores/user'
import { appendToken } from '@/utils/auth_url'

const props = defineProps<{ alarm: any | null }>()

const userStore = useUserStore()

const showViewer = ref(false)

const level = computed(() => {
  const lvl = (props.alarm?.level || props.alarm?.alert_level || 'info').toLowerCase()
  if (lvl === 'critical') return 'critical'
  if (lvl === 'danger') return 'danger'
  if (lvl === 'warning') return 'warning'
  return 'info'
})

const levelText = computed(() => {
  const map: Record<string, string> = { info: '提示', warning: '一般', danger: '高危', critical: '高危' }
  return map[level.value] || '提示'
})

const titleText = computed(() => {
  const a = props.alarm as any
  if (!a) return '告警'
  return a.algorithm_name || a.alarm_type || '告警'
})

const fullTime = computed(() => {
  const a = props.alarm as any
  const ts = a?.alarm_time || a?.timestamp || a?.created_at
  if (!ts) return ''
  try {
    const d = new Date(ts)
    if (Number.isNaN(d.getTime())) return String(ts)
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
    return String(ts)
  }
})

const snapshotUrl = computed(() => {
  const a = props.alarm as any
  const rawUrl = a?.snapshot_url || a?.snapshotUrl || a?.snapshot_path || ''
  // 详情/查看器强制使用原图（列表/冒泡通常传的是 variant=thumb）
  const url = String(rawUrl || '')
  const withOrigin = url.includes('variant=thumb')
    ? url.replace('variant=thumb', 'variant=origin')
    : url.includes('variant=origin')
      ? url
      : (url.includes('?') ? `${url}&variant=origin` : `${url}?variant=origin`)
  return appendToken(withOrigin, userStore.token)
})

const detections = computed<any[] | null>(() => {
  const a = props.alarm as any
  const dets = a?.detection_data || a?.detections
  return Array.isArray(dets) ? dets : null
})

function openViewer() {
  if (!snapshotUrl.value) return
  showViewer.value = true
}
</script>

<style scoped>
.alarm-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alarm-detail__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alarm-detail__level {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.alarm-detail__level--info { background: rgba(6,182,212,0.12); color: #0e7490; }
.alarm-detail__level--warning { background: rgba(245,158,11,0.12); color: #b45309; }
.alarm-detail__level--danger,
.alarm-detail__level--critical { background: rgba(239,68,68,0.12); color: #b91c1c; }

.alarm-detail__type { font-weight: 700; color: var(--text-primary); }
.alarm-detail__time { margin-left: auto; font-size: 12px; color: var(--text-muted); }

.alarm-detail__body {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1.25fr);
  gap: 16px;
}

.alarm-detail__info { display: flex; flex-direction: column; gap: 10px; }
.info-row { display: flex; gap: 10px; }
.info-label { width: 64px; font-size: 12px; color: var(--text-muted); }
.info-value { flex: 1; font-size: 13px; color: var(--text-primary); line-height: 1.5; }

.snapshot-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}
.snapshot-title { margin: 0; font-size: 13px; color: var(--text-secondary); }
.snapshot-tip { font-size: 12px; color: var(--text-muted); }

.alarm-detail__snapshot-clickable {
  cursor: zoom-in;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}
.alarm-detail__snapshot-clickable:hover {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
.alarm-detail__snapshot-clickable img {
  width: 100%;
  display: block;
  object-fit: contain;
}
</style>

