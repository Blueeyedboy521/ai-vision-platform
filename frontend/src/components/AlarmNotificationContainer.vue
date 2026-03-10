<template>
  <!-- 右下角告警气泡 -->
  <div class="alarm-toast-container">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="alarm-toast"
      :class="`alarm-toast--${t.level}`"
      @click="openDetailFromToast(t)"
    >
      <div class="alarm-toast__thumb" v-if="t.thumb">
        <img :src="t.thumb" alt="告警缩略图" />
      </div>
      <div class="alarm-toast__content">
        <div class="alarm-toast__title-row">
          <div class="alarm-toast__title">{{ t.title }}</div>
          <div class="alarm-toast__level-tag" :class="`level-${t.level}`">
            {{ (t.level || '').toLowerCase() === 'danger' || (t.level || '').toLowerCase() === 'critical' ? '高危' : ((t.level || '').toLowerCase() === 'warning' ? '一般' : '提示') }}
          </div>
        </div>
        <div class="alarm-toast__subtitle">{{ t.subtitle }}</div>
      </div>
    </div>
  </div>

  <!-- 告警详情弹框（简版：截图 + 关键信息） -->
  <n-modal
    v-model:show="showDetailModal"
    preset="card"
    title="告警详情"
    :style="{ width: '900px' }"
    :bordered="false"
  >
    <AlarmDetail :alarm="currentAlarmDetail" />
  </n-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NModal } from 'naive-ui'
import { useAlarmNotification } from '@/composables/useAlarmNotification'
import AlarmDetail from '@/components/AlarmDetail.vue'

const {
  toasts,
  showDetailModal,
  currentAlarmDetail,
  openDetailFromToast,
} = useAlarmNotification()

const detailLevel = computed(() => {
  const lvl = (currentAlarmDetail.value?.level || currentAlarmDetail.value?.alert_level || 'info').toLowerCase()
  if (lvl === 'danger') return 'danger'
  if (lvl === 'critical') return 'critical'
  if (lvl === 'warning') return 'warning'
  return 'info'
})

const levelText = computed(() => {
  const map: Record<string, string> = {
    info: '提示',
    warning: '一般',
    danger: '高危',
    critical: '高危',
  }
  return map[detailLevel.value] || '提示'
})

</script>

<style scoped>
.alarm-toast-container {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.alarm-toast {
  pointer-events: auto;
  min-width: 360px;
  max-width: 460px;
  background: var(--bg-card);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.alarm-toast:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.22);
  border-color: var(--primary-color);
}

.alarm-toast__thumb {
  width: 72px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.06);
  flex: 0 0 72px;
}

.alarm-toast__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.alarm-toast__content {
  flex: 1;
  min-width: 0;
}

.alarm-toast__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-toast__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 2px;
}

.alarm-toast__level-tag {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
}

.alarm-toast__level-tag.level-warning {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
}

.alarm-toast__level-tag.level-danger,
.alarm-toast__level-tag.level-critical {
  color: #b91c1c;
  background: rgba(239, 68, 68, 0.12);
}

.alarm-toast__subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.snapshot-title {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
</style>

