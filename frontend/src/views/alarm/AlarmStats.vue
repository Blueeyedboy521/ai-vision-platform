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
          <div class="stat-trend" :style="{ color: overview.total_trend >= 0 ? '#22c55e' : '#ef4444' }">
            <n-icon :size="14">
              <TrendingUpOutline v-if="overview.total_trend >= 0" />
              <TrendingDownOutline v-else />
            </n-icon>
            <span>{{ overview.total_trend >= 0 ? '+' : '' }}{{ overview.total_trend }}%</span>
          </div>
        </div>
        <div class="stat-label">报警总数</div>
        <div class="stat-value">{{ overview.total.toLocaleString() }}</div>
        <div class="stat-desc">今日新增 {{ overview.total_new }} 条</div>
      </div>
      <div class="stat-card card-border-xl">
        <div class="stat-header">
          <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1);">
            <n-icon :size="24" color="#ef4444">
              <AlertCircleOutline />
            </n-icon>
          </div>
          <div class="stat-trend" :style="{ color: overview.unconfirmed_trend >= 0 ? '#ef4444' : '#22c55e' }">
            <n-icon :size="14">
              <TrendingUpOutline v-if="overview.unconfirmed_trend >= 0" />
              <TrendingDownOutline v-else />
            </n-icon>
            <span>{{ overview.unconfirmed_trend >= 0 ? '+' : '' }}{{ overview.unconfirmed_trend }}%</span>
          </div>
        </div>
        <div class="stat-label">待处理告警</div>
        <div class="stat-value">{{ overview.unconfirmed }}</div>
        <div class="stat-desc">紧急处理中 {{ overview.urgent_count }} 条</div>
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
            <span>+{{ overview.confirmed_trend }}%</span>
          </div>
        </div>
        <div class="stat-label">已解决告警</div>
        <div class="stat-value">{{ overview.confirmed }}</div>
        <div class="stat-desc">平均处理时间 {{ overview.avg_handle_time }}m</div>
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
            <span>+{{ overview.completion_trend }}%</span>
          </div>
        </div>
        <div class="stat-label">处理完成率</div>
        <div class="stat-value">{{ overview.completion_rate }}%</div>
        <div class="stat-desc">优于 {{ overview.site_rank_percent }}% 的站点</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <!-- Trend Chart -->
      <div class="chart-main card card-border-xl p-lg card-animated">
        <div class="chart-header">
          <div>
            <h3 class="text-lg font-bold">报警趋势分析</h3>
            <p class="text-sm text-slate-500">数据统计范围: {{ trendRange }}</p>
          </div>
          <div class="chart-controls">
            <div class="time-selector">
              <button 
                class="time-btn" 
                :class="{ active: currentTrendDays === 1 }"
                @click="handleTrendChange(1)"
              >今日</button>
              <button 
                class="time-btn" 
                :class="{ active: currentTrendDays === 7 }"
                @click="handleTrendChange(7)"
              >7日</button>
              <button 
                class="time-btn" 
                :class="{ active: currentTrendDays === 14 }"
                @click="handleTrendChange(14)"
              >14日</button>
              <button 
                class="time-btn" 
                :class="{ active: currentTrendDays === 30 }"
                @click="handleTrendChange(30)"
              >30日</button>
            </div>
            <button class="export-btn">导出报表</button>
          </div>
        </div>
        <div class="chart-container">
          <v-chart
            class="trend-chart"
            :option="chartOption"
            autoresize
          />
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
          <div class="table-row" v-for="device in deviceTop" :key="device.camera_id">
            <span class="device-name">{{ device.camera_name }}</span>
            <span class="device-region">{{ device.area_name || '-' }}</span>
            <span class="device-count">{{ device.count }}</span>
          </div>
          <div v-if="deviceTop.length === 0" class="empty-state">
            暂无数据
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
          <div class="type-item" v-for="(item, index) in typeStats" :key="item.algorithm_id">
            <div class="type-info">
              <div class="type-icon" :style="{ background: getTypeIconBg(index) }">
                <n-icon :size="20" :color="getTypeIconColor(index)">
                  <component :is="getTypeIcon(index)" />
                </n-icon>
              </div>
              <div class="type-detail">
                <span class="type-name">{{ item.algorithm_name }}</span>
                <span class="type-percent">占比 {{ item.percentage }}%</span>
              </div>
            </div>
            <div class="type-count">
              <span class="count-value">{{ item.count }}</span>
            </div>
          </div>
          <div v-if="typeStats.length === 0" class="empty-state">
            暂无数据
          </div>
        </div>
      </div>

      <!-- High-freq Regions -->
      <div class="card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">高频告警区域 Top 5</h3>
        <div class="region-list">
          <div class="region-item" v-for="item in areaTop" :key="item.area_name">
            <div class="region-info">
              <span class="region-name">{{ item.area_name }}</span>
              <span class="region-count">{{ item.count }}</span>
            </div>
            <div class="region-bar">
              <div class="region-progress" :style="{ width: item.percentage + '%' }"></div>
            </div>
          </div>
          <div v-if="areaTop.length === 0" class="empty-state">
            暂无数据
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
              <circle 
                v-for="(item, index) in levelStats" 
                :key="item.level"
                class="donut-segment" 
                :style="getDonutStyle(item, index)"
                cx="18" cy="18" r="16"
              ></circle>
            </svg>
            <div class="donut-center">
              <span class="donut-value">{{ levelTotal.toLocaleString() }}</span>
              <span class="donut-label">告警总计</span>
            </div>
          </div>
          <div class="level-legend">
            <div class="legend-item" v-for="item in levelStats" :key="item.level">
              <div class="legend-dot" :style="{ background: getLevelColor(item.level) }"></div>
              <div class="legend-info">
                <span class="legend-name">{{ item.label }}</span>
                <div class="legend-stats">
                  <span class="legend-count">{{ item.count }}</span>
                  <span class="legend-percent">{{ item.percentage }}%</span>
                </div>
              </div>
            </div>
            <div v-if="levelStats.length === 0" class="empty-state">
              暂无数据
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { getAlarmDashboard, getAlarmTrend, type AlarmDashboardStats } from '@/api/alarm'

