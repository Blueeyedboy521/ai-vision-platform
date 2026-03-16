<template>
  <div class="template-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">模板配置</h1>
        <p class="page-subtitle">管理推送消息模板</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" class="header-btn" @click="openCreate">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建模板
        </n-button>
      </div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">总模板数</span>
          <div class="stat-card__icon stat-card__icon--primary">
            <n-icon><DocumentOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.total }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">纯文本</span>
          <div class="stat-card__icon stat-card__icon--secondary">
            <n-icon><TextOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.text }}</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">富媒体</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><ImageOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">{{ stats.rich }}</div>
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
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">模板类型</span>
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
            placeholder="快速搜索..."
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
        <div class="list-header__col list-header__col--name">模板名称</div>
        <div class="list-header__col list-header__col--type">类型</div>
        <div class="list-header__col list-header__col--status">启用</div>
        <div class="list-header__col list-header__col--time">最后更新</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div
          v-for="(template, index) in paginatedTemplates"
          :key="template.id"
          class="list-row"
        >
          <div class="list-row__col list-row__col--name">
            <div class="template-name">
              <div class="template-avatar" :class="`template-avatar--${template.type === 'text' ? 'primary' : 'success'}`">
                {{ template.name.charAt(0) }}
              </div>
              <span class="template-name-text">{{ template.name }}</span>
            </div>
          </div>
          <div class="list-row__col list-row__col--type">
            <n-tag :type="template.type === 'text' ? 'info' : 'success'" size="small" class="tag-with-icon">
              <template #icon>
                <n-icon :size="14">
                  <component :is="template.type === 'text' ? TextOutline : ImageOutline" />
                </n-icon>
              </template>
              {{ template.type === 'text' ? '文本' : '图文' }}
            </n-tag>
          </div>
          <div class="list-row__col list-row__col--status">
            <n-switch
              :value="template.is_enabled"
              size="small"
              @update:value="(v: boolean) => toggleTemplateEnabled(template, v)"
            />
          </div>
          <div class="list-row__col list-row__col--time">
            <span class="time-text">{{ formatTime(template.updated_at) }}</span>
          </div>
          <div class="list-row__col list-row__col--action">
            <n-button text type="primary" size="small" @click="openEdit(template)">编辑</n-button>
            <n-button text type="error" size="small" @click="confirmDelete(template)">删除</n-button>
          </div>
        </div>
        <div v-if="paginatedTemplates.length === 0" class="empty-state">
          <n-empty description="暂无模板数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 {{ pageStart }} 到 {{ pageEnd }} 条，共 {{ filteredTemplates.length }} 条模板
        </div>
        <n-pagination
          v-model:page="page"
          :item-count="filteredTemplates.length"
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
      :title="editingId ? '编辑模板' : '新建模板'"
      preset="card"
      style="width: 520px"
      :mask-closable="false"
      @after-leave="resetForm"
    >
      <n-form ref="formRef" :model="form" :rules="formRules" label-placement="left" label-width="90">
        <n-form-item label="模板名称" path="name">
          <n-input v-model:value="form.name" placeholder="如：烟火告警-车间版" maxlength="100" show-count />
        </n-form-item>
        <n-form-item v-if="!editingId" label="模板类型" path="type">
          <n-select
            v-model:value="form.type"
            :options="typeOptions"
            placeholder="请选择"
            to="body"
          />
        </n-form-item>
        <n-form-item label="标题" path="content.title">
          <n-input v-model:value="form.content.title" placeholder="消息标题，支持 {{变量}}" to="body" />
        </n-form-item>
        <n-form-item label="正文" path="content.text">
          <n-input
            v-model:value="form.content.text"
            type="textarea"
            placeholder="消息正文，支持 Markdown 与 {{camera_name}}、{{area_name}}、{{level}} 等变量"
            :rows="4"
            to="body"
          />
        </n-form-item>
        <n-form-item v-if="form.type === 'rich'" label="图片 URL" path="content.image_url">
          <n-input
            v-model:value="form.content.image_url"
            placeholder="可选，支持 {{snapshot_url}} 等"
            to="body"
          />
        </n-form-item>
        <n-form-item v-if="form.type === 'rich'" label="链接 URL" path="content.link_url">
          <n-input
            v-model:value="form.content.link_url"
            placeholder="可选，详情页链接"
            to="body"
          />
        </n-form-item>
        <n-form-item label="启用" path="is_enabled">
          <n-switch v-model:value="form.is_enabled" />
        </n-form-item>
      </n-form>
      <!-- 模板示例与变量提示 -->
      <div class="template-helper">
        <div class="template-helper__example">
          <div class="template-helper__title">示例</div>
          <div class="template-helper__block">
            <div class="template-helper__label">标题示例</div>
            <div class="template-helper__code" v-pre>【{{area_name}}】{{camera_name}} {{alarm_type}} 告警</div>
          </div>
          <div class="template-helper__block">
            <div class="template-helper__label">正文示例</div>
            <div class="template-helper__code" v-pre>
              告警时间：{{alarm_time}}
              告警级别：{{level}}
              设备名称：{{camera_name}}
              所在区域：{{area_name}}
            </div>
          </div>
        </div>
        <div class="template-helper__tips">
          <div class="template-helper__title">支持的变量（占位符）</div>
          <ul class="template-helper__list">
            <li><code v-pre>{{camera_name}}</code>：摄像头名称</li>
            <li><code v-pre>{{area_name}}</code>：区域名称/路径</li>
            <li><code v-pre>{{alarm_type}}</code>：告警类型（如 烟雾、火焰）</li>
            <li><code v-pre>{{level}}</code>：告警等级（info / warning / danger / critical）</li>
            <li><code v-pre>{{alarm_time}}</code>：告警时间</li>
            <li><code v-pre>{{snapshot_url}}</code>：告警截图地址（rich 模板中可用于 image_url）</li>
            <li><code v-pre>{{link_url}}</code>：详情链接（rich 模板中可用于 link_url）</li>
          </ul>
          <div class="template-helper__tip-text">
            使用方式：在标题或正文中通过 <code v-pre>{{变量名}}</code> 占位，推送时会自动替换为告警上下文中的实际值。
          </div>
        </div>
      </div>
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
      content="确定要删除该模板吗？删除后无法恢复。"
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
  getNotificationTemplates,
  createNotificationTemplate,
  updateNotificationTemplate,
  deleteNotificationTemplate,
  type NotificationTemplate as ApiTemplate,
  type CreateTemplateRequest,
  type TemplateType
} from '@/api/notification'
import {
  DocumentOutline,
  TextOutline,
  ImageOutline,
  CheckmarkCircleOutline,
  SearchOutline,
  AddOutline
} from '@vicons/ionicons5'
import {
  NButton,
  NInput,
  NIcon,
  NTag,
  NSwitch,
  NPagination,
  NSelect,
  NEmpty,
  NModal,
  NForm,
  NFormItem,
  NSpace,
  useMessage
} from 'naive-ui'

