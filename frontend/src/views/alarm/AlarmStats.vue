<template>
  <div class="dashboard">
    <!-- Stat Cards Row -->
    <div class="stat-grid">
      <div class="stat-card card-border-xl">
        <div class="stat-header">
          <div class="stat-icon" style="background: rgba(67, 24, 255, 0.1);">
            <n-icon :size="24" color="#4318FF">
              <WarningOutline />
            </n-icon>
          </div>
          <div class="stat-trend" style="color: #22c55e;">
            <n-icon :size="14">
              <TrendingUpOutline />
            </n-icon>
            <span>+12%</span>
          </div>
        </div>
        <div class="stat-label">报警总数</div>
        <div class="stat-value">1,284</div>
        <div class="stat-desc">较昨日新增 142 条</div>
      </div>
      <div class="stat-card card-border-xl">
        <div class="stat-header">
          <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1);">
            <n-icon :size="24" color="#ef4444">
              <AlertCircleOutline />
            </n-icon>
          </div>
          <div class="stat-trend" style="color: #ef4444;">
            <n-icon :size="14">
              <TrendingDownOutline />
            </n-icon>
            <span>-5%</span>
          </div>
        </div>
        <div class="stat-label">待处理告警</div>
        <div class="stat-value">42</div>
        <div class="stat-desc">紧急处理中 8 条</div>
      </div>
      <div class="stat-card card-border-xl">
        <div class="stat-header">
          <div class="stat-icon" style="background: rgba(34, 197, 94, 0.1);">
            <n-icon :size="24" color="#22c55e">
              <CheckmarkCircleOutline />
            </n-icon>
          </div>
          <div class="stat-trend" style="color: #22c55e;">
            <n-icon :size="14">
              <TrendingUpOutline />
            </n-icon>
            <span>+15%</span>
          </div>
        </div>
        <div class="stat-label">已解决告警</div>
        <div class="stat-value">1,242</div>
        <div class="stat-desc">平均处理时间 12.4m</div>
      </div>
      <div class="stat-card card-border-xl">
        <div class="stat-header">
          <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1);">
            <n-icon :size="24" color="#f59e0b">
              <SpeedometerOutline />
            </n-icon>
          </div>
          <div class="stat-trend" style="color: #22c55e;">
            <n-icon :size="14">
              <TrendingUpOutline />
            </n-icon>
            <span>+2.1%</span>
          </div>
        </div>
        <div class="stat-label">处理完成率</div>
        <div class="stat-value">96.7%</div>
        <div class="stat-desc">优于 92% 的站点</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <!-- Trend Chart -->
      <div class="chart-main card card-border-xl p-lg card-animated">
        <div class="chart-header">
          <div>
            <h3 class="text-lg font-bold">报警趋势分析</h3>
            <p class="text-sm text-slate-500">数据统计范围: 2023-10-01 至 2023-10-30</p>
          </div>
          <div class="chart-controls">
            <div class="time-selector">
              <button class="time-btn">今日</button>
              <button class="time-btn">7日</button>
              <button class="time-btn">14日</button>
              <button class="time-btn active">30日</button>
            </div>
            <button class="export-btn">导出报表</button>
          </div>
        </div>
        <div class="chart-container">
          <svg class="chart-svg" preserveAspectRatio="none" viewBox="0 0 1000 200">
            <defs>
              <linearGradient id="chart-poly" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#137fec" stop-opacity="0.2"></stop>
                <stop offset="100%" stop-color="#137fec" stop-opacity="0"></stop>
              </linearGradient>
            </defs>
            <path class="chart-gradient" d="M0,150 Q100,80 200,120 T400,60 T600,100 T800,40 T1000,80 L1000,200 L0,200 Z"></path>
            <path class="chart-line" d="M0,150 Q100,80 200,120 T400,60 T600,100 T800,40 T1000,80" fill="none" stroke-linecap="round"></path>
            <line class="grid-line" x1="0" x2="1000" y1="180" y2="180"></line>
            <line class="grid-line" x1="0" x2="1000" y1="120" y2="120"></line>
            <line class="grid-line" x1="0" x2="1000" y1="60" y2="60"></line>
          </svg>
          <div class="chart-labels">
            <span>10-01</span>
            <span>10-07</span>
            <span>10-14</span>
            <span>10-21</span>
            <span>10-30</span>
          </div>
        </div>
      </div>

      <!-- High-freq Devices Table -->
      <div class="chart-side card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-4">高频告警设备 Top 5</h3>
        <div class="device-table">
          <div class="table-header">
            <span>设备名称</span>
            <span>所属区域</span>
            <span>告警数</span>
          </div>
          <div class="table-row">
            <span class="device-name">Core-Switch-01</span>
            <span class="device-region">华东中心</span>
            <span class="device-count">128</span>
          </div>
          <div class="table-row">
            <span class="device-name">Edge-Router-B</span>
            <span class="device-region">华北研发</span>
            <span class="device-count">86</span>
          </div>
          <div class="table-row">
            <span class="device-name">Auth-Server-02</span>
            <span class="device-region">华南分部</span>
            <span class="device-count">64</span>
          </div>
          <div class="table-row">
            <span class="device-name">Storage-Array-A</span>
            <span class="device-region">西部办</span>
            <span class="device-count">42</span>
          </div>
          <div class="table-row">
            <span class="device-name">Gateway-FW-03</span>
            <span class="device-region">海外节点</span>
            <span class="device-count">31</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Sections -->
    <div class="bottom-grid">
      <!-- Type Distribution -->
      <div class="card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">告警类型统计</h3>
        <div class="type-list">
          <div class="type-item">
            <div class="type-info">
              <div class="type-icon" style="background: rgba(67, 24, 255, 0.1);">
                <n-icon :size="20" color="#4318FF">
                  <WifiOutline />
                </n-icon>
              </div>
              <div class="type-detail">
                <span class="type-name">网络入侵</span>
                <span class="type-percent">占比 65%</span>
              </div>
            </div>
            <div class="type-count">
              <span class="count-value">834</span>
            </div>
          </div>
          <div class="type-item">
            <div class="type-info">
              <div class="type-icon" style="background: rgba(99, 102, 241, 0.1);">
                <n-icon :size="20" color="#6366f1">
                  <LockClosedOutline />
                </n-icon>
              </div>
              <div class="type-detail">
                <span class="type-name">非法访问</span>
                <span class="type-percent">占比 20%</span>
              </div>
            </div>
            <div class="type-count">
              <span class="count-value">257</span>
            </div>
          </div>
          <div class="type-item">
            <div class="type-info">
              <div class="type-icon" style="background: rgba(245, 158, 11, 0.1);">
                <n-icon :size="20" color="#f59e0b">
                  <SettingsOutline />
                </n-icon>
              </div>
              <div class="type-detail">
                <span class="type-name">硬件故障</span>
                <span class="type-percent">占比 15%</span>
              </div>
            </div>
            <div class="type-count">
              <span class="count-value">193</span>
            </div>
          </div>
          <div class="type-item">
            <div class="type-info">
              <div class="type-icon" style="background: rgba(148, 163, 184, 0.1);">
                <n-icon :size="20" color="#94a3b8">
                  <EllipsisHorizontalOutline />
                </n-icon>
              </div>
              <div class="type-detail">
                <span class="type-name">其他告警</span>
                <span class="type-percent">占比 0%</span>
              </div>
            </div>
            <div class="type-count">
              <span class="count-value">0</span>
            </div>
          </div>
        </div>
      </div>

      <!-- High-freq Regions -->
      <div class="card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">高频告警区域 Top 5</h3>
        <div class="region-list">
          <div class="region-item">
            <div class="region-info">
              <span class="region-name">华东数据中心</span>
              <span class="region-count">342</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" style="width: 85%"></div>
            </div>
          </div>
          <div class="region-item">
            <div class="region-info">
              <span class="region-name">华北研发部</span>
              <span class="region-count">215</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" style="width: 65%"></div>
            </div>
          </div>
          <div class="region-item">
            <div class="region-info">
              <span class="region-name">华南分公司</span>
              <span class="region-count">189</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" style="width: 55%"></div>
            </div>
          </div>
          <div class="region-item">
            <div class="region-info">
              <span class="region-name">西部办事处</span>
              <span class="region-count">120</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" style="width: 35%"></div>
            </div>
          </div>
          <div class="region-item">
            <div class="region-info">
              <span class="region-name">海外节点</span>
              <span class="region-count">96</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" style="width: 25%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Level Distribution -->
      <div class="card card-border-xl p-lg card-animated level-card">
        <div class="level-header">
          <h3 class="text-base font-bold">告警等级分布</h3>
          <span class="live-badge">实时更新</span>
        </div>
        <div class="level-content">
          <div class="donut-chart">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <circle class="donut-bg" cx="18" cy="18" r="16"></circle>
              <circle class="donut-segment donut-critical" cx="18" cy="18" r="16"></circle>
              <circle class="donut-segment donut-warning" cx="18" cy="18" r="16"></circle>
              <circle class="donut-segment donut-info" cx="18" cy="18" r="16"></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-value">1,284</span>
              <span class="donut-label">告警总计</span>
            </div>
          </div>
          <div class="level-legend">
            <div class="legend-item">
              <div class="legend-dot" style="background: #ef4444;"></div>
              <div class="legend-info">
                <span class="legend-name">致命等级 (Critical)</span>
                <div class="legend-stats">
                  <span class="legend-count">12</span>
                  <span class="legend-percent">0.9%</span>
                </div>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-dot" style="background: #f59e0b;"></div>
              <div class="legend-info">
                <span class="legend-name">警告等级 (Warning)</span>
                <div class="legend-stats">
                  <span class="legend-count">284</span>
                  <span class="legend-percent">22.1%</span>
                </div>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-dot" style="background: #3b82f6;"></div>
              <div class="legend-info">
                <span class="legend-name">提示等级 (Info)</span>
                <div class="legend-stats">
                  <span class="legend-count">988</span>
                  <span class="legend-percent">77.0%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import {
  WarningOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
  SpeedometerOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  WifiOutline,
  LockClosedOutline,
  SettingsOutline,
  EllipsisHorizontalOutline
} from '@vicons/ionicons5'
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
}

