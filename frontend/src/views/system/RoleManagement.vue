<template>
  <div class="role-management">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">角色权限</h1>
        <p class="page-header__subtitle">管理系统角色及其功能权限配置</p>
      </div>
      <n-button type="primary" @click="openCreateModal">
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
          <n-tag v-for="perm in role.permissions.slice(0, 3)" :key="perm" size="small">{{ perm }}</n-tag>
          <n-tag v-if="role.permissions.length > 3" size="small">+{{ role.permissions.length - 3 }}</n-tag>
        </div>
      </div>
    </div>

    <!-- Create/Edit Role Modal -->
    <n-modal v-model:show="showRoleModal" preset="card" :title="editingRole ? '编辑角色' : '新建角色'" :style="{ width: '500px' }" :bordered="false">
      <n-form :model="roleForm" label-placement="left" label-width="80">
        <n-form-item label="角色名称" required>
          <n-input v-model:value="roleForm.name" placeholder="请输入角色名称" />
        </n-form-item>
        <n-form-item label="角色描述">
          <n-input v-model:value="roleForm.description" type="textarea" placeholder="请输入角色描述" :rows="3" />
        </n-form-item>
        <n-form-item label="角色颜色">
          <div class="color-picker">
            <div 
              v-for="color in colorOptions" 
              :key="color" 
              class="color-option" 
              :class="{ active: roleForm.color === color }"
              :style="{ background: color }"
              @click="roleForm.color = color"
            />
          </div>
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showRoleModal = false">取消</n-button>
          <n-button type="primary" @click="saveRole">{{ editingRole ? '保存' : '创建' }}</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Authorization Modal -->
    <n-modal v-model:show="showAuthModal" preset="card" title="权限配置" :style="{ width: '600px' }" :bordered="false">
      <div v-if="authRole" class="auth-header">
        <div class="auth-role-info">
          <div class="auth-role-icon" :style="{ background: authRole.color }">
            <n-icon :size="20" color="#fff"><PersonOutline /></n-icon>
          </div>
          <div>
            <h4 class="auth-role-name">{{ authRole.name }}</h4>
            <span class="auth-role-desc">{{ authRole.description }}</span>
          </div>
        </div>
      </div>

      <div class="permission-groups">
        <div v-for="group in permissionGroups" :key="group.key" class="permission-group">
          <div class="permission-group__header">
            <n-checkbox 
              :checked="isGroupChecked(group.key)" 
              :indeterminate="isGroupIndeterminate(group.key)"
              @update:checked="toggleGroup(group.key, $event)"
            >
              <span class="permission-group__title">{{ group.label }}</span>
            </n-checkbox>
          </div>
          <div class="permission-group__items">
            <n-checkbox
              v-for="item in group.children"
              :key="item.key"
              :checked="selectedPermissions.includes(item.key)"
              @update:checked="togglePermission(item.key, $event)"
            >
              {{ item.label }}
            </n-checkbox>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer">
          <n-button @click="showAuthModal = false">取消</n-button>
          <n-button type="primary" @click="savePermissions">保存授权</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NButton, NIcon, NTag, NDropdown, NModal, NForm, NFormItem, NInput, NCheckbox, useMessage } from 'naive-ui'
import { AddOutline, PersonOutline, EllipsisVertical } from '@vicons/ionicons5'

interface Role {
  id: number
  name: string
  description: string
  userCount: number
  color: string
  permissions: string[]
  permissionKeys: string[]
}

const message = useMessage()
const showRoleModal = ref(false)
const showAuthModal = ref(false)
const editingRole = ref<Role | null>(null)
const authRole = ref<Role | null>(null)
const selectedPermissions = ref<string[]>([])

const roleForm = ref({
  name: '',
  description: '',
  color: '#4318FF'
})

const colorOptions = ['#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#4318FF', '#6366f1']

