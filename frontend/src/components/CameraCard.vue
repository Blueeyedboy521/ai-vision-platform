<template>
  <div class="camera-card" @click="$emit('detail', camera)">
    <!-- Gradient Border Overlay -->
    <div class="camera-card__border-glow"></div>
    
    <!-- Preview Section -->
    <div class="camera-card__preview">
      <img :src="camera.thumbnail" :alt="camera.name" class="camera-card__image" />
      <div class="camera-card__overlay"></div>
      <span
        class="camera-card__status"
        :class="{ 'camera-card__status--online': camera.online }"
      >
        <span class="camera-card__status-dot"></span>
        {{ camera.online ? 'ONLINE' : 'OFFLINE' }}
      </span>
      <!-- Play Icon on Hover -->
      <div class="camera-card__play" @click.stop="emit('play', camera)">
        <n-icon :size="32">
          <PlayCircleOutline v-if="!props.isPlaying" />
          <PlayCircleOutline v-else />
        </n-icon>
      </div>
    </div>
    
    <!-- Info Section -->
    <div class="camera-card__info">
      <div class="camera-card__header">
        <span class="camera-card__name">{{ camera.name }}</span>
        <div v-if="camera.algorithmEnabled" class="camera-card__algo-badge">
          <n-icon :size="14" color="#4318FF">
            <ShieldCheckmarkOutline />
          </n-icon>
        </div>
      </div>
      <div class="camera-card__location">
        <n-icon :size="14" class="camera-card__location-icon">
          <LocationOutline />
        </n-icon>
        <span>{{ camera.location }}</span>
      </div>
      <div class="camera-card__footer">
        <div class="camera-card__ip">
          <n-icon :size="14" class="camera-card__ip-icon">
            <DesktopOutline />
          </n-icon>
          <code>{{ camera.ip }}</code>
        </div>
        <div class="camera-card__footer-right">
          <span
            class="camera-card__inference"
            :class="{
              'camera-card__inference--on': camera.inferenceStarted,
              'camera-card__inference--off': !camera.inferenceStarted
            }"
          >
            <span class="camera-card__inference-dot"></span>
            {{ camera.inferenceStarted ? '推理中' : '未启动推理' }}
          </span>
          <button
            class="camera-card__inference-btn"
            type="button"
            @click.stop="emit('toggleInference', camera)"
          >
            {{ camera.inferenceStarted ? '停止推理' : '启动推理' }}
          </button>
          <span class="camera-card__detail">
            详情配置
            <n-icon :size="14"><ChevronForwardOutline /></n-icon>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { 
  LocationOutline, 
  ShieldCheckmarkOutline, 
  DesktopOutline,
  PlayCircleOutline,
  ChevronForwardOutline
} from '@vicons/ionicons5'
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
  inferenceStarted?: boolean
}

const props = defineProps<{
  camera: CameraInfo
  isPlaying?: boolean
}>()

const emit = defineEmits<{
  (e: 'detail', camera: CameraInfo): void
  (e: 'play', camera: CameraInfo): void
  (e: 'toggleInference', camera: CameraInfo): void
}>()
</script>

<style scoped>
.camera-card {
  position: relative;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-color);
}

/* Gradient Border Glow Effect */
.camera-card__border-glow {
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background: linear-gradient(135deg, transparent 0%, transparent 100%);
  z-index: -1;
  opacity: 0;
  transition: all 0.4s ease;
}

.camera-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 
    0 20px 40px -12px rgba(67, 24, 255, 0.25),
    0 0 0 1px rgba(67, 24, 255, 0.1);
  border-color: transparent;
}

.camera-card:hover .camera-card__border-glow {
  opacity: 1;
  background: linear-gradient(
    135deg,
    rgba(67, 24, 255, 0.6) 0%,
    rgba(99, 102, 241, 0.4) 50%,
    rgba(139, 92, 246, 0.6) 100%
  );
}

/* Preview Section */
.camera-card__preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: #1a1a2e;
}

.camera-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.camera-card:hover .camera-card__image {
  transform: scale(1.1);
}

.camera-card__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    transparent 0%,
    transparent 50%,
    rgba(0, 0, 0, 0.4) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.camera-card:hover .camera-card__overlay {
  opacity: 1;
}

/* Status Badge */
.camera-card__status {
  position: absolute;
  top: var(--spacing-md);
  left: var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.5px;
  color: #fff;
  background: rgba(239, 68, 68, 0.9);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
}

.camera-card__status--online {
  background: rgba(34, 197, 94, 0.9);
}

.camera-card__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

/* Play Button on Hover */
.camera-card__play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0);
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-full);
  color: var(--primary-color);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(67, 24, 255, 0.3);
}

.camera-card:hover .camera-card__play {
  transform: translate(-50%, -50%) scale(1);
  opacity: 1;
}

/* Info Section */
.camera-card__info {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.camera-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.camera-card__name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.camera-card:hover .camera-card__name {
  color: var(--primary-color);
}

.camera-card__algo-badge {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  background: rgba(67, 24, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.camera-card:hover .camera-card__algo-badge {
  background: rgba(67, 24, 255, 0.2);
  transform: rotate(10deg) scale(1.1);
}

.camera-card__location {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.camera-card__location-icon {
  color: var(--primary-color);
  transition: transform 0.3s ease;
}

.camera-card:hover .camera-card__location-icon {
  transform: scale(1.2);
}

.camera-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.camera-card__footer-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.camera-card__inference {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
}

.camera-card__inference-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
}

.camera-card__inference--on {
  border-color: var(--success-color);
  color: var(--success-color);
}

.camera-card__inference--on .camera-card__inference-dot {
  background: var(--success-color);
}

.camera-card__inference-btn {
  border: none;
  background: transparent;
  font-size: var(--font-size-xs);
  color: var(--primary-color);
  cursor: pointer;
  padding: 0;
}

.camera-card__inference-btn:hover {
  text-decoration: underline;
}

.camera-card__ip {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.camera-card__ip code {
  font-family: var(--font-mono);
  background: var(--bg-page);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
}

.camera-card__ip-icon {
  color: var(--text-muted);
}

.camera-card__detail {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
  transition: all 0.3s ease;
}

.camera-card:hover .camera-card__detail {
  gap: var(--spacing-sm);
}

/* ===== Active/Click State ===== */
.camera-card:active {
  transform: translateY(-4px) scale(1);
}

/* ===== Animations ===== */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.camera-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(67, 24, 255, 0.05),
    transparent
  );
  background-size: 200% 100%;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 1;
}

.camera-card:hover::before {
  opacity: 1;
  animation: shimmer 2s ease-in-out infinite;
}
</style>
