<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    :bordered="false"
    :closable="true"
    :mask-closable="false"
    class="camera-modal"
    :content-style="contentStyle"
    :header-style="headerStyle"
    @update:show="handleClose"
  >
    <template #header>
      <div class="camera-modal__header">
        <n-icon :size="20" class="camera-modal__header-icon">
          <VideocamOutline />
        </n-icon>
        <span class="camera-modal__header-title">添加摄像头配置</span>
      </div>
    </template>

    <div class="camera-modal__content">
      <!-- Left Column: Basic Info + Preview -->
      <div class="camera-modal__left">
        <!-- Basic Info Section -->
        <section class="config-section">
          <h3 class="config-section__title">
            <span class="config-section__indicator"></span>
            基础信息
          </h3>
          <div class="config-section__body">
            <div class="form-field">
              <label class="form-field__label">摄像头名称</label>
              <n-input
                v-model:value="formData.name"
                placeholder="输入设备名称，如：东门入口-01"
              />
            </div>
            <div class="form-field__row">
              <div class="form-field form-field--flex">
                <label class="form-field__label">所属区域</label>
                <n-tree-select
                  v-model:value="formData.location"
                  :options="areaOptions"
                  placeholder="请选择区域"
                  clearable
                  :default-expand-all="true"
                />
              </div>
              <div class="form-field form-field--flex">
                <label class="form-field__label">连接状态</label>
                <div 
                  class="connection-status" 
                  :class="{ 'connection-status--online': connectionStatus === 'online' }"
                >
                  <span class="connection-status__dot"></span>
                  {{ connectionStatus === 'online' ? '已连接 (Online)' : '未连接' }}
                </div>
              </div>
            </div>
            <div class="form-field">
              <label class="form-field__label">RTSP 流地址</label>
              <div class="form-field__group">
                <n-input
                  v-model:value="formData.rtspUrl"
                  placeholder="rtsp://admin:password@192.168.1.100:554/ch1"
                  class="form-field__input"
                />
                <n-button
                  type="primary"
                  :loading="testingConnection"
                  @click="testConnection"
                >
                  测试连接
                </n-button>
              </div>
            </div>
          </div>
        </section>

        <!-- Preview Section - Aligned with Algorithm Config -->
        <section class="config-section config-section--preview">
          <div class="config-section__header">
            <h3 class="config-section__title">
              <span class="config-section__indicator"></span>
              实时预览与抓拍
            </h3>
            <n-button type="primary" size="small" @click="captureSnapshot">
              <template #icon>
                <n-icon><CameraOutline /></n-icon>
              </template>
              前拍验证
            </n-button>
          </div>
          <div class="preview">
            <div class="preview__video">
              <img
                v-if="previewImage"
                :src="previewImage"
                alt="Preview"
                class="preview__image"
              />
              <div v-else class="preview__placeholder">
                <n-icon :size="48" class="preview__placeholder-icon">
                  <VideocamOffOutline />
                </n-icon>
                <span>等待连接...</span>
              </div>
              <div class="preview__info">
                <span>1920×1080</span>
                <span class="preview__info-divider">|</span>
                <span>25FPS</span>
                <span class="preview__info-divider">|</span>
                <span>4.2Mbps</span>
              </div>
            </div>
            <div class="preview__snapshots">
              <div
                v-for="(snap, index) in snapshots"
                :key="index"
                class="preview__snapshot"
              >
                <img :src="snap" alt="Snapshot" />
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Right Column: Algorithm Config + Global Settings -->
      <div class="camera-modal__right">
        <!-- Algorithm Config - Top aligned with Basic Info -->
        <section class="config-section">
          <div class="algorithm-config__header">
            <h3 class="config-section__title">
              <span class="config-section__indicator"></span>
              算法能力配置
            </h3>
            <span class="algorithm-config__count">已启用 {{ enabledAlgorithmCount }} 个算法</span>
          </div>

          <div class="algorithm-table">
            <div class="algorithm-table__header">
              <span class="algorithm-table__col algorithm-table__col--enable">启用</span>
              <span class="algorithm-table__col algorithm-table__col--name">算法名称</span>
              <span class="algorithm-table__col algorithm-table__col--confidence">置信度阈值</span>
              <span class="algorithm-table__col algorithm-table__col--region">检测区域</span>
              <span class="algorithm-table__col algorithm-table__col--time">告警时段</span>
            </div>
            <div class="algorithm-table__body">
              <div
                v-for="algo in algorithms"
                :key="algo.id"
                class="algorithm-table__row"
                :class="{ 'algorithm-table__row--enabled': algo.enabled }"
              >
                <div class="algorithm-table__col algorithm-table__col--enable">
                  <n-switch v-model:value="algo.enabled" />
                </div>
                <div class="algorithm-table__col algorithm-table__col--name">
                  <span class="algorithm-table__name">{{ algo.name }}</span>
                  <span v-if="algo.nameEn" class="algorithm-table__name-en">({{ algo.nameEn }})</span>
                </div>
                <div class="algorithm-table__col algorithm-table__col--confidence">
                  <n-slider
                    v-model:value="algo.confidence"
                    :min="0"
                    :max="100"
                    :disabled="!algo.enabled"
                    :format-tooltip="(v: number) => `${v}%`"
                    class="algorithm-table__slider"
                  />
                  <span class="algorithm-table__confidence-value">{{ algo.confidence }}%</span>
                </div>
                <div class="algorithm-table__col algorithm-table__col--region">
                  <n-button
                    v-if="algo.enabled"
                    text
                    type="primary"
                    size="small"
                    @click="configRegion(algo)"
                  >
                    <template #icon>
                      <n-icon><LocationOutline /></n-icon>
                    </template>
                    {{ algo.regionCount ? `${algo.regionCount}个区域` : '绘制区域' }}
                  </n-button>
                  <span v-else class="algorithm-table__disabled">
                    <n-icon :size="14"><LocationOutline /></n-icon>
                    未配置
                  </span>
                </div>
                <div class="algorithm-table__col algorithm-table__col--time">
                  <template v-if="algo.enabled">
                    <n-popover 
                      trigger="click" 
                      placement="bottom"
                      :show="activeTimePopover === algo.id"
                      @update:show="(v) => activeTimePopover = v ? algo.id : null"
                    >
                      <template #trigger>
                        <div class="algorithm-table__time-btn">
                          <n-icon :size="14" class="algorithm-table__time-icon"><TimeOutline /></n-icon>
                          <span class="algorithm-table__time-range">{{ algo.timeRange || '00:00 - 23:59' }}</span>
                          <n-icon :size="12"><ChevronDownOutline /></n-icon>
                        </div>
                      </template>
                      <div class="time-picker-panel">
                        <div class="time-picker-panel__title">设置告警时段</div>
                        <div class="time-picker-panel__row">
                          <n-time-picker
                            v-model:value="algo.startTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('00:00')"
                            @update:value="(v) => updateTimeRange(algo, 'start', v)"
                          />
                          <span class="time-picker-panel__separator">至</span>
                          <n-time-picker
                            v-model:value="algo.endTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('23:59')"
                            @update:value="(v) => updateTimeRange(algo, 'end', v)"
                          />
                        </div>
                        <div class="time-picker-panel__presets">
                          <n-button size="tiny" @click="setTimePreset(algo, '全天')">全天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '白天')">白天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '夜间')">夜间</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '工作时间')">工作时间</n-button>
                        </div>
                        <div class="time-picker-panel__footer">
                          <n-button size="small" type="primary" @click="activeTimePopover = null">
                            确认
                          </n-button>
                        </div>
                      </div>
                    </n-popover>
                  </template>
                  <span v-else class="algorithm-table__disabled">未设置</span>
                </div>
              </div>
            </div>
          </div>
        </section>

    <!-- Draw Region Modal -->
    <DrawRegionModal
      v-model:show="showDrawRegionModal"
      :image-src="previewImage || '/camera-warehouse-01.jpg'"
      :algorithm-name="currentAlgorithm?.name || ''"
      :algorithm-name-en="currentAlgorithm?.nameEn || ''"
      :existing-regions="currentAlgorithm?.regions"
      @save="handleSaveRegions"
    />

        <!-- Global Settings - Moved to right, aligned with preview -->
        <section class="config-section config-section--settings">
          <h3 class="config-section__title">
            <span class="config-section__indicator"></span>
            全局计算策略
          </h3>
          <div class="config-section__body config-section__body--horizontal">
            <div class="form-field form-field--flex">
              <label class="form-field__label">
                识别间隔 (抽帧)
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-icon :size="14" class="form-field__help">
                      <HelpCircleOutline />
                    </n-icon>
                  </template>
                  每隔多少帧进行一次算法识别
                </n-tooltip>
              </label>
              <div class="form-field__with-unit">
                <n-input-number
                  v-model:value="formData.frameInterval"
                  :min="1"
                  :max="30"
                  class="form-field__input--full"
                />
                <span class="form-field__unit">帧/次</span>
              </div>
            </div>
            <div class="form-field form-field--flex">
              <label class="form-field__label">
                告警静默期
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-icon :size="14" class="form-field__help">
                      <HelpCircleOutline />
                    </n-icon>
                  </template>
                  同一告警触发后的静默时间
                </n-tooltip>
              </label>
              <div class="form-field__with-unit">
                <n-input-number
                  v-model:value="formData.silentPeriod"
                  :min="0"
                  :max="3600"
                  class="form-field__input--full"
                />
                <span class="form-field__unit">秒</span>
              </div>
            </div>
          </div>
        </section>

        <div class="algorithm-tip">
          <n-icon :size="16" class="algorithm-tip__icon"><InformationCircleOutline /></n-icon>
          <span class="algorithm-tip__text">提示：配置算法时请确保摄像头角度已覆盖识别目标区域。较高的置信度阈值可以减少误报，但可能会漏检。</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="camera-modal__footer">
        <div class="camera-modal__stats">
          <span class="camera-modal__stat">
            <span class="camera-modal__stat-dot camera-modal__stat-dot--active"></span>
            已激活能力：{{ enabledAlgorithmCount }}
          </span>
          <span class="camera-modal__stat">
            <span class="camera-modal__stat-dot camera-modal__stat-dot--pending"></span>
            待配置：{{ pendingConfigCount }}
          </span>
        </div>
        <div class="camera-modal__actions">
          <n-button @click="handleClose">取消</n-button>
          <n-button type="primary" @click="handleSave">
            <template #icon>
              <n-icon><SaveOutline /></n-icon>
            </template>
            完成并保存
          </n-button>
        </div>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NInput, NTreeSelect, NButton, NIcon, NSwitch,
  NSlider, NInputNumber, NTooltip, NPopover, NTimePicker
} from 'naive-ui'
import type { TreeSelectOption } from 'naive-ui'
import {
  VideocamOutline,
  VideocamOffOutline,
  CameraOutline,
  HelpCircleOutline,
  LocationOutline,
  TimeOutline,
  InformationCircleOutline,
  SaveOutline,
  ChevronDownOutline
} from '@vicons/ionicons5'
import DrawRegionModal from './DrawRegionModal.vue'

