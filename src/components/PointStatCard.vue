<template>
  <div class="point-stat-card" :style="{ borderLeftColor: accentColor }">
    <div class="point-stat-icon" :style="{ background: iconBg }">
      <n-icon :size="22" :color="accentColor">
        <component :is="icon" />
      </n-icon>
    </div>
    <div class="point-stat-content">
      <div class="point-stat-label">{{ label }}</div>
      <div class="point-stat-value" :style="{ color: accentColor }">{{ value }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import type { Component } from 'vue'

defineProps<{
  icon: Component
  iconBg: string
  accentColor: string
  label: string
  value: number | string
}>()
</script>

<style scoped>
.point-stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-card);
  border-radius: 12px;
  padding: 18px 20px;
  border: 1px solid var(--border-color);
  border-left: 3px solid transparent;
  transition: box-shadow 0.3s, background 0.3s, border-color 0.3s;
}

.point-stat-card:hover {
  box-shadow: 0 4px 16px var(--hover-shadow);
}

.point-stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.point-stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.point-stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.point-stat-value {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1.2;
}
</style>
