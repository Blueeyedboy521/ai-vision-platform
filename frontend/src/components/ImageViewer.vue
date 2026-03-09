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
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NModal } from 'naive-ui'

const props = withDefaults(
  defineProps<{
    show: boolean
    src: string | null
  }>(),
  { show: false, src: null }
)

defineEmits<{
  (e: 'update:show', v: boolean): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const imgRef = ref<HTMLImageElement | null>(null)

const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)

const minScale = 0.25
const maxScale = 5
const step = 0.15

const wrapStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  transformOrigin: 'center center'
}))

const imgStyle = computed(() => ({
  maxWidth: '100%',
  maxHeight: '100%',
  objectFit: 'contain',
  userSelect: 'none',
  pointerEvents: 'none'
}))

function onImageLoad() {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
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
}

.image-viewer__img {
  display: block;
  vertical-align: middle;
}
</style>
