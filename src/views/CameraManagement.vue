<template>
  <div class="camera-management">
    <!-- Add Camera Page (covers entire layout when active) -->
    <AddCameraPage
      v-if="showAddPage"
      :area-tree-data="areaTreeData"
      @cancel="showAddPage = false"
      @save="handleSaveCamera"
    />

    <div v-else class="point-layout">
      <!-- Left: Area Tree -->
      <AreaTree 
        ref="areaTreeRef"
        :selected-key="selectedAreaKey" 
        @select="handleAreaSelect"
        @update="handleTreeUpdate"
      />

      <!-- Right: Main Content -->
      <div class="point-content">
        <!-- Fixed Top Section -->
        <div class="point-content__fixed-top">
          <!-- Page Header -->
          <div class="point-header">
            <div class="point-header__info">
              <h1 class="point-header__title">{{ currentAreaLabel }} - 视频资产中心</h1>
              <p class="point-header__subtitle">实时管理并监控该分区的视觉采集端点</p>
            </div>
            <div class="point-header__actions">
              <div class="view-toggle">
                <button
                  class="view-toggle__btn"
                  :class="{ 'view-toggle__btn--active': viewMode === 'list' }"
                  @click="viewMode = 'list'"
                >
                  <n-icon :size="18">
                    <ListOutline />
                  </n-icon>
                </button>
                <button
                  class="view-toggle__btn"
                  :class="{ 'view-toggle__btn--active': viewMode === 'grid' }"
                  @click="viewMode = 'grid'"
                >
                  <n-icon :size="18">
                    <GridOutline />
                  </n-icon>
                </button>
              </div>
              <n-button type="primary" @click="showAddPage = true">
                <template #icon>
                  <n-icon>
                    <AddOutline />
                  </n-icon>
                </template>
                接入新摄像头
              </n-button>
            </div>
          </div>

          <!-- Stat Cards -->
          <div class="stat-cards">
            <PointStatCard
              :icon="VideocamOutline"
              icon-bg="rgba(67, 24, 255, 0.1)"
              accent-color="#4318FF"
              label="已注册摄像头"
              :value="filteredCameras.length"
            />
            <PointStatCard
              :icon="CheckmarkCircleOutline"
              icon-bg="rgba(34, 197, 94, 0.1)"
              accent-color="#22c55e"
              label="在线实况"
              :value="onlineCount"
            />
            <PointStatCard
              :icon="CloseCircleOutline"
              icon-bg="rgba(156, 163, 175, 0.15)"
              accent-color="#9ca3af"
              label="离线异常"
              :value="offlineCount"
            />
            <PointStatCard
              :icon="FlashOutline"
              icon-bg="rgba(67, 24, 255, 0.1)"
              accent-color="#4318FF"
              label="启动算法数"
              :value="algorithmCount"
            />
          </div>

          <!-- Search & Actions Bar -->
          <div class="search-bar">
            <n-input
              v-model:value="searchQuery"
              placeholder="搜索摄像头名称、IP..."
              clearable
              class="search-bar__input"
            >
              <template #prefix>
                <n-icon :size="16" class="search-bar__icon">
                  <SearchOutline />
                </n-icon>
              </template>
            </n-input>
            <div class="search-bar__actions">
              <n-button @click="handleExport">
                <template #icon>
                  <n-icon>
                    <DownloadOutline />
                  </n-icon>
                </template>
                导出
              </n-button>
              <n-button @click="handleBatchDisplay">
                <template #icon>
                  <n-icon>
                    <EyeOutline />
                  </n-icon>
                </template>
                批显
              </n-button>
            </div>
          </div>
        </div>

        <!-- Scrollable Content Section -->
        <div class="point-content__scrollable">
          <!-- Camera Grid View -->
          <div v-if="viewMode === 'grid'" class="camera-grid">
            <CameraCard
              v-for="cam in paginatedCameras"
              :key="cam.id"
              :camera="cam"
              class="camera-card--animated"
              @detail="handleDetail"
            />
            <div v-if="searchedCameras.length === 0" class="camera-grid__empty">
              <n-empty description="暂无匹配的摄像头设备">
                <template #icon>
                  <n-icon :size="48" class="camera-grid__empty-icon">
                    <VideocamOffOutline />
                  </n-icon>
                </template>
              </n-empty>
            </div>
          </div>

          <!-- Camera List View -->
          <div v-else class="camera-table">
            <div class="camera-table__header">
              <span class="camera-table__col camera-table__col--name">摄像头名称</span>
              <span class="camera-table__col camera-table__col--status">状态</span>
              <span class="camera-table__col camera-table__col--area">所属区域</span>
              <span class="camera-table__col camera-table__col--ip">IP 地址</span>
              <span class="camera-table__col camera-table__col--algo">算法</span>
              <span class="camera-table__col camera-table__col--action">操作</span>
            </div>
            <div class="camera-table__body">
              <div
                v-for="cam in paginatedCameras"
                :key="cam.id"
                class="camera-table__row"
              >
                <div class="camera-table__col camera-table__col--name">
                  <div class="camera-table__name-cell">
                    <div class="camera-table__avatar">
                      <img :src="cam.thumbnail" :alt="cam.name" />
                    </div>
                    <div class="camera-table__name-info">
                      <span class="camera-table__name">{{ cam.name }}</span>
                      <span class="camera-table__id">ID: {{ cam.id }}</span>
                    </div>
                  </div>
                </div>
                <div class="camera-table__col camera-table__col--status">
                  <span class="status-badge" :class="{ 'status-badge--online': cam.online }">
                    <span class="status-badge__dot"></span>
                    {{ cam.online ? '在线' : '离线' }}
                  </span>
                </div>
                <div class="camera-table__col camera-table__col--area">
                  <n-icon :size="14" class="camera-table__area-icon"><LocationOutline /></n-icon>
                  {{ cam.location }}
                </div>
                <div class="camera-table__col camera-table__col--ip">
                  <code class="camera-table__ip">{{ cam.ip }}</code>
                </div>
                <div class="camera-table__col camera-table__col--algo">
                  <n-tag
                    :type="cam.algorithmEnabled ? 'info' : 'default'"
                    size="small"
                    round
                  >
                    {{ cam.algorithmEnabled ? '已启用' : '未启用' }}
                  </n-tag>
                </div>
                <div class="camera-table__col camera-table__col--action">
                  <n-button text type="primary" size="small" @click="handleDetail(cam)">
                    详情配置
                  </n-button>
                </div>
              </div>
              <div v-if="searchedCameras.length === 0" class="camera-table__empty">
                <n-empty description="暂无匹配的摄像头设备" />
              </div>
            </div>
          </div>
        </div>

        <!-- Fixed Bottom Section - Pagination -->
        <div class="point-content__fixed-bottom">
          <n-pagination
            v-model:page="currentPage"
            :page-size="pageSize"
            :item-count="searchedCameras.length"
            :page-sizes="[6, 12, 24, 48]"
            show-size-picker
            show-quick-jumper
            @update:page-size="handlePageSizeChange"
          >
            <template #prefix="{ itemCount }">
              共 {{ itemCount }} 条记录
            </template>
          </n-pagination>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NInput, NIcon, NButton, NEmpty, NPagination, NTag
} from 'naive-ui'
import {
  ListOutline,
  GridOutline,
  AddOutline,
  VideocamOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  FlashOutline,
  SearchOutline,
  DownloadOutline,
  EyeOutline,
  VideocamOffOutline,
  LocationOutline
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'
import AreaTree from '@/components/AreaTree.vue'
import CameraCard from '@/components/CameraCard.vue'
import PointStatCard from '@/components/PointStatCard.vue'
import AddCameraPage from '@/components/AddCameraPage.vue'
import type { CameraInfo } from '@/components/CameraCard.vue'

const appStore = useAppStore()

// Refs
const areaTreeRef = ref<InstanceType<typeof AreaTree> | null>(null)

// View state
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const selectedAreaKey = ref('main-park')
const currentAreaLabel = ref('主园区')
const showAddPage = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = ref(6)

// Area tree data (synced from AreaTree component)
const areaTreeData = ref<any[]>([])

// Camera data - Extended test data (20+ cameras in 主园区)
const allCameras = ref<CameraInfo[]>([
  // 主园区摄像头 (20个)
  { id: 'cam-001', name: 'CAM-MAIN-01', location: '主园区', ip: '192.168.1.101', thumbnail: '/camera-lobby-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-002', name: 'CAM-MAIN-02', location: '主园区', ip: '192.168.1.102', thumbnail: '/camera-lobby-02.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-003', name: 'CAM-MAIN-03', location: '主园区', ip: '192.168.1.103', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-004', name: 'CAM-MAIN-04', location: '主园区', ip: '192.168.1.104', thumbnail: '/camera-office-01.jpg', online: false, algorithmEnabled: true },
  { id: 'cam-005', name: 'CAM-MAIN-05', location: '主园区', ip: '192.168.1.105', thumbnail: '/camera-lobby-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-006', name: 'CAM-MAIN-06', location: '主园区', ip: '192.168.1.106', thumbnail: '/camera-lobby-02.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-007', name: 'CAM-MAIN-07', location: '主园区', ip: '192.168.1.107', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-008', name: 'CAM-MAIN-08', location: '主园区', ip: '192.168.1.108', thumbnail: '/camera-office-01.jpg', online: false, algorithmEnabled: false },
  { id: 'cam-009', name: 'CAM-MAIN-09', location: '主园区', ip: '192.168.1.109', thumbnail: '/camera-lobby-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-010', name: 'CAM-MAIN-10', location: '主园区', ip: '192.168.1.110', thumbnail: '/camera-lobby-02.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-011', name: 'CAM-MAIN-11', location: '主园区', ip: '192.168.1.111', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-012', name: 'CAM-MAIN-12', location: '主园区', ip: '192.168.1.112', thumbnail: '/camera-office-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-013', name: 'CAM-MAIN-13', location: '主园区', ip: '192.168.1.113', thumbnail: '/camera-lobby-01.jpg', online: false, algorithmEnabled: true },
  { id: 'cam-014', name: 'CAM-MAIN-14', location: '主园区', ip: '192.168.1.114', thumbnail: '/camera-lobby-02.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-015', name: 'CAM-MAIN-15', location: '主园区', ip: '192.168.1.115', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-016', name: 'CAM-MAIN-16', location: '主园区', ip: '192.168.1.116', thumbnail: '/camera-office-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-017', name: 'CAM-MAIN-17', location: '主园区', ip: '192.168.1.117', thumbnail: '/camera-lobby-01.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-018', name: 'CAM-MAIN-18', location: '主园区', ip: '192.168.1.118', thumbnail: '/camera-lobby-02.jpg', online: false, algorithmEnabled: true },
  { id: 'cam-019', name: 'CAM-MAIN-19', location: '主园区', ip: '192.168.1.119', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-020', name: 'CAM-MAIN-20', location: '主园区', ip: '192.168.1.120', thumbnail: '/camera-office-01.jpg', online: true, algorithmEnabled: false },
  // A栋仓库
  { id: 'cam-021', name: 'CAM-WH-A01', location: 'A栋仓库', ip: '192.168.1.201', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true },
  { id: 'cam-022', name: 'CAM-WH-A02', location: 'A栋仓库', ip: '192.168.1.202', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true },
  // B区办公楼
  { id: 'cam-023', name: 'CAM-OFFICE-B01', location: 'B区办公楼', ip: '192.168.1.150', thumbnail: '/camera-office-01.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-024', name: 'CAM-OFFICE-B02', location: 'B区办公楼', ip: '192.168.1.151', thumbnail: '/camera-office-01.jpg', online: true, algorithmEnabled: true },
  // 安防中心
  { id: 'cam-025', name: 'CAM-SEC-01', location: '安防中心', ip: '192.168.1.50', thumbnail: '/camera-lobby-01.jpg', online: true, algorithmEnabled: true },
  // 堆场
  { id: 'cam-026', name: 'CAM-YARD-A01', location: '堆场A区', ip: '192.168.2.10', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: false },
  { id: 'cam-027', name: 'CAM-YARD-B01', location: '堆场B区', ip: '192.168.2.20', thumbnail: '/camera-warehouse-01.jpg', online: true, algorithmEnabled: true }
])

// Area key to label mapping
const areaKeyLabelMap = ref<Record<string, string>>({
  'main-park': '主园区',
  'a-warehouse': 'A栋仓库',
  'b-office': 'B区办公楼',
  'security-center': '安防中心',
  'b-lobby': 'B栋 - 大厅入口',
  'yard-a': '堆场A区',
  'yard-b': '堆场B区'
})

const filteredCameras = computed(() => {
  const locationFilter = areaKeyLabelMap.value[selectedAreaKey.value]
  if (!locationFilter) return allCameras.value
  return allCameras.value.filter(c => c.location === locationFilter)
})

const searchedCameras = computed(() => {
  if (!searchQuery.value) return filteredCameras.value
  const q = searchQuery.value.toLowerCase()
  return filteredCameras.value.filter(c =>
    c.name.toLowerCase().includes(q) || c.ip.includes(q)
  )
})

const paginatedCameras = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return searchedCameras.value.slice(start, start + pageSize.value)
})

const onlineCount = computed(() => filteredCameras.value.filter(c => c.online).length)
const offlineCount = computed(() => filteredCameras.value.filter(c => !c.online).length)
const algorithmCount = computed(() => filteredCameras.value.filter(c => c.algorithmEnabled).length)

function handleAreaSelect(key: string, label: string) {
  selectedAreaKey.value = key
  currentAreaLabel.value = label
  currentPage.value = 1 // Reset to first page when area changes
}

function handleTreeUpdate(treeData: any[]) {
  areaTreeData.value = treeData
  // Update area key label map
  updateAreaKeyLabelMap(treeData)
}

function updateAreaKeyLabelMap(nodes: any[], map: Record<string, string> = {}) {
  for (const node of nodes) {
    map[node.key] = node.label
    if (node.children) {
      updateAreaKeyLabelMap(node.children, map)
    }
  }
  areaKeyLabelMap.value = map
}

function handleDetail(camera: CameraInfo) {
  // TODO: Open detail modal or navigate to detail page
  console.log('View details:', camera)
}

function handleExport() {
  // TODO: Export functionality
}

function handleBatchDisplay() {
  // TODO: Batch display functionality
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
}

function handleSaveCamera(data: any) {
  // Get location label from key
  const locationLabel = areaKeyLabelMap.value[data.location] || currentAreaLabel.value
  
  const cam: CameraInfo = {
    id: `cam-${Date.now()}`,
    name: data.name || '新摄像头',
    location: locationLabel,
    ip: data.rtspUrl ? data.rtspUrl.match(/\d+\.\d+\.\d+\.\d+/)?.[0] || '0.0.0.0' : '0.0.0.0',
    thumbnail: '/camera-lobby-01.jpg',
    online: true,
    algorithmEnabled: data.algorithms && data.algorithms.length > 0
  }
  allCameras.value.push(cam)
  
  // Close add page
  showAddPage.value = false
  
  // If added to current area, show it
  if (cam.location === currentAreaLabel.value) {
    currentPage.value = Math.ceil(searchedCameras.value.length / pageSize.value)
  }
}
</script>

<style scoped>
/* ===== Page Layout ===== */
.camera-management {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.point-layout {
  display: flex;
  gap: var(--spacing-xl);
  height: 100%;
  overflow: hidden;
}

.point-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.point-content__fixed-top {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
}

.point-content__scrollable {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: var(--spacing-xs);
}

/* Custom scrollbar for scrollable area */
.point-content__scrollable::-webkit-scrollbar {
  width: 6px;
}

.point-content__scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.point-content__scrollable::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.point-content__scrollable::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

.point-content__fixed-bottom {
  flex: 0 0 auto;
  padding: var(--spacing-md) 0 0;
  background: var(--bg-page);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
}

/* ===== Page Header ===== */
.point-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-lg);
}

.point-header__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
  line-height: var(--line-height-tight);
}

.point-header__subtitle {
  font-size: var(--font-size-base);
  color: var(--text-muted);
  margin: var(--spacing-xs) 0 0;
}

.point-header__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

/* ===== View Toggle ===== */
.view-toggle {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.view-toggle__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.view-toggle__btn--active {
  background: var(--primary-color);
  color: #fff;
}

.view-toggle__btn:not(.view-toggle__btn--active):hover {
  background: var(--bg-hover);
}

/* ===== Stat Cards ===== */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

/* ===== Search Bar ===== */
.search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  border: 1px solid var(--border-color);
}

.search-bar__input {
  max-width: 400px;
}

.search-bar__icon {
  color: var(--text-muted);
}

.search-bar__actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* ===== Camera Grid ===== */
.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  align-content: flex-start;
  padding-bottom: var(--spacing-md);
}

.camera-grid__empty {
  grid-column: 1 / -1;
  padding: var(--spacing-4xl) 0;
  text-align: center;
}

.camera-grid__empty-icon {
  color: var(--text-muted);
}

/* ===== Camera Table ===== */
.camera-table {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.camera-table__header {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.camera-table__body {
  /* No max-height, let parent scrollable area control scrolling */
}

.camera-table__row {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.camera-table__row:last-child {
  border-bottom: none;
}

.camera-table__row:hover {
  background: var(--bg-hover);
}

.camera-table__col {
  display: flex;
  align-items: center;
}

.camera-table__col--name {
  flex: 2;
  min-width: 0;
}

.camera-table__col--status {
  flex: 0.8;
}

.camera-table__col--area {
  flex: 1.2;
  gap: var(--spacing-xs);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.camera-table__col--ip {
  flex: 1;
}

.camera-table__col--algo {
  flex: 0.8;
}

.camera-table__col--action {
  flex: 0.8;
  justify-content: flex-end;
}

.camera-table__name-cell {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.camera-table__avatar {
  width: 48px;
  height: 36px;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.camera-table__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-table__name-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.camera-table__name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.camera-table__id {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.camera-table__area-icon {
  color: var(--primary-color);
}

.camera-table__ip {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  background: var(--bg-page);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.camera-table__empty {
  padding: var(--spacing-3xl);
  text-align: center;
}

/* ===== Status Badge ===== */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(156, 163, 175, 0.1);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
}

.status-badge--online {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* ===== Card Animation ===== */
.camera-card--animated {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.camera-card--animated:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgba(67, 24, 255, 0.15);
}

/* ===== Responsive ===== */
@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .point-layout {
    flex-direction: column;
  }

  .stat-cards {
    grid-template-columns: 1fr 1fr;
  }

  .camera-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }

  .point-header {
    flex-direction: column;
  }

  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-bar__input {
    max-width: none;
  }

  .search-bar__actions {
    justify-content: flex-end;
  }
}
</style>
