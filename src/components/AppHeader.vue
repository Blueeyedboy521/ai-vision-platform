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
      <!-- Breadcrumb navigation -->
      <div class="header-breadcrumb">
        <template v-for="(item, index) in breadcrumbItems" :key="item.path">
          <span 
            class="breadcrumb-item" 
            :class="{ 'breadcrumb-current': index === breadcrumbItems.length - 1 }"
            @click="index < breadcrumbItems.length - 1 && navigateTo(item.path)"
          >
            {{ item.title }}
          </span>
          <n-icon 
            v-if="index < breadcrumbItems.length - 1" 
            :size="14" 
            :color="appStore.isDarkMode ? '#6b7280' : '#a0aec0'"
            class="breadcrumb-separator"
          >
            <ChevronForwardOutline />
          </n-icon>
        </template>
      </div>
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
      <n-badge :value="unreadCount" :max="99">
        <n-button quaternary circle @click="goToMessages">
          <template #icon>
            <n-icon :size="20" :color="appStore.isDarkMode ? '#ffffff' : '#2d3748'">
              <NotificationsOutline />
            </n-icon>
          </template>
        </n-button>
      </n-badge>
      
      <!-- User Avatar Popover -->
      <n-popover trigger="click" placement="bottom-end" :show-arrow="false" raw>
        <template #trigger>
          <div class="user-avatar">
            <n-avatar
              round
              :size="36"
              :src="userInfo.avatar"
              :fallback-src="defaultAvatar"
            />
          </div>
        </template>
        <div class="user-menu">
          <div class="user-menu__header">
            <n-avatar
              round
              :size="48"
              :src="userInfo.avatar"
              :fallback-src="defaultAvatar"
            />
            <div class="user-menu__info">
              <span class="user-menu__name">{{ userInfo.name }}</span>
              <span class="user-menu__role">{{ userInfo.role }}</span>
            </div>
          </div>
          <div class="user-menu__divider"></div>
          <div class="user-menu__items">
            <div class="user-menu__item" @click="handleUserMenuSelect('profile')">
              <n-icon :size="18"><PersonOutline /></n-icon>
              <span>个人信息</span>
            </div>
            <div class="user-menu__item" @click="handleUserMenuSelect('settings')">
              <n-icon :size="18"><SettingsOutline /></n-icon>
              <span>账号设置</span>
            </div>
          </div>
          <div class="user-menu__divider"></div>
          <div class="user-menu__item user-menu__item--danger" @click="handleUserMenuSelect('logout')">
            <n-icon :size="18"><LogOutOutline /></n-icon>
            <span>退出登录</span>
          </div>
        </div>
      </n-popover>
    </div>

    <!-- Edit User Modal -->
    <n-modal v-model:show="showEditModal" preset="card" title="修改个人信息" :style="{ width: '450px' }" :bordered="false">
      <n-form :model="editForm" label-placement="left" label-width="80">
        <n-form-item label="用户名">
          <n-input :value="userInfo.username" disabled />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="editForm.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="邮箱">
          <n-input v-model:value="editForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="手机号">
          <n-input v-model:value="editForm.phone" placeholder="请输入手机号" />
        </n-form-item>
        <n-form-item label="修改密码">
          <n-input v-model:value="editForm.password" type="password" placeholder="留空则不修改" show-password-on="click" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="saveUserInfo">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NIcon, NInput, NBadge, NAvatar, NPopover, NModal, NForm, NFormItem, useMessage } from 'naive-ui'
import {
  MenuOutline,
  SearchOutline,
  MoonOutline,
  SunnyOutline,
  NotificationsOutline,
  ChevronForwardOutline,
  PersonOutline,
  LogOutOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()
const message = useMessage()

const showEditModal = ref(false)
const unreadCount = ref(3)
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=default'

// User info
const userInfo = ref({
  username: 'admin',
  name: '系统管理员',
  role: '超级管理员',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin',
  email: 'admin@example.com',
  phone: '138****1234'
})

const editForm = ref({
  name: '',
  email: '',
  phone: '',
  password: ''
})

// Load user info from localStorage
onMounted(() => {
  const stored = localStorage.getItem('user')
  if (stored) {
    try {
      const user = JSON.parse(stored)
      userInfo.value = { ...userInfo.value, ...user }
    } catch (e) {
      // ignore
    }
  }
})

function handleUserMenuSelect(key: string) {
  switch (key) {
    case 'profile':
      editForm.value = {
        name: userInfo.value.name,
        email: userInfo.value.email || '',
        phone: userInfo.value.phone || '',
        password: ''
      }
      showEditModal.value = true
      break
    case 'settings':
      router.push('/system/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

function saveUserInfo() {
  userInfo.value.name = editForm.value.name
  userInfo.value.email = editForm.value.email
  userInfo.value.phone = editForm.value.phone
  
  // Update localStorage
  localStorage.setItem('user', JSON.stringify(userInfo.value))
  
  showEditModal.value = false
  message.success('个人信息已更新')
}

function handleLogout() {
  localStorage.removeItem('user')
  localStorage.removeItem('token')
  message.success('已退出登录')
  router.push('/login')
}

function goToMessages() {
  router.push('/messages')
}

// Generate breadcrumb items from route matched
const breadcrumbItems = computed(() => {
  const items: Array<{ title: string; path: string }> = []
  
  route.matched.forEach((record) => {
    if (record.meta?.title) {
      items.push({
        title: record.meta.title as string,
        path: record.path
      })
    }
  })
  
  return items
})

function navigateTo(path: string) {
  router.push(path)
}

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

/* Breadcrumb styles */
.header-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.breadcrumb-item {
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}

.breadcrumb-item:not(.breadcrumb-current):hover {
  color: #4318FF;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 600;
  cursor: default;
}

.breadcrumb-separator {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  cursor: pointer;
  margin-left: 8px;
  padding: 2px;
  border-radius: 50%;
  transition: all 0.2s;
}

.user-avatar:hover {
  background: rgba(67, 24, 255, 0.1);
}

/* User Menu Popover */
.user-menu {
  width: 240px;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.user-menu__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #4318FF 0%, #6366f1 100%);
}

.user-menu__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-menu__name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.user-menu__role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.user-menu__divider {
  height: 1px;
  background: var(--border-color);
  margin: 0;
}

.user-menu__items {
  padding: 8px 0;
}

.user-menu__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 14px;
  transition: background 0.2s;
}

.user-menu__item:hover {
  background: var(--bg-hover);
}

.user-menu__item--danger {
  color: #ef4444;
  margin: 8px 0;
}

.user-menu__item--danger:hover {
  background: rgba(239, 68, 68, 0.08);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
