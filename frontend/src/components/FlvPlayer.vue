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

const videoRef = ref<HTMLVideoElement | null>(null)
let flvPlayer: flvjs.Player | null = null

function destroyPlayer() {
  if (flvPlayer) {
    flvPlayer.destroy()
    flvPlayer = null
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
  flvPlayer.play().catch(() => {
    // autoplay 失败时静默处理，交给用户手动点击播放
  })
}

onMounted(initPlayer)
onBeforeUnmount(destroyPlayer)

watch(
  () => props.url,
  () => {
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

