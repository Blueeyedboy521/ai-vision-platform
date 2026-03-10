<template>
  <n-config-provider :theme="currentTheme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <AppLayout />
      <!-- 全局告警 WS 提示与详情弹框 -->
      <AlarmNotificationContainer />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NMessageProvider, darkTheme, zhCN, dateZhCN } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useAppStore } from '@/stores/app'
import AppLayout from '@/components/AppLayout.vue'
import AlarmNotificationContainer from '@/components/AlarmNotificationContainer.vue'
import { useAppWebSocket } from '@/composables/useAppWebSocket'

const appStore = useAppStore()
const currentTheme = computed(() => appStore.isDarkMode ? darkTheme : null)

// 初始化全局告警 WebSocket
useAppWebSocket()

/**
 * Naive UI 全局主题覆盖
 * 统一使用项目主题色 #4318FF
 * 
 * 注意：common.primaryColor 是最关键的设置，
 * Naive UI 会自动从这个颜色派生按钮、开关等组件的颜色
 */
const themeOverrides: GlobalThemeOverrides = {
  common: {
    // 主色调 - Naive UI 会从这里派生所有 primary 相关的颜色
    primaryColor: '#4318FF',
    primaryColorHover: '#5a3eff',
    primaryColorPressed: '#3510d9',
    primaryColorSuppl: '#4318FF',
    // 功能色
    successColor: '#22c55e',
    successColorHover: '#4ade80',
    successColorPressed: '#16a34a',
    warningColor: '#f97316',
    warningColorHover: '#fb923c',
    warningColorPressed: '#ea580c',
    errorColor: '#ef4444',
    errorColorHover: '#f87171',
    errorColorPressed: '#dc2626',
    infoColor: '#06b6d4',
    infoColorHover: '#22d3ee',
    infoColorPressed: '#0891b2',
    // 边框和圆角
    borderRadius: '8px',
    borderRadiusSmall: '6px'
  }
}
</script>

<style>
/**
 * App 级别的样式补充
 * 主要样式已移至 assets/styles/
 */

/* 兼容旧代码的 CSS 变量别名 */
:root {
  --bg-sidebar: var(--bg-card);
  --bg-header: var(--bg-card);
  --chart-grid: var(--border-color);
  --hover-shadow: rgba(0, 0, 0, 0.06);
  --offline-color: var(--border-color);
}

html.dark {
  --bg-sidebar: #1e1e22;
  --bg-header: var(--bg-card);
  --chart-grid: var(--border-color);
  --hover-shadow: rgba(0, 0, 0, 0.3);
  --offline-color: var(--border-color);
}
</style>