const message = useMessage()
const templates = ref<ApiTemplate[]>([])
const filterType = ref<string | null>(null)
const filterEnabled = ref<number | null>(null)
const filterName = ref('')
const page = ref(1)
const pageSize = ref(10)

const typeOptions = [
  { label: '文本', value: 'text' },
  { label: '图文', value: 'rich' }
]
const enabledOptions = [
  { label: '已启用', value: 1 },
  { label: '已禁用', value: 0 }
]

function formatTime(t: string | null | undefined): string {
  if (!t) return '-'
  try {
    const d = new Date(t)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return '-'
  }
}

const filteredTemplates = computed(() => {
  let list = templates.value
  if (filterType.value) list = list.filter((t) => t.type === filterType.value)
  if (filterEnabled.value !== null) list = list.filter((t) => t.is_enabled === (filterEnabled.value === 1))
  if (filterName.value.trim()) {
    const q = filterName.value.trim().toLowerCase()
    list = list.filter((t) => t.name.toLowerCase().includes(q))
  }
  return list
})

const pageStart = computed(() => (page.value - 1) * pageSize.value + 1)
const pageEnd = computed(() =>
  Math.min((page.value - 1) * pageSize.value + pageSize.value, filteredTemplates.value.length)
)
const paginatedTemplates = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredTemplates.value.slice(start, start + pageSize.value)
})

async function fetchList() {
  try {
    const res = await getNotificationTemplates()
    templates.value = (res.data?.data ?? []) as ApiTemplate[]
  } catch (e: any) {
    message.error(e?.message || '获取模板列表失败')
  }
}

const stats = computed(() => {
  const total = templates.value.length
  const text = templates.value.filter((t) => t.type === 'text').length
  const rich = templates.value.filter((t) => t.type === 'rich').length
  const enabled = templates.value.filter((t) => t.is_enabled).length
  return { total, text, rich, enabled }
})

async function applyFilter() {
  page.value = 1
  // 重新从后端拉取最新列表，保证查询行为有请求后台
  await fetchList()
}

async function resetFilter() {
  filterType.value = null
  filterEnabled.value = null
  filterName.value = ''
  page.value = 1
  // 重置后重新拉取，保持与后端一致
  await fetchList()
}

async function toggleTemplateEnabled(row: ApiTemplate, v: boolean) {
  try {
    await updateNotificationTemplate(row.id, { is_enabled: v })
    message.success(v ? '已启用' : '已禁用')
    row.is_enabled = v
  } catch (e: any) {
    message.error(e?.message || '操作失败')
  }
}

