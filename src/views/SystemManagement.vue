<template>
  <div class="system-management">
    <!-- Tab Navigation -->
    <n-tabs v-model:value="activeTab" type="line" animated>
      <!-- System Overview Tab -->
      <n-tab-pane name="overview" tab="系统概览">
        <div class="tab-content">
          <!-- System Info Cards -->
          <div class="info-section">
            <h3 class="section-title">运行状态</h3>
            <div class="info-grid">
              <div class="info-card">
                <div class="info-card__icon info-card__icon--primary">
                  <n-icon :size="24"><ServerOutline /></n-icon>
                </div>
                <div class="info-card__content">
                  <span class="info-card__label">系统运行时长</span>
                  <span class="info-card__value">{{ systemInfo.uptime }}</span>
                </div>
              </div>
              <div class="info-card">
                <div class="info-card__icon info-card__icon--success">
                  <n-icon :size="24"><SpeedometerOutline /></n-icon>
                </div>
                <div class="info-card__content">
                  <span class="info-card__label">CPU 使用率</span>
                  <span class="info-card__value">{{ systemInfo.cpuUsage }}%</span>
                </div>
                <n-progress type="line" :percentage="systemInfo.cpuUsage" :show-indicator="false" />
              </div>
              <div class="info-card">
                <div class="info-card__icon info-card__icon--warning">
                  <n-icon :size="24"><HardwareChipOutline /></n-icon>
                </div>
                <div class="info-card__content">
                  <span class="info-card__label">内存使用</span>
                  <span class="info-card__value">{{ systemInfo.memoryUsed }}GB / {{ systemInfo.memoryTotal }}GB</span>
                </div>
                <n-progress type="line" :percentage="(systemInfo.memoryUsed / systemInfo.memoryTotal) * 100" :show-indicator="false" status="warning" />
              </div>
              <div class="info-card">
                <div class="info-card__icon info-card__icon--info">
                  <n-icon :size="24"><CloudOutline /></n-icon>
                </div>
                <div class="info-card__content">
                  <span class="info-card__label">存储空间</span>
                  <span class="info-card__value">{{ systemInfo.diskUsed }}TB / {{ systemInfo.diskTotal }}TB</span>
                </div>
                <n-progress type="line" :percentage="(systemInfo.diskUsed / systemInfo.diskTotal) * 100" :show-indicator="false" status="info" />
              </div>
            </div>
          </div>

          <!-- Version Info -->
          <div class="info-section">
            <h3 class="section-title">版本信息</h3>
            <div class="version-table">
              <div class="version-row">
                <span class="version-label">平台版本</span>
                <span class="version-value">V2.5.1</span>
                <n-tag type="success" size="small">最新版本</n-tag>
              </div>
              <div class="version-row">
                <span class="version-label">AI 引擎版本</span>
                <span class="version-value">V1.8.3</span>
                <n-button text type="primary" size="small">检查更新</n-button>
              </div>
              <div class="version-row">
                <span class="version-label">数据库版本</span>
                <span class="version-value">PostgreSQL 15.2</span>
              </div>
              <div class="version-row">
                <span class="version-label">最后更新时间</span>
                <span class="version-value">2024-01-10 09:30:00</span>
              </div>
            </div>
          </div>

          <!-- License Info -->
          <div class="info-section">
            <h3 class="section-title">授权信息</h3>
            <div class="license-card">
              <div class="license-header">
                <span class="license-type">企业版授权</span>
                <n-tag type="success">有效</n-tag>
              </div>
              <div class="license-info">
                <div class="license-item">
                  <span class="license-label">授权单位</span>
                  <span class="license-value">XX科技有限公司</span>
                </div>
                <div class="license-item">
                  <span class="license-label">设备限制</span>
                  <span class="license-value">500 台</span>
                </div>
                <div class="license-item">
                  <span class="license-label">到期时间</span>
                  <span class="license-value">2025-12-31</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- User Management Tab -->
      <n-tab-pane name="users" tab="用户管理">
        <div class="tab-content">
          <div class="toolbar">
            <n-input v-model:value="userSearch" placeholder="搜索用户..." style="width: 280px">
              <template #prefix><n-icon><SearchOutline /></n-icon></template>
            </n-input>
            <n-button type="primary" @click="showUserModal = true">
              <template #icon><n-icon><AddOutline /></n-icon></template>
              添加用户
            </n-button>
          </div>
          <n-data-table
            :columns="userColumns"
            :data="filteredUsers"
            :pagination="{ pageSize: 10 }"
            :bordered="false"
          />
        </div>
      </n-tab-pane>

      <!-- Role Management Tab -->
      <n-tab-pane name="roles" tab="角色权限">
        <div class="tab-content">
          <div class="toolbar">
            <n-button type="primary" @click="showRoleModal = true">
              <template #icon><n-icon><AddOutline /></n-icon></template>
              新建角色
            </n-button>
          </div>
          <div class="role-grid">
            <div v-for="role in roles" :key="role.id" class="role-card">
              <div class="role-card__header">
                <div class="role-card__icon" :style="{ background: role.color }">
                  <n-icon :size="20" color="#fff"><PersonOutline /></n-icon>
                </div>
                <div class="role-card__info">
                  <h4 class="role-card__name">{{ role.name }}</h4>
                  <span class="role-card__count">{{ role.userCount }} 位用户</span>
                </div>
                <n-dropdown :options="roleActions" @select="(key) => handleRoleAction(key, role)">
                  <n-button quaternary size="small">
                    <template #icon><n-icon><EllipsisVertical /></n-icon></template>
                  </n-button>
                </n-dropdown>
              </div>
              <p class="role-card__desc">{{ role.description }}</p>
              <div class="role-card__permissions">
                <n-tag v-for="perm in role.permissions.slice(0, 3)" :key="perm" size="small">
                  {{ perm }}
                </n-tag>
                <n-tag v-if="role.permissions.length > 3" size="small">
                  +{{ role.permissions.length - 3 }}
                </n-tag>
              </div>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- System Settings Tab -->
      <n-tab-pane name="settings" tab="系统设置">
        <div class="tab-content">
          <div class="settings-section">
            <h3 class="section-title">基础设置</h3>
            <n-form label-placement="left" label-width="160">
              <n-form-item label="平台名称">
                <n-input v-model:value="settingsForm.platformName" style="max-width: 400px" />
              </n-form-item>
              <n-form-item label="系统Logo">
                <n-upload :max="1" accept="image/*">
                  <n-button>上传Logo</n-button>
                </n-upload>
              </n-form-item>
              <n-form-item label="登录有效期">
                <n-input-number v-model:value="settingsForm.sessionTimeout" :min="1" :max="24" style="width: 200px">
                  <template #suffix>小时</template>
                </n-input-number>
              </n-form-item>
            </n-form>
          </div>

          <div class="settings-section">
            <h3 class="section-title">安全设置</h3>
            <n-form label-placement="left" label-width="160">
              <n-form-item label="密码最小长度">
                <n-input-number v-model:value="settingsForm.minPasswordLength" :min="6" :max="32" style="width: 200px" />
              </n-form-item>
              <n-form-item label="登录失败锁定">
                <n-switch v-model:value="settingsForm.lockOnFailure" />
                <span class="form-hint">连续5次失败后锁定账户30分钟</span>
              </n-form-item>
              <n-form-item label="强制双因素认证">
                <n-switch v-model:value="settingsForm.twoFactorAuth" />
              </n-form-item>
              <n-form-item label="IP白名单">
                <n-switch v-model:value="settingsForm.ipWhitelist" />
              </n-form-item>
            </n-form>
          </div>

          <div class="settings-section">
            <h3 class="section-title">存储设置</h3>
            <n-form label-placement="left" label-width="160">
              <n-form-item label="视频保留天数">
                <n-input-number v-model:value="settingsForm.videoRetention" :min="7" :max="365" style="width: 200px">
                  <template #suffix>天</template>
                </n-input-number>
              </n-form-item>
              <n-form-item label="告警保留天数">
                <n-input-number v-model:value="settingsForm.alarmRetention" :min="30" :max="365" style="width: 200px">
                  <template #suffix>天</template>
                </n-input-number>
              </n-form-item>
              <n-form-item label="日志保留天数">
                <n-input-number v-model:value="settingsForm.logRetention" :min="30" :max="365" style="width: 200px">
                  <template #suffix>天</template>
                </n-input-number>
              </n-form-item>
            </n-form>
          </div>

          <div class="settings-actions">
            <n-button>恢复默认</n-button>
            <n-button type="primary" @click="saveSettings">保存设置</n-button>
          </div>
        </div>
      </n-tab-pane>

      <!-- Operation Logs Tab -->
      <n-tab-pane name="logs" tab="操作日志">
        <div class="tab-content">
          <div class="toolbar">
            <n-select v-model:value="logFilter.type" :options="logTypeOptions" placeholder="操作类型" clearable style="width: 160px" />
            <n-select v-model:value="logFilter.user" :options="logUserOptions" placeholder="操作用户" clearable style="width: 160px" />
            <n-date-picker v-model:value="logFilter.dateRange" type="daterange" clearable style="width: 260px" />
            <n-button @click="exportLogs">
              <template #icon><n-icon><DownloadOutline /></n-icon></template>
              导出日志
            </n-button>
          </div>
          <n-data-table
            :columns="logColumns"
            :data="operationLogs"
            :pagination="{ pageSize: 10 }"
            :bordered="false"
          />
        </div>
      </n-tab-pane>
    </n-tabs>

    <!-- Add User Modal -->
    <n-modal v-model:show="showUserModal" preset="card" title="添加用户" :style="{ width: '500px' }" :bordered="false">
      <n-form :model="userForm" label-placement="left" label-width="80">
        <n-form-item label="用户名">
          <n-input v-model:value="userForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="userForm.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="邮箱">
          <n-input v-model:value="userForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="角色">
          <n-select v-model:value="userForm.role" :options="roleOptions" placeholder="请选择角色" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="userForm.department" placeholder="请输入部门" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showUserModal = false">取消</n-button>
          <n-button type="primary" @click="addUser">确认添加</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Add Role Modal -->
    <n-modal v-model:show="showRoleModal" preset="card" title="新建角色" :style="{ width: '600px' }" :bordered="false">
      <n-form :model="roleForm" label-placement="left" label-width="80">
        <n-form-item label="角色名称">
          <n-input v-model:value="roleForm.name" placeholder="请输入角色名称" />
        </n-form-item>
        <n-form-item label="角色描述">
          <n-input v-model:value="roleForm.description" type="textarea" placeholder="请输入角色描述" />
        </n-form-item>
        <n-form-item label="权限配置">
          <n-checkbox-group v-model:value="roleForm.permissions">
            <n-space vertical>
              <n-checkbox value="dashboard">首页概览</n-checkbox>
              <n-checkbox value="video">视频管理</n-checkbox>
              <n-checkbox value="algorithm">算法管理</n-checkbox>
              <n-checkbox value="alarm">告警管理</n-checkbox>
              <n-checkbox value="push">推送管理</n-checkbox>
              <n-checkbox value="system">系统管理</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showRoleModal = false">取消</n-button>
          <n-button type="primary" @click="addRole">确认创建</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { 
  NTabs, NTabPane, NButton, NIcon, NInput, NInputNumber, NSelect,
  NDataTable, NTag, NProgress, NForm, NFormItem, NSwitch, NUpload,
  NDatePicker, NModal, NCheckbox, NCheckboxGroup, NSpace, NDropdown,
  useMessage 
} from 'naive-ui'
import { 
  ServerOutline, SpeedometerOutline, HardwareChipOutline, CloudOutline,
  SearchOutline, AddOutline, PersonOutline, EllipsisVertical, DownloadOutline
} from '@vicons/ionicons5'

