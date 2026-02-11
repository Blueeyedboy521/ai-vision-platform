<template>
  <!-- Login page without layout -->
  <router-view v-if="isLoginPage" />
  
  <!-- Normal pages with layout -->
  <n-layout v-else has-sider style="height: 100vh;">
    <AppSidebar />
    <n-layout style="height: 100vh; overflow: hidden;">
      <div class="sticky-header">
        <AppHeader />
      </div>
      <div class="main-content">
        <router-view />
      </div>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NLayout } from 'naive-ui'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const route = useRoute()

// Check if current route is login page
const isLoginPage = computed(() => route.path === '/login')
</script>

<style scoped>
.sticky-header {
  position: fixed;
  top: 0;
  left: var(--sidebar-width, 220px);
  right: 0;
  z-index: 100;
}

.main-content {
  height: calc(100vh - 56px);
  margin-top: 56px;
  padding: 24px;
  overflow: hidden;
  background: var(--bg-page);
  box-sizing: border-box;
}
</style>