const roles = ref<Role[]>([
  { id: 1, name: '超级管理员', description: '拥有系统全部权限，可进行任何操作', userCount: 2, color: '#ef4444', permissions: ['首页概览', '视频管理', '算法管理', '告警管理', '推送管理', '系统配置'], permissionKeys: ['dashboard', 'video-view', 'video-edit', 'algorithm-view', 'algorithm-edit', 'alarm-view', 'alarm-handle', 'push-view', 'push-edit', 'system-overview', 'system-users', 'system-roles', 'system-settings', 'system-logs'] },
  { id: 2, name: '运维管理员', description: '负责系统运维，设备管理等日常运营工作', userCount: 5, color: '#3b82f6', permissions: ['首页概览', '视频管理', '告警管理'], permissionKeys: ['dashboard', 'video-view', 'video-edit', 'alarm-view', 'alarm-handle'] },
  { id: 3, name: '安全管理员', description: '负责安全事件处理，告警响应等安全相关工作', userCount: 8, color: '#22c55e', permissions: ['首页概览', '告警管理', '推送管理'], permissionKeys: ['dashboard', 'alarm-view', 'alarm-handle', 'push-view'] },
  { id: 4, name: '普通用户', description: '基础查看权限，仅可查看首页和部分功能', userCount: 24, color: '#9ca3af', permissions: ['首页概览'], permissionKeys: ['dashboard'] }
])

const permissionGroups = [
  {
    key: 'dashboard',
    label: '首页概览',
    children: [
      { key: 'dashboard', label: '查看首页' }
    ]
  },
  {
    key: 'video',
    label: '视频管理',
    children: [
      { key: 'video-view', label: '查看视频' },
      { key: 'video-edit', label: '编辑摄像头' },
      { key: 'video-delete', label: '删除摄像头' }
    ]
  },
  {
    key: 'algorithm',
    label: '算法管理',
    children: [
      { key: 'algorithm-view', label: '查看算法' },
      { key: 'algorithm-edit', label: '配置算法' },
      { key: 'algorithm-deploy', label: '部署算法' }
    ]
  },
  {
    key: 'alarm',
    label: '告警管理',
    children: [
      { key: 'alarm-view', label: '查看告警' },
      { key: 'alarm-handle', label: '处理告警' },
      { key: 'alarm-delete', label: '删除告警' }
    ]
  },
  {
    key: 'push',
    label: '推送管理',
    children: [
      { key: 'push-view', label: '查看推送配置' },
      { key: 'push-edit', label: '编辑推送配置' }
    ]
  },
  {
    key: 'system',
    label: '系统配置',
    children: [
      { key: 'system-overview', label: '系统概览' },
      { key: 'system-users', label: '用户管理' },
      { key: 'system-roles', label: '角色权限' },
      { key: 'system-settings', label: '系统设置' },
      { key: 'system-logs', label: '操作日志' }
    ]
  }
]

const roleActions = [
  { label: '授权配置', key: 'auth' },
  { label: '编辑角色', key: 'edit' },
  { label: '复制角色', key: 'copy' },
  { type: 'divider', key: 'd1' },
  { label: '删除角色', key: 'delete' }
]

function isGroupChecked(groupKey: string) {
  const group = permissionGroups.find(g => g.key === groupKey)
  if (!group) return false
  return group.children.every(child => selectedPermissions.value.includes(child.key))
}

function isGroupIndeterminate(groupKey: string) {
  const group = permissionGroups.find(g => g.key === groupKey)
  if (!group) return false
  const checkedCount = group.children.filter(child => selectedPermissions.value.includes(child.key)).length
  return checkedCount > 0 && checkedCount < group.children.length
}

function toggleGroup(groupKey: string, checked: boolean) {
  const group = permissionGroups.find(g => g.key === groupKey)
  if (!group) return
  
  if (checked) {
    group.children.forEach(child => {
      if (!selectedPermissions.value.includes(child.key)) {
        selectedPermissions.value.push(child.key)
      }
    })
  } else {
    group.children.forEach(child => {
      const index = selectedPermissions.value.indexOf(child.key)
      if (index > -1) selectedPermissions.value.splice(index, 1)
    })
  }
}

