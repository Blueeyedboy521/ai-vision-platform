import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', hideLayout: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页概览' }
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('@/views/Messages.vue'),
    meta: { title: '消息中心' }
  },
  {
    path: '/video',
    name: 'VideoManagement',
    component: () => import('@/views/RouterViewWrapper.vue'),
    redirect: '/video/cameras',
    meta: { title: '视频管理' },
    children: [
      {
        path: 'cameras',
        name: 'CameraManagement',
        component: () => import('@/views/CameraManagement.vue'),
        meta: { title: '摄像头管理' }
      },
      {
        path: 'preview',
        name: 'VideoPreview',
        component: () => import('@/views/VideoPreview.vue'),
        meta: { title: '视频预览' }
      }
    ]
  },
  {
    path: '/algorithm',
    name: 'AlgorithmManagement',
    component: () => import('@/views/AlgorithmManagement.vue'),
    meta: { title: '算法管理' }
  },
  {
    path: '/push',
    name: 'PushManagement',
    component: () => import('@/views/PushManagement.vue'),
    meta: { title: '推送管理' }
  },
  {
    path: '/alarm',
    name: 'AlarmManagement',
    component: () => import('@/views/AlarmManagement.vue'),
    meta: { title: '告警管理' }
  },
  {
    path: '/system',
    name: 'SystemConfig',
    component: () => import('@/views/RouterViewWrapper.vue'),
    redirect: '/system/overview',
    meta: { title: '系统配置' },
    children: [
      {
        path: 'overview',
        name: 'SystemOverview',
        component: () => import('@/views/system/SystemOverview.vue'),
        meta: { title: '系统概览' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/system/UserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'roles',
        name: 'RoleManagement',
        component: () => import('@/views/system/RoleManagement.vue'),
        meta: { title: '角色权限' }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/system/SystemSettings.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'logs',
        name: 'OperationLogs',
        component: () => import('@/views/system/OperationLogs.vue'),
        meta: { title: '操作日志' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
// Note: Authentication is optional for development. Set VITE_REQUIRE_AUTH=true to enable.
router.beforeEach((to, from, next) => {
  // Skip auth check in development for easier testing
  const requireAuth = false // Set to true to enable login requirement
  
  if (!requireAuth) {
    next()
    return
  }
  
  const token = localStorage.getItem('token')
  
  // If going to login page and already logged in, redirect to dashboard
  if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
    return
  }
  
  // If not going to login and not logged in, redirect to login
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
    return
  }
  
  next()
})

export default router
