<template>
  <div class="stat-card card-border-xl">
    <div class="stat-header">
      <div class="stat-icon" :style="{ background: iconBg }">
        <n-icon :size="24" :color="iconColor">
          <component :is="icon" />
        </n-icon>
      </div>
      <div class="stat-trend" :style="{ color: trendUp ? '#22c55e' : '#ef4444' }">
        <n-icon :size="14">
          <TrendingUpOutline v-if="trendUp" />
          <TrendingDownOutline v-else />
        </n-icon>
        <span>{{ trend }}</span>
      </div>
    </div>
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { TrendingUpOutline, TrendingDownOutline } from '@vicons/ionicons5'
import type { Component } from 'vue'

defineProps<{
  icon: Component
  iconBg: string
  iconColor: string
  label: string
  value: string
  trend: string
  trendUp: boolean
}>()
</script>

<style scoped>
.stat-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  transition: box-shadow 0.3s, background 0.3s, transform 0.3s, border-color 0.3s;
  cursor: pointer;
  border-top: 3px solid transparent;
}

.stat-card:hover {
  box-shadow: 0 8px 24px var(--hover-shadow);
  transform: translateY(-4px);
  border-top-color: #4318FF;
}

.stat-card:hover .stat-icon {
  transform: scale(1.15);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
</style>