const message = useMessage()
const activeTab = ref('overview')

// System Info
const systemInfo = ref({
  uptime: '45天 12小时 32分',
  cpuUsage: 32,
  memoryUsed: 12.5,
  memoryTotal: 32,
  diskUsed: 1.8,
  diskTotal: 4
})

// User Management
const showUserModal = ref(false)
const userSearch = ref('')
const userForm = ref({
  username: '',
  name: '',
  email: '',
  role: null,
  department: ''
})

const users = ref([
  { id: 1, username: 'admin', name: '系统管理员', email: 'admin@example.com', role: '超级管理员', department: '技术部', status: 'active', lastLogin: '2024-01-15 14:30' },
  { id: 2, username: 'zhangsan', name: '张三', email: 'zhangsan@example.com', role: '运维管理员', department: '运维部', status: 'active', lastLogin: '2024-01-15 13:20' },
  { id: 3, username: 'lisi', name: '李四', email: 'lisi@example.com', role: '安全管理员', department: '安防部', status: 'active', lastLogin: '2024-01-15 10:15' },
  { id: 4, username: 'wangwu', name: '王五', email: 'wangwu@example.com', role: '普通用户', department: '业务部', status: 'inactive', lastLogin: '2024-01-10 09:30' }
])

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  const q = userSearch.value.toLowerCase()
  return users.value.filter(u => 
    u.username.toLowerCase().includes(q) || 
    u.name.includes(q) || 
    u.email.toLowerCase().includes(q)
  )
})

