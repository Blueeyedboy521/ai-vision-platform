<template>
  <div class="video-preview">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">视频预览</h1>
        <p class="page-header__subtitle">实时查看监控画面，支持多画面分割显示</p>
      </div>
      <div class="page-header__actions">
        <n-button-group>
          <n-button 
            v-for="layout in layouts" 
            :key="layout.value"
            :type="gridLayout === layout.value ? 'primary' : 'default'"
            @click="gridLayout = layout.value"
          >
            <template #icon>
              <n-icon><component :is="layout.icon" /></n-icon>
            </template>
            {{ layout.label }}
          </n-button>
        </n-button-group>
        <n-button @click="showConfigModal = true">
          <template #icon><n-icon><SettingsOutline /></n-icon></template>
          配置画面
        </n-button>
      </div>
    </div>

    <div 
      ref="gridContainerRef"
      class="video-grid" 
      :class="`video-grid--${gridLayout}`"
      :style="gridStyle"
    >
      <div 
        v-for="(slot, index) in visibleSlots" 
        :key="index"
        class="video-slot"
        :class="{ 'video-slot--selected': selectedSlot === index }"
      >
        <div class="video-slot__ratio">
          <template v-if="slot.camera">
            <img :src="slot.camera.thumbnail" :alt="slot.camera.name" class="video-slot__video" />
            <div class="video-slot__info-overlay">
              <div class="video-slot__top-bar">
                <div class="video-slot__live">LIVE</div>
                <div class="video-slot__actions">
                  <n-button circle size="tiny" quaternary @click.stop="playFullscreen(slot.camera)">
                    <template #icon><n-icon color="#fff"><ExpandOutline /></n-icon></template>
                  </n-button>
                </div>
              </div>
              <div class="video-slot__bottom-bar">
                <div class="video-slot__name-status">
                  <span class="video-slot__name">{{ slot.camera.name }}</span>
                  <span class="status-dot" :class="{ 'status-dot--online': slot.camera.online }"></span>
                </div>
                <span class="video-slot__time">{{ currentTime }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="video-slot__no-signal">
              <n-icon :size="40" color="rgba(255,255,255,0.3)"><VideocamOffOutline /></n-icon>
              <span>无信号</span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Camera Select Modal -->
    <n-modal v-model:show="showSelectModal" preset="card" title="选择摄像头" :style="{ width: '600px' }" :bordered="false">
      <n-input v-model:value="searchCamera" placeholder="搜索摄像头..." clearable style="margin-bottom: 16px">
        <template #prefix><n-icon><SearchOutline /></n-icon></template>
      </n-input>
      <div class="camera-select-list">
        <div 
          v-for="camera in filteredCameras" 
          :key="camera.id"
          class="camera-select-item"
          @click="addCamera(camera)"
        >
          <img :src="camera.thumbnail" :alt="camera.name" class="camera-select-item__thumb" />
          <div class="camera-select-item__info">
            <span class="camera-select-item__name">{{ camera.name }}</span>
            <span class="camera-select-item__location">{{ camera.location }}</span>
          </div>
          <span class="camera-select-item__status" :class="{ online: camera.online }">
            {{ camera.online ? '在线' : '离线' }}
          </span>
        </div>
      </div>
    </n-modal>

    <!-- Config Modal -->
    <n-modal v-model:show="showConfigModal" preset="card" title="画面配置" :style="{ width: '700px' }" :bordered="false">
      <n-tabs type="line">
        <n-tab-pane name="cameras" tab="摄像头配置">
          <div class="config-grid" :class="`config-grid--${gridLayout}`">
            <div 
              v-for="(slot, index) in visibleSlots" 
              :key="index"
              class="config-slot"
              :class="{ 'config-slot--has-camera': slot.camera }"
            >
              <div class="config-slot__label">画面 {{ index + 1 }}</div>
              <n-select 
                :value="slot.camera?.id || null"
                :options="getCameraOptions(index)"
                placeholder="选择摄像头"
                clearable
                @update:value="(val: string | null) => updateSlotCamera(index, val)"
              />
            </div>
          </div>
        </n-tab-pane>
        <n-tab-pane name="settings" tab="显示设置">
          <n-form label-placement="left" label-width="100">
            <n-form-item label="默认布局">
              <n-select v-model:value="config.defaultLayout" :options="layoutOptions" />
            </n-form-item>
            <n-form-item label="自动轮巡">
              <n-switch v-model:value="config.autoRotate" />
            </n-form-item>
            <n-form-item v-if="config.autoRotate" label="轮巡间隔">
              <n-input-number v-model:value="config.rotateInterval" :min="5" :max="300" />
              <span style="margin-left: 8px; color: var(--text-muted)">秒</span>
            </n-form-item>
            <n-form-item label="显示时间">
              <n-switch v-model:value="config.showTime" />
            </n-form-item>
            <n-form-item label="显示位置">
              <n-switch v-model:value="config.showLocation" />
            </n-form-item>
          </n-form>
        </n-tab-pane>
      </n-tabs>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showConfigModal = false">取消</n-button>
          <n-button type="primary" @click="saveConfig">保存配置</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, markRaw, watch, nextTick } from 'vue'