interface Region {
  points: { x: number; y: number }[]
  color: string
  type: string
}

interface Algorithm {
  id: string
  name: string
  nameEn?: string
  enabled: boolean
  confidence: number
  regionCount?: number
  timeRange?: string
  startTime?: number
  endTime?: number
  regions?: Region[]
}

const props = defineProps<{
  show: boolean
  areaTreeData?: any[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'save', data: any): void
}>()

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const contentStyle = { padding: 0 }
const headerStyle = { 
  padding: 'var(--spacing-lg) var(--spacing-xl)', 
  borderBottom: '1px solid var(--border-color)' 
}

// Form data
const formData = ref({
  name: '',
  location: null as string | null,
  rtspUrl: '',
  frameInterval: 5,
  silentPeriod: 60
})

const connectionStatus = ref<'online' | 'offline'>('offline')
const testingConnection = ref(false)
const previewImage = ref('/camera-warehouse-01.jpg')
const snapshots = ref<string[]>(['/camera-lobby-01.jpg', '/camera-lobby-02.jpg'])

// Area tree options for select
const areaOptions = computed<TreeSelectOption[]>(() => {
  if (props.areaTreeData) {
    return convertToTreeSelectOptions(props.areaTreeData)
  }
  // Default options
  return [
    {
      key: 'main-park',
      label: '主园区',
      children: [
        { key: 'a-warehouse', label: 'A栋仓库' },
        { key: 'b-office', label: 'B区办公楼' },
        { key: 'security-center', label: '安防中心' }
      ]
    },
    {
      key: 'material-yard',
      label: '物料堆场',
      children: [
        { key: 'yard-a', label: '堆场A区' },
        { key: 'yard-b', label: '堆场B区' }
      ]
    },
    {
      key: 'parking-lot',
      label: '停车场',
      children: [
        { key: 'b-lobby', label: 'B栋 - 大厅入口' }
      ]
    }
  ]
})