const userColumns = [
  { title: '用户名', key: 'username' },
  { title: '姓名', key: 'name' },
  { title: '邮箱', key: 'email' },
  { title: '角色', key: 'role', render: (row: any) => h(NTag, { type: row.role === '超级管理员' ? 'error' : 'info', size: 'small' }, () => row.role) },
  { title: '部门', key: 'department' },
  { title: '状态', key: 'status', render: (row: any) => h(NTag, { type: row.status === 'active' ? 'success' : 'default', size: 'small' }, () => row.status === 'active' ? '正常' : '禁用') },
  { title: '最后登录', key: 'lastLogin' },
  { 
    title: '操作', 
    key: 'actions',
    render: (row: any) => h('div', { style: 'display: flex; gap: 8px' }, [
      h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => message.info(`编辑用户: ${row.name}`) }, () => '编辑'),
      h(NButton, { text: true, type: 'error', size: 'small', onClick: () => message.warning(`删除用户: ${row.name}`) }, () => '删除')
    ])
  }
]

const roleOptions = [
  { label: '超级管理员', value: 'super' },
  { label: '运维管理员', value: 'ops' },
  { label: '安全管理员', value: 'security' },
  { label: '普通用户', value: 'user' }
]

// Role Management
const showRoleModal = ref(false)
const roleForm = ref({
  name: '',
  description: '',
  permissions: []
})

