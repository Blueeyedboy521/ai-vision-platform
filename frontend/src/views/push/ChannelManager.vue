<template>
  <div class="channel-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">通道配置</h1>
        <p class="page-subtitle">管理推送通道配置</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" class="header-btn" @click="openCreate">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建通道
        </n-button>
      </div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">总通道数</span>
          <div class="stat-card__icon stat-card__icon--primary">
                <n-icon><GlobeOutline /></n-icon>
              </div>
        </div>
        <div class="stat-card__value">{{ stats.total }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">已启用</span>
          <div class="stat-card__icon stat-card__icon--success">
            <n-icon><CheckmarkCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.enabled }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">已禁用</span>
          <div class="stat-card__icon stat-card__icon--warning">
            <n-icon><AlertCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.disabled }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">钉钉</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><ChatbubbleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.dingtalk }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">通道类型</span>
          <n-select
            v-model:value="filterProvider"
            :options="providerOptions"
            placeholder="全部类型"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group">
          <span class="filter-label">状态</span>
          <n-select
            v-model:value="filterEnabled"
            :options="enabledOptions"
            placeholder="全部状态"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group filter-group--search">
          <n-input
            v-model:value="filterName"
            placeholder="快速搜索通道名称..."
            size="small"
            clearable
            class="filter-search"
            @keyup.enter="applyFilter"
          >
            <template #prefix>
              <n-icon :size="16">
                <SearchOutline />
              </n-icon>
            </template>
          </n-input>
        </div>
        <div class="filter-actions">
          <n-button type="primary" size="small" class="filter-btn" @click="applyFilter">
            <template #icon>
              <n-icon><SearchOutline /></n-icon>
            </template>
            查询
          </n-button>
          <n-button size="small" class="filter-btn" @click="resetFilter">
            重置
          </n-button>
        </div>
      </div>
    </div>

    <!-- 列表卡片 -->
    <div class="list-card card card-border-xl">
      <!-- 表头 -->
      <div class="list-header">
        <div class="list-header__col list-header__col--name">通道名称</div>
        <div class="list-header__col list-header__col--type">通道类型</div>
        <div class="list-header__col list-header__col--status">状态</div>
        <div class="list-header__col list-header__col--config">启用状态</div>
        <div class="list-header__col list-header__col--last">更新时间</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div
          v-for="(channel, index) in paginatedChannels"
          :key="channel.id"
          class="list-row"
          :class="`list-row--${channel.is_enabled ? 'online' : 'offline'}`"
        >
          <div class="list-row__col list-row__col--name">
            <div class="channel-name">
              <div class="channel-avatar" :class="`channel-avatar--${providerLabel(channel.provider)}`">
                {{ channel.name.charAt(0) }}
              </div>
              <span class="channel-name-text">{{ channel.name }}</span>
            </div>
          </div>
          <div class="list-row__col list-row__col--type">
            <n-tag :type="getTagType(channel.provider)" size="small" class="tag-with-icon">
              <template #icon>
                <n-icon :size="14">
                  <component :is="getTagIcon(channel.provider)" />
                </n-icon>
              </template>
              {{ providerLabel(channel.provider) }}
            </n-tag>
          </div>
          <div class="list-row__col list-row__col--status">
            <span class="status-dot" :class="`status-dot--${channel.is_enabled ? 'online' : 'offline'}`"></span>
            <span class="status-text">{{ channel.is_enabled ? '已启用' : '已禁用' }}</span>
          </div>
          <div class="list-row__col list-row__col--config">
            <span class="config-status" :class="channel.is_enabled ? 'config-status--ok' : 'config-status--off'">
              {{ channel.is_enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          <div class="list-row__col list-row__col--last">
            <span class="time-text">{{ formatTime(channel.updated_at) }}</span>
          </div>
          <div class="list-row__col list-row__col--action">
            <n-button text type="primary" size="small" @click="openEdit(channel)">编辑</n-button>
            <n-button text type="error" size="small" @click="confirmDelete(channel)">删除</n-button>
          </div>
        </div>
        <div v-if="paginatedChannels.length === 0" class="empty-state">
          <n-empty description="暂无通道数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 {{ pageStart }} 到 {{ pageEnd }} 条，共 {{ filteredChannels.length }} 条通道
        </div>
        <n-pagination
          v-model:page="page"
          :item-count="filteredChannels.length"
          v-model:page-size="pageSize"
          show-size-picker
          size="small"
          :page-sizes="[5, 10, 20]"
        />
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <n-modal
      v-model:show="modalVisible"
      :title="editingId ? '编辑通道' : '新建通道'"
      preset="card"
      style="width: 480px"
      :mask-closable="false"
      @after-leave="resetForm"
    >
      <n-form ref="formRef" :model="form" :rules="formRules" label-placement="left" label-width="90">
        <n-form-item label="通道名称" path="name">
          <n-input v-model:value="form.name" placeholder="如：涂装车间钉钉群" maxlength="100" show-count />
        </n-form-item>
        <n-form-item v-if="!editingId" label="通道类型" path="provider">
          <n-select
            v-model:value="form.provider"
            :options="providerOptions"
            placeholder="请选择"
            to="body"
          />
        </n-form-item>
        <template v-if="form.provider === 'dingtalk_bot'">
          <n-form-item label="Webhook 地址" path="config.webhook_url">
            <n-input
              v-model:value="form.config.webhook_url"
              type="text"
              placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
              to="body"
            />
          </n-form-item>
          <n-form-item label="加签密钥" path="config.secret">
            <n-input
              v-model:value="form.config.secret"
              type="password"
              show-password-on="click"
              placeholder="选填，安全设置中的加签密钥"
              to="body"
            />
          </n-form-item>
        </template>
        <template v-if="form.provider === 'wecom_bot'">
          <n-form-item label="Webhook 地址" path="config.webhook_url">
            <n-input
              v-model:value="form.config.webhook_url"
              type="text"
              placeholder="企业微信群机器人 Webhook URL"
              to="body"
            />
          </n-form-item>
        </template>
        <n-form-item label="启用" path="is_enabled">
          <n-switch v-model:value="form.is_enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" :loading="submitLoading" @click="submitForm">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 删除确认 -->
    <n-modal
      v-model:show="deleteModalVisible"
      preset="dialog"
      type="warning"
      title="确认删除"
      content="确定要删除该通道吗？删除后无法恢复。"
      positive-text="删除"
      negative-text="取消"
      @positive-click="doDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { FormInst, FormRules } from 'naive-ui'
import {
  getNotificationEndpoints,
  createNotificationEndpoint,
  updateNotificationEndpoint,
  deleteNotificationEndpoint,
  type NotificationEndpoint as ApiEndpoint,
  type CreateEndpointRequest,
  type ProviderType
} from '@/api/notification'
import {
  GlobeOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  SettingsOutline,
  SearchOutline,
  ChatbubbleOutline,
  MailOutline,
  PhonePortraitOutline,
  AddOutline
} from '@vicons/ionicons5'
import {
  NButton,
  NInput,
  NIcon,
  NTag,
  NSelect,
  NEmpty,
  NPagination,
  NModal,
  NForm,
  NFormItem,
  NSwitch,
  NSpace,
  useMessage
} from 'naive-ui'

const message = useMessage()
const channels = ref<ApiEndpoint[]>([])
const loading = ref(false)
const filterProvider = ref<string | null>(null)
const filterEnabled = ref<number | null>(null) // 1 启用 0 禁用
const filterName = ref('')
const page = ref(1)
const pageSize = ref(10)

const providerOptions = [
  { label: '钉钉', value: 'dingtalk_bot' },
  { label: '企业微信', value: 'wecom_bot' }
]
const enabledOptions = [
  { label: '已启用', value: 1 },
  { label: '已禁用', value: 0 }
]

function providerLabel(provider: string): string {
  return provider === 'dingtalk_bot' ? '钉钉' : provider === 'wecom_bot' ? '企业微信' : provider
}

function getTagType(provider: string): 'default' | 'error' | 'warning' | 'success' | 'primary' | 'info' {
  const map: Record<string, 'default' | 'info' | 'success' | 'warning'> = {
    dingtalk_bot: 'info',
    wecom_bot: 'success'
  }
  return map[provider] || 'default'
}

function getTagIcon(provider: string) {
  return ChatbubbleOutline
}

function formatTime(t: string | null | undefined): string {
  if (!t) return '-'
  try {
    const d = new Date(t)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return '-'
  }
}

const filteredChannels = computed(() => {
  let list = channels.value
  if (filterProvider.value) {
    list = list.filter((c) => c.provider === filterProvider.value)
  }
  if (filterEnabled.value !== null) {
    list = list.filter((c) => c.is_enabled === (filterEnabled.value === 1))
  }
  if (filterName.value.trim()) {
    const q = filterName.value.trim().toLowerCase()
    list = list.filter((c) => c.name.toLowerCase().includes(q))
  }
  return list
})

const pageStart = computed(() => (page.value - 1) * pageSize.value + 1)
const pageEnd = computed(() =>
  Math.min((page.value - 1) * pageSize.value + pageSize.value, filteredChannels.value.length)
)
const paginatedChannels = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredChannels.value.slice(start, start + pageSize.value)
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getNotificationEndpoints()
    channels.value = (res.data?.data ?? []) as ApiEndpoint[]
  } catch (e: any) {
    message.error(e?.message || '获取通道列表失败')
  } finally {
    loading.value = false
  }
}