function convertToTreeSelectOptions(nodes: any[]): TreeSelectOption[] {
  return nodes.map(node => ({
    key: node.key,
    label: node.label,
    children: node.children ? convertToTreeSelectOptions(node.children) : undefined
  }))
}

// Draw Region Modal
const showDrawRegionModal = ref(false)
const currentAlgorithm = ref<Algorithm | null>(null)

// Time Popover
const activeTimePopover = ref<string | null>(null)

// Algorithm configurations
const algorithms = ref<Algorithm[]>([
  { id: 'face', name: '人脸识别', nameEn: 'Face ID', enabled: true, confidence: 85, regionCount: 1, timeRange: '00:00 - 23:59', startTime: 0, endTime: 86340000 },
  { id: 'intrusion', name: '区域入侵检测', enabled: true, confidence: 78, regionCount: 2, timeRange: '18:00 - 06:00', startTime: 64800000, endTime: 21600000 },
  { id: 'helmet', name: '安全帽佩戴识别', enabled: true, confidence: 90, timeRange: '08:00 - 18:00', startTime: 28800000, endTime: 64800000 },
  { id: 'fire', name: '烟火检测', enabled: false, confidence: 75, startTime: 0, endTime: 86340000 },
  { id: 'fall', name: '高空抛物', enabled: false, confidence: 50, startTime: 0, endTime: 86340000 }
])

