<template>
  <div class="health-card">
    <div class="chart-title">
      <div class="title-bar"></div>
      <span>设备健康状态</span>
    </div>
    <div class="health-chart-wrapper">
      <v-chart :option="chartOption" autoresize style="height: 220px;" />
    </div>
    <div class="health-stats">
      <div class="health-stat">
        <div class="health-stat-label">设备总数</div>
        <div class="health-stat-value">144</div>
      </div>
      <div class="health-divider"></div>
      <div class="health-stat">
        <div class="health-stat-label">离线异常</div>
        <div class="health-stat-value danger">16</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useAppStore } from '@/stores/app'

use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const appStore = useAppStore()

const chartOption = computed(() => {
  const dark = appStore.isDarkMode
  return {
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['60%', '80%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'center',
          formatter: () => '{a|89%}\n{b|在线占比}',
          rich: {
            a: {
              fontSize: 32,
              fontWeight: 700,
              color: dark ? '#e4e4e8' : '#1a1a2e',
              lineHeight: 40
            },
            b: {
              fontSize: 13,
              color: '#4318FF',
              lineHeight: 20
            }
          }
        },
        emphasis: {
          label: { show: true }
        },
        labelLine: { show: false },
        data: [
          {
            value: 128,
            name: '在线设备',
            itemStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 1, y2: 1,
                colorStops: [
                  { offset: 0, color: '#4318FF' },
                  { offset: 1, color: '#7b5dff' }
                ]
              }
            }
          },
          {
            value: 16,
            name: '离线设备',
            itemStyle: { color: dark ? '#3a3a40' : '#e8e8e8' }
          }
        ]
      }
    ]
  }
})
</script>

<style scoped>
.health-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box;
  border-top: 3px solid transparent;
}

.health-card:hover {
  border-top-color: #4318FF;
  box-shadow: 0 4px 16px var(--hover-shadow);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.title-bar {
  width: 4px;
  height: 18px;
  background: #4318FF;
  border-radius: 2px;
}

.health-chart-wrapper {
  flex: 1;
}

.health-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.health-stat {
  flex: 1;
  text-align: center;
}

.health-divider {
  width: 1px;
  height: 40px;
  background: var(--border-color);
}

.health-stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.health-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.health-stat-value.danger {
  color: #ef4444;
}
</style>
