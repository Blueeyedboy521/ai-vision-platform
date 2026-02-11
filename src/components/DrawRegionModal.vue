<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    :bordered="false"
    :closable="true"
    :mask-closable="false"
    class="draw-region-modal"
    :style="{ width: '70vw', maxWidth: '1100px' }"
    :content-style="{ padding: 0, maxHeight: '70vh', overflow: 'hidden' }"
  >
    <template #header>
      <div class="draw-region-modal__header">
        <div class="draw-region-modal__header-icon">
          <n-icon :size="20"><ScanOutline /></n-icon>
        </div>
        <div class="draw-region-modal__header-text">
          <span class="draw-region-modal__title">绘制检测区域</span>
          <span class="draw-region-modal__subtitle">{{ algorithmName }} ({{ algorithmNameEn }})</span>
        </div>
      </div>
    </template>

    <div class="draw-region-modal__body">
      <!-- Canvas Container -->
      <div class="canvas-container">
        <div class="canvas-container__wrapper" ref="canvasContainerRef">
          <img 
            ref="imageRef"
            :src="imageSrc" 
            alt="Camera Preview" 
            class="canvas-container__image"
            @load="handleImageLoad"
          />
          <canvas 
            ref="canvasRef"
            class="canvas-container__canvas"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @contextmenu.prevent="handleRightClick"
          ></canvas>
        </div>
        
        <!-- Toolbar -->
        <div class="canvas-toolbar">
          <n-button 
            type="primary" 
            size="small"
            :disabled="isDrawing"
            @click="startDrawPolygon"
          >
            <template #icon>
              <n-icon><CreateOutline /></n-icon>
            </template>
            开始绘制多边形
          </n-button>
        </div>

        <!-- Action Buttons -->
        <div class="canvas-actions">
          <n-button 
            size="small" 
            @click="undoLastPoint" 
            :disabled="currentPoints.length === 0 && regions.length === 0"
            class="action-btn action-btn--undo"
          >
            <template #icon>
              <n-icon><ArrowUndoOutline /></n-icon>
            </template>
            撤销
          </n-button>
          <n-button 
            size="small" 
            type="error" 
            @click="clearAllRegions" 
            :disabled="regions.length === 0 && currentPoints.length === 0"
            class="action-btn action-btn--clear"
          >
            <template #icon>
              <n-icon><TrashOutline /></n-icon>
            </template>
            清除全部
          </n-button>
        </div>

        <!-- Drawing Hint -->
        <div v-if="isDrawing" class="canvas-hint">
          点击添加顶点，右键或双击完成绘制
        </div>
      </div>

      <!-- Region List -->
      <div class="region-list">
        <div 
          v-for="(region, index) in regions" 
          :key="index"
          class="region-item"
          :style="{ '--region-color': region.color }"
        >
          <span class="region-item__dot"></span>
          <span class="region-item__name">区域 #{{ index + 1 }} ({{ region.type }})</span>
          <n-button 
            text 
            size="tiny" 
            type="error"
            @click="removeRegion(index)"
          >
            <n-icon :size="14"><CloseOutline /></n-icon>
          </n-button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="draw-region-modal__footer">
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" @click="handleConfirm">
          确认保存
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { NModal, NButton, NIcon } from 'naive-ui'
import { 
  ScanOutline, 
  CreateOutline, 
  ArrowUndoOutline, 
  TrashOutline,
  CloseOutline
} from '@vicons/ionicons5'

interface Point {
  x: number
  y: number
}

interface Region {
  points: Point[]
  color: string
  type: string
}

const props = defineProps<{
  show: boolean
  imageSrc: string
  algorithmName: string
  algorithmNameEn?: string
  existingRegions?: Region[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'save', regions: Region[]): void
}>()

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

// Refs
const canvasContainerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

// State
const regions = ref<Region[]>([])
const currentPoints = ref<Point[]>([])
const isDrawing = ref(false)
const imageLoaded = ref(false)

// Colors for regions
const regionColors = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']
let colorIndex = 0

function getNextColor() {
  const color = regionColors[colorIndex % regionColors.length]
  colorIndex++
  return color
}

function handleImageLoad() {
  imageLoaded.value = true
  nextTick(() => {
    initCanvas()
    if (props.existingRegions) {
      regions.value = [...props.existingRegions]
      redrawCanvas()
    }
  })
}

