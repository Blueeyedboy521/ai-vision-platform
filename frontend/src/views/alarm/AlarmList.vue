<template>
  <div class="alarm-page">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">告警列表</h1>
        <p class="page-header__subtitle">聚合展示告警事件，支持快速定位设备与区域</p>
      </div>
      <div class="page-header__actions">
        <n-button @click="handleExport">
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          导出
        </n-button>
        <n-button type="primary" @click="showSettingsModal = true">
          <template #icon>
            <n-icon><SettingsOutline /></n-icon>
          </template>
          设置
        </n-button>
      </div>
    </div>

    <div class="filter-bar card-border-xl">
      <div class="filter-bar__left">
        <n-select
          v-model:value="filters.level"
          :options="levelOptions"
          placeholder="告警级别"
          clearable
          style="width: 140px"
        />
        <n-select
          v-model:value="filters.status"
          :options="statusOptions"
          placeholder="处理状态"
          clearable
          style="width: 140px"
        />
        <n-date-picker
          v-model:value="filters.dateRange"
          type="daterange"
          clearable
          style="width: 260px"
        />
      </div>
      <div class="filter-bar__right">
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索告警标题、设备、区域..."
          clearable
          style="width: 320px"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
      </div>
    </div>

    <div class="list-card card-border-xl">
      <div class="list-head">
        <div class="list-head__left">
          <n-checkbox
            :checked="isAllSelected"
            :indeterminate="isIndeterminate"
            @update:checked="handleSelectAll"
          />
          <span class="list-head__title">告警事件</span>
          <span class="list-head__meta">共 {{ pageInfo.total }} 条</span>
        </div>
        <div class="list-head__right">
          <n-button v-if="selectedCount > 0" text type="primary" size="small" @click="batchHandle">
            批量处理（{{ selectedCount }}）
          </n-button>
        </div>
      </div>

      <div class="list-body">
        <div
          v-for="alarm in paginatedAlarms"
          :key="alarm.id"
          class="alarm-row"
          :class="`alarm-row--${alarm.level}`"
        >
          <div class="alarm-row__check">
            <n-checkbox v-model:checked="alarm.selected" />
          </div>

          <div
            class="alarm-row__thumb alarm-thumb--clickable"
            role="button"
            tabindex="0"
            @click="viewAlarm(alarm)"
            @keydown.enter="viewAlarm(alarm)"
          >
            <img v-if="alarm.snapshotUrl" :src="alarm.snapshotUrl" alt="告警截图" />
            <div v-else class="alarm-thumb__placeholder">—</div>
            <span class="level-pill" :class="`level-pill--${alarm.level}`">
              {{ getLevelText(alarm.level) }}
            </span>
          </div>

          <div class="alarm-row__main">
            <div class="alarm-row__title">
              <span class="alarm-title">{{ alarm.content || '告警' }}</span>
              <span class="alarm-type">
                <n-icon :size="16" class="type-icon"><component :is="getTypeIcon(alarm.type)" /></n-icon>
                {{ alarm.type }}
              </span>
            </div>

            <div class="alarm-row__meta">
              <span class="meta-chip">
                <span class="meta-label">区域</span>
                <span class="meta-value">{{ alarm.areaName || '未关联区域' }}</span>
              </span>
              <span class="meta-chip">
                <span class="meta-label">设备</span>
                <span class="meta-value">{{ alarm.device || '-' }}</span>
              </span>
              <span class="meta-chip meta-chip--time">
                <span class="meta-label">时间</span>
                <span class="meta-value">{{ alarm.time }}</span>
              </span>
            </div>
          </div>

          <div class="alarm-row__actions">
            <n-button text type="primary" size="small" @click="viewAlarm(alarm)">
              <template #icon><n-icon><EyeOutline /></n-icon></template>
            </n-button>
            <n-button text type="primary" size="small" @click="handleLivePlay(alarm)">
              视频直播
            </n-button>
            <n-button
              v-if="alarm.status === 'pending'"
              text
              type="success"
              size="small"
              @click="handleAlarm(alarm)"
            >
              <template #icon><n-icon><CheckmarkOutline /></n-icon></template>
            </n-button>
            <n-button text type="error" size="small" @click="deleteAlarm(alarm)">
              <template #icon><n-icon><TrashOutline /></n-icon></template>
            </n-button>
          </div>
        </div>
      </div>
    </div>

    <div class="pagination">
      <div class="pagination__info">已选择 {{ selectedCount }} 项</div>
      <n-pagination
        v-model:page="currentPage"
        :page-size="pageSize"
        :item-count="pageInfo.total"
        show-size-picker
        show-quick-jumper
        :page-sizes="[10, 20, 50]"
        @update:page-size="handlePageSizeChange"
        @update:page="handlePageChange"
      />
    </div>

    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      title="告警详情"
      :style="{ width: '900px' }"
      :bordered="false"
    >
      <AlarmDetail
        v-if="currentAlarm"
        :alarm="{
          level: currentAlarm.level,
          alarm_time: currentAlarm.time,
          camera_name: currentAlarm.device,
          area_name: currentAlarm.areaName,
          algorithm_name: currentAlarm.type,
          title: currentAlarm.content,
          description: currentAlarm.content,
          snapshot_url: currentAlarm.snapshotUrl,
          detection_data: currentAlarm.detectionData,
        }"
      />
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showDetailModal = false">关闭</n-button>
          <n-button type="primary" @click="handleCurrentAlarm">标记已处理</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showPlayer"
      preset="card"
      title="实时预览"
      :style="{ width: '960px' }"
      @after-leave="handlePlayerClosed"
    >
      <div style="width: 100%; aspect-ratio: 16 / 9;">
        <FlvPlayer v-if="currentPlayUrl" :url="currentPlayUrl" />
      </div>
    </n-modal>

    <n-modal
      v-model:show="showSettingsModal"
      preset="card"
      title="告警设置"
      :style="{ width: '500px' }"
      :bordered="false"
    >
      <n-form label-placement="left" label-width="120">
        <n-form-item label="告警声音提醒">
          <n-switch v-model:value="settings.soundEnabled" />
        </n-form-item>
        <n-form-item label="桌面通知">
          <n-switch v-model:value="settings.desktopNotification" />
        </n-form-item>
        <n-form-item label="自动刷新间隔">
          <n-select v-model:value="settings.refreshInterval" :options="refreshOptions" style="width: 200px" />
        </n-form-item>
        <n-form-item label="告警保留天数">
          <n-input-number v-model:value="settings.retentionDays" :min="7" :max="365" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showSettingsModal = false">取消</n-button>
          <n-button type="primary" @click="saveSettings">保存设置</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import {
  NButton,
  NCheckbox,
  NDatePicker,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NSelect,
  NSwitch,
  useMessage,
} from 'naive-ui'
import {
  AlertCircleOutline,
  BanOutline,
  BodyOutline,
  CarOutline,
  CheckmarkOutline,
  DownloadOutline,
  EyeOutline,
  FlameOutline,
  PersonOutline,
  SearchOutline,
  SettingsOutline,
  ShieldCheckmarkOutline,
  TrashOutline,
  WarningOutline,
} from '@vicons/ionicons5'
import { getAlarmList, type Alarm as ApiAlarm } from '@/api/alarm'
import FlvPlayer from '@/components/FlvPlayer.vue'
import AlarmDetail from '@/components/AlarmDetail.vue'
import { useUserStore } from '@/stores/user'
import { appendToken } from '@/utils/auth_url'
import { cameraLiveHeartbeat, getCameraPlayUrls, startCamera, stopCamera } from '@/api/camera'