/* Stat Card Styles - Same as Home Page */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  transition: box-shadow 0.3s, background 0.3s, transform 0.3s, border-color 0.3s;
  cursor: pointer;
  border-top: 3px solid transparent;
}

.stat-card:hover {
  box-shadow: 0 8px 24px var(--hover-shadow);
  transform: translateY(-4px);
  border-top-color: #4318FF;
}

.stat-card:hover .stat-icon {
  transform: scale(1.15);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.stat-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.chart-main {
  min-width: 0;
}

.chart-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

@media (min-width: 640px) {
  .chart-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.time-selector {
  display: flex;
  background: var(--bg-page);
  padding: 4px;
  border-radius: 8px;
}

.time-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.time-btn:hover {
  background: var(--bg-card);
}

.time-btn.active {
  background: var(--bg-card);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.export-btn {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  background: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

.export-btn:hover {
  opacity: 0.9;
}

.chart-container {
  position: relative;
}

.chart-svg {
  width: 100%;
  height: 200px;
}

.chart-gradient {
  fill: url(#chart-poly);
}

.chart-line {
  stroke: #137fec;
  stroke-width: 3;
}

.grid-line {
  stroke: var(--border-color);
  stroke-dasharray: 4, 4;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

/* Device Table */
.chart-side {
  min-width: 0;
}

.device-table {
  width: 100%;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 60px;
  gap: 12px;
  padding: 12px 0;
  font-size: 12px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 60px;
  gap: 12px;
  padding: 14px 0;
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}

.table-row:last-child {
  border-bottom: none;
}

.device-name {
  font-weight: 500;
  color: var(--text-primary);
}

.device-region {
  color: var(--text-secondary);
}

.device-count {
  font-weight: 600;
  color: var(--text-primary);
  text-align: right;
}

/* Bottom Grid */
.bottom-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

/* Type Distribution */
.type-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.type-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--bg-page);
  border-radius: 10px;
}

.type-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.type-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.type-percent {
  font-size: 12px;
  color: var(--text-muted);
}

.type-count {
  text-align: right;
}

.count-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Region List */
.region-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.region-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.region-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.region-name {
  font-size: 14px;
  color: var(--text-secondary);
}

.region-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.region-bar {
  height: 8px;
  background: var(--bg-page);
  border-radius: 4px;
  overflow: hidden;
}

.region-progress {
  height: 100%;
  background: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Level Distribution */
.level-card {
  display: flex;
  flex-direction: column;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.live-badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--bg-page);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.level-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.donut-chart {
  position: relative;
  width: 140px;
  height: 140px;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.donut-bg {
  fill: none;
  stroke: var(--border-color);
  stroke-width: 4;
}

.donut-segment {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
}

.donut-critical {
  stroke: #ef4444;
  stroke-dasharray: 1 100;
}

.donut-warning {
  stroke: #f59e0b;
  stroke-dasharray: 23 100;
  stroke-dashoffset: -1;
}

.donut-info {
  stroke: #3b82f6;
  stroke-dasharray: 76 100;
  stroke-dashoffset: -24;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.donut-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.donut-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.level-legend {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-info {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.legend-name {
  font-size: 13px;
  color: var(--text-secondary);
}

.legend-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.legend-percent {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 40px;
  text-align: right;
}

/* Responsive */
@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .bottom-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>