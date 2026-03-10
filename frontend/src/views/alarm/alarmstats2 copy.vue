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
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-grid">
      <div class="chart-half card card-border-xl p-lg card-animated">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div>
            <h3 class="text-lg font-bold">报警趋势分析</h3>
            <p class="text-sm text-slate-500">数据统计范围: 2023-10-01 至 2023-10-30</p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
              <button class="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-700">今日</button>
              <button class="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-700">7日</button>
              <button class="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-700">14日</button>
              <button class="px-3 py-1 text-xs font-medium rounded bg-white dark:bg-slate-700 shadow-sm">30日</button>
            </div>
            <div class="h-4 w-px bg-slate-300 dark:bg-slate-700"></div>
            <button class="px-3 py-1.5 text-xs font-bold rounded bg-primary text-white">导出报表</button>
          </div>
        </div>
        <div class="h-64 w-full">
          <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 200">
            <defs>
              <linearGradient id="chart-poly" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#137fec" stop-opacity="0.2"></stop>
                <stop offset="100%" stop-color="#137fec" stop-opacity="0"></stop>
              </linearGradient>
            </defs>
            <path class="chart-gradient" d="M0,150 Q100,80 200,120 T400,60 T600,100 T800,40 T1000,80 L1000,200 L0,200 Z"></path>
            <path d="M0,150 Q100,80 200,120 T400,60 T600,100 T800,40 T1000,80" fill="none" stroke="#137fec" stroke-linecap="round" stroke-width="3"></path>
            <line class="dark:stroke-slate-800" stroke="#e2e8f0" stroke-dasharray="4,4" x1="0" x2="1000" y1="180" y2="180"></line>
            <line class="dark:stroke-slate-800" stroke="#e2e8f0" stroke-dasharray="4,4" x1="0" x2="1000" y1="120" y2="120"></line>
            <line class="dark:stroke-slate-800" stroke="#e2e8f0" stroke-dasharray="4,4" x1="0" x2="1000" y1="60" y2="60"></line>
          </svg>
        </div>
      </div>
      <div class="chart-half card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">高频告警设备 Top 5</h3>
        <div class="space-y-5">
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">摄像头-CAM-001</span>
              <span class="font-bold">156</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary" style="width: 85%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">摄像头-CAM-002</span>
              <span class="font-bold">124</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/80" style="width: 65%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">摄像头-CAM-003</span>
              <span class="font-bold">98</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/60" style="width: 55%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">摄像头-CAM-004</span>
              <span class="font-bold">76</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/40" style="width: 35%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">摄像头-CAM-005</span>
              <span class="font-bold">54</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/20" style="width: 25%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Sections -->
    <div class="bottom-grid">
      <!-- Type Distribution -->
      <div class="card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">告警类型统计</h3>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-primary">router</span>
              <span class="text-sm font-medium">网络入侵</span>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold">834</p>
              <p class="text-[10px] text-slate-400">占比 65%</p>
            </div>
          </div>
          <div class="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-accent-deep">lock_open</span>
              <span class="text-sm font-medium">非法访问</span>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold">257</p>
              <p class="text-[10px] text-slate-400">占比 20%</p>
            </div>
          </div>
          <div class="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-amber-500">settings_suggest</span>
              <span class="text-sm font-medium">硬件故障</span>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold">193</p>
              <p class="text-[10px] text-slate-400">占比 15%</p>
            </div>
          </div>
          <div class="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-slate-400">more_horiz</span>
              <span class="text-sm font-medium">其他告警</span>
            </div>
            <div class="text-right">
              <p class="text-sm font-bold">0</p>
              <p class="text-[10px] text-slate-400">占比 0%</p>
            </div>
          </div>
        </div>
      </div>

      <!-- High-freq Regions -->
      <div class="card card-border-xl p-lg card-animated">
        <h3 class="text-base font-bold mb-6">高频告警区域 Top 5</h3>
        <div class="space-y-5">
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">华东数据中心</span>
              <span class="font-bold">342</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary" style="width: 85%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">华北研发部</span>
              <span class="font-bold">215</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/80" style="width: 65%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">华南分公司</span>
              <span class="font-bold">189</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/60" style="width: 55%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">西部办事处</span>
              <span class="font-bold">120</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/40" style="width: 35%"></div>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600 dark:text-slate-400">海外节点</span>
              <span class="font-bold">96</span>
            </div>
            <div class="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary/20" style="width: 25%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Level Distribution -->
      <div class="card card-border-xl p-lg card-animated flex flex-col">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-base font-bold">告警等级分布</h3>
          <span class="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase tracking-wider font-bold">实时更新</span>
        </div>
        <div class="flex-1 flex flex-col items-center justify-center">
          <div class="relative size-32 mb-8">
            <svg class="size-full -rotate-90" viewBox="0 0 36 36">
              <circle class="dark:stroke-slate-800" cx="18" cy="18" fill="none" r="16" stroke="#e2e8f0" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#ef4444" stroke-dasharray="1, 100" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#f59e0b" stroke-dasharray="23, 100" stroke-dashoffset="-1" stroke-width="4"></circle>
              <circle cx="18" cy="18" fill="none" r="16" stroke="#60a5fa" stroke-dasharray="76, 100" stroke-dashoffset="-24" stroke-width="4"></circle>
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-xl font-bold">1,284</span>
              <span class="text-[10px] text-slate-400 uppercase">告警总计</span>
            </div>
          </div>
          <div class="w-full space-y-2">
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-red-500"></span>
                <span class="text-slate-600 dark:text-slate-400">致命等级 (Critical)</span>
              </div>
              <div class="flex gap-3 text-slate-900 dark:text-slate-100">
                <span class="font-bold">12</span>
                <span>0.9%</span>
              </div>
            </div>
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-amber-500"></span>
                <span class="text-slate-600 dark:text-slate-400">警告等级 (Warning)</span>
              </div>
              <div class="flex gap-3 text-slate-900 dark:text-slate-100">
                <span class="font-bold">284</span>
                <span>22.1%</span>
              </div>
            </div>
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-blue-500"></span>
                <span class="text-slate-600 dark:text-slate-400">信息等级 (Info)</span>
              </div>
              <div class="flex gap-3 text-slate-900 dark:text-slate-100">
                <span class="font-bold">988</span>
                <span>77.0%</span>
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
  TrendingDownOutline
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
  gap: 2px;
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

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.chart-half {
  min-width: 0;
}

.chart-gradient {
  fill: url(#chart-poly);
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