interface Alarm {
  id: string
  level: 'critical' | 'warning' | 'info'
  type: string
  content: string
  device: string
  time: string
  status: 'pending' | 'processing' | 'resolved'
  selected?: boolean
  snapshotUrl?: string | null
  cameraId?: string
  detectionData?: any | null
  areaName?: string | null
}

const message = useMessage()
const userStore = useUserStore()

// Filters
const filters = ref({
  level: null as string | null,
  status: null as string | null,
  dateRange: null as [number, number] | null,
})
const searchQuery = ref('')

const levelOptions = [
  { label: '紧急', value: 'critical' },
  { label: '一般', value: 'warning' },
  { label: '提示', value: 'info' },
]
const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已处理', value: 'resolved' },
]

// Pagination（服务端分页）
const currentPage = ref(1)
const pageSize = ref(10)
const pageInfo = ref<{ page: number; page_size: number; total: number }>({
  page: 1,
  page_size: 10,
  total: 0,
})

// Modal
const showDetailModal = ref(false)
const showSettingsModal = ref(false)
const currentAlarm = ref<Alarm | null>(null)

// Live player
const showPlayer = ref(false)
const currentPlayUrl = ref<string | null>(null)
const livePlayingId = ref<string | null>(null)
let liveHeartbeatTimer: number | null = null