import { 
  NButton, NButtonGroup, NIcon, NModal, NInput, NForm, NFormItem, 
  NSelect, NSwitch, NInputNumber, NTabs, NTabPane, useMessage 
} from 'naive-ui'
import { 
  SettingsOutline, AddOutline, SearchOutline, ExpandOutline, 
  CloseOutline, SquareOutline, GridOutline, AppsOutline, VideocamOffOutline
} from '@vicons/ionicons5'
import { createDetectionWebSocket, type WebSocketClient } from '@/utils/websocket'

interface Camera {
  id: string
  name: string
  location: string
  thumbnail: string
  online: boolean
}

interface GridSlot {
  camera: Camera | null
  detections?: Detection[]
}

interface Detection {
  class_name: string
  confidence: number
  bbox: [number, number, number, number]
}

const message = useMessage()
const gridLayout = ref<'1x1' | '2x2' | '3x3'>('2x2')
const selectedSlot = ref<number | null>(null)
const showSelectModal = ref(false)
const showConfigModal = ref(false)
const searchCamera = ref('')
const currentTime = ref('')

// WebSocket 连接管理
const wsClients = ref<Map<string, WebSocketClient>>(new Map())

// 处理检测结果
function handleDetectionMessage(cameraId: string, data: any) {
  if (data.type === 'detection' && data.detections) {
    // 更新对应摄像头的检测结果
    const slot = gridSlots.value.find((s: GridSlot) => s.camera?.id === cameraId)
    if (slot) {
      slot.detections = data.detections
    }
  }
}

// 连接摄像头 WebSocket
function connectCameraWs(cameraId: string) {
  if (wsClients.value.has(cameraId)) return
  
  const client = createDetectionWebSocket(cameraId, (data) => {
    handleDetectionMessage(cameraId, data)
  })
  client.connect()
  wsClients.value.set(cameraId, client)
}

// 断开摄像头 WebSocket
function disconnectCameraWs(cameraId: string) {
  const client = wsClients.value.get(cameraId)
  if (client) {
    client.disconnect()
    wsClients.value.delete(cameraId)
  }
}

// Grid container ref and calculated dimensions
const gridContainerRef = ref<HTMLElement | null>(null)
const containerSize = ref({ width: 0, height: 0 })

// Calculate grid style based on container size and layout
const gridStyle = computed(() => {
  const { width: W, height: H } = containerSize.value
  if (W === 0 || H === 0) return {}

  const layout = gridLayout.value
  const aspectRatio = 16 / 9

  if (layout === '1x1') {
    // Single video: fill as much as possible while keeping 16:9
    let cardWidth: number, cardHeight: number
    if (W / H > aspectRatio) {
      // Height is limiting factor
      cardHeight = H
      cardWidth = H * aspectRatio
    } else {
      // Width is limiting factor
      cardWidth = W
      cardHeight = W / aspectRatio
    }
    return {
      '--card-width': `${cardWidth}px`,
      '--card-height': `${cardHeight}px`,
    }
  }

  // For 2x2 and 3x3
  const cols = layout === '2x2' ? 2 : 3
  const rows = layout === '2x2' ? 2 : 3
  const minGap = 8 // minimum gap between cards

  let cardWidth: number, cardHeight: number
  let horizontalGap: number, verticalGap: number

  // Try width-based calculation first
  const widthBasedCardWidth = (W - (cols - 1) * minGap) / cols
  const widthBasedCardHeight = widthBasedCardWidth / aspectRatio
  const widthBasedTotalHeight = rows * widthBasedCardHeight + (rows - 1) * minGap

  if (widthBasedTotalHeight <= H) {
    // Width is the constraint, cards fit height-wise
    cardWidth = widthBasedCardWidth
    cardHeight = widthBasedCardHeight
    // Horizontal gap stays at minGap, vertical gap fills remaining space
    horizontalGap = minGap
    const remainingHeight = H - rows * cardHeight
    verticalGap = rows > 1 ? remainingHeight / (rows - 1) : 0
  } else {
    // Height is the constraint
    const heightBasedCardHeight = (H - (rows - 1) * minGap) / rows
    const heightBasedCardWidth = heightBasedCardHeight * aspectRatio
    cardWidth = heightBasedCardWidth
    cardHeight = heightBasedCardHeight
    // Vertical gap stays at minGap, horizontal gap fills remaining space
    verticalGap = minGap
    const remainingWidth = W - cols * cardWidth
    horizontalGap = cols > 1 ? remainingWidth / (cols - 1) : 0
  }

  return {
    '--card-width': `${cardWidth}px`,
    '--card-height': `${cardHeight}px`,
    '--h-gap': `${Math.max(horizontalGap, minGap)}px`,
    '--v-gap': `${Math.max(verticalGap, minGap)}px`,
  }
})