const stats = computed(() => {
  const total = channels.value.length
  const enabled = channels.value.filter((c) => c.is_enabled).length
  const dingtalk = channels.value.filter((c) => c.provider === 'dingtalk_bot').length
  return { total, enabled, disabled: total - enabled, dingtalk }
})

async function applyFilter() {
  page.value = 1
  // 查询时重新调用后端接口，确保有请求后台
  await fetchList()
}

async function resetFilter() {
  filterProvider.value = null
  filterEnabled.value = null
  filterName.value = ''
  page.value = 1
  // 重置后也重新拉取列表
  await fetchList()
}

onMounted(() => {
  fetchList()
})

// 弹窗与表单
const modalVisible = ref(false)
const editingId = ref<string | null>(null)
const submitLoading = ref(false)
const formRef = ref<FormInst | null>(null)
const form = ref<CreateEndpointRequest & { config: Record<string, string> }>({
  name: '',
  provider: 'dingtalk_bot',
  is_enabled: true,
  config: { webhook_url: '', secret: '' }
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入通道名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择通道类型', trigger: 'change' }]
}

function openCreate() {
  editingId.value = null
  form.value = {
    name: '',
    provider: 'dingtalk_bot',
    is_enabled: true,
    config: { webhook_url: '', secret: '' }
  }
  modalVisible.value = true
}

function openEdit(row: ApiEndpoint) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    provider: row.provider,
    is_enabled: row.is_enabled,
    config: { webhook_url: '', secret: '' }
  }
  modalVisible.value = true
}

