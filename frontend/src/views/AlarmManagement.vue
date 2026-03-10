<template>
  <div class="alarm-management">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">告警事件中心</h1>
        <p class="page-header__subtitle">实时监控、处理和分析全平台告警事件</p>
      </div>
      <div class="page-header__actions">
        <n-button @click="handleExport">
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          导出报表
        </n-button>
        <n-button type="primary" @click="showSettingsModal = true">
          <template #icon>
            <n-icon><SettingsOutline /></n-icon>
          </template>
          告警设置
        </n-button>
      </div>
    </div>

    <!-- Main Tabs -->
    <n-tabs v-model:value="activeTab" type="line" class="alarm-tabs">
      <n-tab-pane name="list" tab="告警列表">
        <!-- Filters & Search -->
        <div class="filter-bar">
          <div class="filter-bar__left">
            <n-select
              v-model:value="filters.level"
              :options="levelOptions"
              placeholder="告警级别"
              clearable
              style="width: 140px"
            />
            <n-select
              v-model:value="filters.type"
              :options="typeOptions"
              placeholder="告警类型"
              clearable
              style="width: 160px"
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
              placeholder="搜索告警内容、设备名称或区域..."
              clearable
              style="width: 280px"
            >
              <template #prefix>
                <n-icon><SearchOutline /></n-icon>
              </template>
            </n-input>
          </div>
        </div>

        <!-- Alarm List -->
        <div class="alarm-list">
          <div class="alarm-list__header">
            <n-checkbox 
              :checked="isAllSelected" 
              :indeterminate="isIndeterminate"
              @update:checked="handleSelectAll"
            />
            <span class="alarm-list__col alarm-list__col--level">级别</span>
            <span class="alarm-list__col alarm-list__col--thumb">截图</span>
            <span class="alarm-list__col alarm-list__col--type">类型</span>
            <span class="alarm-list__col alarm-list__col--content">告警内容</span>
            <span class="alarm-list__col alarm-list__col--device">关联设备 / 区域</span>
            <span class="alarm-list__col alarm-list__col--time">告警时间</span>
            <span class="alarm-list__col alarm-list__col--status">状态</span>
            <span class="alarm-list__col alarm-list__col--action">操作</span>
          </div>
          <div class="alarm-list__body">
            <div 
              v-for="alarm in paginatedAlarms" 
              :key="alarm.id" 
              class="alarm-item"
              :class="`alarm-item--${alarm.level}`"
            >
              <n-checkbox v-model:checked="alarm.selected" />
              <div class="alarm-list__col alarm-list__col--level">
                <span class="level-badge" :class="`level-badge--${alarm.level}`">
                  {{ getLevelText(alarm.level) }}
                </span>
              </div>
              <div class="alarm-list__col alarm-list__col--thumb">
                <div
                  class="alarm-thumb alarm-thumb--clickable"
                  role="button"
                  tabindex="0"
                  @click="viewAlarm(alarm)"
                  @keydown.enter="viewAlarm(alarm)"
                >
                  <img v-if="alarm.snapshotUrl" :src="alarm.snapshotUrl" alt="告警截图" />
                  <div v-else class="alarm-thumb__placeholder">—</div>
                </div>
              </div>
              <div class="alarm-list__col alarm-list__col--type">
                <n-icon :size="16" class="type-icon"><component :is="getTypeIcon(alarm.type)" /></n-icon>
                {{ alarm.type }}
              </div>
              <div class="alarm-list__col alarm-list__col--content">
                <span class="alarm-content">{{ alarm.content }}</span>
              </div>
              <div class="alarm-list__col alarm-list__col--device">
                <div class="device-info">
                  <div class="device-name">{{ alarm.device }}</div>
                  <div class="device-area" v-if="alarm.areaName">
                    {{ alarm.areaName }}
                  </div>
                  <div class="device-area device-area--empty" v-else>
                    未关联区域
                  </div>
                </div>
              </div>
              <div class="alarm-list__col alarm-list__col--time">
                {{ alarm.time }}
              </div>
              <div class="alarm-list__col alarm-list__col--status">
                <span class="status-tag" :class="`status-tag--${alarm.status}`">
                  {{ getStatusText(alarm.status) }}
                </span>
              </div>
              <div class="alarm-list__col alarm-list__col--action">
                <n-button text type="primary" size="small" @click="viewAlarm(alarm)">
                  <template #icon><n-icon><EyeOutline /></n-icon></template>
                </n-button>
                <n-button
                  text
                  type="primary"
                  size="small"
                  @click="handleLivePlay(alarm)"
                >
                  视频直播
                </n-button>
                <n-button 
                  v-if="alarm.status === 'pending'" 
                  text type="success" size="small" 
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

        <!-- Pagination -->
        <div class="pagination">
          <div class="pagination__info">
            已选择 {{ selectedCount }} 项
            <n-button v-if="selectedCount > 0" text type="primary" size="small" @click="batchHandle">
              批量处理
            </n-button>
          </div>
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
      </n-tab-pane>

      <n-tab-pane name="stats" tab="告警统计">
        <div class="stats-page">
          <!-- Overview Cards -->
          <div class="stats-grid">
            <div class="stat-card stat-card--danger">
              <div class="stat-card__icon">
                <n-icon :size="24"><AlertCircleOutline /></n-icon>
              </div>
              <div class="stat-card__content">
                <span class="stat-card__value">{{ stats.critical }}</span>
                <span class="stat-card__label">紧急告警</span>
              </div>
            </div>
            <div class="stat-card stat-card--warning">
              <div class="stat-card__icon">
                <n-icon :size="24"><WarningOutline /></n-icon>
              </div>
              <div class="stat-card__content">
                <span class="stat-card__value">{{ stats.warning }}</span>
                <span class="stat-card__label">一般告警</span>
              </div>
            </div>
            <div class="stat-card stat-card--info">
              <div class="stat-card__icon">
                <n-icon :size="24"><InformationCircleOutline /></n-icon>
              </div>
              <div class="stat-card__content">
                <span class="stat-card__value">{{ stats.info }}</span>
                <span class="stat-card__label">提示信息</span>
              </div>
            </div>
            <div class="stat-card stat-card--success">
              <div class="stat-card__icon">
                <n-icon :size="24"><CheckmarkCircleOutline /></n-icon>
              </div>
              <div class="stat-card__content">
                <span class="stat-card__value">{{ stats.resolved }}</span>
                <span class="stat-card__label">已处理</span>
              </div>
            </div>
          </div>

          <!-- Detail Sections -->
          <div class="stats-layout">
            <div class="stats-left">
              <div class="stats-section-card">
                <div class="stats-section-header">
                  <span class="stats-section-title">近 {{ statsDays }} 天趋势</span>
                  <span class="stats-section-subtitle">日告警数量变化</span>
                </div>
                <div class="trend-list" v-if="alarmStats && alarmStats.trend.length">
                  <div
                    v-for="item in alarmStats.trend"
                    :key="item.date"
                    class="trend-item"
                  >
                    <span class="trend-date">{{ item.date }}</span>
                    <div class="trend-bar-wrap">
                      <div
                        class="trend-bar"
                        :style="{ width: trendMaxCount ? `${Math.max(6, (item.count / trendMaxCount) * 100)}%` : '0%' }"
                      ></div>
                    </div>
                    <span class="trend-count">{{ item.count }}</span>
                  </div>
                </div>
                <div v-else class="stats-empty">暂无统计数据</div>
              </div>
            </div>

            <div class="stats-right">
              <div class="stats-section-card">
                <div class="stats-section-header">
                  <span class="stats-section-title">高频告警摄像头 TOP10</span>
                  <span class="stats-section-subtitle">按告警次数排序</span>
                </div>
                <div class="stats-list" v-if="alarmStats && alarmStats.by_camera.length">
                  <div
                    v-for="(item, index) in alarmStats.by_camera"
                    :key="item.label"
                    class="stats-list-item"
                  >
                    <span class="stats-rank">#{{ index + 1 }}</span>
                    <div class="stats-list-main">
                      <div class="stats-list-label">{{ item.label }}</div>
                      <div class="stats-list-bar-wrap">
                        <div
                          class="stats-list-bar"
                          :style="{ width: cameraMaxCount ? `${Math.max(8, (item.value / cameraMaxCount) * 100)}%` : '0%' }"
                        ></div>
                      </div>
                    </div>
                    <span class="stats-list-value">{{ item.value }}</span>
                  </div>
                </div>
                <div v-else class="stats-empty">暂无摄像头统计</div>
              </div>

              <div class="stats-section-card">
                <div class="stats-section-header">
                  <span class="stats-section-title">高频告警算法 TOP10</span>
                  <span class="stats-section-subtitle">按告警次数排序</span>
                </div>
                <div class="stats-list" v-if="alarmStats && alarmStats.by_algorithm.length">
                  <div
                    v-for="(item, index) in alarmStats.by_algorithm"
                    :key="item.label"
                    class="stats-list-item"
                  >
                    <span class="stats-rank">#{{ index + 1 }}</span>
                    <div class="stats-list-main">
                      <div class="stats-list-label">{{ item.label }}</div>
                      <div class="stats-list-bar-wrap">
                        <div
                          class="stats-list-bar stats-list-bar--secondary"
                          :style="{ width: algorithmMaxCount ? `${Math.max(8, (item.value / algorithmMaxCount) * 100)}%` : '0%' }"
                        ></div>
                      </div>
                    </div>
                    <span class="stats-list-value">{{ item.value }}</span>
                  </div>
                </div>
                <div v-else class="stats-empty">暂无算法统计</div>
              </div>
            </div>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>

    <!-- Alarm Detail Modal -->
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

    <!-- Live Player Modal -->
    <n-modal
      v-model:show="showPlayer"
      preset="card"
      title="实时预览"
      :style="{ width: '960px' }"
      @after-leave="handlePlayerClosed"
    >
      <div style="width: 100%; aspect-ratio: 16 / 9;">
        <FlvPlayer
          v-if="currentPlayUrl"
          :url="currentPlayUrl"
        />
      </div>
    </n-modal>

    <!-- 图片查看（缩放/平移）由 AlarmDetail 内部实现 -->

    <!-- Settings Modal -->
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
          <n-select 
            v-model:value="settings.refreshInterval" 
            :options="refreshOptions"
            style="width: 200px"
          />
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
import { ref, computed, markRaw, onMounted } from 'vue'
import type { Component } from 'vue'
import { 
  NButton, NIcon, NSelect, NDatePicker, NInput, NCheckbox,
  NPagination, NModal, NForm, NFormItem, NSwitch, NInputNumber,
  NTabs, NTabPane,
  useMessage 
} from 'naive-ui'
import { 
  DownloadOutline, SettingsOutline, AlertCircleOutline, WarningOutline,
  InformationCircleOutline, CheckmarkCircleOutline, TrendingUpOutline,
  TrendingDownOutline, SearchOutline, EyeOutline, CheckmarkOutline,
  TrashOutline, ShieldCheckmarkOutline, FlameOutline, BodyOutline,
  PersonOutline, CarOutline, BanOutline
} from '@vicons/ionicons5'
import { getAlarmList, getAlarmStatistics, type Alarm as ApiAlarm, type AlarmStatistics } from '@/api/alarm'
import FlvPlayer from '@/components/FlvPlayer.vue'
import { getCameraPlayUrls, startCamera, stopCamera, cameraLiveHeartbeat } from '@/api/camera'
import { useUserStore } from '@/stores/user'
import AlarmDetail from '@/components/AlarmDetail.vue'
import { appendToken } from '@/utils/auth_url'