// Settings
const settings = ref({
  soundEnabled: true,
  desktopNotification: true,
  refreshInterval: 30,
  retentionDays: 30,
})
const refreshOptions = [
  { label: '10秒', value: 10 },
  { label: '30秒', value: 30 },
  { label: '1分钟', value: 60 },
  { label: '5分钟', value: 300 },
]

const alarms = ref<Alarm[]>([])

function convertApiAlarm(a: ApiAlarm): Alarm {
  const level = (a.level as any) === 'danger' ? 'warning' : (a.level as any)
  const token = userStore.token
  return {
    id: a.id,
    level: level || 'info',
    type: a.algorithm_name || a.alarm_type || '告警',
    content: a.title || a.description || '',
    device: a.camera_name || a.camera_id || '',
    time: a.alarm_time || a.created_at,
    status: (a.status as any) === 'processed' ? 'resolved' : ((a.status as any) === 'unconfirmed' ? 'pending' : 'processing'),
    selected: false,
    snapshotUrl: appendToken((a as any).snapshot_url ?? null, token),
    cameraId: a.camera_id,
    detectionData: (a as any).detection_data ?? null,
    areaName: (a as any).area_name ?? null,
  }
}

async function loadAlarms(page = currentPage.value, size = pageSize.value) {
  try {
    currentPage.value = page
    pageSize.value = size
    const res = await getAlarmList({ page, page_size: size })
    const payload = res.data as any
    const items = (payload.data || []) as ApiAlarm[]
    alarms.value = items.map(convertApiAlarm)
    const pi = (payload.page_info as any) || {}
    pageInfo.value = {
      page: pi.page ?? page,
      page_size: pi.page_size ?? size,
      total: pi.total ?? items.length,
    }
  } catch (e) {
    message.error('加载告警列表失败')
    console.error(e)
  }
}

const filteredAlarms = computed(() => {
  return alarms.value.filter((alarm) => {
    if (filters.value.level && alarm.level !== filters.value.level) return false
    if (filters.value.status && alarm.status !== filters.value.status) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const area = (alarm.areaName || '').toLowerCase()
      return alarm.content.toLowerCase().includes(q) || alarm.device.toLowerCase().includes(q) || area.includes(q)
    }
    return true
  })
})
const paginatedAlarms = computed(() => filteredAlarms.value)

const selectedCount = computed(() => alarms.value.filter((a) => a.selected).length)
const isAllSelected = computed(() => paginatedAlarms.value.length > 0 && paginatedAlarms.value.every((a) => a.selected))
const isIndeterminate = computed(() => paginatedAlarms.value.some((a) => a.selected) && !isAllSelected.value)

function handleSelectAll(checked: boolean) {
  paginatedAlarms.value.forEach((a) => (a.selected = checked))
}

async function handlePageSizeChange(size: number) {
  await loadAlarms(1, size)
}
async function handlePageChange(page: number) {
  await loadAlarms(page, pageSize.value)
}

function getLevelText(level: string) {
  const map: Record<string, string> = { critical: '紧急', warning: '一般', info: '提示' }
  return map[level] || level
}

function getTypeIcon(type: string): Component {
  const map: Record<string, Component> = {
    入侵检测: markRaw(ShieldCheckmarkOutline),
    烟火检测: markRaw(FlameOutline),
    人员跌倒: markRaw(BodyOutline),
    未戴安全帽: markRaw(PersonOutline),
    车辆违停: markRaw(CarOutline),
    设备离线: markRaw(BanOutline),
  }
  return map[type] || markRaw(AlertCircleOutline)
}

function viewAlarm(alarm: Alarm) {
  currentAlarm.value = alarm
  showDetailModal.value = true
}

async function handleLivePlay(alarm: Alarm) {
  const cameraId = alarm.cameraId
  if (!cameraId) {
    message.warning('缺少 camera_id，无法直播')
    return
  }
  try {
    if (livePlayingId.value === cameraId) {
      await stopCamera(cameraId)
      livePlayingId.value = null
      if (liveHeartbeatTimer !== null) {
        window.clearInterval(liveHeartbeatTimer)
        liveHeartbeatTimer = null
      }
      showPlayer.value = false
      message.success('已停止直播')
      return
    }

    await startCamera(cameraId)
    const res = await getCameraPlayUrls(cameraId)
    const data = (res.data as any)?.data ?? res.data
    let flvUrl = (data as any)?.flv_url || (data as any)?.http_flv
    if (!flvUrl) {
      message.error('未获取到播放地址')
      return
    }
    const token = userStore.token
    if (token) {
      flvUrl += flvUrl.includes('?') ? `&token=${encodeURIComponent(token)}` : `?token=${encodeURIComponent(token)}`
    }
    if (flvUrl.startsWith('http://127.0.0.1:8080')) {
      flvUrl = flvUrl.replace('http://127.0.0.1:8080', '/flv')
    }
    currentPlayUrl.value = flvUrl
    showPlayer.value = true
    livePlayingId.value = cameraId

    if (liveHeartbeatTimer !== null) {
      window.clearInterval(liveHeartbeatTimer)
    }
    liveHeartbeatTimer = window.setInterval(() => {
      cameraLiveHeartbeat(cameraId).catch(() => {})
    }, 60000)
  } catch (e) {
    console.error(e)
    message.error('获取播放地址失败')
  }
}

