<template>
  <div class="template-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">模板配置</h1>
        <p class="page-subtitle">管理推送消息模板</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" class="header-btn">
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
        <div class="stat-card__value">128</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">纯文本模板</span>
          <div class="stat-card__icon stat-card__icon--secondary">
            <n-icon><TextOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">84</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">富媒体模板</span>
          <div class="stat-card__icon stat-card__icon--info">
            <n-icon><ImageOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">44</div>
      </div>
      <div class="stat-card card card-border-xl">
        <div class="stat-card__header">
          <span class="stat-card__label">已启用模板</span>
          <div class="stat-card__icon stat-card__icon--success">
            <n-icon><CheckmarkCircleOutline /></n-icon>
          </div>
        </div>
        <div class="stat-card__value">112</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section card card-border-xl">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">模板类型</span>
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
            placeholder="快速搜索..."
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
        <div class="list-header__col list-header__col--name">模板名称</div>
        <div class="list-header__col list-header__col--type">类型</div>
        <div class="list-header__col list-header__col--version">版本</div>
        <div class="list-header__col list-header__col--status">状态</div>
        <div class="list-header__col list-header__col--time">最后更新</div>
        <div class="list-header__col list-header__col--action">操作</div>
      </div>

      <!-- 列表内容 -->
      <div class="list-body">
        <div
          v-for="(template, index) in templates"
          :key="template.id"
          class="list-row"
        >
          <div class="list-row__col list-row__col--name">
            <div class="template-name">
              <div class="template-avatar" :class="`template-avatar--${template.type === '文本' ? 'primary' : 'success'}`">
                {{ template.name.charAt(0) }}
              </div>
              <span class="template-name-text">{{ template.name }}</span>
            </div>
          </div>
          <div class="list-row__col list-row__col--type">
            <n-tag :type="template.type === '文本' ? 'info' : 'success'" size="small" class="tag-with-icon">
              <template #icon>
                <n-icon :size="14">
                  <component :is="template.type === '文本' ? TextOutline : ImageOutline" />
                </n-icon>
              </template>
              {{ template.type }}
            </n-tag>
          </div>
          <div class="list-row__col list-row__col--version">
            <span class="version-tag">{{ template.version }}</span>
          </div>
          <div class="list-row__col list-row__col--status">
            <n-switch v-model:value="template.status" size="small" />
          </div>
          <div class="list-row__col list-row__col--time">
            <span class="time-text">{{ template.updateTime }}</span>
          </div>
          <div class="list-row__col list-row__col--action">
            <n-button text type="primary" size="small">编辑</n-button>
            <n-button text type="error" size="small">删除</n-button>
          </div>
        </div>
        <div v-if="templates.length === 0" class="empty-state">
          <n-empty description="暂无模板数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="list-footer">
        <div class="list-footer__info">
          显示第 1 到 5 条，共 128 条模板
        </div>
        <n-pagination
          :page="1"
          :item-count="128"
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
  DocumentOutline, 
  TextOutline, 
  ImageOutline, 
  CheckmarkCircleOutline, 
  SearchOutline,
  AddOutline 
} from '@vicons/ionicons5'
import { NButton, NInput, NIcon, NTag, NSwitch, NPagination, NSelect, NEmpty } from 'naive-ui'

// 模板数据
const templates = ref([
  {
    id: 1,
    name: '欢迎推送 (新注册用户)',
    type: '文本',
    version: 'v1.0.2',
    status: true,
    updateTime: '2023-10-24 14:00'
  },
  {
    id: 2,
    name: '双11促销活动通知',
    type: '图文',
    version: 'v2.1.0',
    status: true,
    updateTime: '2023-10-23 09:30'
  },
  {
    id: 3,
    name: '验证码模板 (通用型)',
    type: '文本',
    version: 'v1.0.0',
    status: true,
    updateTime: '2023-10-22 18:15'
  },
  {
    id: 4,
    name: '会员等级升级提醒',
    type: '图文',
    version: 'v1.2.4',
    status: true,
    updateTime: '2023-10-21 11:45'
  },
  {
    id: 5,
    name: '系统维护通知',
    type: '文本',
    version: 'v3.0.1',
    status: false,
    updateTime: '2023-10-20 09:15'
  }
])
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
