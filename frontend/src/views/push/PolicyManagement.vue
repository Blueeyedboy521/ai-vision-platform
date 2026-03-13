<template>
  <div class="policy-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">策略配置</h1>
        <p class="page-subtitle">管理推送策略配置</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" class="header-btn" @click="handleAddPolicy">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            新建策略
          </n-button>
      </div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">总策略</span>
          <div class="stat-card__icon stat-card__icon--primary">
            <n-icon><DocumentTextOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ totalPolicies }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">启用策略</span>
          <div class="stat-card__icon stat-card__icon--success">
            <n-icon><ToggleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ enabledPolicies }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">系统策略</span>
          <div class="stat-card__icon stat-card__icon--warning">
            <n-icon><SettingsOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ systemPolicies }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">业务策略</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><BusinessOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ businessPolicies }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">策略类型</span>
          <n-select
            v-model:value="filterType"
            :options="typeOptions"
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
            v-model:value="filterStatus"
            :options="statusOptions"
            placeholder="全部状态"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group filter-group--search">
          <n-input
            v-model:value="filterKeyword"
            placeholder="快速搜索策略名称..."
            size="small"
            clearable
            class="filter-search"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <n-icon :size="16">
                <SearchOutline />
              </n-icon>
            </template>
          </n-input>
        </div>
        <div class="filter-actions">
          <n-button type="primary" size="small" class="filter-btn" @click="handleSearch">
            <template #icon>
              <n-icon><SearchOutline /></n-icon>
            </template>
            查询
          </n-button>
          <n-button size="small" class="filter-btn" @click="handleReset">
            重置
          </n-button>
        </div>
      </div>
    </div>

    <!-- 列表卡片 -->
    <div class="list-card card card-border-xl">
      <!-- 表头 -->
      <div class="list-header">
        <div class="list-header__col list-header__col--name">策略名称</div>
        <div class="list-header__col list-header__col--type">类型</div>
        <div class="list-header__col list-header__col--alarm">告警类型</div>
        <div class="list-header__col list-header__col--rule">匹配规则</div>
        <div class="list-header__col list-header__col--desc">推动动作</div>
        <div class="list-header__col list-header__col--channel">渠道</div>
        <div class="list-header__col list-header__col--status">状态</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div
          v-for="(policy, index) in pagedPolicies"
          :key="policy.id"
          class="list-row"
          :class="`list-row--${policy.status ? 'enabled' : 'disabled'}`"
        >
          <div class="list-row__col list-row__col--name">
            <div class="policy-name">
              <div class="policy-avatar" :class="`policy-avatar--${getAvatarClass(policy.name)}`">
                {{ policy.name.charAt(0) }}
              </div>
              <span class="policy-name-text">{{ policy.name }}</span>
            </div>
          </div>
          <div class="list-row__col list-row__col--type">
            <n-tag :type="policy.type === '触发式' ? 'info' : 'success'" size="small" class="tag-with-icon">
                <template #icon>
                  <n-icon :size="14">
                    <component :is="policy.type === '触发式' ? AlertCircleOutline : CalendarOutline" />
                  </n-icon>
                </template>
                {{ policy.type }}
              </n-tag>
          </div>
          <div class="list-row__col list-row__col--alarm">
            <n-tooltip trigger="hover" :disabled="!policy.alarmType">
              <template #trigger>
                <n-tag type="warning" size="small" class="ellipsis-tag">{{ policy.alarmType || '-' }}</n-tag>
              </template>
              <span>{{ policy.alarmType }}</span>
            </n-tooltip>
          </div>
          <div class="list-row__col list-row__col--rule">
            <n-tooltip trigger="hover" :disabled="!policy.matchRule">
              <template #trigger>
                <span class="rule-text ellipsis">{{ policy.matchRule || '-' }}</span>
              </template>
              <span>{{ policy.matchRule }}</span>
            </n-tooltip>
          </div>
          <div class="list-row__col list-row__col--desc">
            <n-tooltip trigger="hover" :disabled="!policy.actionDesc">
              <template #trigger>
                <span class="desc-text ellipsis">{{ policy.actionDesc || '-' }}</span>
              </template>
              <span>{{ policy.actionDesc }}</span>
            </n-tooltip>
          </div>
          <div class="list-row__col list-row__col--channel">
            <n-tooltip trigger="hover" :disabled="policy.channels.length <= 1">
              <template #trigger>
                <div class="channel-tags">
                  <n-tag
                    v-for="(channel, idx) in policy.channels.slice(0, 2)"
                    :key="idx"
                    size="small"
                    type="default"
                    class="channel-tag"
                  >
                    {{ channel }}
                  </n-tag>
                  <n-tag v-if="policy.channels.length > 2" size="small" type="default" class="channel-tag">
                    +{{ policy.channels.length - 2 }}
                  </n-tag>
                  <span v-if="policy.channels.length === 0" class="text-muted">-</span>
                </div>
              </template>
              <span>{{ policy.channels.join('、') }}</span>
            </n-tooltip>
          </div>
          <div class="list-row__col list-row__col--status">
            <n-switch v-model:value="policy.status" size="small" @update:value="() => handleToggleStatus(policy)" />
          </div>
          <div class="list-row__col list-row__col--action">
            <n-button text type="primary" size="small" @click="handleEditPolicy(policy)">编辑</n-button>
            <n-button text type="error" size="small" @click="handleDeletePolicy(policy)">删除</n-button>
          </div>
        </div>
        <div v-if="policies.length === 0" class="empty-state">
          <n-empty description="暂无策略数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 {{ pageStart }} 到 {{ pageEnd }} 条，共 {{ filteredPolicies.length }} 条策略
        </div>
        <n-pagination
          v-model:page="page"
          v-model:page-size="pageSize"
          :item-count="filteredPolicies.length"
          show-size-picker
          size="small"
          :page-sizes="[5, 10, 20]"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  DocumentTextOutline, 
  ToggleOutline, 
  CalendarOutline, 
  FlameOutline, 
  SearchOutline, 
  AlertCircleOutline,
  SettingsOutline,
  BusinessOutline,
  AddOutline
} from '@vicons/ionicons5'
import { NButton, NInput, NIcon, NTag, NSelect, NEmpty, NPagination, NSwitch, NTooltip, useMessage } from 'naive-ui'
import {
  getNotificationPolicies,
  getNotificationEndpoints,
  deleteNotificationPolicy,
  updateNotificationPolicy,
  type NotificationPolicy,
  type NotificationEndpoint
} from '@/api/notification'

