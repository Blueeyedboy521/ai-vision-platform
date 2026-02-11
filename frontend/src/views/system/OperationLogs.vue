<template>
  <div class="operation-logs">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">操作日志</h1>
        <p class="page-header__subtitle">记录系统中所有用户的操作行为</p>
      </div>
      <n-button @click="exportLogs">
        <template #icon><n-icon><DownloadOutline /></n-icon></template>
        导出日志
      </n-button>
    </div>

    <div class="filter-bar">
      <n-input v-model:value="filters.keyword" placeholder="搜索操作内容、用户名..." style="width: 250px" clearable>
        <template #prefix><n-icon><SearchOutline /></n-icon></template>
      </n-input>
      <n-select v-model:value="filters.module" :options="moduleOptions" placeholder="模块" clearable style="width: 140px" />
      <n-select v-model:value="filters.action" :options="actionOptions" placeholder="操作类型" clearable style="width: 140px" />
      <n-select v-model:value="filters.status" :options="statusOptions" placeholder="状态" clearable style="width: 120px" />
      <n-date-picker v-model:value="filters.dateRange" type="daterange" clearable style="width: 280px" />
    </div>

    <div class="table-wrapper">
      <n-data-table
        :columns="columns"
        :data="filteredLogs"
        :pagination="pagination"
        :bordered="false"
        :row-class-name="getRowClassName"
      />
    </div>

    <!-- Detail Modal -->
    <n-modal v-model:show="showDetail" preset="card" title="操作详情" :style="{ width: '600px' }" :bordered="false">
      <div v-if="selectedLog" class="log-detail">
        <div class="detail-row">
          <span class="detail-label">操作时间</span>
          <span class="detail-value">{{ selectedLog.time }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">操作用户</span>
          <span class="detail-value">{{ selectedLog.username }} ({{ selectedLog.ip }})</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">操作模块</span>
          <span class="detail-value">{{ selectedLog.module }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">操作类型</span>
          <span class="detail-value">{{ selectedLog.action }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">操作内容</span>
          <span class="detail-value">{{ selectedLog.content }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">执行状态</span>
          <n-tag :type="selectedLog.status === 'success' ? 'success' : 'error'" size="small">
            {{ selectedLog.status === 'success' ? '成功' : '失败' }}
          </n-tag>
        </div>
        <div v-if="selectedLog.detail" class="detail-row detail-row--block">
          <span class="detail-label">详细信息</span>
          <pre class="detail-code">{{ selectedLog.detail }}</pre>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { NButton, NIcon, NInput, NSelect, NDatePicker, NDataTable, NModal, NTag, useMessage } from 'naive-ui'
import { DownloadOutline, SearchOutline } from '@vicons/ionicons5'

interface Log {
  id: number
  time: string
  username: string
  ip: string
  module: string
  action: string
  content: string
  status: 'success' | 'failed'
  detail?: string
}

const message = useMessage()
const showDetail = ref(false)
const selectedLog = ref<Log | null>(null)

const filters = ref({
  keyword: '',
  module: null as string | null,
  action: null as string | null,
  status: null as string | null,
  dateRange: null as [number, number] | null
})

const pagination = { pageSize: 15 }

const logs = ref<Log[]>([
  { id: 1, time: '2024-01-15 14:32:15', username: 'admin', ip: '192.168.1.100', module: '用户管理', action: '创建', content: '创建用户 zhangsan', status: 'success' },
  { id: 2, time: '2024-01-15 14:30:22', username: 'admin', ip: '192.168.1.100', module: '角色权限', action: '修改', content: '修改角色"运维管理员"权限', status: 'success', detail: '新增权限: 告警管理-删除告警' },
  { id: 3, time: '2024-01-15 14:28:10', username: 'zhangsan', ip: '192.168.1.101', module: '摄像头管理', action: '创建', content: '添加摄像头"园区入口"', status: 'success' },
  { id: 4, time: '2024-01-15 14:25:03', username: 'zhangsan', ip: '192.168.1.101', module: '算法管理', action: '修改', content: '修改算法"安全帽检测"配置', status: 'failed', detail: '错误: 参数验证失败' },
  { id: 5, time: '2024-01-15 14:20:45', username: 'lisi', ip: '192.168.1.102', module: '告警管理', action: '处理', content: '处理告警#1234', status: 'success' },
  { id: 6, time: '2024-01-15 14:18:30', username: 'admin', ip: '192.168.1.100', module: '系统设置', action: '修改', content: '修改系统基础设置', status: 'success' },
  { id: 7, time: '2024-01-15 14:15:12', username: 'wangwu', ip: '192.168.1.103', module: '登录认证', action: '登录', content: '用户登录系统', status: 'success' },
  { id: 8, time: '2024-01-15 14:10:08', username: 'unknown', ip: '192.168.1.200', module: '登录认证', action: '登录', content: '尝试登录失败', status: 'failed', detail: '错误: 密码错误，第3次尝试' },
  { id: 9, time: '2024-01-15 13:55:20', username: 'admin', ip: '192.168.1.100', module: '推送管理', action: '修改', content: '修改钉钉推送配置', status: 'success' },
  { id: 10, time: '2024-01-15 13:50:15', username: 'lisi', ip: '192.168.1.102', module: '告警管理', action: '导出', content: '导出告警报表', status: 'success' },
  { id: 11, time: '2024-01-15 13:45:00', username: 'zhangsan', ip: '192.168.1.101', module: '摄像头管理', action: '删除', content: '删除摄像头"测试摄像头"', status: 'success' },
  { id: 12, time: '2024-01-15 13:40:33', username: 'admin', ip: '192.168.1.100', module: '用户管理', action: '修改', content: '重置用户 wangwu 密码', status: 'success' }
])

const moduleOptions = [
  { label: '用户管理', value: '用户管理' },
  { label: '角色权限', value: '角色权限' },
  { label: '摄像头管理', value: '摄像头管理' },
  { label: '算法管理', value: '算法管理' },
  { label: '告警管理', value: '告警管理' },
  { label: '推送管理', value: '推送管理' },
  { label: '系统设置', value: '系统设置' },
  { label: '登录认证', value: '登录认证' }
]

const actionOptions = [
  { label: '创建', value: '创建' },
  { label: '修改', value: '修改' },
  { label: '删除', value: '删除' },
  { label: '查看', value: '查看' },
  { label: '导出', value: '导出' },
  { label: '登录', value: '登录' },
  { label: '处理', value: '处理' }
]

const statusOptions = [
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' }
]

const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    if (filters.value.keyword) {
      const k = filters.value.keyword.toLowerCase()
      if (!log.content.toLowerCase().includes(k) && !log.username.toLowerCase().includes(k)) return false
    }
    if (filters.value.module && log.module !== filters.value.module) return false
    if (filters.value.action && log.action !== filters.value.action) return false
    if (filters.value.status && log.status !== filters.value.status) return false
    return true
  })
})