interface Alarm {
  id: string
  level: 'critical' | 'warning' | 'info'
  type: string
  content: string
  device: string
  time: string
  status: 'pending' | 'processing' | 'resolved'
  selected?: boolean
  location?: string
  snapshotUrl?: string | null
  cameraId?: string
  detectionData?: any | null
  areaName?: string | null
}

const message = useMessage()
const userStore = useUserStore()

// Tabs
const activeTab = ref<'list' | 'stats'>('list')

// Stats（从后端统计接口加载）
const stats = ref({
  critical: 0,
  warning: 0,
  info: 0,
  resolved: 0
})

const statsDays = 7
const alarmStats = ref<AlarmStatistics | null>(null)

// Filters
const filters = ref({
  level: null as string | null,
  type: null as string | null,
  status: null as string | null,
  dateRange: null as [number, number] | null
})
const searchQuery = ref('')

const levelOptions = [
  { label: '紧急', value: 'critical' },
  { label: '一般', value: 'warning' },
  { label: '提示', value: 'info' }
]

const typeOptions = [
  { label: '入侵检测', value: '入侵检测' },
  { label: '烟火检测', value: '烟火检测' },
  { label: '人员跌倒', value: '人员跌倒' },
  { label: '未戴安全帽', value: '未戴安全帽' },
  { label: '车辆违停', value: '车辆违停' },
  { label: '设备离线', value: '设备离线' }
]

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已处理', value: 'resolved' }
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