const roles = ref([
  { id: 1, name: '超级管理员', description: '拥有系统全部权限，可进行任何操作', userCount: 2, color: '#ef4444', permissions: ['首页概览', '视频管理', '算法管理', '告警管理', '推送管理', '系统管理'] },
  { id: 2, name: '运维管理员', description: '负责系统运维，设备管理等日常运营工作', userCount: 5, color: '#3b82f6', permissions: ['首页概览', '视频管理', '告警管理'] },
  { id: 3, name: '安全管理员', description: '负责安全事件处理，告警响应等安全相关工作', userCount: 8, color: '#22c55e', permissions: ['首页概览', '告警管理', '推送管理'] },
  { id: 4, name: '普通用户', description: '基础查看权限，仅可查看首页和部分功能', userCount: 24, color: '#9ca3af', permissions: ['首页概览'] }
])

const roleActions = [
  { label: '编辑角色', key: 'edit' },
  { label: '复制角色', key: 'copy' },
  { type: 'divider', key: 'd1' },
  { label: '删除角色', key: 'delete' }
]

// Settings
const settingsForm = ref({
  platformName: 'AI 视觉分析平台',
  sessionTimeout: 8,
  minPasswordLength: 8,
  lockOnFailure: true,
  twoFactorAuth: false,
  ipWhitelist: false,
  videoRetention: 30,
  alarmRetention: 90,
  logRetention: 180
})

// Operation Logs
const logFilter = ref({
  type: null,
  user: null,
  dateRange: null
})

const logTypeOptions = [
  { label: '登录/登出', value: 'auth' },
  { label: '用户管理', value: 'user' },
  { label: '系统设置', value: 'settings' },
  { label: '设备操作', value: 'device' }
]

