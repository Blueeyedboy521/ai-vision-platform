<template>
  <div class="camera-card">
    <div class="camera-preview">
      <img :src="camera.thumbnail" :alt="camera.name" class="camera-image" />
      <span
        class="status-badge"
        :class="camera.online ? 'online' : 'offline'"
      >
        {{ camera.online ? 'ONLINE' : 'OFFLINE' }}
      </span>
    </div>
    <div class="camera-info">
      <div class="camera-name-row">
        <span class="camera-name">{{ camera.name }}</span>
        <div class="camera-algo-badge" v-if="camera.algorithmEnabled">
          <n-icon :size="14" color="#4318FF">
            <ShieldCheckmarkOutline />
          </n-icon>
        </div>
      </div>
      <div class="camera-location">
        <n-icon :size="14" color="#4318FF">
          <LocationOutline />
        </n-icon>
        <span>{{ camera.location }}</span>
      </div>
      <div class="camera-footer">
        <div class="camera-ip">
          <n-icon :size="14" :color="appStore.isDarkMode ? '#9090a0' : '#999'">
            <DesktopOutline />
          </n-icon>
          <span>{{ camera.ip }}</span>
        </div>
        <span class="camera-detail-link" @click="$emit('detail', camera)">详情配置</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { LocationOutline, ShieldCheckmarkOutline, DesktopOutline } from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

export interface CameraInfo {
  id: string
  name: string
  location: string
  ip: string
  thumbnail: string
  online: boolean
  algorithmEnabled: boolean
}

defineProps<{
  camera: CameraInfo
}>()

defineEmits<{
  (e: 'detail', camera: CameraInfo): void
}>()
</script>

<style scoped>
.camera-card {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: box-shadow 0.3s, transform 0.2s, border-color 0.3s;
  cursor: pointer;
}

.camera-card:hover {
  box-shadow: 0 8px 24px var(--hover-shadow);
  transform: translateY(-2px);
  border-color: rgba(67, 24, 255, 0.3);
}

.camera-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: #1a1a2e;
}

.camera-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.status-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
}

.status-badge.online {
  background: #22c55e;
}

.status-badge.offline {
  background: #ef4444;
}

.camera-info {
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.camera-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.camera-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.camera-algo-badge {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(67, 24, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.camera-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.camera-ip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}

.camera-detail-link {
  font-size: 13px;
  color: #4318FF;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.camera-detail-link:hover {
  opacity: 0.7;
}
</style>
