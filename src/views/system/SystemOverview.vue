<template>
  <div class="system-overview">
    <div class="page-header">
      <h1 class="page-header__title">系统概览</h1>
      <p class="page-header__subtitle">查看系统运行状态、版本信息和授权详情</p>
    </div>

    <!-- Running Status -->
    <section class="section">
      <h3 class="section__title">运行状态</h3>
      <div class="status-grid">
        <div class="status-card">
          <div class="status-card__icon status-card__icon--primary">
            <n-icon :size="24"><ServerOutline /></n-icon>
          </div>
          <div class="status-card__content">
            <span class="status-card__label">系统运行时长</span>
            <span class="status-card__value">{{ systemInfo.uptime }}</span>
          </div>
        </div>
        <div class="status-card">
          <div class="status-card__icon status-card__icon--success">
            <n-icon :size="24"><SpeedometerOutline /></n-icon>
          </div>
          <div class="status-card__content">
            <span class="status-card__label">CPU 使用率</span>
            <span class="status-card__value">{{ systemInfo.cpuUsage }}%</span>
          </div>
          <n-progress type="line" :percentage="systemInfo.cpuUsage" :show-indicator="false" />
        </div>
        <div class="status-card">
          <div class="status-card__icon status-card__icon--warning">
            <n-icon :size="24"><HardwareChipOutline /></n-icon>
          </div>
          <div class="status-card__content">
            <span class="status-card__label">内存使用</span>
            <span class="status-card__value">{{ systemInfo.memoryUsed }}GB / {{ systemInfo.memoryTotal }}GB</span>
          </div>
          <n-progress type="line" :percentage="(systemInfo.memoryUsed / systemInfo.memoryTotal) * 100" :show-indicator="false" status="warning" />
        </div>
        <div class="status-card">
          <div class="status-card__icon status-card__icon--info">
            <n-icon :size="24"><CloudOutline /></n-icon>
          </div>
          <div class="status-card__content">
            <span class="status-card__label">存储空间</span>
            <span class="status-card__value">{{ systemInfo.diskUsed }}TB / {{ systemInfo.diskTotal }}TB</span>
          </div>
          <n-progress type="line" :percentage="(systemInfo.diskUsed / systemInfo.diskTotal) * 100" :show-indicator="false" status="info" />
        </div>
      </div>
    </section>

    <!-- Version Info -->
    <section class="section">
      <h3 class="section__title">版本信息</h3>
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
    </section>

    <!-- License Info -->
    <section class="section">
      <h3 class="section__title">授权信息</h3>
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
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NIcon, NProgress, NTag, NButton } from 'naive-ui'
import { ServerOutline, SpeedometerOutline, HardwareChipOutline, CloudOutline } from '@vicons/ionicons5'

const systemInfo = ref({
  uptime: '45天 12小时 32分',
  cpuUsage: 32,
  memoryUsed: 12.5,
  memoryTotal: 32,
  diskUsed: 1.8,
  diskTotal: 4
})
</script>

<style scoped>
.system-overview {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
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

.section__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section__title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: var(--primary-color);
  border-radius: 2px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.status-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  align-items: center;
}

.status-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-card__icon--primary { background: rgba(67, 24, 255, 0.1); color: var(--primary-color); }
.status-card__icon--success { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.status-card__icon--warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.status-card__icon--info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }

.status-card__content { flex: 1; min-width: 0; }
.status-card__label { font-size: var(--font-size-sm); color: var(--text-muted); display: block; }
.status-card__value { font-size: var(--font-size-lg); font-weight: var(--font-weight-bold); color: var(--text-primary); }
.status-card :deep(.n-progress) { width: 100%; margin-top: var(--spacing-xs); }

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
.version-label { width: 160px; color: var(--text-muted); font-size: var(--font-size-sm); }
.version-value { flex: 1; font-weight: var(--font-weight-medium); color: var(--text-primary); }

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

.license-item { display: flex; flex-direction: column; gap: 4px; }
.license-label { font-size: var(--font-size-sm); color: var(--text-muted); }
.license-value { font-weight: var(--font-weight-medium); color: var(--text-primary); }

@media (max-width: 1200px) {
  .status-grid { grid-template-columns: repeat(2, 1fr); }
  .license-info { grid-template-columns: 1fr; }
}
</style>