function initCanvas() {
  const canvas = canvasRef.value
  const image = imageRef.value
  if (!canvas || !image) return

  // Get the actual rendered size of the image
  const imageWidth = image.offsetWidth
  const imageHeight = image.offsetHeight
  
  // Set canvas internal resolution to match image display size
  canvas.width = imageWidth
  canvas.height = imageHeight
  
  // Also set CSS size to ensure 1:1 pixel mapping
  canvas.style.width = `${imageWidth}px`
  canvas.style.height = `${imageHeight}px`
  
  console.log('Canvas initialized:', imageWidth, 'x', imageHeight)
}

function startDrawPolygon() {
  isDrawing.value = true
  currentPoints.value = []
}

// Snap distance threshold (in pixels)
const SNAP_DISTANCE = 15

function getCanvasCoordinates(e: MouseEvent): { x: number; y: number } {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }

  const rect = canvas.getBoundingClientRect()
  
  // Direct mapping - since we set canvas size = CSS size, scale should be 1:1
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  return { x, y }
}

function getDistance(p1: Point, p2: Point): number {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2))
}

function isNearStartPoint(point: Point): boolean {
  if (currentPoints.value.length < 3) return false
  const startPoint = currentPoints.value[0]
  return getDistance(point, startPoint) <= SNAP_DISTANCE
}

function handleMouseDown(e: MouseEvent) {
  if (!isDrawing.value) return
  
  const { x, y } = getCanvasCoordinates(e)
  const clickPoint = { x, y }
  
  // Check if clicking near start point to close the polygon
  if (currentPoints.value.length >= 3 && isNearStartPoint(clickPoint)) {
    finishDrawing()
    return
  }
  
  currentPoints.value.push(clickPoint)
  redrawCanvas()
}

function handleMouseMove(e: MouseEvent) {
  if (!isDrawing.value || currentPoints.value.length === 0) return
  redrawCanvas(e)
}

function handleMouseUp(e: MouseEvent) {
  // Double click to finish
  if (e.detail === 2 && currentPoints.value.length >= 3) {
    finishDrawing()
  }
}

function handleRightClick() {
  if (isDrawing.value && currentPoints.value.length >= 3) {
    finishDrawing()
  }
}

function finishDrawing() {
  if (currentPoints.value.length < 3) return

  const newRegion: Region = {
    points: [...currentPoints.value],
    color: getNextColor(),
    type: regions.value.length % 2 === 0 ? '入侵区' : '排查区'
  }
  
  regions.value.push(newRegion)
  currentPoints.value = []
  isDrawing.value = false
  redrawCanvas()
}

function undoLastPoint() {
  if (currentPoints.value.length > 0) {
    currentPoints.value.pop()
    redrawCanvas()
  } else if (regions.value.length > 0) {
    regions.value.pop()
    redrawCanvas()
  }
}

function clearAllRegions() {
  regions.value = []
  currentPoints.value = []
  isDrawing.value = false
  redrawCanvas()
}

function removeRegion(index: number) {
  regions.value.splice(index, 1)
  redrawCanvas()
}

function setFullScreen() {
  const canvas = canvasRef.value
  if (!canvas) return

  currentPoints.value = []
  isDrawing.value = false

  const fullScreenRegion: Region = {
    points: [
      { x: 0, y: 0 },
      { x: canvas.width, y: 0 },
      { x: canvas.width, y: canvas.height },
      { x: 0, y: canvas.height }
    ],
    color: getNextColor(),
    type: '全屏区'
  }

  regions.value = [fullScreenRegion]
  redrawCanvas()
}

