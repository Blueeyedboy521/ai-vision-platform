<template>
  <div class="user-management">
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">用户管理</h1>
        <p class="page-header__subtitle">管理系统用户账号、权限分配</p>
      </div>
      <n-button type="primary" @click="showModal = true">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        添加用户
      </n-button>
    </div>

    <div class="toolbar">
      <n-input v-model:value="searchQuery" placeholder="搜索用户名、姓名、邮箱..." style="width: 300px" clearable>
        <template #prefix><n-icon><SearchOutline /></n-icon></template>
      </n-input>
      <n-select v-model:value="roleFilter" :options="roleOptions" placeholder="筛选角色" clearable style="width: 160px" />
      <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="筛选状态" clearable style="width: 140px" />
    </div>

    <div class="table-wrapper">
      <n-data-table
        :columns="columns"
        :data="filteredUsers"
        :pagination="{ pageSize: 10 }"
        :bordered="false"
      />
    </div>

    <!-- Add/Edit User Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingUser ? '编辑用户' : '添加用户'" :style="{ width: '500px' }" :bordered="false">
      <n-form :model="formData" label-placement="left" label-width="80">
        <n-form-item label="用户名" required>
          <n-input v-model:value="formData.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="姓名" required>
          <n-input v-model:value="formData.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="邮箱" required>
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="手机号">
          <n-input v-model:value="formData.phone" placeholder="请输入手机号" />
        </n-form-item>
        <n-form-item label="角色" required>
          <n-select v-model:value="formData.role" :options="roleOptions" placeholder="请选择角色" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="formData.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item v-if="!editingUser" label="初始密码">
          <n-input v-model:value="formData.password" type="password" placeholder="请输入初始密码" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="saveUser">{{ editingUser ? '保存' : '添加' }}</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { NButton, NIcon, NInput, NSelect, NDataTable, NModal, NForm, NFormItem, NTag, NSwitch, useMessage } from 'naive-ui'
import { AddOutline, SearchOutline } from '@vicons/ionicons5'
import { getUserList, createUser, updateUser, deleteUser as deleteUserApi, resetUserPassword, enableUser, disableUser, type User as ApiUser } from '@/api/user'

interface User {
  id: string
  username: string
  name: string
  email: string
  phone: string
  role: string
  department: string
  status: 'active' | 'inactive'
  lastLogin: string
}

const message = useMessage()
const showModal = ref(false)
const editingUser = ref<User | null>(null)
const searchQuery = ref('')
const roleFilter = ref(null)
const statusFilter = ref(null)
const loading = ref(false)

const formData = ref({
  username: '',
  name: '',
  email: '',
  phone: '',
  role: null as string | null,
  department: '',
  password: ''
})

const users = ref<User[]>([])

// 转换后端用户数据
function convertUser(apiUser: ApiUser): User {
  return {
    id: apiUser.id,
    username: apiUser.username,
    name: apiUser.nickname || apiUser.username,
    email: apiUser.email || '',
    phone: apiUser.phone || '',
    role: apiUser.is_admin ? '超级管理员' : (apiUser.role === 'admin' ? '运维管理员' : apiUser.role === 'operator' ? '安全管理员' : '普通用户'),
    department: '',
    status: apiUser.is_active ? 'active' : 'inactive',
    lastLogin: apiUser.last_login_at || '-'
  }
}

// 加载用户列表
async function loadUsers() {
  loading.value = true
  try {
    const response = await getUserList({ keyword: searchQuery.value || undefined })
    if (response.data.data) {
      users.value = response.data.data.items.map(convertUser)
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadUsers(), 300)
})

onMounted(() => {
  loadUsers()
})

const roleOptions = [
  { label: '超级管理员', value: '超级管理员' },
  { label: '运维管理员', value: '运维管理员' },
  { label: '安全管理员', value: '安全管理员' },
  { label: '普通用户', value: '普通用户' }
]

const statusOptions = [
  { label: '正常', value: 'active' },
  { label: '禁用', value: 'inactive' }
]

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    if (roleFilter.value && user.role !== roleFilter.value) return false
    if (statusFilter.value && user.status !== statusFilter.value) return false
    return true
  })
})

const columns = [
  { title: '用户名', key: 'username', width: 120 },
  { title: '姓名', key: 'name', width: 100 },
  { title: '邮箱', key: 'email', width: 180 },
  { title: '手机号', key: 'phone', width: 120 },
  { title: '角色', key: 'role', width: 120, render: (row: User) => h(NTag, { type: row.role === '超级管理员' ? 'error' : row.role === '运维管理员' ? 'warning' : 'info', size: 'small' }, () => row.role) },
  { title: '部门', key: 'department', width: 100 },
  { title: '状态', key: 'status', width: 80, render: (row: User) => h(NSwitch, { value: row.status === 'active', onUpdateValue: (v: boolean) => toggleStatus(row, v) }) },
  { title: '最后登录', key: 'lastLogin', width: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: User) => h('div', { style: 'display: flex; gap: 8px' }, [
      h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => editUser(row) }, () => '编辑'),
      h(NButton, { text: true, type: 'warning', size: 'small', onClick: () => handleResetPassword(row) }, () => '重置密码'),
      h(NButton, { text: true, type: 'error', size: 'small', onClick: () => handleDeleteUser(row) }, () => '删除')
    ])
  }
]

async function toggleStatus(user: User, active: boolean) {
  try {
    if (active) {
      await enableUser(user.id)
    } else {
      await disableUser(user.id)
    }
    user.status = active ? 'active' : 'inactive'
    message.success(active ? '用户已启用' : '用户已禁用')
  } catch (error: any) {
    message.error(error.message || '操作失败')
  }
}

function editUser(user: User) {
  editingUser.value = user
  formData.value = { ...user, password: '', role: user.role }
  showModal.value = true
}

async function handleResetPassword(user: User) {
  try {
    await resetUserPassword(user.id, 'password123')
    message.success(`已重置 ${user.name} 的密码为: password123`)
  } catch (error: any) {
    message.error(error.message || '重置密码失败')
  }
}

async function handleDeleteUser(user: User) {
  try {
    await deleteUserApi(user.id)
    await loadUsers()
    message.success('用户已删除')
  } catch (error: any) {
    message.error(error.message || '删除用户失败')
  }
}

async function saveUser() {
  try {
    const roleMap: Record<string, string> = {
      '超级管理员': 'admin',
      '运维管理员': 'admin',
      '安全管理员': 'operator',
      '普通用户': 'viewer'
    }
    
    if (editingUser.value) {
      await updateUser(editingUser.value.id, {
        nickname: formData.value.name,
        email: formData.value.email || undefined,
        phone: formData.value.phone || undefined,
        role: roleMap[formData.value.role || '普通用户'] as any
      })
      message.success('用户信息已更新')
    } else {
      await createUser({
        username: formData.value.username,
        password: formData.value.password || 'password123',
        nickname: formData.value.name,
        email: formData.value.email || undefined,
        phone: formData.value.phone || undefined,
        role: roleMap[formData.value.role || '普通用户'] as any
      })
      message.success('用户添加成功')
    }
    showModal.value = false
    editingUser.value = null
    formData.value = { username: '', name: '', email: '', phone: '', role: null, department: '', password: '' }
    await loadUsers()
  } catch (error: any) {
    message.error(error.message || '保存失败')
  }
}
</script>

<style scoped>
.user-management {
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

.toolbar {
  display: flex;
  gap: var(--spacing-md);
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
