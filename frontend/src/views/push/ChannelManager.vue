<template>
  <div class="channel-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">通道配置</h1>
        <p class="page-subtitle">管理推送通道配置</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" class="header-btn">
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
        <div class="stat-card__value">16</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">正常通道</span>
          <div class="stat-card__icon stat-card__icon--success">
            <n-icon><CheckmarkCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">14</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">异常通道</span>
          <div class="stat-card__icon stat-card__icon--warning">
            <n-icon><AlertCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">2</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">已启用通道</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><SettingsOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">8</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">通道类型</span>
          <n-select
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
            placeholder="全部状态"
            clearable
            size="small"
            class="filter-select"
            to="body"
          />
        </div>
        <div class="filter-group filter-group--search">
          <n-input
            placeholder="快速搜索通道名称..."
            size="small"
            clearable
            class="filter-search"
          >
            <template #prefix>
              <n-icon :size="16">
                <SearchOutline />
              </n-icon>
            </template>
          </n-input>
        </div>
        <div class="filter-actions">
          <n-button type="primary" size="small" class="filter-btn">
            <template #icon>
              <n-icon><SearchOutline /></n-icon>
            </template>
            查询
          </n-button>
          <n-button size="small" class="filter-btn">
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
        <div class="list-header__col list-header__col--last">最后测试</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div
          v-for="(channel, index) in channels"
          :key="channel.id"
          class="list-row"
          :class="`list-row--${channel.status === '正常' ? 'online' : 'offline'}`"
        >
          <div class="list-row__col list-row__col--name">
            <div class="channel-name">
              <div class="channel-avatar" :class="`channel-avatar--${channel.type}`">
                {{ channel.name.charAt(0) }}
              </div>
              <span class="channel-name-text">{{ channel.name }}</span>
            </div>
          </div>
          <div class="list-row__col list-row__col--type">
            <n-tag :type="getTagType(channel.type)" size="small" class="tag-with-icon">
              <template #icon>
                <n-icon :size="14">
                  <component :is="getTagIcon(channel.type)" />
                </n-icon>
              </template>
              {{ channel.type }}
            </n-tag>
          </div>
          <div class="list-row__col list-row__col--status">
            <span class="status-dot" :class="`status-dot--${channel.status === '正常' ? 'online' : 'offline'}`"></span>
            <span class="status-text">{{ channel.status }}</span>
          </div>
          <div class="list-row__col list-row__col--config">
            <span class="config-status config-status--ok">{{ channel.enabledStatus }}</span>
          </div>
          <div class="list-row__col list-row__col--last">
            <span class="time-text">{{ channel.lastTest }}</span>
          </div>
          <div class="list-row__col list-row__col--action">
            <n-button text type="primary" size="small">编辑</n-button>
            <n-button text type="error" size="small">删除</n-button>
          </div>
        </div>
        <div v-if="channels.length === 0" class="empty-state">
          <n-empty description="暂无通道数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 1 到 5 条，共 16 条通道
        </div>
        <n-pagination
          :page="1"
          :item-count="16"
          :page-size="5"
          show-size-picker
          size="small"
          :page-sizes="[5, 10, 20]"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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
import { NButton, NInput, NIcon, NTag, NSelect, NEmpty, NPagination } from 'naive-ui'

// 通道数据
const channels = ref([
  {
    id: 1,
    name: '阿里云短信通道',
    type: '短信',
    status: '正常',
    enabledStatus: '已启用',
    lastTest: '2023-10-24 09:30'
  },
  {
    id: 2,
    name: '企业邮件服务',
    type: '邮件',
    status: '正常',
    enabledStatus: '已启用',
    lastTest: '2023-10-23 16:45'
  },
  {
    id: 3,
    name: '企业微信',
    type: '企业微信',
    status: '异常',
    enabledStatus: '已启用',
    lastTest: '2023-10-22 11:20'
  },
  {
    id: 4,
    name: 'APP推送',
    type: 'APP',
    status: '正常',
    enabledStatus: '已启用',
    lastTest: '2023-10-21 14:10'
  },
  {
    id: 5,
    name: '钉钉通知',
    type: '钉钉',
    status: '异常',
    enabledStatus: '已启用',
    lastTest: '2023-10-20 09:00'
  }
])

// 获取标签类型
function getTagType(type: string): "default" | "error" | "warning" | "success" | "primary" | "info" {
  const typeMap: Record<string, "default" | "error" | "warning" | "success" | "primary" | "info"> = {
    '短信': 'info',
    '邮件': 'success',
    '企业微信': 'success',
    'APP': 'warning',
    '钉钉': 'info'
  }
  return typeMap[type] || 'default'
}

// 获取标签图标
function getTagIcon(type: string) {
  const iconMap: Record<string, any> = {
    '短信': ChatbubbleOutline,
    '邮件': MailOutline,
    '企业微信': ChatbubbleOutline,
    'APP': PhonePortraitOutline,
    '钉钉': ChatbubbleOutline
  }
  return iconMap[type] || ChatbubbleOutline
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
