<template>
  <n-layout-sider
    :collapsed="appStore.sidebarCollapsed"
    collapse-mode="width"
    :collapsed-width="64"
    :width="220"
    :native-scrollable="true"
    :style="{ height: '100vh', background: 'var(--bg-sidebar)', transition: 'background 0.3s, border-color 0.3s', borderRight: '1px solid var(--border-color)' }"
  >
    <div class="sidebar-wrapper">
      <!-- Logo -->
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="6" fill="#4318FF" />
            <path d="M8 10h4v8H8V10zm8 0h4v8h-4V10z" fill="white" opacity="0.9" />
            <path d="M12 8h4v12h-4V8z" fill="white" />
          </svg>
        </div>
        <span v-if="!appStore.sidebarCollapsed" class="logo-text">AI 视觉管理平台</span>
      </div>

      <!-- Menu -->
      <div class="menu-section">
        <div v-if="!appStore.sidebarCollapsed" class="menu-group-label">平台中心</div>
        <n-menu
          :collapsed="appStore.sidebarCollapsed"
          :collapsed-width="64"
          :collapsed-icon-size="20"
          :options="platformMenuOptions"
          :value="currentKey"
          @update:value="handleMenuSelect"
          :indent="16"
          :theme-overrides="menuThemeOverrides"
        />

        <div v-if="!appStore.sidebarCollapsed" class="menu-group-label" style="margin-top: 12px;">系统配置</div>
        <n-menu
          :collapsed="appStore.sidebarCollapsed"
          :collapsed-width="64"
          :collapsed-icon-size="20"
          :options="configMenuOptions"
          :value="currentKey"
          @update:value="handleMenuSelect"
          :indent="16"
          :theme-overrides="menuThemeOverrides"
        />
      </div>

      <!-- User Info -->
      <div class="user-section">
        <n-avatar
          round
          :size="36"
          src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin"
          style="background: #e8eaf6;"
        />
        <div v-if="!appStore.sidebarCollapsed" class="user-info">
          <div class="user-name">管理员</div>
          <div class="user-role">SUPER ADMINISTRATOR</div>
        </div>
      </div>
    </div>
  </n-layout-sider>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NLayoutSider, NMenu, NAvatar, NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  HomeOutline,
  VideocamOutline,
  CodeSlashOutline,
  SendOutline,
  NotificationsOutline,
  SettingsOutline,
  PeopleOutline,
  ShieldCheckmarkOutline,
  OptionsOutline,
  DocumentTextOutline,
  ServerOutline
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const currentKey = computed(() => {
  const name = route.name as string
  // Map child route names to sidebar keys
  if (name === 'CameraManagement') return 'video-devices'
  if (name === 'VideoPreview') return 'video-preview'
  if (name === 'AlarmList') return 'alarm-list'
  if (name === 'AlarmStats') return 'alarm-stats'
  if (name === 'AlarmStats2') return 'alarm-stats2'
  if (name === 'SystemOverview') return 'system-overview'
  if (name === 'UserManagement') return 'system-users'
  if (name === 'RoleManagement') return 'system-roles'
  if (name === 'SystemSettings') return 'system-settings'
  if (name === 'OperationLogs') return 'system-logs'
  return name
})

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const platformMenuOptions: MenuOption[] = [
  {
    label: '首页概览',
    key: 'Dashboard',
    icon: renderIcon(HomeOutline)
  },
  {
    label: '视频管理',
    key: 'VideoManagement',
    icon: renderIcon(VideocamOutline),
    children: [
      { label: '摄像头管理', key: 'video-devices' },
      { label: '视频预览', key: 'video-preview' }
    ]
  },
  {
    label: '算法管理',
    key: 'AlgorithmManagement',
    icon: renderIcon(CodeSlashOutline)
  },
  {
    label: '推送管理',
    key: 'PushManagement',
    icon: renderIcon(SendOutline)
  },
  {
    label: '告警管理',
    key: 'AlarmManagement',
    icon: renderIcon(NotificationsOutline),
    children: [
      { label: '告警统计', key: 'alarm-stats' },
      { label: '告警统计2', key: 'alarm-stats2' },
      { label: '告警列表', key: 'alarm-list' }
    ]
  }
]

const configMenuOptions: MenuOption[] = [
  {
    label: '系统配置',
    key: 'SystemConfig',
    icon: renderIcon(SettingsOutline),
    children: [
      { label: '系统概览', key: 'system-overview', icon: renderIcon(ServerOutline) },
      { label: '用户管理', key: 'system-users', icon: renderIcon(PeopleOutline) },
      { label: '角色权限', key: 'system-roles', icon: renderIcon(ShieldCheckmarkOutline) },
      { label: '系统设置', key: 'system-settings', icon: renderIcon(OptionsOutline) },
      { label: '操作日志', key: 'system-logs', icon: renderIcon(DocumentTextOutline) }
    ]
  }
]

const menuThemeOverrides = computed(() => {
  const dark = appStore.isDarkMode
  return {
    itemTextColor: dark ? '#c0c0c8' : '#333',
    itemTextColorHover: dark ? '#e4e4e8' : '#111',
    itemIconColor: dark ? '#9090a0' : '#666',
    itemIconColorHover: dark ? '#c0c0c8' : '#333',
    itemColorHover: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
    itemTextColorActive: '#4318FF',
    itemTextColorActiveHover: '#4318FF',
    itemIconColorActive: '#4318FF',
    itemIconColorActiveHover: '#4318FF',
    itemColorActive: dark ? 'rgba(67, 24, 255, 0.15)' : 'rgba(67, 24, 255, 0.08)',
    itemColorActiveHover: dark ? 'rgba(67, 24, 255, 0.2)' : 'rgba(67, 24, 255, 0.12)',
    itemTextColorChildActive: '#4318FF',
    itemTextColorChildActiveHover: '#4318FF',
    itemIconColorChildActive: '#4318FF',
    itemIconColorChildActiveHover: '#4318FF',
    arrowColor: dark ? '#9090a0' : '#999',
    arrowColorHover: dark ? '#c0c0c8' : '#333',
    arrowColorActive: '#4318FF',
    arrowColorActiveHover: '#4318FF',
    arrowColorChildActive: '#4318FF',
    arrowColorChildActiveHover: '#4318FF',
    groupTextColor: dark ? '#6b7280' : '#a0aec0'
  }
})

function handleMenuSelect(key: string) {
  // Map sidebar keys to route names
  const keyToRoute: Record<string, string> = {
    'Dashboard': 'Dashboard',
    'VideoManagement': 'CameraManagement',
    'video-devices': 'CameraManagement',
    'video-preview': 'VideoPreview',
    'AlgorithmManagement': 'AlgorithmManagement',
    'PushManagement': 'PushManagement',
    'AlarmManagement': 'AlarmList',
    'alarm-list': 'AlarmList',
    'alarm-stats': 'AlarmStats',
    'alarm-stats2': 'AlarmStats2',
    'system-overview': 'SystemOverview',
    'system-users': 'UserManagement',
    'system-roles': 'RoleManagement',
    'system-settings': 'SystemSettings',
    'system-logs': 'OperationLogs'
  }
  const routeName = keyToRoute[key]
  if (routeName) {
    router.push({ name: routeName })
  }
}
</script>

<style scoped>
.sidebar-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.menu-section {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.menu-group-label {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 12px 20px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.user-info {
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 11px;
  color: #4318FF;
  font-weight: 500;
  letter-spacing: 0.3px;
}
</style>
