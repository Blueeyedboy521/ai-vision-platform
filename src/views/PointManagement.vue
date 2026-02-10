<template>
  <div class="point-management">
    <div class="point-layout">
      <!-- Left: Area Tree -->
      <AreaTree :selected-key="selectedAreaKey" @select="handleAreaSelect" />

      <!-- Right: Main Content -->
      <div class="point-content">
        <!-- Breadcrumb -->
        <div class="point-breadcrumb">
          <span class="breadcrumb-item" @click="$router.push({ name: 'VideoManagement' })">视频管理</span>
          <n-icon :size="14" :color="appStore.isDarkMode ? '#6b7280' : '#a0aec0'">
            <ChevronForwardOutline />
          </n-icon>
          <span class="breadcrumb-current">点位管理</span>
        </div>

        <!-- Page Header -->
        <div class="point-header">
          <div class="point-header-info">
            <h1 class="point-title">{{ currentAreaLabel }} - 视频资产中心</h1>
            <p class="point-subtitle">实时管理并监控该分区的视觉采集端点</p>
          </div>
          <div class="point-header-actions">
            <div class="view-toggle">
              <button
                class="toggle-btn"
                :class="{ active: viewMode === 'list' }"
                @click="viewMode = 'list'"
              >
                <n-icon :size="18">
                  <ListOutline />
                </n-icon>
              </button>
              <button
                class="toggle-btn"
                :class="{ active: viewMode === 'grid' }"
                @click="viewMode = 'grid'"
              >
                <n-icon :size="18">
                  <GridOutline />
                </n-icon>
              </button>
            </div>
            <n-button type="primary" :theme-overrides="primaryBtnOverrides" @click="showAddModal = true">
              <template #icon>
                <n-icon>
                  <AddOutline />
                </n-icon>
              </template>
              接入新点位
            </n-button>
          </div>
        </div>

        <!-- Stat Cards -->
        <div class="stat-row">
          <PointStatCard
            :icon="VideocamOutline"
            icon-bg="rgba(67, 24, 255, 0.1)"
            accent-color="#4318FF"
            label="已注册点位"
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
            label="启动算法点位"
            :value="algorithmCount"
          />
        </div>

        <!-- Search & Actions Bar -->
        <div class="search-bar">
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索点位名称、IP..."
            clearable
            style="max-width: 400px;"
          >
            <template #prefix>
              <n-icon :size="16" :color="appStore.isDarkMode ? '#9090a0' : '#a0aec0'">
                <SearchOutline />
              </n-icon>
            </template>
          </n-input>
          <div class="search-actions">
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

        <!-- Camera Grid -->
        <div v-if="viewMode === 'grid'" class="camera-grid">
          <CameraCard
            v-for="cam in searchedCameras"
            :key="cam.id"
            :camera="cam"
            @detail="handleDetail"
          />
          <div v-if="searchedCameras.length === 0" class="empty-state">
            <n-empty description="暂无匹配的点位设备">
              <template #icon>
                <n-icon :size="48" :color="appStore.isDarkMode ? '#6b7280' : '#d1d5db'">
                  <VideocamOffOutline />
                </n-icon>
              </template>
            </n-empty>
          </div>
        </div>

        <!-- Camera List View -->
        <div v-else class="camera-list">
          <n-data-table
            :columns="tableColumns"
            :data="searchedCameras"
            :bordered="false"
            :single-line="false"
            :row-class-name="() => 'camera-row'"
          />
        </div>
      </div>
    </div>

    <!-- Add Camera Modal -->
    <n-modal v-model:show="showAddModal" preset="card" title="接入新点位" style="width: 520px;" :bordered="false">
      <n-form ref="formRef" :model="newCamera" :rules="formRules" label-placement="left" label-width="80">
        <n-form-item label="点位名称" path="name">
          <n-input v-model:value="newCamera.name" placeholder="请输入点位名称" />
        </n-form-item>
        <n-form-item label="IP 地址" path="ip">
          <n-input v-model:value="newCamera.ip" placeholder="请输入 IP 地址" />
        </n-form-item>
        <n-form-item label="所属区域" path="location">
          <n-select v-model:value="newCamera.location" :options="locationOptions" placeholder="请选择所属区域" />
        </n-form-item>
        <n-form-item label="启用算法">
          <n-switch v-model:value="newCamera.algorithmEnabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px;">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" :theme-overrides="primaryBtnOverrides" @click="handleAddCamera">确认接入</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import {
  NInput, NIcon, NButton, NEmpty, NModal, NForm, NFormItem,
  NSelect, NSwitch, NDataTable, NBadge, NTag
} from 'naive-ui'
import type { DataTableColumns, FormRules } from 'naive-ui'
import {
  ChevronForwardOutline,
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
  LocationOutline,
  ShieldCheckmarkOutline
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'
import AreaTree from '@/components/AreaTree.vue'
import CameraCard from '@/components/CameraCard.vue'
import PointStatCard from '@/components/PointStatCard.vue'
import type { CameraInfo } from '@/components/CameraCard.vue'

const appStore = useAppStore()

// View state
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const selectedAreaKey = ref('b-lobby')
const currentAreaLabel = ref('B栋 - 大厅入口')
const showAddModal = ref(false)

// New camera form
const formRef = ref()
const newCamera = ref({
  name: '',
  ip: '',
  location: '',
  algorithmEnabled: false
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入点位名称', trigger: 'blur' }],
  ip: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  location: [{ required: true, message: '请选择所属区域', trigger: 'change' }]
}

const locationOptions = [
  { label: 'A栋仓库', value: 'A栋仓库' },
  { label: 'B区办公楼', value: 'B区办公楼' },
  { label: '安防中心', value: '安防中心' },
  { label: 'B栋 - 大厅入口', value: 'B栋 - 大厅入口' },
  { label: '堆场A区', value: '堆场A区' },
  { label: '堆场B区', value: '堆场B区' }
]

// Camera data
const allCameras = ref<CameraInfo[]>([
  {
    id: 'cam-001',
    name: 'CAM-LOBBY-01',
    location: 'B栋 - 大厅入口',
    ip: '192.168.1.104',
    thumbnail: '/camera-lobby-01.jpg',
    online: true,
    algorithmEnabled: true
  },
  {
    id: 'cam-002',
    name: 'CAM-LOBBY-02',
    location: 'B栋 - 大厅入口',
    ip: '192.168.1.105',
    thumbnail: '/camera-lobby-02.jpg',
    online: true,
    algorithmEnabled: true
  },
  {
    id: 'cam-003',
    name: 'CAM-WH-A01',
    location: 'A栋仓库',
    ip: '192.168.1.201',
    thumbnail: '/camera-warehouse-01.jpg',
    online: true,
    algorithmEnabled: true
  },
  {
    id: 'cam-004',
    name: 'CAM-OFFICE-B01',
    location: 'B区办公楼',
    ip: '192.168.1.150',
    thumbnail: '/camera-office-01.jpg',
    online: false,
    algorithmEnabled: false
  },
  {
    id: 'cam-005',
    name: 'CAM-SEC-01',
    location: '安防中心',
    ip: '192.168.1.50',
    thumbnail: '/camera-lobby-01.jpg',
    online: true,
    algorithmEnabled: true
  },
  {
    id: 'cam-006',
    name: 'CAM-YARD-A01',
    location: '堆场A区',
    ip: '192.168.2.10',
    thumbnail: '/camera-warehouse-01.jpg',
    online: true,
    algorithmEnabled: false
  }
])

// Area-to-location mapping
const areaLocationMap: Record<string, string> = {
  'a-warehouse': 'A栋仓库',
  'b-office': 'B区办公楼',
  'security-center': '安防中心',
  'b-lobby': 'B栋 - 大厅入口',
  'yard-a': '堆场A区',
  'yard-b': '堆场B区'
}

const filteredCameras = computed(() => {
  const locationFilter = areaLocationMap[selectedAreaKey.value]
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

const onlineCount = computed(() => filteredCameras.value.filter(c => c.online).length)
const offlineCount = computed(() => filteredCameras.value.filter(c => !c.online).length)
const algorithmCount = computed(() => filteredCameras.value.filter(c => c.algorithmEnabled).length)

// Table columns for list view
const tableColumns: DataTableColumns<CameraInfo> = [
  {
    title: '点位名称',
    key: 'name',
    render(row) {
      return h('span', { style: { fontWeight: 600, color: 'var(--text-primary)' } }, row.name)
    }
  },
  {
    title: '状态',
    key: 'online',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.online ? 'success' : 'error',
        size: 'small',
        round: true
      }, { default: () => row.online ? '在线' : '离线' })
    }
  },
  {
    title: '所属区域',
    key: 'location',
    render(row) {
      return h('span', { style: { color: 'var(--text-muted)', fontSize: '13px' } }, row.location)
    }
  },
  {
    title: 'IP 地址',
    key: 'ip',
    render(row) {
      return h('span', {
        style: { fontFamily: "'SF Mono', Monaco, 'Courier New', monospace", fontSize: '12px', color: 'var(--text-muted)' }
      }, row.ip)
    }
  },
  {
    title: '算法',
    key: 'algorithmEnabled',
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.algorithmEnabled ? 'info' : 'default',
        size: 'small',
        round: true
      }, { default: () => row.algorithmEnabled ? '启用' : '未启用' })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      return h('span', {
        style: { color: '#4318FF', cursor: 'pointer', fontSize: '13px', fontWeight: 500 },
        onClick: () => handleDetail(row)
      }, '详情配置')
    }
  }
]