function togglePermission(key: string, checked: boolean) {
  if (checked) {
    if (!selectedPermissions.value.includes(key)) {
      selectedPermissions.value.push(key)
    }
  } else {
    const index = selectedPermissions.value.indexOf(key)
    if (index > -1) selectedPermissions.value.splice(index, 1)
  }
}

function openCreateModal() {
  editingRole.value = null
  roleForm.value = { name: '', description: '', color: '#4318FF' }
  showRoleModal.value = true
}

function handleRoleAction(key: string, role: Role) {
  switch (key) {
    case 'auth':
      authRole.value = role
      selectedPermissions.value = [...role.permissionKeys]
      showAuthModal.value = true
      break
    case 'edit':
      editingRole.value = role
      roleForm.value = { name: role.name, description: role.description, color: role.color }
      showRoleModal.value = true
      break
    case 'copy':
      roles.value.push({
        ...role,
        id: Date.now(),
        name: role.name + ' (副本)',
        userCount: 0
      })
      message.success('角色已复制')
      break
    case 'delete':
      const index = roles.value.findIndex(r => r.id === role.id)
      if (index > -1) {
        roles.value.splice(index, 1)
        message.success('角色已删除')
      }
      break
  }
}

function saveRole() {
  if (editingRole.value) {
    editingRole.value.name = roleForm.value.name
    editingRole.value.description = roleForm.value.description
    editingRole.value.color = roleForm.value.color
    message.success('角色已更新')
  } else {
    roles.value.push({
      id: Date.now(),
      name: roleForm.value.name,
      description: roleForm.value.description,
      color: roleForm.value.color,
      userCount: 0,
      permissions: [],
      permissionKeys: []
    })
    message.success('角色创建成功')
  }
  showRoleModal.value = false
}

function savePermissions() {
  if (authRole.value) {
    authRole.value.permissionKeys = [...selectedPermissions.value]
    // Update display permissions based on groups
    const permNames: string[] = []
    permissionGroups.forEach(group => {
      if (group.children.some(c => selectedPermissions.value.includes(c.key))) {
        permNames.push(group.label)
      }
    })
    authRole.value.permissions = permNames
    message.success('权限配置已保存')
  }
  showAuthModal.value = false
}
</script>

<style scoped>
.role-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
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

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  flex: 1;
  overflow-y: auto;
  padding-bottom: var(--spacing-lg);
}

.role-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  transition: all 0.3s ease;
  height: 180px;
  max-height: 180px;
  display: flex;
  flex-direction: column;
}

.role-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
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
.role-card__name { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); color: var(--text-primary); margin: 0; }
.role-card__count { font-size: var(--font-size-sm); color: var(--text-muted); }
.role-card__desc { font-size: var(--font-size-sm); color: var(--text-muted); margin: 0 0 var(--spacing-md); line-height: 1.5; flex: 1; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.role-card__permissions { display: flex; flex-wrap: wrap; gap: var(--spacing-xs); flex-shrink: 0; }

.color-picker {
  display: flex;
  gap: var(--spacing-sm);
}

.color-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-option:hover { transform: scale(1.1); }
.color-option.active { border-color: var(--text-primary); box-shadow: 0 0 0 2px var(--bg-card); }

.auth-header {
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: var(--spacing-lg);
}

.auth-role-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.auth-role-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-role-name { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); color: var(--text-primary); margin: 0 0 4px; }
.auth-role-desc { font-size: var(--font-size-sm); color: var(--text-muted); }

.permission-groups {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-height: 400px;
  overflow-y: auto;
}

.permission-group {
  background: var(--bg-page);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.permission-group__header {
  margin-bottom: var(--spacing-sm);
}

.permission-group__title {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.permission-group__items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  padding-left: var(--spacing-xl);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
