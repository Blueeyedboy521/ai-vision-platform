<template>
  <div class="alert-list-card">
    <div class="alert-list-header">
      <div class="alert-list-title">
        <div class="title-bar"></div>
        <span>实时动态告警实况</span>
      </div>
      <a href="#" class="history-link" @click.prevent="goHistory">查看历史追溯</a>
    </div>
    <div class="alert-items">
      <div
        v-for="item in alerts"
        :key="item.id"
        class="alert-item"
      >
        <div class="alert-thumb">
          <img :src="item.thumb" :alt="item.title" />
          <span class="live-badge">LIVE</span>
        </div>
        <div class="alert-info">
          <div class="alert-title-row">
            <span class="alert-name">{{ item.title }}</span>
            <span :class="['alert-level', `level-${item.level}`]">{{ item.levelText }}</span>
          </div>
          <div class="alert-meta">
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.6 11.6L22 7v10l-6.4-4.5v-1zM4 5h9a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7c0-1.1.9-2 2-2z"/></svg>
              {{ item.location }}
            </span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              {{ item.timeAgo }}
            </span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              {{ item.datetime }}
            </span>
          </div>
        </div>
        <div class="alert-actions">
          <button class="replay-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            视频回放
          </button>
          <button class="check-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAlarmList, type Alarm } from '@/api/alarm'

interface AlertItem {
  id: string
  thumb: string
  title: string
  level: string
  levelText: string
  location: string
  timeAgo: string
  datetime: string
}

const router = useRouter()
const alerts = ref<AlertItem[]>([])

function goHistory() {
  router.push('/alarm')
}

function levelText(level: string): string {
  const l = (level || '').toLowerCase()
  if (l === 'critical') return '高危'
  if (l === 'danger') return '高危'
  if (l === 'warning') return '中等'
  return '提示'
}

function timeAgoFromIso(iso: string): string {
  try {
    const t = new Date(iso).getTime()
    const diffSec = Math.max(0, Math.floor((Date.now() - t) / 1000))
    if (diffSec < 60) return `${diffSec} 秒前`
    const diffMin = Math.floor(diffSec / 60)
    if (diffMin < 60) return `${diffMin} 分钟前`
    const diffHour = Math.floor(diffMin / 60)
    if (diffHour < 24) return `${diffHour} 小时前`
    const diffDay = Math.floor(diffHour / 24)
    return `${diffDay} 天前`
  } catch {
    return '-'
  }
}

async function loadAlerts() {
  try {
    const res = await getAlarmList({ page: 1, page_size: 4 })
    const items = (res.data.data || []) as Alarm[]
    alerts.value = items.map((a) => ({
      id: a.id,
      thumb: a.snapshot_url || '/camera-warehouse-01.jpg',
      title: a.title || a.algorithm_name || '告警',
      level: a.level || 'info',
      levelText: levelText(a.level),
      location: a.camera_name || a.camera_id,
      timeAgo: timeAgoFromIso(a.alarm_time),
      datetime: a.alarm_time?.replace('T', ' ') || a.created_at
    }))
  } catch (e) {
    console.error('加载首页告警列表失败:', e)
  }
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alert-list-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
  border-top: 3px solid transparent;
}

.alert-list-card:hover {
  border-top-color: #f59e0b;
  box-shadow: 0 4px 16px var(--hover-shadow);
}

.alert-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.alert-list-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.title-bar {
  width: 4px;
  height: 18px;
  background: #f59e0b;
  border-radius: 2px;
}

.history-link {
  font-size: 13px;
  color: #4318FF;
  text-decoration: none;
  cursor: pointer;
}

.history-link:hover {
  text-decoration: underline;
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
}

.alert-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.alert-item:first-child {
  padding-top: 0;
}

.alert-thumb {
  position: relative;
  width: 120px;
  min-width: 120px;
  height: 72px;
  border-radius: 8px;
  overflow: hidden;
}

.alert-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.live-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  padding: 2px 6px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.alert-info {
  flex: 1;
  min-width: 0;
}

.alert-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.alert-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.alert-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.level-critical {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.level-medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.level-warning {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.level-urgent {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.alert-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-item svg {
  flex-shrink: 0;
}

.alert-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.replay-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: #4318FF;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}

.replay-btn:hover {
  background: #3614d0;
}

.check-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 2px solid #4318FF;
  background: transparent;
  color: #4318FF;
  cursor: pointer;
  transition: all 0.2s;
}

.check-btn:hover {
  background: #4318FF;
  color: #fff;
}
</style>
