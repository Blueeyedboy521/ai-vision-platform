<template>
  <div class="alarm-page">
    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">致命告警</span>
          <div class="stat-card__icon stat-card__icon--critical">
            <n-icon><CloseCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.critical }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">严重告警</span>
          <div class="stat-card__icon stat-card__icon--danger">
            <n-icon><AlertCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.danger }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">一般告警</span>
          <div class="stat-card__icon stat-card__icon--warning">
            <n-icon><WarningOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.warning }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">提示信息</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><InformationCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.info }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">告警等级</span>
          <n-select
            v-model:value="filters.level"
            :options="levelOptions"
            placeholder="全部等级"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group">
          <span class="filter-label">告警类型</span>
          <n-select
            v-model:value="filters.type"
            :options="typeOptions"
            placeholder="全部类型"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group">
          <span class="filter-label">区域选择</span>
          <n-tree-select
            v-model:value="filters.area"
            :options="areaTreeData"
            placeholder="全厂区"
            clearable
            size="small"
            class="filter-select"
            :filterable="true"
            :checkable="false"
            :multiple="false"
            check-strategy="child"
            to="body"
          />
        </div>
        <div class="filter-group filter-group--date">
          <span class="filter-label">时间范围</span>
          <n-date-picker
            v-model:value="filters.dateRange"
            type="daterange"
            clearable
            size="small"
            class="filter-date"
          />
        </div>
        <div class="filter-actions">
          <n-button type="primary" size="small" class="filter-btn" @click="handleSearch">
            <template #icon>
              <n-icon><SearchOutline /></n-icon>
            </template>
            查询
          </n-button>
          <n-button size="small" class="filter-btn" @click="handleReset">
            重置
          </n-button>
        </div>
      </div>
    </div>

    <!-- 列表卡片 -->
    <div class="list-card card card-border-xl">
      <!-- 表头 -->
      <div class="list-header">
        <div class="list-header__col list-header__col--checkbox">
          <n-checkbox
            :checked="isAllSelected"
            :indeterminate="isIndeterminate"
            @update:checked="handleSelectAll"
          />
        </div>
        <div class="list-header__col list-header__col--thumb">告警快照</div>
        <div class="list-header__col list-header__col--device">设备名称</div>
        <div class="list-header__col list-header__col--type">告警类型</div>
        <div class="list-header__col list-header__col--area">所在区域</div>
        <div class="list-header__col list-header__col--level">等级</div>
        <div class="list-header__col list-header__col--time">告警时间</div>
        <div class="list-header__col list-header__col--status">状态</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div v-if="loading" class="loading-state">
          <n-spin>
            <div class="loading-text">加载中...</div>
          </n-spin>
        </div>
        <div v-else>
          <div
            v-for="alarm in paginatedAlarms"
            :key="alarm.id"
            class="list-row"
            :class="`list-row--${alarm.level}`"
          >
            <div class="list-row__col list-row__col--checkbox">
              <n-checkbox v-model:checked="alarm.selected" />
            </div>
            <div class="list-row__col list-row__col--thumb">
              <div
                class="alarm-thumb"
                role="button"
                tabindex="0"
                @click="viewAlarm(alarm)"
                @keydown.enter="viewAlarm(alarm)"
              >
                <img v-if="alarm.snapshotUrl" :src="alarm.snapshotUrl" alt="告警截图" />
                <div v-else class="alarm-thumb__placeholder">
                  <n-icon><ImageOutline /></n-icon>
                </div>
              </div>
            </div>
            <div class="list-row__col list-row__col--device">
              <span class="device-name">{{ alarm.device }}</span>
            </div>
            <div class="list-row__col list-row__col--type">
              <span class="type-text">{{ alarm.type }}</span>
            </div>
            <div class="list-row__col list-row__col--area">
              <span class="area-text">{{ alarm.areaName || '-' }}</span>
            </div>
            <div class="list-row__col list-row__col--level">
              <span class="level-tag" :class="`level-tag--${alarm.level}`">
                {{ getLevelText(alarm.level) }}
              </span>
            </div>
            <div class="list-row__col list-row__col--time">
              <span class="time-text">{{ formatTime(alarm.time) }}</span>
            </div>
            <div class="list-row__col list-row__col--status">
              <span class="status-tag" :class="`status-tag--${alarm.status}`">
                {{ getStatusText(alarm.status) }}
              </span>
            </div>
            <div class="list-row__col list-row__col--action">
              <n-button text type="primary" size="small" @click="viewAlarm(alarm)">详情</n-button>
              <n-button text type="primary" size="small" @click="handleAlarm(alarm)">处理</n-button>
            </div>
          </div>
          <div v-if="paginatedAlarms.length === 0" class="empty-state">
            <n-empty description="暂无告警数据" />
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 {{ (currentPage - 1) * pageSize + 1 }} 到 {{ Math.min(currentPage * pageSize, pageInfo.total) }} 条，共 {{ pageInfo.total }} 条记录
        </div>
        <n-pagination
          v-model:page="currentPage"
          :page-size="pageSize"
          :item-count="pageInfo.total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          size="small"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  NButton,
  NCheckbox,
  NDatePicker,
  NEmpty,
  NIcon,
  NModal,
  NPagination,
  NSelect,
  NSpin,
  NTreeSelect,
  useMessage,
} from 'naive-ui'
import {
  AlertCircleOutline,
  CloseCircleOutline,
  InformationCircleOutline,
  SearchOutline,
  WarningOutline,
  ImageOutline,
} from '@vicons/ionicons5'
import { getAlarmList, type Alarm as ApiAlarm } from '@/api/alarm'
import { getAlgorithmList } from '@/api/algorithm'
import { getAreaList } from '@/api/area'
import AlarmDetail from '@/components/AlarmDetail.vue'
import { useUserStore } from '@/stores/user'
import { appendToken } from '@/utils/auth_url'

