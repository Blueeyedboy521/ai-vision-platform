<template>
  <div class="dashboard">
    <!-- Stat Cards Row -->
    <div class="stat-grid">
      <StatCard
        :icon="VideocamOutline"
        icon-bg="rgba(67, 24, 255, 0.1)"
        icon-color="#4318FF"
        label="在线摄像头"
        value="128"
        trend="+5.2%"
        :trend-up="true"
      />
      <StatCard
        :icon="AlertCircleOutline"
        icon-bg="rgba(239, 68, 68, 0.1)"
        icon-color="#ef4444"
        label="今日告警"
        value="42"
        trend="-12.5%"
        :trend-up="false"
      />
      <StatCard
        :icon="GitNetworkOutline"
        icon-bg="rgba(34, 197, 94, 0.1)"
        icon-color="#22c55e"
        label="活跃模型"
        value="24"
        trend="+2.4%"
        :trend-up="true"
      />
      <StatCard
        :icon="FlashOutline"
        icon-bg="rgba(245, 158, 11, 0.1)"
        icon-color="#f59e0b"
        label="推理性能"
        value="45ms"
        trend="+0.5%"
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
