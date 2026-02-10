<template>
  <div class="app-header" :style="headerStyle">
    <div class="header-left">
      <n-button quaternary circle @click="appStore.toggleSidebar">
        <template #icon>
          <n-icon :size="20" :color="appStore.isDarkMode ? '#ffffff' : '#2d3748'">
            <MenuOutline />
          </n-icon>
        </template>
      </n-button>
      <span class="page-title">{{ currentTitle }}</span>
    </div>
    <div class="header-right">
      <n-input
        placeholder="搜索设备、算法或日志..."
        style="width: 260px;"
        round
        size="small"
      >
        <template #prefix>
          <n-icon :size="16" :color="appStore.isDarkMode ? '#ffffff' : '#a0aec0'">
            <SearchOutline />
          </n-icon>
        </template>
      </n-input>
      <n-button quaternary circle @click="appStore.toggleDarkMode">
        <template #icon>
          <n-icon :size="20" :color="appStore.isDarkMode ? '#ffffff' : '#2d3748'">
            <MoonOutline v-if="!appStore.isDarkMode" />
            <SunnyOutline v-else />
          </n-icon>
        </template>
      </n-button>
      <n-badge :value="3" :max="99">
        <n-button quaternary circle>
          <template #icon>
            <n-icon :size="20" :color="appStore.isDarkMode ? '#ffffff' : '#2d3748'">
              <NotificationsOutline />
            </n-icon>
          </template>
        </n-button>
      </n-badge>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NIcon, NInput, NBadge } from 'naive-ui'
import {
  MenuOutline,
  SearchOutline,
  MoonOutline,
  SunnyOutline,
  NotificationsOutline
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()

const currentTitle = computed(() => {
  return (route.meta?.title as string) || '首页概览'
})

const headerStyle = computed(() => ({
  left: appStore.sidebarCollapsed ? '64px' : '220px'
}))
</script>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 20px;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s, border-color 0.3s, left 0.3s;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