// Live player modal (reuse camera management approach)
const showPlayer = ref(false)
const currentPlayUrl = ref<string | null>(null)

// 图片预览统一由 AlarmDetail 内部的 ImageViewer 提供，此页不再单独维护 ImageViewer 状态
const livePlayingId = ref<string | null>(null)
let liveHeartbeatTimer: number | null = null

// Settings
const settings = ref({
  soundEnabled: true,
  desktopNotification: true,
  refreshInterval: 30,
  retentionDays: 30
})

const refreshOptions = [
  { label: '10秒', value: 10 },
  { label: '30秒', value: 30 },
  { label: '1分钟', value: 60 },
  { label: '5分钟', value: 300 }
]

// Alarm data（从后端接口加载，已分页）
const alarms = ref<Alarm[]>([])

const trendMaxCount = computed(() => {
  if (!alarmStats.value || !alarmStats.value.trend.length) return 0
  return Math.max(...alarmStats.value.trend.map(t => t.count))
})

const cameraMaxCount = computed(() => {
  if (!alarmStats.value || !alarmStats.value.by_camera.length) return 0
  return Math.max(...alarmStats.value.by_camera.map(c => c.value))
})

const algorithmMaxCount = computed(() => {
  if (!alarmStats.value || !alarmStats.value.by_algorithm.length) return 0
  return Math.max(...alarmStats.value.by_algorithm.map(a => a.value))
})