const enabledAlgorithmCount = computed(() => 
  algorithms.value.filter(a => a.enabled).length
)

const pendingConfigCount = computed(() =>
  algorithms.value.filter(a => a.enabled && !a.regionCount).length
)

function testConnection() {
  testingConnection.value = true
  setTimeout(() => {
    connectionStatus.value = 'online'
    testingConnection.value = false
  }, 1500)
}

function captureSnapshot() {
  if (snapshots.value.length < 4) {
    snapshots.value.push(previewImage.value || '/camera-lobby-01.jpg')
  }
}

// Region drawing
function configRegion(algo: Algorithm) {
  currentAlgorithm.value = algo
  showDrawRegionModal.value = true
}

function handleSaveRegions(regions: Region[]) {
  if (currentAlgorithm.value) {
    currentAlgorithm.value.regions = regions
    currentAlgorithm.value.regionCount = regions.length
  }
}

// Time handling
function getDefaultTime(time: string): number {
  const [hours, minutes] = time.split(':').map(Number)
  return (hours * 60 + minutes) * 60 * 1000
}

function formatTime(timestamp: number | undefined): string {
  if (timestamp === undefined) return '00:00'
  const totalMinutes = Math.floor(timestamp / 60000)
  const hours = Math.floor(totalMinutes / 60) % 24
  const minutes = totalMinutes % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
}

function updateTimeRange(algo: Algorithm, type: 'start' | 'end', value: number | null) {
  if (value === null) return
  
  if (type === 'start') {
    algo.startTime = value
  } else {
    algo.endTime = value
  }
  
  algo.timeRange = `${formatTime(algo.startTime)} - ${formatTime(algo.endTime)}`
}

function setTimePreset(algo: Algorithm, preset: string) {
  switch (preset) {
    case '全天':
      algo.startTime = 0
      algo.endTime = getDefaultTime('23:59')
      break
    case '白天':
      algo.startTime = getDefaultTime('06:00')
      algo.endTime = getDefaultTime('18:00')
      break
    case '夜间':
      algo.startTime = getDefaultTime('18:00')
      algo.endTime = getDefaultTime('06:00')
      break
    case '工作时间':
      algo.startTime = getDefaultTime('08:00')
      algo.endTime = getDefaultTime('18:00')
      break
  }
  algo.timeRange = `${formatTime(algo.startTime)} - ${formatTime(algo.endTime)}`
}

function handleClose() {
  emit('update:show', false)
}

function handleSave() {
  const data = {
    ...formData.value,
    algorithms: algorithms.value.filter(a => a.enabled)
  }
  emit('save', data)
  handleClose()
}

watch(() => props.show, (val) => {
  if (val) {
    formData.value = {
      name: '',
      location: null,
      rtspUrl: '',
      frameInterval: 5,
      silentPeriod: 60
    }
    connectionStatus.value = 'offline'
  }
})
</script>

<style scoped>
/* ===== Modal Container ===== */
.camera-modal {
  width: 70vw;
  min-width: 900px;
  max-width: 1400px;
}

.camera-modal__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.camera-modal__header-icon {
  color: var(--primary-color);
}

.camera-modal__header-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.camera-modal__content {
  display: flex;
  gap: var(--spacing-2xl);
  padding: var(--spacing-xl) var(--spacing-2xl);
  max-height: calc(80vh - 140px);
  overflow-y: auto;
}

.camera-modal__left {
  flex: 0 0 45%;
  min-width: 400px;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.camera-modal__right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* ===== Config Section ===== */
.config-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
}

.config-section--preview {
  flex: 1;
}

.config-section--settings {
  flex-shrink: 0;
}

.config-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.config-section__title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.config-section__indicator {
  width: 4px;
  height: 16px;
  background: var(--primary-color);
  border-radius: var(--radius-xs);
}

.config-section__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.config-section__body--horizontal {
  flex-direction: row;
  gap: var(--spacing-xl);
}

