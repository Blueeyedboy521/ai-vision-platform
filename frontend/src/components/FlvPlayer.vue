<template>
  <div class="flv-player">
    <video
      ref="videoRef"
      class="flv-player__video"
      controls
      autoplay
      muted
      playsinline
    ></video>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import flvjs from 'flv.js'

const props = defineProps<{
  url: string
}>()

const emit = defineEmits<{
  (e: 'fatal'): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
let flvPlayer: flvjs.Player | null = null
let retryCount = 0
const maxRetry = 6
const retryIntervalMs = 5000

function destroyPlayer() {
  if (flvPlayer) {
    try {
      flvPlayer.off(flvjs.Events.ERROR, onPlayerError as any)
    } catch {
      // ignore
    }
    flvPlayer.destroy()
    flvPlayer = null
  }
}

function onPlayerError() {
  destroyPlayer()
  retryCount += 1
  if (retryCount < maxRetry) {
    setTimeout(() => {
      initPlayer()
    }, retryIntervalMs)
  } else {
    emit('fatal')
  }
}

function initPlayer() {
  destroyPlayer()
  if (!flvjs.isSupported() || !videoRef.value || !props.url) return

  flvPlayer = flvjs.createPlayer({
    type: 'flv',
    url: props.url,
    isLive: true,
  })
  flvPlayer.attachMediaElement(videoRef.value)
  flvPlayer.load()
  const playRet = flvPlayer.play()
  if (playRet && typeof (playRet as any).catch === 'function') {
    ;(playRet as Promise<void>).catch(() => {
      // autoplay 失败时静默处理，交给用户手动点击播放
    })
  }
  try {
    flvPlayer.on(flvjs.Events.ERROR, onPlayerError as any)
  } catch {
    // ignore
  }
}

onMounted(() => {
  retryCount = 0
  initPlayer()
})
onBeforeUnmount(() => {
  destroyPlayer()
  retryCount = 0
})

watch(
  () => props.url,
  () => {
    retryCount = 0
    initPlayer()
  }
)
</script>

<style scoped>
.flv-player {
  width: 100%;
  height: 100%;
}

.flv-player__video {
  width: 100%;
  height: 100%;
  background: #000;
  display: block;
}
</style>