const columns = [
  { title: '时间', key: 'time', width: 160 },
  { title: '用户', key: 'username', width: 100 },
  { title: 'IP 地址', key: 'ip', width: 130 },
  { title: '模块', key: 'module', width: 100 },
  { title: '操作', key: 'action', width: 80, render: (row: Log) => h(NTag, { type: getActionType(row.action), size: 'small', bordered: false }, () => row.action) },
  { title: '操作内容', key: 'content', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 80, render: (row: Log) => h(NTag, { type: row.status === 'success' ? 'success' : 'error', size: 'small' }, () => row.status === 'success' ? '成功' : '失败') },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: Log) => h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => viewDetail(row) }, () => '详情')
  }
]

function getActionType(action: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  switch (action) {
    case '创建': return 'success'
    case '删除': return 'error'
    case '修改': return 'warning'
    case '导出': return 'info'
    default: return 'default'
  }
}

function getRowClassName(row: Log) {
  return row.status === 'failed' ? 'row-failed' : ''
}

function viewDetail(log: Log) {
  selectedLog.value = log
  showDetail.value = true
}

function exportLogs() {
  message.success('日志导出成功')
}
</script>

<style scoped>
.operation-logs {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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

.filter-bar {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
  overflow: auto;
}

.table-wrapper :deep(.row-failed) {
  background: rgba(239, 68, 68, 0.05);
}

.log-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-row {
  display: flex;
  align-items: flex-start;
}

.detail-row--block {
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-label {
  width: 80px;
  flex-shrink: 0;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.detail-value {
  flex: 1;
  color: var(--text-primary);
}

.detail-code {
  width: 100%;
  background: var(--bg-page);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  font-family: monospace;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
