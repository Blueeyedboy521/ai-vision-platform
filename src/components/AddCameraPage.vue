<template>
  <div class="add-camera-page">
    <!-- Header -->
    <div class="add-camera-page__header">
      <div class="add-camera-page__header-left">
        <h1 class="add-camera-page__title">配置智能摄像头</h1>
        <span class="add-camera-page__id">ID: CAM-NEW-#{{ Date.now().toString().slice(-4) }}</span>
      </div>
      <div class="add-camera-page__header-actions">
        <n-button @click="handleCancel">取消配置</n-button>
        <n-button type="primary" @click="handleSave">
          <template #icon>
            <n-icon><SaveOutline /></n-icon>
          </template>
          保存并启动
        </n-button>
      </div>
    </div>

    <!-- Content -->
    <div class="add-camera-page__content">
      <!-- Left Column -->
      <div class="add-camera-page__left">
        <!-- Network & Media Config -->
        <section class="config-card">
          <h3 class="config-card__title">
            <span class="config-card__indicator"></span>
            网络与流媒体配置
          </h3>
          <div class="config-card__body">
            <div class="form-field">
              <label class="form-field__label">设备显示名称</label>
              <n-input
                v-model:value="formData.name"
                placeholder="例如：西门 01 号抓拍机"
              />
            </div>
            <div class="form-field__row">
              <div class="form-field form-field--flex">
                <label class="form-field__label">管理分区</label>
                <n-tree-select
                  v-model:value="formData.location"
                  :options="areaOptions"
                  placeholder="生产 A 车间"
                  clearable
                  :default-expand-all="true"
                />
              </div>
              <div class="form-field form-field--flex">
                <label class="form-field__label">网络状态</label>
                <div 
                  class="connection-status" 
                  :class="{ 'connection-status--online': connectionStatus === 'online' }"
                >
                  <span class="connection-status__dot"></span>
                  {{ connectionStatus === 'online' ? 'ONLINE' : '未连接' }}
                </div>
              </div>
            </div>
            <div class="form-field">
              <label class="form-field__label">RTSP 流地址</label>
              <div class="form-field__group">
                <n-input
                  v-model:value="formData.rtspUrl"
                  placeholder="rtsp://admin:pwd@192.168.1.100:554/ch1"
                  class="form-field__input"
                />
                <n-button @click="testConnection" :loading="testingConnection">
                  流通性测试
                </n-button>
              </div>
            </div>
          </div>
        </section>

        <!-- Preview Section -->
        <section class="config-card config-card--preview">
          <div class="config-card__header">
            <h3 class="config-card__title">
              <span class="config-card__indicator"></span>
              16:9 实时预监实况
            </h3>
            <n-button type="error" size="small" @click="captureSnapshot">
              <template #icon>
                <n-icon><CameraOutline /></n-icon>
              </template>
              抓拍
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
            </div>
            <div v-if="snapshots.length > 0" class="preview__snapshots">
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

      <!-- Right Column -->
      <div class="add-camera-page__right">
        <!-- Algorithm Config -->
        <section class="config-card">
          <div class="config-card__header">
            <h3 class="config-card__title">
              <span class="config-card__indicator"></span>
              算法能力与阈值配置
            </h3>
            <span class="config-card__badge">ACTIVE: {{ enabledAlgorithmCount }} / {{ algorithms.length }}</span>
          </div>

          <div class="algorithm-list">
            <div class="algorithm-list__header">
              <span class="algorithm-list__col algorithm-list__col--enable">启用</span>
              <span class="algorithm-list__col algorithm-list__col--name">算法类型</span>
              <span class="algorithm-list__col algorithm-list__col--confidence">置信度 (%)</span>
              <span class="algorithm-list__col algorithm-list__col--region">检测范围</span>
              <span class="algorithm-list__col algorithm-list__col--time">时间计划</span>
            </div>
            <div class="algorithm-list__body">
              <div
                v-for="algo in algorithms"
                :key="algo.id"
                class="algorithm-list__row"
                :class="{ 'algorithm-list__row--enabled': algo.enabled }"
              >
                <div class="algorithm-list__col algorithm-list__col--enable">
                  <n-switch v-model:value="algo.enabled" />
                </div>
                <div class="algorithm-list__col algorithm-list__col--name">
                  <span class="algorithm-list__name">{{ algo.name }}</span>
                  <span v-if="algo.nameEn" class="algorithm-list__name-en">({{ algo.nameEn }})</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--confidence">
                  <n-slider
                    v-model:value="algo.confidence"
                    :min="0"
                    :max="100"
                    :disabled="!algo.enabled"
                    class="algorithm-list__slider"
                  />
                  <span class="algorithm-list__confidence-value">{{ algo.confidence }}%</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--region">
                  <n-button
                    v-if="algo.enabled"
                    text
                    type="primary"
                    size="small"
                    @click="configRegion(algo)"
                  >
                    <template #icon>
                      <n-icon><ScanOutline /></n-icon>
                    </template>
                    {{ algo.regionCount ? `${algo.regionCount} 个区域` : '绘制区域' }}
                  </n-button>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--time">
                  <template v-if="algo.enabled">
                    <n-popover 
                      trigger="click" 
                      placement="bottom"
                      :show="activeTimePopover === algo.id"
                      @update:show="(v) => activeTimePopover = v ? algo.id : null"
                    >
                      <template #trigger>
                        <div class="algorithm-list__time-btn">
                          <n-icon :size="14"><TimeOutline /></n-icon>
                          <span>{{ algo.timeRange || '00:00 - 23:59' }}</span>
                        </div>
                      </template>
                      <div class="time-picker-panel">
                        <div class="time-picker-panel__title">设置告警时段</div>
                        <div class="time-picker-panel__row">
                          <n-time-picker
                            v-model:value="algo.startTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('00:00')"
                          />
                          <span class="time-picker-panel__separator">至</span>
                          <n-time-picker
                            v-model:value="algo.endTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('23:59')"
                          />
                        </div>
                        <div class="time-picker-panel__presets">
                          <n-button size="tiny" @click="setTimePreset(algo, '全天')">全天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '白天')">白天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '夜间')">夜间</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '工作时间')">工作时间</n-button>
                        </div>
                        <div class="time-picker-panel__footer">
                          <n-button size="small" type="primary" @click="confirmTimeSelection(algo)">
                            确认
                          </n-button>
                        </div>
                      </div>
                    </n-popover>
                  </template>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Draw Region Modal -->
    <DrawRegionModal
      v-model:show="showDrawRegionModal"
      :image-src="previewImage || '/camera-warehouse-01.jpg'"
      :algorithm-name="currentAlgorithm?.name || ''"
      :algorithm-name-en="currentAlgorithm?.nameEn || ''"
      :existing-regions="currentAlgorithm?.regions"
      @save="handleSaveRegions"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NInput, NTreeSelect, NButton, NIcon, NSwitch,
  NSlider, NPopover, NTimePicker
} from 'naive-ui'
import type { TreeSelectOption } from 'naive-ui'
import {
  VideocamOffOutline,
  CameraOutline,
  SaveOutline,
  ScanOutline,
  TimeOutline
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
  areaTreeData?: any[]
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'save', data: any): void
}>()