// 将接口 Alarm 转换为本页使用的 Alarm 结构
function convertApiAlarm(a: ApiAlarm): Alarm {
  // level 映射：后端 level 字段为 'info' | 'warning' | 'danger' | 'critical'
  const level = (a.level as any) === 'danger' ? 'warning' : (a.level as any)
  const token = userStore.token
  return {
    id: a.id,
    level: level || 'info',
    type: a.algorithm_name || a.alarm_type || '告警',
    content: a.title || a.description || '',
    device: a.camera_name || a.camera_id || '',
    time: a.alarm_time || a.created_at,
    // 状态映射：后端 status 字段（如 unconfirmed/confirmed/ignored/processed）
    status: (a.status as any) === 'processed'
      ? 'resolved'
      : ((a.status as any) === 'unconfirmed' ? 'pending' : 'processing'),
    selected: false,
    location: undefined,
    snapshotUrl: appendToken((a as any).snapshot_url ?? (a as any).snapshotUrl ?? null, token),
    cameraId: a.camera_id,
    detectionData: (a as any).detection_data ?? null,
    areaName: (a as any).area_name ?? null,
  }
}

// 从后端加载告警列表（服务端分页）
async function loadAlarms(page = currentPage.value, size = pageSize.value) {
  try {
    currentPage.value = page
    pageSize.value = size
    // 后端 page_size 最大 100
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

// 从后端加载告警统计（顶部四个卡片）
async function loadAlarmStats() {
  try {
    const res = await getAlarmStatistics({ days: 7 })
    const s: AlarmStatistics = (res.data as any).data || (res.data as any)
    alarmStats.value = s
    const byLevel = s.by_level || []
    const getCount = (lvl: string) => byLevel.find(i => i.label === lvl)?.value ?? 0
    stats.value = {
      critical: getCount('critical'),
      warning: getCount('warning'),
      info: getCount('info'),
      resolved: s.processed ?? 0,
    }
  } catch (e) {
    console.error(e)
  }
}

// 过滤仅作用于当前页（如需全量过滤可改为后端查询）
const filteredAlarms = computed(() => {
  return alarms.value.filter(alarm => {
    if (filters.value.level && alarm.level !== filters.value.level) return false
    if (filters.value.type && alarm.type !== filters.value.type) return false
    if (filters.value.status && alarm.status !== filters.value.status) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const area = (alarm.areaName || '').toLowerCase()
      return (
        alarm.content.toLowerCase().includes(q) ||
        alarm.device.toLowerCase().includes(q) ||
        area.includes(q)
      )
    }
    return true
  })
})

// 当前页数据直接来自服务端 + 本地过滤，不再二次切片
const paginatedAlarms = computed(() => filteredAlarms.value)

const selectedCount = computed(() => alarms.value.filter(a => a.selected).length)
const isAllSelected = computed(() => paginatedAlarms.value.length > 0 && paginatedAlarms.value.every(a => a.selected))
const isIndeterminate = computed(() => paginatedAlarms.value.some(a => a.selected) && !isAllSelected.value)

function getLevelText(level: string) {
  const map: Record<string, string> = { critical: '紧急', warning: '一般', info: '提示' }
  return map[level] || level
}

function getStatusText(status: string) {
  const map: Record<string, string> = { pending: '待处理', processing: '处理中', resolved: '已处理' }
  return map[status] || status
}

function getTypeIcon(type: string): Component {
  const map: Record<string, Component> = {
    '入侵检测': markRaw(ShieldCheckmarkOutline),
    '烟火检测': markRaw(FlameOutline),
    '人员跌倒': markRaw(BodyOutline),
    '未戴安全帽': markRaw(PersonOutline),
    '车辆违停': markRaw(CarOutline),
    '设备离线': markRaw(BanOutline)
  }
  return map[type] || markRaw(AlertCircleOutline)
}

function handleSelectAll(checked: boolean) {
  paginatedAlarms.value.forEach(a => a.selected = checked)
}

async function handlePageSizeChange(size: number) {
  await loadAlarms(1, size)
}

async function handlePageChange(page: number) {
  await loadAlarms(page, pageSize.value)
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
    // 若正在播放同一路摄像头，则点击视为停止
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
    // 开发环境通过 Vite 代理避免跨域，将后端完整地址替换为 /flv 前缀
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
  const index = alarms.value.findIndex(a => a.id === alarm.id)
  if (index > -1) {
    alarms.value.splice(index, 1)
    message.success('告警已删除')
  }
}

function batchHandle() {
  alarms.value.filter(a => a.selected).forEach(a => {
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

// 初始化加载
onMounted(() => {
  loadAlarms(1, pageSize.value)
  loadAlarmStats()
})
</script>

<style scoped>
.alarm-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  overflow: hidden;
}

/* Page Header */
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

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.stat-card--danger::before { background: #ef4444; }
.stat-card--warning::before { background: #f59e0b; }
.stat-card--info::before { background: #3b82f6; }
.stat-card--success::before { background: #22c55e; }

.stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card--danger .stat-card__icon { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.stat-card--warning .stat-card__icon { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.stat-card--info .stat-card__icon { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.stat-card--success .stat-card__icon { background: rgba(34, 197, 94, 0.1); color: #22c55e; }

.stat-card__content {
  flex: 1;
}

.stat-card__value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  display: block;
}

.stat-card__label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.stat-card__trend {
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-card__trend.up { color: #22c55e; }
.stat-card__trend.down { color: #ef4444; }

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.filter-bar__left {
  display: flex;
  gap: var(--spacing-sm);
}

/* Alarm List */
.alarm-list {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.alarm-list__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
  flex-shrink: 0;
}

.alarm-list__body {
  flex: 1;
  overflow-y: auto;
}

.alarm-list__col { display: flex; align-items: center; }
.alarm-list__col--level { width: 80px; }
.alarm-list__col--type { width: 120px; gap: var(--spacing-xs); }
.alarm-list__col--content { flex: 1; min-width: 0; }
.alarm-list__col--device { width: 220px; }
.alarm-list__col--time { width: 160px; color: var(--text-muted); font-size: var(--font-size-sm); }
.alarm-list__col--status { width: 90px; }
.alarm-list__col--action { width: 100px; justify-content: flex-end; gap: var(--spacing-xs); }

.alarm-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.alarm-item:hover { background: var(--bg-hover); }
.alarm-item:last-child { border-bottom: none; }

.alarm-item--critical { border-left: 3px solid #ef4444; }
.alarm-item--warning { border-left: 3px solid #f59e0b; }
.alarm-item--info { border-left: 3px solid #3b82f6; }

.level-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.level-badge--critical { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.level-badge--warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.level-badge--info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.level-badge.large { padding: 4px 12px; font-size: var(--font-size-sm); }

.type-icon { color: var(--text-muted); }
.alarm-content { 
  overflow: hidden; 
  text-overflow: ellipsis; 
  white-space: nowrap;
  font-size: var(--font-size-sm);
}
.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.device-name {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-semibold);
}
.device-area {
  font-size: 12px;
  color: var(--text-muted);
}
.device-area--empty {
  font-style: italic;
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}

.status-tag--pending { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.status-tag--processing { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.status-tag--resolved { background: rgba(34, 197, 94, 0.1); color: #22c55e; }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.pagination__info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

/* Tabs */
.alarm-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.alarm-tabs :deep(.n-tabs-nav-scroll-content) {
  font-weight: var(--font-weight-medium);
}

/* Stats Page layout */
.stats-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.stats-layout {
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: var(--spacing-lg);
}

.stats-section-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.stats-section-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.stats-section-subtitle {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.stats-empty {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

/* Trend list */
.trend-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.trend-item {
  display: grid;
  grid-template-columns: 96px 1fr 48px;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
}

.trend-date {
  color: var(--text-secondary);
}

.trend-bar-wrap {
  height: 6px;
  border-radius: 999px;
  background: var(--bg-page);
  overflow: hidden;
}

.trend-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #3b82f6, #22c55e);
}

.trend-count {
  text-align: right;
  color: var(--text-primary);
}

/* Stats list */
.stats-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.stats-list-item {
  display: grid;
  grid-template-columns: 36px 1fr 40px;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
}

.stats-rank {
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
}

.stats-list-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-list-label {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.stats-list-bar-wrap {
  height: 6px;
  border-radius: 999px;
  background: var(--bg-page);
  overflow: hidden;
}

.stats-list-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f97316, #ef4444);
}

.stats-list-bar--secondary {
  background: linear-gradient(90deg, #6366f1, #0ea5e9);
}

.stats-list-value {
  text-align: right;
  color: var(--text-primary);
}

/* Modal Detail */
.alarm-detail { display: flex; flex-direction: column; gap: var(--spacing-lg); }
.detail-header { display: flex; align-items: center; gap: var(--spacing-md); }
.detail-type { font-weight: var(--font-weight-semibold); color: var(--text-primary); }
.detail-time { color: var(--text-muted); font-size: var(--font-size-sm); margin-left: auto; }
.detail-content h4, .detail-snapshot h4 { margin: 0 0 var(--spacing-sm); font-size: var(--font-size-base); color: var(--text-primary); }
.detail-content p { margin: 0; color: var(--text-secondary); line-height: 1.6; }
.detail-info { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-md); padding: var(--spacing-md); background: var(--bg-page); border-radius: var(--radius-lg); }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: var(--font-size-xs); color: var(--text-muted); }
.info-value { font-size: var(--font-size-sm); color: var(--text-primary); }
.snapshot-grid img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius-lg);
  object-fit: contain;
}
.alarm-detail__img--clickable {
  cursor: zoom-in;
}
.alarm-detail__img--clickable:hover {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Alarm list thumbnail */
.alarm-list__col--thumb { width: 96px; flex: 0 0 96px; }
.alarm-thumb {
  width: 84px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
}
.alarm-thumb--clickable {
  cursor: pointer;
}
.alarm-thumb--clickable:hover {
  opacity: 0.9;
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
.alarm-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.alarm-thumb__placeholder {
  color: var(--text-muted);
  font-size: 12px;
}

.modal-footer { display: flex; justify-content: flex-end; gap: var(--spacing-sm); }

/* Scrollbar */
.alarm-list__body::-webkit-scrollbar { width: 6px; }
.alarm-list__body::-webkit-scrollbar-track { background: transparent; }
.alarm-list__body::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }

@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