function handlePlayerClosed() {
  currentPlayUrl.value = null
  if (livePlayingId.value) {
    const id = livePlayingId.value
    stopCamera(id).catch(() => {})
    livePlayingId.value = null
  }
  if (liveHeartbeatTimer !== null) {
    window.clearInterval(liveHeartbeatTimer)
    liveHeartbeatTimer = null
  }
}

function handleAlarm(alarm: Alarm) {
  alarm.status = 'resolved'
  message.success('告警已处理')
}
function handleCurrentAlarm() {
  if (currentAlarm.value) {
    currentAlarm.value.status = 'resolved'
    message.success('告警已处理')
    showDetailModal.value = false
  }
}
function deleteAlarm(alarm: Alarm) {
  const index = alarms.value.findIndex((a) => a.id === alarm.id)
  if (index > -1) {
    alarms.value.splice(index, 1)
    message.success('告警已删除')
  }
}
function batchHandle() {
  alarms.value.filter((a) => a.selected).forEach((a) => {
    a.status = 'resolved'
    a.selected = false
  })
  message.success(`已批量处理 ${selectedCount.value} 条告警`)
}
function handleExport() {
  message.success('正在导出告警报表...')
}
function saveSettings() {
  message.success('设置已保存')
  showSettingsModal.value = false
}

onMounted(() => {
  loadAlarms(1, pageSize.value)
})
</script>

<style scoped>
.alarm-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-shrink: 0;
}

.page-header__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.page-header__subtitle {
  font-size: var(--font-size-base);
  color: var(--text-muted);
  margin: var(--spacing-xs) 0 0;
}

.page-header__actions {
  display: flex;
  gap: var(--spacing-sm);
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  background: var(--bg-card);
  padding: var(--spacing-md) var(--spacing-lg);
  flex-shrink: 0;
}

.filter-bar__left {
  display: flex;
  gap: var(--spacing-sm);
}

.list-card {
  flex: 1;
  background: var(--bg-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.list-head {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.list-head__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.list-head__title {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.list-head__meta {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.list-body {
  flex: 1;
  overflow-y: auto;
}

.alarm-row {
  display: grid;
  grid-template-columns: 40px 120px 1fr 150px;
  gap: var(--spacing-md);
  align-items: center;
  padding: 14px var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s, transform 0.2s;
}

.alarm-row:hover {
  background: var(--bg-hover);
}

.alarm-row--critical {
  border-left: 3px solid #ef4444;
}
.alarm-row--warning {
  border-left: 3px solid #f59e0b;
}
.alarm-row--info {
  border-left: 3px solid #3b82f6;
}

.alarm-row__thumb {
  position: relative;
  width: 120px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.06);
}

.alarm-thumb--clickable {
  cursor: pointer;
}

.alarm-thumb--clickable:hover {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.alarm-row__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.alarm-thumb__placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 12px;
}

.level-pill {
  position: absolute;
  left: 8px;
  top: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  backdrop-filter: blur(6px);
  background: rgba(255, 255, 255, 0.85);
}

.level-pill--critical {
  color: #ef4444;
}
.level-pill--warning {
  color: #f59e0b;
}
.level-pill--info {
  color: #3b82f6;
}

.alarm-row__main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alarm-row__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.alarm-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.alarm-type {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.type-icon {
  color: var(--text-muted);
}

.alarm-row__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  max-width: 100%;
}

.meta-label {
  font-size: 12px;
  color: var(--text-muted);
}

.meta-value {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 360px;
}

.meta-chip--time .meta-value {
  max-width: 200px;
}

.alarm-row__actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.pagination__info {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

@media (max-width: 1200px) {
  .alarm-row {
    grid-template-columns: 40px 120px 1fr;
  }
  .alarm-row__actions {
    justify-content: flex-start;
  }
}
</style>

