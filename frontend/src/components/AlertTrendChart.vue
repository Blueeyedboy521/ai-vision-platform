<template>
  <div class="chart-card">
    <div class="chart-header">
      <div class="chart-title">
        <div class="title-bar"></div>
        <span>告警趋势分析</span>
      </div>
      <div class="chart-tabs">
        <button
          :class="['tab-btn', { active: activeTab === 'today' }]"
          @click="activeTab = 'today'"
        >
          今日实况
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'week' }]"
          @click="activeTab = 'week'"
        >
          本周趋势
        </button>
      </div>
    </div>
    <div class="chart-body">
      <v-chart :option="chartOption" autoresize style="width: 100%; height: 100%; min-height: 260px;" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useAppStore } from '@/stores/app'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const appStore = useAppStore()
const activeTab = ref('today')

const todayData = [12, 10, 8, 6, 14, 16, 22, 24, 23, 20, 26, 28, 22]
const weekData = [18, 22, 16, 28, 20, 14, 24, 30, 26, 18, 22, 20, 16]
const timeLabels = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

const chartOption = computed(() => {
  const dark = appStore.isDarkMode
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: dark ? '#333338' : '#fff',
      borderColor: dark ? '#444' : '#e0e0e0',
      borderWidth: 1,
      textStyle: { color: dark ? '#e4e4e8' : '#333' }
    },
    grid: {
      left: 40,
      right: 20,
      top: 20,
      bottom: 30
    },
    xAxis: {
      type: 'category',
      data: timeLabels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: dark ? '#444' : '#e8e8e8' } },
      axisTick: { show: false },
      axisLabel: { color: dark ? '#6b7280' : '#a0aec0', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 32,
      interval: 8,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: dark ? '#333338' : '#f0f0f0', type: 'dashed' } },
      axisLabel: { color: dark ? '#6b7280' : '#a0aec0', fontSize: 12 }
    },
    series: [
      {
        type: 'line',
        data: activeTab.value === 'today' ? todayData : weekData,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#4318FF',
          width: 3
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(67, 24, 255, 0.12)' },
              { offset: 1, color: 'rgba(67, 24, 255, 0)' }
            ]
          }
        }
      }
    ]
  }
})
</script>

<style scoped>
.chart-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  border-top: 3px solid transparent;
}

.chart-card:hover {
  border-top-color: #4318FF;
  box-shadow: 0 4px 16px var(--hover-shadow);
}

.chart-body {
  flex: 1;
  min-height: 0;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.title-bar {
  width: 4px;
  height: 18px;
  background: #4318FF;
  border-radius: 2px;
}

.chart-tabs {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  overflow: hidden;
}

.tab-btn {
  padding: 6px 14px;
  font-size: 13px;
  border: none;
  background: var(--bg-card);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #4318FF;
  color: #fff;
}
</style>
