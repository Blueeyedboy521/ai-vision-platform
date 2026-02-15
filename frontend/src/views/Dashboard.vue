<template>
  <div class="dashboard">
    <!-- Stat Cards Row -->
    <div class="stat-grid">
      <StatCard
        :icon="VideocamOutline"
        icon-bg="rgba(67, 24, 255, 0.1)"
        icon-color="#4318FF"
        label="在线摄像头"
        :value="String(stats.cameras.online)"
        :trend="calcTrend(stats.cameras.online, stats.cameras.total)"
        :trend-up="stats.cameras.online > 0"
      />
      <StatCard
        :icon="AlertCircleOutline"
        icon-bg="rgba(239, 68, 68, 0.1)"
        icon-color="#ef4444"
        label="今日告警"
        :value="String(stats.alarms.today)"
        :trend="stats.alarms.pending > 0 ? `${stats.alarms.pending}待处理` : '无待处理'"
        :trend-up="false"
      />
      <StatCard
        :icon="GitNetworkOutline"
        icon-bg="rgba(34, 197, 94, 0.1)"
        icon-color="#22c55e"
        label="活跃模型"
        :value="String(stats.models.loaded)"
        :trend="`共${stats.models.total}个模型`"
        :trend-up="true"
      />
      <StatCard
        :icon="FlashOutline"
        icon-bg="rgba(245, 158, 11, 0.1)"
        icon-color="#f59e0b"
        label="已启用算法"
        :value="String(stats.algorithms.enabled)"
        :trend="`共${stats.algorithms.total}个算法`"
        :trend-up="true"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <div class="chart-half">
        <AlertTrendChart />
      </div>
      <div class="chart-half">
        <DeviceHealthChart />
      </div>
    </div>

    <!-- Alert List -->
    <AlertList />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  VideocamOutline,
  AlertCircleOutline,
  GitNetworkOutline,
  FlashOutline
} from '@vicons/ionicons5'
import StatCard from '@/components/StatCard.vue'
import AlertTrendChart from '@/components/AlertTrendChart.vue'
import DeviceHealthChart from '@/components/DeviceHealthChart.vue'
import AlertList from '@/components/AlertList.vue'
import { getSystemStatistics, type SystemStatistics } from '@/api/system'

// 统计数据
const stats = ref<SystemStatistics>({
  cameras: { total: 0, online: 0, offline: 0 },
  algorithms: { total: 0, enabled: 0 },
  models: { total: 0, loaded: 0 },
  alarms: { total: 0, today: 0, pending: 0 },
  users: { total: 0, active: 0 }
})

// 计算趋势百分比
function calcTrend(current: number, total: number): string {
  if (total === 0) return '0%'
  return `${((current / total) * 100).toFixed(1)}%`
}

// 加载统计数据
async function loadStats() {
  try {
    const response = await getSystemStatistics()
    if (response.data.data) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
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

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-half {
  min-width: 0;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