function redrawCanvas(mouseEvent?: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Draw existing regions
  regions.value.forEach(region => {
    drawPolygon(ctx, region.points, region.color, true)
  })

  // Draw current polygon being drawn
  if (currentPoints.value.length > 0) {
    const color = regionColors[regions.value.length % regionColors.length]
    const startPoint = currentPoints.value[0]
    
    // Check if mouse is near start point for snap indicator
    let nearStart = false
    let mouseX = 0
    let mouseY = 0
    
    if (mouseEvent && isDrawing.value) {
      const coords = getCanvasCoordinates(mouseEvent)
      mouseX = coords.x
      mouseY = coords.y
      nearStart = currentPoints.value.length >= 3 && isNearStartPoint({ x: mouseX, y: mouseY })
    }
    
    // Draw lines between points
    ctx.beginPath()
    ctx.moveTo(startPoint.x, startPoint.y)
    
    for (let i = 1; i < currentPoints.value.length; i++) {
      ctx.lineTo(currentPoints.value[i].x, currentPoints.value[i].y)
    }

    // Draw line to mouse position (snap to start if near)
    if (mouseEvent && isDrawing.value) {
      if (nearStart) {
        ctx.lineTo(startPoint.x, startPoint.y)
      } else {
        ctx.lineTo(mouseX, mouseY)
      }
    }

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.stroke()

    // Draw points
    currentPoints.value.forEach((point, index) => {
      ctx.beginPath()
      
      // Highlight start point when mouse is near (for snap indicator)
      if (index === 0 && nearStart) {
        // Draw larger glowing circle for snap indicator
        ctx.arc(point.x, point.y, 12, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(34, 197, 94, 0.3)'
        ctx.fill()
        ctx.beginPath()
        ctx.arc(point.x, point.y, 8, 0, Math.PI * 2)
        ctx.fillStyle = '#22c55e'
        ctx.fill()
      } else {
        ctx.arc(point.x, point.y, 5, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
      }
    })
    
    // Draw snap hint text when near start
    if (nearStart) {
      ctx.font = '12px sans-serif'
      ctx.fillStyle = '#22c55e'
      ctx.fillText('点击闭合', startPoint.x + 15, startPoint.y - 10)
    }
  }
}

function drawPolygon(ctx: CanvasRenderingContext2D, points: Point[], color: string, fill: boolean) {
  if (points.length < 3) return

  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  
  ctx.closePath()

  if (fill) {
    ctx.fillStyle = color + '40' // 25% opacity
    ctx.fill()
  }

  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.stroke()

  // Draw corner points
  points.forEach(point => {
    ctx.beginPath()
    ctx.arc(point.x, point.y, 4, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()
  })
}

function handleCancel() {
  emit('update:show', false)
}

function handleConfirm() {
  emit('save', regions.value)
  emit('update:show', false)
}

// Watch for modal open
watch(() => props.show, (val) => {
  if (val) {
    colorIndex = 0
    if (props.existingRegions) {
      regions.value = [...props.existingRegions]
    } else {
      regions.value = []
    }
    currentPoints.value = []
    isDrawing.value = false
    nextTick(() => {
      if (imageLoaded.value) {
        initCanvas()
        redrawCanvas()
      }
    })
  }
})

// Handle window resize
onMounted(() => {
  window.addEventListener('resize', () => {
    if (showModal.value) {
      nextTick(() => {
        initCanvas()
        redrawCanvas()
      })
    }
  })
})
</script>

<style scoped>
.draw-region-modal {
  max-height: 80vh;
}

.draw-region-modal :deep(.n-card) {
  max-height: 80vh;
}

.draw-region-modal :deep(.n-card__content) {
  max-height: calc(80vh - 140px);
  overflow: hidden;
}

.draw-region-modal__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.draw-region-modal__header-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  background: rgba(67, 24, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
}

.draw-region-modal__header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.draw-region-modal__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.draw-region-modal__subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.draw-region-modal__body {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  max-height: calc(70vh - 140px);
  overflow: hidden;
}

/* Canvas Container */
.canvas-container {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #1a1a2e;
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-container__wrapper {
  position: relative;
  max-width: 100%;
  max-height: 100%;
}

.canvas-container__image {
  max-width: 100%;
  max-height: calc(70vh - 200px);
  display: block;
}

.canvas-container__canvas {
  position: absolute;
  top: 0;
  left: 0;
  cursor: crosshair;
}

/* Toolbar */
.canvas-toolbar {
  position: absolute;
  top: var(--spacing-md);
  left: var(--spacing-md);
  display: flex;
  gap: var(--spacing-sm);
}

/* Action Buttons */
.canvas-actions {
  position: absolute;
  bottom: var(--spacing-md);
  right: var(--spacing-md);
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn--undo {
  background: rgba(255, 255, 255, 0.95) !important;
  color: #333 !important;
  border: 1px solid #ddd !important;
  font-weight: 500;
}

.action-btn--undo:hover:not(:disabled) {
  background: #fff !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

.action-btn--clear {
  background: rgba(239, 68, 68, 0.9) !important;
  border-color: transparent !important;
}

.action-btn--clear:hover:not(:disabled) {
  background: #ef4444 !important;
}

/* Drawing Hint */
.canvas-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  pointer-events: none;
}

/* Region List */
.region-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.region-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-md);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
}

.region-item__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--region-color);
}

.region-item__name {
  color: var(--text-primary);
}

/* Footer */
.draw-region-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}
</style>
