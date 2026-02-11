<template>
  <div class="messages-page">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">消息中心</h1>
        <p class="page-header__subtitle">查看系统通知、告警消息和操作提醒</p>
      </div>
      <div class="page-header__actions">
        <n-button @click="markAllRead" :disabled="unreadCount === 0">
          <template #icon><n-icon><CheckmarkDoneOutline /></n-icon></template>
          全部标为已读
        </n-button>
      </div>
    </div>

    <div class="messages-content">
      <!-- Tabs -->
      <n-tabs v-model:value="activeTab" type="line">
        <n-tab-pane name="all" :tab="`全部 (${messages.length})`">
          <MessageList :messages="messages" @read="markAsRead" @delete="deleteMessage" />
        </n-tab-pane>
        <n-tab-pane name="unread" :tab="`未读 (${unreadCount})`">
          <MessageList :messages="unreadMessages" @read="markAsRead" @delete="deleteMessage" />
        </n-tab-pane>
        <n-tab-pane name="alarm" :tab="`告警 (${alarmMessages.length})`">
          <MessageList :messages="alarmMessages" @read="markAsRead" @delete="deleteMessage" />
        </n-tab-pane>
        <n-tab-pane name="system" :tab="`系统 (${systemMessages.length})`">
          <MessageList :messages="systemMessages" @read="markAsRead" @delete="deleteMessage" />
        </n-tab-pane>
      </n-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { NTabs, NTabPane, NButton, NIcon, NEmpty, NTag, useMessage } from 'naive-ui'
import { CheckmarkDoneOutline, AlertCircleOutline, InformationCircleOutline, SettingsOutline, TrashOutline, CheckmarkOutline } from '@vicons/ionicons5'

interface Message {
  id: number
  type: 'alarm' | 'system' | 'info'
  title: string
  content: string
  time: string
  read: boolean
}

const message = useMessage()
const activeTab = ref('all')

const messages = ref<Message[]>([
  { id: 1, type: 'alarm', title: '高危告警：区域入侵检测', content: 'A栋大厅出口-01 检测到未授权人员入侵，请立即处理。', time: '2024-01-15 14:32:15', read: false },
  { id: 2, type: 'alarm', title: '中危告警：人员聚集', content: 'B区员工通道-02 检测到人员聚集超过阈值（当前12人，阈值10人）。', time: '2024-01-15 14:22:45', read: false },
  { id: 3, type: 'system', title: '系统更新通知', content: '平台将于今晚 22:00 进行版本更新，预计维护时间 30 分钟。', time: '2024-01-15 10:00:00', read: false },
  { id: 4, type: 'info', title: '算法模型更新完成', content: 'YOLOv8 目标检测模型已更新至 V1.2.1 版本，推理性能提升 15%。', time: '2024-01-15 09:30:00', read: true },
  { id: 5, type: 'alarm', title: '警告：设备离线', content: '摄像头"园区入口-03"已离线超过 10 分钟，请检查网络连接。', time: '2024-01-15 08:45:00', read: true },
  { id: 6, type: 'system', title: '存储空间预警', content: '系统存储空间使用率已达 85%，建议清理历史数据或扩容。', time: '2024-01-14 16:20:00', read: true },
  { id: 7, type: 'info', title: '新设备接入', content: '新摄像头"B栋会议室-01"已成功接入平台。', time: '2024-01-14 14:10:00', read: true },
  { id: 8, type: 'system', title: '定时任务执行完成', content: '每日数据备份任务已于 03:00 执行完成，备份文件大小 2.3GB。', time: '2024-01-14 03:00:00', read: true }
])

const unreadCount = computed(() => messages.value.filter(m => !m.read).length)
const unreadMessages = computed(() => messages.value.filter(m => !m.read))
const alarmMessages = computed(() => messages.value.filter(m => m.type === 'alarm'))
const systemMessages = computed(() => messages.value.filter(m => m.type === 'system'))

function markAsRead(id: number) {
  const msg = messages.value.find(m => m.id === id)
  if (msg) msg.read = true
}

function deleteMessage(id: number) {
  const index = messages.value.findIndex(m => m.id === id)
  if (index > -1) {
    messages.value.splice(index, 1)
    message.success('消息已删除')
  }
}

function markAllRead() {
  messages.value.forEach(m => m.read = true)
  message.success('已全部标为已读')
}

// MessageList Component
const MessageList = (props: { messages: Message[] }, { emit }: any) => {
  if (props.messages.length === 0) {
    return h(NEmpty, { description: '暂无消息' })
  }

  return h('div', { class: 'message-list' }, props.messages.map(msg => 
    h('div', { 
      class: ['message-item', { 'message-item--unread': !msg.read }],
      onClick: () => emit('read', msg.id)
    }, [
      h('div', { class: 'message-item__icon' }, [
        h(NIcon, { size: 20, color: msg.type === 'alarm' ? '#ef4444' : msg.type === 'system' ? '#3b82f6' : '#22c55e' }, () => 
          h(msg.type === 'alarm' ? AlertCircleOutline : msg.type === 'system' ? SettingsOutline : InformationCircleOutline)
        )
      ]),
      h('div', { class: 'message-item__content' }, [
        h('div', { class: 'message-item__header' }, [
          h('span', { class: 'message-item__title' }, msg.title),
          h(NTag, { 
            size: 'small', 
            type: msg.type === 'alarm' ? 'error' : msg.type === 'system' ? 'info' : 'success',
            bordered: false
          }, () => msg.type === 'alarm' ? '告警' : msg.type === 'system' ? '系统' : '通知')
        ]),
        h('p', { class: 'message-item__text' }, msg.content),
        h('span', { class: 'message-item__time' }, msg.time)
      ]),
      h('div', { class: 'message-item__actions' }, [
        !msg.read && h(NButton, { text: true, type: 'primary', size: 'small', onClick: (e: Event) => { e.stopPropagation(); emit('read', msg.id) } }, () => [
          h(NIcon, { size: 16 }, () => h(CheckmarkOutline)),
          ' 已读'
        ]),
        h(NButton, { text: true, type: 'error', size: 'small', onClick: (e: Event) => { e.stopPropagation(); emit('delete', msg.id) } }, () => [
          h(NIcon, { size: 16 }, () => h(TrashOutline)),
          ' 删除'
        ])
      ])
    ])
  ))
}
</script>

<style scoped>
.messages-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  flex-shrink: 0;
}

.page-header__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.page-header__subtitle {
  font-size: var(--font-size-base);
  color: var(--text-muted);
  margin: var(--spacing-xs) 0 0;
}

.messages-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
}

.messages-content :deep(.n-tabs-pane-wrapper) {
  height: calc(100% - 50px);
  overflow-y: auto;
}

:deep(.message-list) {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

:deep(.message-item) {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: var(--bg-page);
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.message-item:hover) {
  background: var(--bg-hover);
}

:deep(.message-item--unread) {
  background: rgba(67, 24, 255, 0.03);
  border-left: 3px solid var(--primary-color);
}

:deep(.message-item__icon) {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

:deep(.message-item__content) {
  flex: 1;
  min-width: 0;
}

:deep(.message-item__header) {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

:deep(.message-item__title) {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

:deep(.message-item__text) {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-xs);
  line-height: 1.5;
}

:deep(.message-item__time) {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

:deep(.message-item__actions) {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}
</style>
