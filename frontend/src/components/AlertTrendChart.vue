<template>
  <div class="chart-card card-border-xl">
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
          今日
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'week' }]"
          @click="activeTab = 'week'"
        >
          近7天
        </button>
      </div>
    </div>
    <div class="chart-body">
      <v-chart :option="chartOption" autoresize style="width: 100%; height: 100%; min-height: 260px;" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useAppStore } from '@/stores/app'
import { getAlarmDashboard, getAlarmTrend } from '@/api/alarm'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const appStore = useAppStore()
const activeTab = ref('today')
const loading = ref(false)

const todayData = ref([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
const weekData = ref([0, 0, 0, 0, 0, 0, 0])
const timeLabels = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']
const weekLabels = ref<string[]>([])

// 生成近7天的日期标签
function generateWeekLabels() {
  const labels: string[] = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const month = date.getMonth() + 1
    const day = date.getDate()
    labels.push(`${month}/${day}`)
  }
  return labels
}

// 加载今日趋势数据
async function loadTodayData() {
  loading.value = true
  try {
    const response = await getAlarmDashboard(1)
    if (response.data && response.data.data && response.data.data.trend) {
      // 处理今日数据，按小时整理
      const trendData = response.data.data.trend
      const hourlyData = Array(13).fill(0)
      
      // 假设数据格式为 {date: '2024-01-01 12:00:00', count: 5}
      trendData.forEach((item: any) => {
        const hour = new Date(item.date).getHours()
        if (hour >= 8 && hour <= 20) {
          const index = hour - 8
          hourlyData[index] = item.count
        }
      })
      
      todayData.value = hourlyData
    }
  } catch (error) {
    console.error('加载今日趋势数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载近7天趋势数据
async function loadWeekData() {
  loading.value = true
  try {
    // 生成近7天的日期标签
    weekLabels.value = generateWeekLabels()
    
    const response = await getAlarmTrend(7)
    if (response.data && response.data.data && response.data.data.trend) {
      // 处理近7天数据，按日期整理
      const trendData = response.data.data.trend
      const dailyData = Array(7).fill(0)
      
      // 假设数据格式为 {date: '2024-01-01', count: 10}
      trendData.forEach((item: any) => {
        const itemDate = new Date(item.date)
        const itemDateStr = `${itemDate.getMonth() + 1}/${itemDate.getDate()}`
        const index = weekLabels.value.indexOf(itemDateStr)
        if (index >= 0) {
          dailyData[index] = item.count
        }
      })
      
      weekData.value = dailyData
    }
  } catch (error) {
    console.error('加载近7天趋势数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 监听标签切换
watch(activeTab, (newTab) => {
  if (newTab === 'today') {
    loadTodayData()
  } else {
    loadWeekData()
  }
})

onMounted(() => {
  loadTodayData()
})

const chartOption = computed(() => {
  const dark = appStore.isDarkMode
  const data = activeTab.value === 'today' ? todayData.value : weekData.value
  const labels = activeTab.value === 'today' ? timeLabels : weekLabels.value
  
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
      data: labels,
      axisLine: {
        lineStyle: {
          color: dark ? '#444' : '#e2e8f0'
        }
      },
      axisLabel: {
        color: dark ? '#6b7280' : '#64748b',
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: dark ? '#333338' : '#f1f5f9',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: dark ? '#6b7280' : '#64748b',
        fontSize: 12
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: dark ? '#333338' : 'rgba(255, 255, 255, 0.95)',
      borderColor: dark ? '#444' : '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: dark ? '#e4e4e8' : '#1e293b' }
    },
    series: [
      {
        name: '告警数',
        type: 'line',
        smooth: true,
        data: data,
        lineStyle: {
          width: 3,
          color: '#137fec'
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