onMounted(() => {
  fetchList()
})

const modalVisible = ref(false)
const editingId = ref<string | null>(null)
const submitLoading = ref(false)
const formRef = ref<FormInst | null>(null)
const form = ref<CreateTemplateRequest & { content: Record<string, string> }>({
  name: '',
  type: 'text',
  is_enabled: true,
  content: { title: '', text: '', image_url: '', link_url: '' }
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择模板类型', trigger: 'change' }]
}

function openCreate() {
  editingId.value = null
  form.value = {
    name: '',
    type: 'text',
    is_enabled: true,
    content: { title: '', text: '', image_url: '', link_url: '' }
  }
  modalVisible.value = true
}

function openEdit(row: ApiTemplate) {
  editingId.value = row.id
  const c = row.content || {}
  form.value = {
    name: row.name,
    type: row.type,
    is_enabled: row.is_enabled,
    content: {
      title: (c.title as string) ?? '',
      text: (c.text as string) ?? '',
      image_url: (c.image_url as string) ?? '',
      link_url: (c.link_url as string) ?? ''
    }
  }
  modalVisible.value = true
}

function resetForm() {
  editingId.value = null
  form.value = {
    name: '',
    type: 'text',
    is_enabled: true,
    content: { title: '', text: '', image_url: '', link_url: '' }
  }
  formRef.value?.restoreValidation()
}

async function submitForm() {
  await formRef.value?.validate().catch(() => {})
  const content: Record<string, string> = {
    title: form.value.content.title?.trim() ?? '',
    text: form.value.content.text?.trim() ?? ''
  }
  if (form.value.type === 'rich') {
    if (form.value.content.image_url?.trim()) content.image_url = form.value.content.image_url.trim()
    if (form.value.content.link_url?.trim()) content.link_url = form.value.content.link_url.trim()
  }
  if (editingId.value) {
    submitLoading.value = true
    try {
      await updateNotificationTemplate(editingId.value, {
        name: form.value.name.trim(),
        is_enabled: form.value.is_enabled,
        content
      })
      message.success('更新成功')
      modalVisible.value = false
      fetchList()
    } catch (e: any) {
      message.error(e?.message || '更新失败')
    } finally {
      submitLoading.value = false
    }
  } else {
    submitLoading.value = true
    try {
      await createNotificationTemplate({
        name: form.value.name.trim(),
        type: form.value.type as TemplateType,
        is_enabled: form.value.is_enabled,
        content
      })
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

const deleteModalVisible = ref(false)
const toDelete = ref<ApiTemplate | null>(null)

function confirmDelete(row: ApiTemplate) {
  toDelete.value = row
  deleteModalVisible.value = true
}

async function doDelete() {
  if (!toDelete.value) return
  try {
    await deleteNotificationTemplate(toDelete.value.id)
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
.template-page {
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

.stat-card__icon--secondary {
  background: rgba(124, 58, 237, 0.1);
  color: #7c3aed;
}

.stat-card__icon--info {
  background: rgba(6, 182, 212, 0.1);
  color: var(--info-color);
}

.stat-card__icon--success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
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
  grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr;
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
  grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.list-row:hover {
  background: var(--bg-hover);
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

/* 模板名称样式 */
.template-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.template-avatar {
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

.template-avatar--primary {
  background: rgba(67, 24, 255, 0.1);
  color: var(--primary-color);
}

.template-avatar--success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.template-name-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 版本标签 */
.version-tag {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: var(--bg-page);
  border-radius: var(--radius-sm);
}

/* 时间文本 */
.time-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* 标签样式 */
.tag-with-icon :deep(.n-tag__content) {
  display: flex;
  align-items: center;
  gap: 4px;
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

/* 模板示例与变量提示 */
.template-helper {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px dashed var(--border-color);
  display: grid;
  grid-template-columns: 1.4fr 1.6fr;
  gap: var(--spacing-lg);
}

.template-helper__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.template-helper__block {
  margin-bottom: var(--spacing-sm);
}

.template-helper__label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.template-helper__code {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-page);
  font-family: var(--font-family-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace);
  font-size: 12px;
  white-space: pre-line;
  color: var(--text-secondary);
}

.template-helper__tips {
  font-size: var(--font-size-xs);
}

.template-helper__list {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--spacing-sm);
}

.template-helper__list li {
  margin-bottom: 4px;
  color: var(--text-secondary);
}

.template-helper__list code {
  background: rgba(148, 163, 184, 0.16);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}

.template-helper__tip-text {
  color: var(--text-muted);
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .list-header,
  .list-row {
    grid-template-columns: 1.5fr 1fr 1fr 1.2fr 1fr;
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