const router = useRouter()
const message = useMessage()

function handleAddPolicy() {
  router.push('/push/add-policy')
}

interface PolicyRow {
  id: string
  name: string
  type: string
  alarmType: string
  matchRule: string
  actionDesc: string
  channels: string[]
  status: boolean
}

const policies = ref<PolicyRow[]>([])
const loading = ref(false)
const endpointNameMap = ref<Record<string, string>>({})

// 查询条件
const filterType = ref<string | null>(null)
const filterStatus = ref<string | null>(null)
const filterKeyword = ref('')

const typeOptions = [
  { label: 'AI告警', value: 'AI告警' },
  { label: '系统告警', value: '系统告警' }
]

const statusOptions = [
  { label: '已启用', value: 'enabled' },
  { label: '已禁用', value: 'disabled' }
]

const totalPolicies = computed(() => policies.value.length)
const enabledPolicies = computed(() => policies.value.filter((p) => p.status).length)
const systemPolicies = computed(() => policies.value.filter((p) => p.type === '系统告警').length)
const businessPolicies = computed(() => policies.value.filter((p) => p.type === 'AI告警').length)

const filteredPolicies = computed(() => {
  return policies.value.filter((p) => {
    if (filterType.value && p.type !== filterType.value) return false
    if (filterStatus.value === 'enabled' && !p.status) return false
    if (filterStatus.value === 'disabled' && p.status) return false
    const kw = filterKeyword.value.trim().toLowerCase()
    if (kw) {
      const joined = `${p.name} ${p.alarmType} ${p.matchRule} ${p.actionDesc}`.toLowerCase()
      if (!joined.includes(kw)) return false
    }
    return true
  })
})

const page = ref(1)
const pageSize = ref(5)

const pagedPolicies = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredPolicies.value.slice(start, start + pageSize.value)
})

const pageStart = computed(() =>
  filteredPolicies.value.length === 0 ? 0 : (page.value - 1) * pageSize.value + 1
)
const pageEnd = computed(() =>
  Math.min(page.value * pageSize.value, filteredPolicies.value.length)
)