function resetForm() {
  editingId.value = null
  form.value = {
    name: '',
    provider: 'dingtalk_bot',
    is_enabled: true,
    config: { webhook_url: '', secret: '' }
  }
  formRef.value?.restoreValidation()
}

async function submitForm() {
  await formRef.value?.validate().catch(() => {})
  const payload: CreateEndpointRequest = {
    name: form.value.name.trim(),
    provider: form.value.provider as ProviderType,
    is_enabled: form.value.is_enabled
  }
  if (form.value.provider === 'dingtalk_bot' || form.value.provider === 'wecom_bot') {
    payload.config = {}
    if (form.value.config.webhook_url?.trim()) payload.config.webhook_url = form.value.config.webhook_url.trim()
    if (form.value.config.secret?.trim()) payload.config.secret = form.value.config.secret.trim()
  }
  if (editingId.value) {
    submitLoading.value = true
    try {
      const updatePayload: { name: string; is_enabled: boolean; config?: Record<string, unknown> } = {
        name: payload.name,
        is_enabled: payload.is_enabled
      }
      const cfg = payload.config || {}
      const hasNewConfig = (cfg.webhook_url && !String(cfg.webhook_url).includes('*')) || (cfg.secret && String(cfg.secret).trim() !== '')
      if (hasNewConfig) updatePayload.config = cfg
      await updateNotificationEndpoint(editingId.value, updatePayload)
      message.success('更新成功')
      modalVisible.value = false
      fetchList()
    } catch (e: any) {
      message.error(e?.message || '更新失败')
    } finally {
      submitLoading.value = false
    }
  } else {
    if (!payload.config?.webhook_url) {
      message.warning('请填写 Webhook 地址')
      return
    }
    submitLoading.value = true
    try {
      await createNotificationEndpoint(payload)
      message.success('创建成功')
      modalVisible.value = false
      fetchList()
    } catch (e: any) {
      message.error(e?.message || '创建失败')
    } finally {
      submitLoading.value = false
    }
  }
}

