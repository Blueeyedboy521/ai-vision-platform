<template>
  <n-config-provider :theme="currentTheme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <AppLayout />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import { useAppStore } from '@/stores/app'
import AppLayout from '@/components/AppLayout.vue'

const appStore = useAppStore()
const currentTheme = computed(() => appStore.isDarkMode ? darkTheme : null)
</script>

<style>
:root {
  --bg-page: #f5f7fa;
  --bg-card: #ffffff;
  --bg-sidebar: #ffffff;
  --bg-header: #ffffff;
  --text-primary: #1a1a2e;
  --text-secondary: #a0aec0;
  --text-muted: #666666;
  --border-color: #f0f0f0;
  --border-light: #e8e8e8;
  --chart-grid: #f0f0f0;
  --hover-shadow: rgba(0, 0, 0, 0.06);
  --offline-color: #e8e8e8;
}

html.dark {
  --bg-page: #18181c;
  --bg-card: #242428;
  --bg-sidebar: #1e1e22;
  --bg-header: #242428;
  --text-primary: #e4e4e8;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --border-color: #333338;
  --border-light: #3a3a40;
  --chart-grid: #333338;
  --hover-shadow: rgba(0, 0, 0, 0.3);
  --offline-color: #3a3a40;
}

body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
  background: var(--bg-page);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}
</style>