interface AreaNode {
  key: string
  label: string
  children?: AreaNode[]
  isLeaf?: boolean
}

interface Alarm {
  id: string
  level: 'critical' | 'danger' | 'warning' | 'info'
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

// 统计数据
const stats = ref({
  critical: 12,
  danger: 45,
  warning: 128,
  info: 342,
})

// 加载状态
const loading = ref(false)

// 筛选条件
const filters = ref({
  level: null as string | null,
  type: null as string | null,
  area: null as string | null,
  dateRange: null as [number, number] | null,
})

const levelOptions = [
  { label: '致命告警', value: 'critical' },
  { label: '严重告警', value: 'danger' },
  { label: '一般告警', value: 'warning' },
  { label: '提示信息', value: 'info' },
]

// 类型和区域数据
const typeOptions = ref<any[]>([])
const areaTreeData = ref<AreaNode[]>([])


// 加载算法类型数据
const loadAlgorithmTypes = async () => {
  try {
    const res = await getAlgorithmList()
    const data = res.data?.data
    if (data && Array.isArray(data)) {
      typeOptions.value = data.map((algo: any) => ({
        label: algo.name,
        value: algo.id
      }))
    }
  } catch (error) {
    console.error('加载算法类型失败:', error)
  }
}

// 加载区域数据
const loadAreas = async () => {
  try {
    const res = await getAreaList()
    if (res.data && res.data.data) {
      // 构建区域树结构
      const buildAreaTree = (areas: any[], parentId: string | null = null): AreaNode[] => {
        const isRoot = (pid: any) => pid === null || pid === undefined || pid === '' || pid === '0'
        return areas
          .filter(area => {
            if (parentId === null) return isRoot(area.parent_id)
            return area.parent_id === parentId
          })
          .map(area => {
            const children = buildAreaTree(areas, area.id)
            return {
              key: area.id,
              label: area.name,
              isLeaf: children.length === 0,
              children: children.length > 0 ? children : undefined
            }
          })
      }
      areaTreeData.value = buildAreaTree(res.data.data)
    }
  } catch (error) {
    console.error('加载区域数据失败:', error)
  }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const pageInfo = ref<{ page: number; page_size: number; total: number }>({
  page: 1,
  page_size: 10,
  total: 0,
})

// 弹窗
const showDetailModal = ref(false)
const currentAlarm = ref<Alarm | null>(null)

const alarms = ref<Alarm[]>([])

function convertApiAlarm(a: ApiAlarm): Alarm {
  const levelMap: Record<string, string> = {
    critical: 'critical',
    danger: 'danger',
    warning: 'warning',
    info: 'info',
  }
  const level = levelMap[a.level] || 'info'
  const token = userStore.token
  return {
    id: a.id,
    level: level as any,
    type: a.algorithm_name || a.alarm_type || '告警',
    content: a.title || a.description || '',
    device: a.camera_name || a.camera_id || '',
    time: a.alarm_time || a.created_at,
    status: a.status === 'processed' ? 'resolved' : a.status === 'unconfirmed' ? 'pending' : 'processing',
    selected: false,
    snapshotUrl: appendToken((a as any).snapshot_url ?? null, token),
    cameraId: a.camera_id,
    detectionData: (a as any).detection_data ?? null,
    areaName: (a as any).area_name ?? null,
  }
}

async function loadAlarms(page = currentPage.value, size = pageSize.value) {
  loading.value = true
  try {
    currentPage.value = page
    pageSize.value = size
    
    // 构建查询参数
    const params: any = { page, page_size: size }
    
    if (filters.value.level) {
      params.level = filters.value.level
    }
    
    if (filters.value.type) {
      params.algorithm_id = filters.value.type
    }
    
    if (filters.value.area) {
      params.area_id = filters.value.area
    }
    
    if (filters.value.dateRange) {
      params.start_time = new Date(filters.value.dateRange[0]).toISOString()
      params.end_time = new Date(filters.value.dateRange[1]).toISOString()
    }
    
    const res = await getAlarmList(params)
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
  } finally {
    loading.value = false
  }
}

const paginatedAlarms = computed(() => alarms.value)

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
  const map: Record<string, string> = {
    critical: '致命告警',
    danger: '严重告警',
    warning: '一般告警',
    info: '提示信息',
  }
  return map[level] || level
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决',
  }
  return map[status] || status
}