// Form data
const formData = ref({
  name: '',
  location: null as string | null,
  rtspUrl: ''
})

const connectionStatus = ref<'online' | 'offline'>('offline')
const testingConnection = ref(false)
const previewImage = ref('/camera-warehouse-01.jpg')
const snapshots = ref<string[]>([])

// Draw Region Modal
const showDrawRegionModal = ref(false)
const currentAlgorithm = ref<Algorithm | null>(null)

// Time Popover
const activeTimePopover = ref<string | null>(null)

// Area options
const areaOptions = computed<TreeSelectOption[]>(() => {
  if (props.areaTreeData && props.areaTreeData.length > 0) {
    return convertToTreeSelectOptions(props.areaTreeData)
  }
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

// Algorithms
const algorithms = ref<Algorithm[]>([
  { id: 'face', name: '人脸识别', nameEn: 'Face ID', enabled: true, confidence: 85, regionCount: 0, timeRange: '00:00 - 23:59', startTime: 0, endTime: 86340000 },
  { id: 'intrusion', name: '区域入侵检测', enabled: true, confidence: 70, regionCount: 2, timeRange: '18:00 - 06:00', startTime: 64800000, endTime: 21600000 },
  { id: 'helmet', name: '安全帽佩戴识别', enabled: true, confidence: 90, regionCount: 0, timeRange: '08:00 - 18:00', startTime: 28800000, endTime: 64800000 },
  { id: 'fire', name: '烟火检测', enabled: false, confidence: 65, startTime: 0, endTime: 86340000 },
  { id: 'fall', name: '异常检测', enabled: false, confidence: 50, startTime: 0, endTime: 86340000 }
])

const enabledAlgorithmCount = computed(() => 
  algorithms.value.filter(a => a.enabled).length
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

function setTimePreset(algo: Algorithm, preset: string) {
  const idx = algorithms.value.findIndex(a => a.id === algo.id)
  if (idx === -1) return
  
  let startTime = 0
  let endTime = getDefaultTime('23:59')
  
  switch (preset) {
    case '全天':
      startTime = 0
      endTime = getDefaultTime('23:59')
      break
    case '白天':
      startTime = getDefaultTime('06:00')
      endTime = getDefaultTime('18:00')
      break
    case '夜间':
      startTime = getDefaultTime('18:00')
      endTime = getDefaultTime('06:00')
      break
    case '工作时间':
      startTime = getDefaultTime('08:00')
      endTime = getDefaultTime('18:00')
      break
  }
  
  // Update using array index for proper reactivity
  algorithms.value[idx].startTime = startTime
  algorithms.value[idx].endTime = endTime
  algorithms.value[idx].timeRange = `${formatTime(startTime)} - ${formatTime(endTime)}`
}

function confirmTimeSelection(algo: Algorithm) {
  const idx = algorithms.value.findIndex(a => a.id === algo.id)
  if (idx === -1) return
  
  // Update timeRange when confirm button is clicked using array index
  const startTime = algorithms.value[idx].startTime
  const endTime = algorithms.value[idx].endTime
  algorithms.value[idx].timeRange = `${formatTime(startTime)} - ${formatTime(endTime)}`
  activeTimePopover.value = null
}

function handleCancel() {
  emit('cancel')
}

function handleSave() {
  const data = {
    ...formData.value,
    algorithms: algorithms.value.filter(a => a.enabled)
  }
  emit('save', data)
}
</script>

<style scoped>
.add-camera-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

/* Header */
.add-camera-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.add-camera-page__header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.add-camera-page__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.add-camera-page__id {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.add-camera-page__header-actions {
  display: flex;
  gap: var(--spacing-md);
}

/* Content */
.add-camera-page__content {
  flex: 1;
  display: flex;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-xl);
  overflow-y: auto;
}

.add-camera-page__left {
  flex: 0 0 45%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.add-camera-page__right {
  flex: 1;
  min-width: 0;
}

/* Config Card */
.config-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
}

.config-card--preview {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.config-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.config-card__title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.config-card__indicator {
  width: 4px;
  height: 16px;
  background: var(--primary-color);
  border-radius: var(--radius-xs);
}

.config-card__badge {
  font-size: var(--font-size-sm);
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
}

.config-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

/* Form Fields */
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
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
}

.form-field__group {
  display: flex;
  gap: var(--spacing-sm);
}

.form-field__input {
  flex: 1;
}

/* Connection Status */
.connection-status {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
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
  border-radius: 50%;
  background: currentColor;
}

/* Preview */
.preview {
  flex: 1;
  margin-top: var(--spacing-md);
  display: flex;
  flex-direction: column;
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
}

.preview__snapshots {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.preview__snapshot {
  width: 60px;
  height: 45px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--border-color);
}

.preview__snapshot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Algorithm List */
.algorithm-list {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-top: var(--spacing-md);
}

.algorithm-list__header {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.algorithm-list__body {
  max-height: 320px;
  overflow-y: auto;
}

.algorithm-list__row {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-normal);
}

.algorithm-list__row:last-child {
  border-bottom: none;
}

.algorithm-list__row:hover {
  background: var(--bg-card);
}

.algorithm-list__row--enabled {
  background: rgba(67, 24, 255, 0.02);
}

.algorithm-list__col {
  display: flex;
  align-items: center;
}

.algorithm-list__col--enable {
  width: 50px;
  flex-shrink: 0;
}

.algorithm-list__col--name {
  flex: 1.5;
  gap: var(--spacing-xs);
}

.algorithm-list__col--confidence {
  flex: 1.2;
  gap: var(--spacing-sm);
}

.algorithm-list__col--region {
  flex: 1;
}

.algorithm-list__col--time {
  flex: 1;
}

.algorithm-list__name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.algorithm-list__name-en {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.algorithm-list__slider {
  width: 80px;
}

.algorithm-list__confidence-value {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  min-width: 36px;
}

.algorithm-list__disabled {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.algorithm-list__time-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.algorithm-list__time-btn:hover {
  border-color: var(--primary-color);
}

/* Time Picker Panel */
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

/* Responsive */
@media (max-width: 1000px) {
  .add-camera-page__content {
    flex-direction: column;
  }

  .add-camera-page__left {
    flex: none;
    max-width: none;
  }
}
</style>
