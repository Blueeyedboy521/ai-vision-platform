<template>
  <n-layout has-sider style="height: 100vh;">
    <AppSidebar />
    <n-layout style="display: flex; flex-direction: column; height: 100vh; overflow: hidden;">
      <div class="sticky-header">
        <AppHeader />
      </div>
      <n-layout-content
        :content-style="{ padding: '80px 24px 24px', background: 'var(--bg-page)', transition: 'background 0.3s' }"
        :native-scrollable="true"
        style="flex: 1; overflow-y: auto;"
      >
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { NLayout, NLayoutContent } from 'naive-ui'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<style scoped>
.sticky-header {
  flex-shrink: 0;
  z-index: 10;
}
</style>
