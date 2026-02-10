import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页概览' }
  },
  {
    path: '/video',
    name: 'VideoManagement',
    component: () => import('@/views/Placeholder.vue'),
    meta: { title: '视频管理' }
  },
  {
    path: '/algorithm',
    name: 'AlgorithmManagement',
    component: () => import('@/views/Placeholder.vue'),
    meta: { title: '算法管理' }
  },
  {
    path: '/push',
    name: 'PushManagement',
    component: () => import('@/views/Placeholder.vue'),
    meta: { title: '推送管理' }
  },
  {
    path: '/alarm',
    name: 'AlarmManagement',
    component: () => import('@/views/Placeholder.vue'),
    meta: { title: '告警管理' }
  },
  {
    path: '/system',
    name: 'SystemManagement',
    component: () => import('@/views/Placeholder.vue'),
    meta: { title: '系统管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