async function fetchPolicies() {
  loading.value = true
  try {
    const res = await getNotificationPolicies()
    const list = (res.data?.data || []) as NotificationPolicy[]
    policies.value = list.map((p) => ({
      id: p.id,
      name: p.name,
      type: (p.match as any)?.category === 'system' ? '系统告警' : 'AI告警',
      alarmType: (() => {
        const m: any = p.match || {}
        const cfg = Array.isArray(m.alarm_config) ? m.alarm_config : []
        const labels = cfg
          .map((x: any) => String(x?.label || x?.value || ''))
          .filter((x: string) => x)
        return labels.join('、') || ''
      })(),
      matchRule: p.match_desc || '',
      actionDesc: p.actions_desc || '',
      channels: (() => {
        const acts: any[] = Array.isArray(p.actions) ? p.actions : []
        const ids = new Set<string>()
        for (const a of acts) {
          const epIds = Array.isArray(a?.endpoint_ids) ? a.endpoint_ids : []
          for (const eid of epIds) ids.add(String(eid))
        }
        return Array.from(ids).map((id) => endpointNameMap.value[id] || id)
      })(),
      status: p.is_enabled
    }))
  } catch (e: any) {
    console.error('加载策略列表失败:', e)
    message.error(e?.message || '加载策略列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
}

function handleReset() {
  filterType.value = null
  filterStatus.value = null
  filterKeyword.value = ''
  page.value = 1
}

async function fetchEndpoints() {
  try {
    const res = await getNotificationEndpoints()
    const list = (res.data?.data || []) as NotificationEndpoint[]
    const map: Record<string, string> = {}
    for (const ep of list) map[ep.id] = ep.name
    endpointNameMap.value = map
  } catch {
    endpointNameMap.value = {}
  }
}

function getAvatarClass(name: string): string {
  const firstChar = name.charAt(0)
  const classes = ['primary', 'success', 'warning', 'info', 'secondary']
  return classes[firstChar.charCodeAt(0) % classes.length]
}

async function handleToggleStatus(row: PolicyRow) {
  try {
    await updateNotificationPolicy(row.id, { is_enabled: row.status })
    message.success(row.status ? '已启用' : '已禁用')
  } catch (e: any) {
    message.error(e?.message || '更新状态失败')
    row.status = !row.status
  }
}

async function handleDeletePolicy(row: PolicyRow) {
  try {
    await deleteNotificationPolicy(row.id)
    policies.value = policies.value.filter((p) => p.id !== row.id)
    message.success('删除成功')
  } catch (e: any) {
    message.error(e?.message || '删除失败')
  }
}

function handleEditPolicy(row: PolicyRow) {
  router.push({ path: '/push/add-policy', query: { id: row.id } })
}

onMounted(() => {
  Promise.resolve(fetchEndpoints()).finally(fetchPolicies)
})
</script>

<style scoped>
.policy-page {
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
  grid-template-columns: 2fr 0.9fr 1.2fr 2fr 2fr 1.5fr 0.8fr 0.9fr;
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
  grid-template-columns: 2fr 0.9fr 1.2fr 2fr 2fr 1.5fr 0.8fr 0.9fr;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.list-row:hover {
  background: var(--bg-hover);
}

.list-row--enabled {
  background: rgba(34, 197, 94, 0.02);
}

.list-row--disabled {
  background: rgba(239, 68, 68, 0.02);
}

.list-row__col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ellipsis-tag {
  max-width: 100%;
}

.list-row__col--action {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

/* 策略名称样式 */
.policy-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.policy-avatar {
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

.policy-avatar--primary {
  background: rgba(67, 24, 255, 0.1);
  color: var(--primary-color);
}

.policy-avatar--success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.policy-avatar--warning {
  background: rgba(249, 115, 22, 0.1);
  color: var(--warning-color);
}

.policy-avatar--info {
  background: rgba(6, 182, 212, 0.1);
  color: var(--info-color);
}

.policy-avatar--secondary {
  background: rgba(124, 58, 237, 0.1);
  color: #7c3aed;
}

.policy-name-text {
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

/* 通道标签 */
.channel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  align-items: center;
}

.channel-tag {
  margin-right: var(--spacing-xs);
}

/* 时间文本 */
.time-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* 规则文本 */
.rule-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 描述文本 */
.desc-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
    grid-template-columns: 1.5fr 1fr 1.2fr 1fr 1.2fr 1fr;
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
