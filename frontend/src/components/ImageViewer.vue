<template>
  <n-modal
    :show="show"
    preset="card"
    title="图片查看"
    :style="{ width: '90vw', maxWidth: '1200px' }"
    :mask-closable="true"
    @update:show="(v: boolean) => !v && $emit('update:show', false)"
  >
    <div
      ref="containerRef"
      class="image-viewer"
      @wheel.prevent="onWheel"
      @mousedown="onMouseDown"
    >
      <div
        class="image-viewer__wrap"
        :style="wrapStyle"
      >
        <img
          v-if="src"
          ref="imgRef"
          :src="src"
          alt="预览"
          class="image-viewer__img"
          :style="imgStyle"
          draggable="false"
          @load="onImageLoad"
        />
        <!-- 前端绘制检测框 Overlay -->
        <div v-if="boxes.length" class="image-viewer__overlay">
          <div
            v-for="(box, idx) in boxes"
            :key="idx"
            class="image-viewer__bbox"
            :style="{
              left: box.left,
              top: box.top,
              width: box.width,
              height: box.height,
            }"
          >
            <span v-if="box.label" class="image-viewer__bbox-label">{{ box.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { CSSProperties } from 'vue'
import { NModal } from 'naive-ui'

const props = withDefaults(
  defineProps<{
    show: boolean
    src: string | null
    // 告警检测结果，用于在前端绘制检测框（可选）
    detections?: any[] | null
  }>(),
  { show: false, src: null, detections: null }
)

defineEmits<{
  (e: 'update:show', v: boolean): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const imgRef = ref<HTMLImageElement | null>(null)

const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)

// 原始图片尺寸，用于根据 bbox 做等比缩放
const naturalWidth = ref(0)
const naturalHeight = ref(0)

const minScale = 0.25
const maxScale = 5
const step = 0.15

const wrapStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transformOrigin: 'center center'
}))

const imgStyle = computed<CSSProperties>(() => ({
  maxWidth: '100%',
  maxHeight: '100%',
  objectFit: 'contain' as const,
  userSelect: 'none',
  pointerEvents: 'none',
}))

function onImageLoad() {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
  if (imgRef.value) {
    naturalWidth.value = imgRef.value.naturalWidth
    naturalHeight.value = imgRef.value.naturalHeight
  }
}

function onWheel(e: WheelEvent) {
  const delta = e.deltaY > 0 ? -step : step
  scale.value = Math.min(maxScale, Math.max(minScale, scale.value + delta))
}

let dragging = false
let startX = 0
let startY = 0
let startTx = 0
let startTy = 0

function onMouseDown(e: MouseEvent) {
  if (!props.src) return
  dragging = true
  startX = e.clientX
  startY = e.clientY
  startTx = translateX.value
  startTy = translateY.value
  const onMove = (e2: MouseEvent) => {
    if (!dragging) return
    translateX.value = startTx + e2.clientX - startX
    translateY.value = startTy + e2.clientY - startY
  }
  const onUp = () => {
    dragging = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

watch(
  () => props.show,
  (v) => {
    if (v) {
      scale.value = 1
      translateX.value = 0
      translateY.value = 0
    }
  }
)

type DrawBox = {
  left: string
  top: string
  width: string
  height: string
  label?: string
}

// 计算用于绘制的检测框（以百分比坐标表示，适配缩放）
const boxes = computed(() => {
  const dets = props.detections || []
  if (!dets || !dets.length || !naturalWidth.value || !naturalHeight.value) return []
  return dets
    .map((d: any) => {
      const bbox = d?.bbox || d?.box || []
      if (!bbox || bbox.length < 4) return null
      const [x1, y1, x2, y2] = bbox
      const w = naturalWidth.value
      const h = naturalHeight.value
      if (!w || !h) return null
      const leftPct = (x1 / w) * 100
      const topPct = (y1 / h) * 100
      const widthPct = ((x2 - x1) / w) * 100
      const heightPct = ((y2 - y1) / h) * 100
      const baseLabel = d.class_name || d.className || d.label || ''
      const rawConf = typeof d.confidence === 'number'
        ? d.confidence
        : (typeof d.score === 'number' ? d.score : null)
      const label = rawConf != null
        ? `${baseLabel} ${(rawConf as number).toFixed(2)}`
        : baseLabel
      const box: DrawBox = {
        left: `${leftPct}%`,
        top: `${topPct}%`,
        width: `${widthPct}%`,
        height: `${heightPct}%`,
        label,
      }
      return box
    })
    .filter((b): b is DrawBox => Boolean(b))
})
</script>

<style scoped>
.image-viewer {
  min-height: 60vh;
  max-height: 80vh;
  overflow: hidden;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
  border-radius: 8px;
}

.image-viewer:active {
  cursor: grabbing;
}

.image-viewer__wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.05s ease-out;
  position: relative;
}

.image-viewer__img {
  display: block;
  vertical-align: middle;
}

.image-viewer__overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.image-viewer__bbox {
  position: absolute;
  border: 2px solid #ff4d4f;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.4);
}

.image-viewer__bbox-label {
  position: absolute;
  left: 0;
  top: 0;
  transform: translateY(-100%);
  padding: 2px 6px;
  background: rgba(255, 77, 79, 0.9);
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
}
</style>