// 注册 ECharts 组件
use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  CanvasRenderer
])

const loading = ref(false)
const currentTrendDays = ref(1)
const dashboardData = ref<AlarmDashboardStats | null>(null)

const overview = computed(() => dashboardData.value?.overview || {
  total: 0,
  total_trend: 0,
  total_new: 0,
  unconfirmed: 0,
  unconfirmed_trend: 0,
  urgent_count: 0,
  confirmed: 0,
  confirmed_trend: 0,
  avg_handle_time: 0,
  completion_rate: 0,
  completion_trend: 0,
  site_rank_percent: 0
})

const trendData = computed(() => dashboardData.value?.trend || [])
const trendRange = computed(() => dashboardData.value?.trend_range || '')
const deviceTop = computed(() => dashboardData.value?.device_top || [])
const areaTop = computed(() => dashboardData.value?.area_top || [])
const typeStats = computed(() => dashboardData.value?.type_stats || [])
const levelStats = computed(() => dashboardData.value?.level_stats || [])
const levelTotal = computed(() => levelStats.value.reduce((sum, item) => sum + item.count, 0))



const chartOption = computed(() => {
  const data = trendData.value
  return {
    color: ['#137fec'],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      },
      axisLabel: {
        color: '#64748b'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#f1f5f9'
        }
      },
      axisLabel: {
        color: '#64748b'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: {
        color: '#1e293b'
      }
    },
    series: [
      {
        name: '告警数',
        type: 'line',
        smooth: true,
        data: data.map(item => item.count),
        lineStyle: {
          width: 3
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0,
              color: 'rgba(19, 127, 236, 0.2)'
            }, {
              offset: 1,
              color: 'rgba(19, 127, 236, 0)'
            }]
          }
        },
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#137fec'
        }
      }
    ]
  }
})

const typeIcons = [WifiOutline, LockClosedOutline, SettingsOutline, EllipsisHorizontalOutline]
const typeColors = ['#4318FF', '#6366f1', '#f59e0b', '#94a3b8']
const typeBgs = ['rgba(67, 24, 255, 0.1)', 'rgba(99, 102, 241, 0.1)', 'rgba(245, 158, 11, 0.1)', 'rgba(148, 163, 184, 0.1)']

const getTypeIcon = (index: number) => typeIcons[index % typeIcons.length]
const getTypeIconColor = (index: number) => typeColors[index % typeColors.length]
const getTypeIconBg = (index: number) => typeBgs[index % typeBgs.length]

const levelColors: Record<string, string> = {
  critical: 'var(--error-color)',
  danger: 'var(--warning-color)',
  warning: 'var(--warning-color)',
  info: 'var(--info-color)'
}

const getLevelColor = (level: string) => levelColors[level] || '#94a3b8'

const getDonutStyle = (item: { level: string; count: number; percentage: number }, index: number) => {
  const prevOffset = levelStats.value.slice(0, index).reduce((sum, s) => sum + s.percentage, 0)
  return {
    stroke: getLevelColor(item.level),
    strokeDasharray: `${item.percentage} 100`,
    strokeDashoffset: `-${prevOffset}`
  }
}

const fetchDashboardData = async (trendDays: number = 1) => {
  loading.value = true
  try {
    const res = await getAlarmDashboard(trendDays)
    dashboardData.value = res.data?.data ?? null
    currentTrendDays.value = trendDays
  } catch (error) {
    console.error('获取告警统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTrendChange = async (days: number) => {
  if (days === currentTrendDays.value) return
  loading.value = true
  try {
    const res = await getAlarmTrend(days)
    const payload = res.data?.data
    if (!payload) return
    if (!dashboardData.value) {
      // 理论上不会发生：onMounted 已先加载 dashboard
      dashboardData.value = {
        overview: overview.value as any,
        trend: payload.trend || [],
        trend_range: payload.trend_range || '',
        device_top: [],
        area_top: [],
        type_stats: [],
        level_stats: []
      }
    } else {
      dashboardData.value = {
        ...dashboardData.value,
        trend: payload.trend || [],
        trend_range: payload.trend_range || ''
      }
    }
    currentTrendDays.value = days
  } catch (error) {
    console.error('获取告警趋势失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData(1)
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
}

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
  height: 300px;
}

.trend-chart {
  width: 100%;
  height: 100%;
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

.bottom-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

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

.empty-state {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 14px;
}

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