function handleAreaSelect(key: string, label: string) {
  selectedAreaKey.value = key
  currentAreaLabel.value = label
}

function handleDetail(camera: CameraInfo) {
  // Placeholder for detail navigation
}

function handleExport() {
  // Placeholder for export functionality
}

function handleBatchDisplay() {
  // Placeholder for batch display
}

function handleAddCamera() {
  formRef.value?.validate((errors: any) => {
    if (!errors) {
      const cam: CameraInfo = {
        id: `cam-${Date.now()}`,
        name: newCamera.value.name,
        location: newCamera.value.location,
        ip: newCamera.value.ip,
        thumbnail: '/camera-lobby-01.jpg',
        online: true,
        algorithmEnabled: newCamera.value.algorithmEnabled
      }
      allCameras.value.push(cam)
      showAddModal.value = false
      newCamera.value = { name: '', ip: '', location: '', algorithmEnabled: false }
    }
  })
}

const primaryBtnOverrides = {
  colorHover: '#3510d9',
  color: '#4318FF',
  colorPressed: '#2d0ec0',
  borderHover: '1px solid #4318FF',
  border: '1px solid #4318FF',
  borderPressed: '1px solid #2d0ec0',
  textColor: '#ffffff',
  textColorHover: '#ffffff',
  textColorPressed: '#ffffff'
}
</script>

<style scoped>
.point-management {
  display: flex;
  flex-direction: column;
}

.point-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.point-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Breadcrumb */
.point-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.breadcrumb-item {
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #4318FF;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 500;
}

/* Header */
.point-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.point-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
}

.point-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin: 4px 0 0;
}

.point-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* View toggle */
.view-toggle {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.toggle-btn.active {
  background: #4318FF;
  color: #fff;
}

.toggle-btn:not(.active):hover {
  background: rgba(67, 24, 255, 0.06);
}

/* Stat row */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

/* Search bar */
.search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--bg-card);
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
}

.search-actions {
  display: flex;
  gap: 8px;
}

/* Camera grid */
.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px 0;
  text-align: center;
}

/* Camera list */
.camera-list {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

@media (max-width: 1200px) {
  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .point-layout {
    flex-direction: column;
  }

  .stat-row {
    grid-template-columns: 1fr 1fr;
  }

  .camera-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stat-row {
    grid-template-columns: 1fr;
  }

  .point-header {
    flex-direction: column;
  }

  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-actions {
    justify-content: flex-end;
  }
}
</style>