function formatTime(time: string) {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function viewAlarm(alarm: Alarm) {
  currentAlarm.value = alarm
  showDetailModal.value = true
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

function handleSearch() {
  loadAlarms(1)
}

function handleReset() {
  filters.value = {
    level: null,
    type: null,
    area: null,
    dateRange: null,
  }
  loadAlarms(1)
}

onMounted(async () => {
  // 加载算法类型和区域数据
  await Promise.all([
    loadAlgorithmTypes(),
    loadAreas()
  ])
  // 加载告警列表
  loadAlarms(1, pageSize.value)
})
</script>

<style scoped>
.alarm-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  overflow: hidden;
  background: var(--bg-page);
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.stat-card {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
}

.stat-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.stat-card__label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.stat-card__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-card__icon--critical {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.stat-card__icon--danger {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.stat-card__icon--warning {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.stat-card__icon--info {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-card__value {
  font-size: 32px;
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

/* 筛选栏 */
.filter-section {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: nowrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.filter-group--date {
  flex: 0 0 auto;
}

.filter-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-select {
  width: 120px;
}

.filter-date {
  width: 220px;
}

.filter-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-left: auto;
  flex-shrink: 0;
}

.filter-btn {
  min-width: 70px;
}

/* 列表卡片 */
.list-card {
  flex: 1;
  background: var(--bg-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 0;
}

/* 表头 */
.list-header {
  display: grid;
  grid-template-columns: 40px 100px 1.5fr 1fr 1fr 100px 140px 100px 100px;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.list-header__col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-header__col--checkbox {
  display: flex;
  justify-content: center;
}

.list-header__col--action {
  text-align: center;
}

/* 列表内容 */
.list-body {
  flex: 1;
  overflow-y: auto;
}

.list-row {
  display: grid;
  grid-template-columns: 40px 100px 1.5fr 1fr 1fr 100px 140px 100px 100px;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.list-row:hover {
  background: var(--bg-hover);
}

.list-row--critical {
  background: rgba(239, 68, 68, 0.02);
}

.list-row--danger {
  background: rgba(249, 115, 22, 0.02);
}

.list-row__col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-row__col--checkbox {
  display: flex;
  justify-content: center;
}

.list-row__col--action {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

/* 告警缩略图 */
.alarm-thumb {
  width: 80px;
  height: 48px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-page);
  cursor: pointer;
  position: relative;
}

.alarm-thumb:hover {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.alarm-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.alarm-thumb__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 20px;
}

/* 设备名称 */
.device-name {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

/* 类型和区域 */
.type-text,
.area-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* 等级标签 */
.level-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.level-tag--critical {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.level-tag--danger {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.level-tag--warning {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.level-tag--info {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

/* 时间 */
.time-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-family: monospace;
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-tag--pending {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-tag--processing {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.status-tag--resolved {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

/* 分页 */
.list-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  background: var(--bg-page);
  flex-shrink: 0;
}

.list-footer__info {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

@media (max-width: 1400px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1200px) {
  .list-header,
  .list-row {
    grid-template-columns: 40px 80px 1.5fr 1fr 100px 120px 100px 80px;
  }

  .list-header__col--area,
  .list-row__col--area {
    display: none;
  }
}

@media (max-width: 992px) {
  .filter-row {
    flex-wrap: wrap;
  }

  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .list-header,
  .list-row {
    grid-template-columns: 40px 80px 1.5fr 100px 120px 100px 80px;
  }

  .list-header__col--type,
  .list-row__col--type {
    display: none;
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }

  .list-header,
  .list-row {
    grid-template-columns: 40px 80px 1fr 100px 80px;
  }

  .list-header__col--time,
  .list-row__col--time,
  .list-header__col--status,
  .list-row__col--status {
    display: none;
  }
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.loading-text {
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 14px;
}
</style>