/* ===== Form Fields ===== */
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-field--flex {
  flex: 1;
}

.form-field__row {
  display: flex;
  gap: var(--spacing-lg);
}

.form-field__label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  display: flex;
  align-items: center;
}

.form-field__help {
  cursor: help;
  margin-left: var(--spacing-xs);
  color: var(--text-muted);
}

.form-field__group {
  display: flex;
  gap: var(--spacing-sm);
}

.form-field__input {
  flex: 1;
}

.form-field__input--full {
  width: 100%;
}

.form-field__with-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.form-field__unit {
  font-size: var(--font-size-base);
  color: var(--text-muted);
  white-space: nowrap;
}

/* ===== Connection Status ===== */
.connection-status {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  color: var(--text-muted);
}

.connection-status--online {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: var(--success-color);
}

.connection-status__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--text-muted);
}

.connection-status--online .connection-status__dot {
  background: var(--success-color);
}

/* ===== Preview ===== */
.preview {
  margin-top: var(--spacing-md);
}

.preview__video {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #1a1a2e;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.preview__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-sm);
  color: var(--text-muted);
  font-size: var(--font-size-base);
}

.preview__placeholder-icon {
  color: var(--text-muted);
}

.preview__info {
  position: absolute;
  bottom: var(--spacing-sm);
  left: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  background: rgba(0, 0, 0, 0.6);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: #fff;
}

.preview__info-divider {
  opacity: 0.5;
}

.preview__snapshots {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.preview__snapshot {
  width: 56px;
  height: 42px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.preview__snapshot:hover {
  border-color: var(--primary-color);
  transform: scale(1.05);
}

.preview__snapshot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ===== Algorithm Config ===== */
.algorithm-config__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.algorithm-config__count {
  font-size: var(--font-size-base);
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
}

/* ===== Algorithm Table ===== */
.algorithm-table {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.algorithm-table__header {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.algorithm-table__body {
  max-height: 240px;
  overflow-y: auto;
}

.algorithm-table__row {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-normal);
}

.algorithm-table__row:last-child {
  border-bottom: none;
}

.algorithm-table__row:hover {
  background: var(--bg-card);
}

.algorithm-table__row--enabled {
  background: rgba(67, 24, 255, 0.03);
}

.algorithm-table__col {
  display: flex;
  align-items: center;
}

.algorithm-table__col--enable {
  width: 50px;
  flex-shrink: 0;
}

.algorithm-table__col--name {
  flex: 1.2;
  min-width: 0;
  gap: var(--spacing-xs);
}

.algorithm-table__col--confidence {
  flex: 1.2;
  gap: var(--spacing-sm);
}

.algorithm-table__col--region {
  flex: 0.9;
  gap: var(--spacing-xs);
}

.algorithm-table__col--time {
  flex: 1;
  gap: var(--spacing-xs);
}

.algorithm-table__name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.algorithm-table__name-en {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.algorithm-table__slider {
  width: 80px;
}

.algorithm-table__confidence-value {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  min-width: 32px;
}

.algorithm-table__time-icon {
  color: var(--primary-color);
}

.algorithm-table__time-range {
  font-size: var(--font-size-xs);
  color: var(--text-primary);
}

.algorithm-table__time-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.algorithm-table__time-btn:hover {
  border-color: var(--primary-color);
  background: rgba(67, 24, 255, 0.04);
}

.algorithm-table__disabled {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* ===== Time Picker Panel ===== */
.time-picker-panel {
  padding: var(--spacing-sm);
  min-width: 280px;
}

.time-picker-panel__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.time-picker-panel__row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.time-picker-panel__separator {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.time-picker-panel__presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
}

.time-picker-panel__footer {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
}

/* ===== Algorithm Tip ===== */
.algorithm-tip {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: rgba(67, 24, 255, 0.04);
  border-radius: var(--radius-lg);
}

.algorithm-tip__icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--primary-color);
}

.algorithm-tip__text {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  line-height: var(--line-height-relaxed);
}

/* ===== Modal Footer ===== */
.camera-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.camera-modal__stats {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.camera-modal__stat {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-base);
  color: var(--text-muted);
}

.camera-modal__stat-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.camera-modal__stat-dot--active {
  background: var(--success-color);
}

.camera-modal__stat-dot--pending {
  background: var(--text-muted);
}

.camera-modal__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* ===== Responsive ===== */
@media (max-width: 1000px) {
  .camera-modal__content {
    flex-direction: column;
  }

  .camera-modal__left {
    flex: none;
    width: 100%;
  }

  .config-section__body--horizontal {
    flex-direction: column;
    gap: var(--spacing-md);
  }
}
</style>