// Resize observer to track container size
let resizeObserver: ResizeObserver | null = null

function updateContainerSize() {
  if (gridContainerRef.value) {
    const rect = gridContainerRef.value.getBoundingClientRect()
    containerSize.value = { width: rect.width, height: rect.height }
  }
}

watch(gridLayout, () => {
  nextTick(updateContainerSize)
})

const layouts = [
  { label: '1宫格', value: '1x1' as const, icon: markRaw(SquareOutline) },
  { label: '4宫格', value: '2x2' as const, icon: markRaw(GridOutline) },
  { label: '9宫格', value: '3x3' as const, icon: markRaw(AppsOutline) }
]

const layoutOptions = [
  { label: '1宫格', value: '1x1' },
  { label: '4宫格', value: '2x2' },
  { label: '9宫格', value: '3x3' }
]

const config = ref({
  defaultLayout: '2x2',
  autoRotate: false,
  rotateInterval: 30,
  showTime: true,
  showLocation: true
})

// Available cameras
const availableCameras = ref<Camera[]>([
  { id: '1', name: '园区入口-01', location: '主园区', thumbnail: 'https://images.unsplash.com/photo-1557597774-9d273605dfa9?w=400&h=225&fit=crop', online: true },
  { id: '2', name: '大厅出口-01', location: 'A栋', thumbnail: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=225&fit=crop', online: true },
  { id: '3', name: '员工通道-02', location: 'B区', thumbnail: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=225&fit=crop', online: true },
  { id: '4', name: '装卸平台-04', location: '南门', thumbnail: 'https://images.unsplash.com/photo-1564182842519-8a3b2af3e228?w=400&h=225&fit=crop', online: false },
  { id: '5', name: '仓储内部-02', location: 'C栋', thumbnail: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400&h=225&fit=crop', online: true },
  { id: '6', name: '停车场-01', location: '地下', thumbnail: 'https://images.unsplash.com/photo-1573348722427-f1d6819fdf98?w=400&h=225&fit=crop', online: true },
  { id: '7', name: '会议室-01', location: 'B栋', thumbnail: 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=400&h=225&fit=crop', online: true },
  { id: '8', name: '研发中心-01', location: 'D栋', thumbnail: 'https://images.unsplash.com/photo-1497215842964-222b430dc094?w=400&h=225&fit=crop', online: true },
  { id: '9', name: '食堂入口-01', location: 'E区', thumbnail: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=225&fit=crop', online: true }
])

// Grid slots with initial cameras
const gridSlots = ref<GridSlot[]>([
  { camera: availableCameras.value[0] },
  { camera: availableCameras.value[1] },
  { camera: availableCameras.value[2] },
  { camera: availableCameras.value[3] },
  { camera: null },
  { camera: null },
  { camera: null },
  { camera: null },
  { camera: null }
])

const gridSize = computed(() => {
  switch (gridLayout.value) {
    case '1x1': return 1
    case '2x2': return 4
    case '3x3': return 9
    default: return 4
  }
})

// Only show slots based on current grid layout
const visibleSlots = computed(() => {
  return gridSlots.value.slice(0, gridSize.value)
})

const filteredCameras = computed(() => {
  const usedIds = new Set(gridSlots.value.filter(s => s.camera).map(s => s.camera!.id))
  return availableCameras.value.filter(cam => {
    if (usedIds.has(cam.id)) return false
    if (searchCamera.value) {
      const q = searchCamera.value.toLowerCase()
      return cam.name.toLowerCase().includes(q) || cam.location.toLowerCase().includes(q)
    }
    return true
  })
})

// Get camera options for select, excluding cameras used in other slots
function getCameraOptions(currentIndex: number) {
  const usedIds = new Set(
    gridSlots.value
      .filter((s, i) => s.camera && i !== currentIndex)
      .map(s => s.camera!.id)
  )
  return availableCameras.value
    .filter(cam => !usedIds.has(cam.id))
    .map(cam => ({
      label: `${cam.name} - ${cam.location}`,
      value: cam.id,
      disabled: !cam.online
    }))
}

// Update slot camera by id
function updateSlotCamera(index: number, cameraId: string | null) {
  if (cameraId === null) {
    gridSlots.value[index].camera = null
  } else {
    const camera = availableCameras.value.find(c => c.id === cameraId)
    if (camera) {
      gridSlots.value[index].camera = camera
    }
  }
}

function selectSlot(index: number) {
  selectedSlot.value = index
}

function openCameraSelect(index: number) {
  selectedSlot.value = index
  showSelectModal.value = true
}

function addCamera(camera: Camera) {
  if (selectedSlot.value !== null) {
    gridSlots.value[selectedSlot.value].camera = camera
  }
  showSelectModal.value = false
  selectedSlot.value = null
}

function removeCamera(index: number) {
  gridSlots.value[index].camera = null
}

function playFullscreen(camera: Camera) {
  message.info(`全屏播放: ${camera.name}`)
}

function saveConfig() {
  gridLayout.value = config.value.defaultLayout as '1x1' | '2x2' | '3x3'
  showConfigModal.value = false
  message.success('配置已保存')
}

// Update current time
let timeInterval: number
function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)

  // Set up resize observer
  nextTick(() => {
    updateContainerSize()
    if (gridContainerRef.value) {
      resizeObserver = new ResizeObserver(() => {
        updateContainerSize()
      })
      resizeObserver.observe(gridContainerRef.value)
    }
  })
  // 为现有摄像头连接 WebSocket
  gridSlots.value.forEach((slot: GridSlot) => {
    if (slot.camera) {
      connectCameraWs(slot.camera.id)
    }
  })
})

onUnmounted(() => {
  clearInterval(timeInterval)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  
  // 断开所有 WebSocket 连接
  wsClients.value.forEach(client => client.disconnect())
  wsClients.value.clear()
})
</script>

<style scoped>
.video-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: var(--spacing-lg);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  flex-shrink: 0;
}

.page-header__info {
  flex: 1;
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
  gap: var(--spacing-md);
}

/* Video Grid Container */
.video-grid {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  overflow: hidden;
}

/* 1x1: Single video centered with calculated size */
.video-grid--1x1 {
  width: 100%;
  height: 100%;
}

.video-grid--1x1 .video-slot {
  width: var(--card-width, 100%);
  height: var(--card-height, auto);
  background: #1a1a2e;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.video-grid--1x1 .video-slot__ratio {
  width: 100%;
  height: 100%;
}

/* 2x2 and 3x3: Grid with calculated card sizes and gaps */
.video-grid--2x2,
.video-grid--3x3 {
  display: grid;
  width: 100%;
  height: 100%;
  align-content: center;
  justify-content: center;
}

.video-grid--2x2 {
  grid-template-columns: repeat(2, var(--card-width, 1fr));
  grid-template-rows: repeat(2, var(--card-height, 1fr));
  column-gap: var(--h-gap, 8px);
  row-gap: var(--v-gap, 8px);
}

.video-grid--3x3 {
  grid-template-columns: repeat(3, var(--card-width, 1fr));
  grid-template-rows: repeat(3, var(--card-height, 1fr));
  column-gap: var(--h-gap, 6px);
  row-gap: var(--v-gap, 6px);
}

/* Video Slot */
.video-slot {
  background: #1a1a2e;
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all 0.2s;
  width: 100%;
  height: 100%;
}

.video-slot--selected {
  box-shadow: 0 0 0 2px var(--primary-color);
}

/* 16:9 Aspect Ratio Container */
.video-slot__ratio {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a2e;
}

.video-slot__video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-slot__info-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.video-slot__top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-sm);
}

.video-slot__live {
  padding: 2px 8px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
  letter-spacing: 1px;
}

.video-slot__actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: auto;
}

.video-slot:hover .video-slot__actions {
  opacity: 1;
}

.video-slot__bottom-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
}

.video-slot__name-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-slot__name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: #fff;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
}

.status-dot--online {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.video-slot__time {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.8);
}

/* No Signal State */
.video-slot__no-signal {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  color: rgba(255, 255, 255, 0.4);
  font-size: var(--font-size-sm);
}

/* Config Grid */
.config-grid {
  display: grid;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
}

.config-grid--1x1 {
  grid-template-columns: 1fr;
}

.config-grid--2x2 {
  grid-template-columns: repeat(2, 1fr);
}

.config-grid--3x3 {
  grid-template-columns: repeat(3, 1fr);
}

.config-slot {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.config-slot__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
}

.config-slot--has-camera .config-slot__label {
  color: var(--primary-color);
}

/* Camera Select List */
.camera-select-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.camera-select-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.camera-select-item:hover {
  background: var(--bg-hover);
}

.camera-select-item__thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.camera-select-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.camera-select-item__name {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.camera-select-item__location {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.camera-select-item__status {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.camera-select-item__status.online {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