// 删除
const deleteModalVisible = ref(false)
const toDelete = ref<ApiEndpoint | null>(null)

function confirmDelete(row: ApiEndpoint) {
  toDelete.value = row
  deleteModalVisible.value = true
}

async function doDelete() {
  if (!toDelete.value) return
  try {
    await deleteNotificationEndpoint(toDelete.value.id)
    message.success('删除成功')
    deleteModalVisible.value = false
    toDelete.value = null
    fetchList()
  } catch (e: any) {
    message.error(e?.message || '删除失败')
  }
}
</script>

<style scoped>
.channel-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  overflow: hidden;
  background: var(--bg-page);
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.page-header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.header-btn {
  min-width: 100px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.stat-card {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
}

.stat-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.stat-card__label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.stat-card__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-card__icon--primary {
  background: rgba(67, 24, 255, 0.1);
  color: var(--primary-color);
}

.stat-card__icon--success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.stat-card__icon--warning {
  background: rgba(249, 115, 22, 0.1);
  color: var(--warning-color);
}

.stat-card__icon--info {
  background: rgba(6, 182, 212, 0.1);
  color: var(--info-color);
}

.stat-card__value {
  font-size: 32px;
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

/* 筛选栏 */
.filter-section {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: nowrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.filter-group--search {
  flex: 1;
  min-width: 200px;
}

.filter-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-select {
  width: 120px;
}

.filter-search {
  width: 100%;
  max-width: 300px;
}

.filter-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-left: auto;
  flex-shrink: 0;
}

.filter-btn {
  min-width: 70px;
}

/* 列表卡片 */
.list-card {
  flex: 1;
  background: var(--bg-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 0;
}

/* 表头 */
.list-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr 1fr;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.list-header__col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-header__col--action {
  text-align: center;
}

/* 列表内容 */
.list-body {
  flex: 1;
  overflow-y: auto;
}

.list-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr 1fr;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.list-row:hover {
  background: var(--bg-hover);
}

.list-row--online {
  background: rgba(34, 197, 94, 0.02);
}

.list-row--offline {
  background: rgba(239, 68, 68, 0.02);
}

.list-row__col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-row__col--action {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

/* 通道名称样式 */
.channel-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.channel-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.channel-avatar--短信 {
  background: rgba(6, 182, 212, 0.1);
  color: var(--info-color);
}

.channel-avatar--邮件 {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.channel-avatar--企业微信 {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.channel-avatar--APP {
  background: rgba(249, 115, 22, 0.1);
  color: var(--warning-color);
}

.channel-avatar--钉钉 {
  background: rgba(67, 56, 202, 0.1);
  color: #4338ca;
}

.channel-name-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 标签样式 */
.tag-with-icon :deep(.n-tag__content) {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 状态样式 */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  display: inline-block;
  margin-right: var(--spacing-xs);
  vertical-align: middle;
}

.status-dot--online {
  background: var(--success-color);
}

.status-dot--offline {
  background: var(--error-color);
}

.status-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  vertical-align: middle;
}

/* 配置状态 */
.config-status {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-sm);
}

.config-status--ok {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.config-status--off {
  background: rgba(156, 163, 175, 0.2);
  color: var(--text-secondary);
}

/* 时间文本 */
.time-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* 分页 */
.list-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.list-footer__info {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--text-muted);
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .list-header,
  .list-row {
    grid-template-columns: 1.5fr 1fr 1fr 1fr 1.2fr 1fr;
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }
  
  .filter-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-select,
  .filter-search {
    width: 100%;
    max-width: none;
  }
  
  .filter-actions {
    margin-left: 0;
    justify-content: flex-end;
  }
  
  .list-header,
  .list-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .list-header__col,
  .list-row__col {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }
  
  .list-header__col::before {
    content: attr(data-label);
    font-weight: var(--font-weight-medium);
    color: var(--text-secondary);
    min-width: 80px;
  }
}
</style>