const logUserOptions = [
  { label: 'admin', value: 'admin' },
  { label: 'zhangsan', value: 'zhangsan' },
  { label: 'lisi', value: 'lisi' }
]

const operationLogs = ref([
  { id: 1, time: '2024-01-15 14:32:15', user: 'admin', type: '系统设置', action: '修改了告警保留天数配置', ip: '192.168.1.100', result: '成功' },
  { id: 2, time: '2024-01-15 14:28:42', user: 'zhangsan', type: '设备操作', action: '重启了设备 CAM-WH-A01', ip: '192.168.1.101', result: '成功' },
  { id: 3, time: '2024-01-15 14:25:18', user: 'admin', type: '用户管理', action: '创建了新用户 wangwu', ip: '192.168.1.100', result: '成功' },
  { id: 4, time: '2024-01-15 14:20:33', user: 'lisi', type: '登录/登出', action: '用户登录系统', ip: '192.168.1.102', result: '成功' },
  { id: 5, time: '2024-01-15 14:15:27', user: 'admin', type: '系统设置', action: '启用了双因素认证', ip: '192.168.1.100', result: '成功' }
])

const logColumns = [
  { title: '时间', key: 'time', width: 180 },
  { title: '用户', key: 'user', width: 100 },
  { title: '类型', key: 'type', width: 100 },
  { title: '操作内容', key: 'action' },
  { title: 'IP 地址', key: 'ip', width: 140 },
  { title: '结果', key: 'result', width: 80, render: (row: any) => h(NTag, { type: row.result === '成功' ? 'success' : 'error', size: 'small' }, () => row.result) }
]

function addUser() {
  message.success('用户添加成功')
  showUserModal.value = false
  userForm.value = { username: '', name: '', email: '', role: null, department: '' }
}

function handleRoleAction(key: string, role: any) {
  switch (key) {
    case 'edit': message.info(`编辑角色: ${role.name}`); break
    case 'copy': message.success(`已复制角色: ${role.name}`); break
    case 'delete': message.warning(`删除角色: ${role.name}`); break
  }
}

function addRole() {
  message.success('角色创建成功')
  showRoleModal.value = false
  roleForm.value = { name: '', description: '', permissions: [] }
}

function saveSettings() {
  message.success('设置保存成功')
}

function exportLogs() {
  message.success('正在导出操作日志...')
}
</script>

<style scoped>
.system-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.system-management :deep(.n-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.system-management :deep(.n-tabs-pane-wrapper) {
  flex: 1;
  min-height: 0;
}

.system-management :deep(.n-tab-pane) {
  height: 100%;
}

.tab-content {
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-lg) 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* Section Title */
.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: var(--primary-color);
  border-radius: 2px;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.info-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  align-items: center;
}

.info-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-card__icon--primary { background: rgba(67, 24, 255, 0.1); color: var(--primary-color); }
.info-card__icon--success { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.info-card__icon--warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.info-card__icon--info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }

.info-card__content {
  flex: 1;
  min-width: 0;
}

.info-card__label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  display: block;
}

.info-card__value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.info-card :deep(.n-progress) {
  width: 100%;
  margin-top: var(--spacing-xs);
}

/* Version Table */
.version-table {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.version-row {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.version-row:last-child { border-bottom: none; }

.version-label {
  width: 160px;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.version-value {
  flex: 1;
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

/* License Card */
.license-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
}

.license-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.license-type {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.license-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.license-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.license-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.license-value {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

/* Role Grid */
.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.role-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
}

.role-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.role-card__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.role-card__info { flex: 1; }

.role-card__name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.role-card__count {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.role-card__desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin: 0 0 var(--spacing-md);
  line-height: 1.5;
}

.role-card__permissions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

/* Settings */
.settings-section {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-xl);
}

.settings-section .section-title {
  margin-bottom: var(--spacing-lg);
}

.form-hint {
  margin-left: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* Modal */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* Scrollbar */
.tab-content::-webkit-scrollbar { width: 6px; }
.tab-content::-webkit-scrollbar-track { background: transparent; }
.tab-content::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }

@media (max-width: 1200px) {
  .info-grid { grid-template-columns: repeat(2, 1fr); }
  .license-info { grid-template-columns: 1fr; }
}
</style>
