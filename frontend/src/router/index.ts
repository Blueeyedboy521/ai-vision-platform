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
    component: () => import('@/views/RouterViewWrapper.vue'),
    redirect: '/alarm/stats',
    meta: { title: '告警管理' },
    children: [
      {
        path: 'list',
        name: 'AlarmList',
        component: () => import('@/views/alarm/AlarmList.vue'),
        meta: { title: '告警列表' }
      },
      {
        path: 'stats',
        name: 'AlarmStats',
        component: () => import('@/views/alarm/AlarmStats.vue'),
        meta: { title: '告警统计' }
      },

    ]
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

// 白名单路由（不需要登录）
const whiteList = ['/login']

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - AI 视觉管理平台`
  }
  
  // 动态导入 userStore（避免循环依赖）
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()
  
  // 检查是否有 Token
  const hasToken = userStore.checkAuth()
  
  if (hasToken) {
    // 已登录
    if (to.path === '/login') {
      // 已登录但访问登录页，重定向到首页
      next({ path: '/dashboard' })
    } else {
      // 如果没有用户信息，尝试获取
      if (!userStore.userInfo) {
        try {
          await userStore.fetchUserInfo()
          next()
        } catch (error) {
          // 获取用户信息失败，清除 Token 并跳转登录
          userStore.clearAuth()
          next(`/login?redirect=${to.path}`)
        }
      } else {
        next()
      }
    }
  } else {
    // 未登录
    if (whiteList.includes(to.path)) {
      // 在白名单中，直接进入
      next()
    } else {
      // 重定向到登录页，并记录原始路径
      next(`/login?redirect=${to.path}`)
    }
  }
})

export default router
