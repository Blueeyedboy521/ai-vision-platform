<template>
  <div class="camera-management">
    <div class="point-layout">
      <!-- Left: Area Tree -->
      <AreaTree 
        ref="areaTreeRef"
        :selected-key="selectedAreaKey || ''" 
        @select="handleAreaSelect"
        @update="handleTreeUpdate"
      />

      <!-- Right: Main Content -->
      <div class="point-content">
        <!-- Add/Edit Camera Page -->
        <AddCameraPage
          v-if="showAddPage"
          :camera-id="editingCameraId"
          :area-tree-data="areaTreeData"
          @cancel="handleCancelCameraPage"
          @save="handleSaveCamera"
        />

        <template v-else>
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
              <n-button type="primary" @click="openAddCamera()">
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
              :value="totalCount"
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
              :is-playing="livePlayingId === cam.id"
              class="camera-card--animated"
              @detail="handleDetail"
              @play="handlePlayCamera"
              @toggleInference="toggleInference"
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
                      <div class="camera-table__thumb-wrapper">
                        <img :src="cam.thumbnail" :alt="cam.name" />
                        <div class="camera-table__thumb-play" @click.stop="handlePlayCamera(cam)">
                          <n-icon :size="20"><VideocamOffOutline /></n-icon>
                        </div>
                      </div>
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
                  <div class="camera-table__actions">
                    <div class="camera-table__action-buttons">
                      <n-button text type="primary" size="small" @click="openEditCamera(cam)">
                        编辑
                      </n-button>
                      <n-button text size="small" @click="handleDetail(cam)">
                        详情
                      </n-button>
                      <n-button text ghost size="small" type="primary" @click="toggleInference(cam)">
                        {{ cam.inferenceStarted ? '停止推理' : '启动推理' }}
                      </n-button>
                    </div>
                    <div class="camera-table__inference-status">
                      <span
                        class="inference-badge"
                        :class="{
                          'inference-badge--on': cam.inferenceStarted,
                          'inference-badge--off': !cam.inferenceStarted
                        }"
                      >
                        <span class="inference-badge__dot"></span>
                        {{ cam.inferenceStarted ? '推理中' : '未启动推理' }}
                      </span>
                    </div>
                  </div>
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
            :item-count="totalCount"
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
        </template>
      </div>
    </div>

    <!-- 实时预览弹窗 -->
    <n-modal
      v-model:show="showPlayer"
      preset="card"
      title="实时预览"
      :style="{ width: '960px' }"
      @after-leave="handlePlayerClosed"
    >
      <div style="width: 100%; aspect-ratio: 16 / 9;">
        <FlvPlayer
          v-if="currentPlayUrl"
          :url="currentPlayUrl"
          @fatal="handlePlayFatalError"
        />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NInput, NIcon, NButton, NEmpty, NPagination, NTag, NModal, useMessage
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
import { useUserStore } from '@/stores/user'
import AreaTree from '@/components/AreaTree.vue'
import CameraCard from '@/components/CameraCard.vue'
import PointStatCard from '@/components/PointStatCard.vue'
import AddCameraPage from '@/components/AddCameraPage.vue'
import type { CameraInfo } from '@/components/CameraCard.vue'
import { getCameraList, createCamera, updateCamera, type Camera, getCameraPlayUrls, cameraLiveHeartbeat, startCamera, stopCamera, startCameraInference, stopCameraInference } from '@/api/camera'
import FlvPlayer from '@/components/FlvPlayer.vue'

const appStore = useAppStore()
const userStore = useUserStore()
const message = useMessage()

// Refs
const areaTreeRef = ref<InstanceType<typeof AreaTree> | null>(null)

// View state
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const selectedAreaKey = ref<string | null>(null)
const currentAreaLabel = ref('全部区域')
const showAddPage = ref(false)
const editingCameraId = ref<string | null>(null)
const loading = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = ref(6)
const totalCount = ref(0)

// Area tree data (synced from AreaTree component)
const areaTreeData = ref<any[]>([])

// Camera data - 从 API 加载
const allCameras = ref<CameraInfo[]>([])

// Area key to label mapping
const areaKeyLabelMap = ref<Record<string, string>>({})

// Live play state
const livePlayingId = ref<string | null>(null)
let liveHeartbeatTimer: number | null = null

// 内嵌 FLV 播放弹窗
const showPlayer = ref(false)
const currentPlayUrl = ref<string | null>(null)

// 将后端摄像头数据转换为组件格式（缩略图优先使用最新抓拍）
function convertCamera(camera: Camera): CameraInfo {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const raw = (camera as any).snapshot_url as string | null | undefined
  let thumb = '/camera-lobby-01.jpg'
  if (raw) {
    if (raw.startsWith('http://') || raw.startsWith('https://')) {
      thumb = raw
    } else {
      thumb = base + raw
    }
  }
  return {
    id: camera.id,
    name: camera.name,
    location: camera.area_name || '未分配',
    ip: camera.ip_address || '-',
    thumbnail: thumb,
    // 在线状态直接使用后端返回的 online 字段，fallback 到 status 仅为兼容旧数据
    online: (camera as any).online ?? (camera.status === 'online'),
    algorithmEnabled: ((camera as any).algorithm_count ?? 0) > 0,
    inferenceStarted: (camera as any).inference_started ?? (camera as any).inferenceStarted ?? false
  }
}

async function toggleInference(cam: CameraInfo) {
  const id = cam.id
  try {
    if (cam.inferenceStarted) {
      await stopCameraInference(id)
      message.success('已停止推理')
    } else {
      await startCameraInference(id)
      message.success('已启动推理')
    }
    await loadCameras()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '操作失败')
  }
}

// 加载摄像头列表（后端返回 data 为数组，分页在 page_info）
async function loadCameras() {
  loading.value = true
  try {
    const areaId =
      selectedAreaKey.value && selectedAreaKey.value !== 'root'
        ? selectedAreaKey.value
        : undefined
    const response = await getCameraList({
      page: currentPage.value,
      page_size: pageSize.value,
      area_id: areaId,
      keyword: searchQuery.value || undefined
    })
    const res = response.data as any
    const list = Array.isArray(res.data) ? res.data : res.data?.items ?? []
    const pageInfo = res.page_info || {}
    allCameras.value = list.map(convertCamera)
    totalCount.value = pageInfo.total ?? list.length
  } catch (error: any) {
    console.error('加载摄像头列表失败:', error)
    message.error(error?.response?.data?.detail || error.message || '加载摄像头列表失败')
  } finally {
    loading.value = false
  }
}

async function handlePlayCamera(cam: CameraInfo) {
  const id = cam.id
  try {
    if (livePlayingId.value === id) {
      await stopCamera(id)
      livePlayingId.value = null
      if (liveHeartbeatTimer !== null) {
        window.clearInterval(liveHeartbeatTimer)
        liveHeartbeatTimer = null
      }
      message.success('已停止直播')
      return
    }

    await startCamera(id)
    const res = await getCameraPlayUrls(id)
    const data = (res.data as any)?.data ?? res.data
    let flvUrl = (data as any)?.flv_url || (data as any)?.http_flv
    if (!flvUrl) {
      message.error('未获取到播放地址')
      return
    }
    const token = userStore.token
    if (token) {
      flvUrl += flvUrl.includes('?') ? `&token=${encodeURIComponent(token)}` : `?token=${encodeURIComponent(token)}`
    }
    // 开发环境通过 Vite 代理避免跨域，将后端完整地址替换为 /flv 前缀
    if (flvUrl.startsWith('http://127.0.0.1:8080')) {
      flvUrl = flvUrl.replace('http://127.0.0.1:8080', '/flv')
    }
    currentPlayUrl.value = flvUrl
    showPlayer.value = true
    livePlayingId.value = id

    if (liveHeartbeatTimer !== null) {
      window.clearInterval(liveHeartbeatTimer)
    }
    liveHeartbeatTimer = window.setInterval(() => {
      cameraLiveHeartbeat(id).catch(() => {})
    }, 60000)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '播放失败')
  }
}

function handlePlayerClosed() {
  currentPlayUrl.value = null
  if (livePlayingId.value) {
    const id = livePlayingId.value
    stopCamera(id).catch(() => {})
    livePlayingId.value = null
  }
  if (liveHeartbeatTimer !== null) {
    window.clearInterval(liveHeartbeatTimer)
    liveHeartbeatTimer = null
  }
}

function handlePlayFatalError() {
  message.error('30 秒内未能播放该摄像头的流，请稍后重试')
  showPlayer.value = false
}

// 搜索时重新加载
const searchedCameras = computed(() => allCameras.value)
const paginatedCameras = computed(() => allCameras.value)

const onlineCount = computed(() => allCameras.value.filter(c => c.online).length)
const offlineCount = computed(() => allCameras.value.filter(c => !c.online).length)
const algorithmCount = computed(() => allCameras.value.filter(c => c.algorithmEnabled).length)

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadCameras()
  }, 300)
})

function handleAreaSelect(key: string, label: string) {
  selectedAreaKey.value = key
  currentAreaLabel.value = label
  currentPage.value = 1
  loadCameras()
}

// 组件挂载时加载数据
onMounted(() => {
  loadCameras()
})

function handleTreeUpdate(treeData: any[]) {
  areaTreeData.value = treeData
  // Update area key label map
  updateAreaKeyLabelMap(treeData)

   // 默认选中根节点（第一个节点），并同步到摄像头列表
  if (!selectedAreaKey.value && treeData && treeData.length > 0) {
    const root = treeData[0]
    if (root && root.key) {
      selectedAreaKey.value = root.key as string
      currentAreaLabel.value = root.label as string
      currentPage.value = 1
      loadCameras()
    }
  }
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

function openAddCamera() {
  editingCameraId.value = null
  showAddPage.value = true
}

function openEditCamera(cam: CameraInfo) {
  editingCameraId.value = cam.id
  showAddPage.value = true
}

function handleCancelCameraPage() {
  showAddPage.value = false
  editingCameraId.value = null
}

function handleDetail(camera: CameraInfo) {
  openEditCamera(camera)
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
  loadCameras()
}

// 页码变化时重新加载
watch(currentPage, () => {
  loadCameras()
})

async function handleSaveCamera(data: any) {
  try {
    const ipMatch = data.rtspUrl?.match(/\d+\.\d+\.\d+\.\d+/)
    const areaId = data.location || selectedAreaKey.value || undefined
    const isUuid = areaId && /^[0-9a-f]{32}$/i.test(String(areaId))
    const payload = {
      name: data.name || '新摄像头',
      area_id: isUuid ? areaId : undefined,
      rtsp_url: data.rtspUrl,
      rtsp_username: data.username || undefined,
      rtsp_password: data.password || undefined,
      ip_address: ipMatch ? ipMatch[0] : undefined,
      is_enabled: true,
      ...(data.fps != null && { fps: data.fps }),
      ...(data.resolution && { resolution: data.resolution })
    }
    if (data.id) {
      await updateCamera(data.id, payload)
      message.success('摄像头已更新')
    } else {
      await createCamera(payload)
      message.success('摄像头添加成功')
    }
    showAddPage.value = false
    editingCameraId.value = null
    await loadCameras()
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error.message || (data.id ? '更新失败' : '添加摄像头失败')
    message.error(Array.isArray(msg) ? msg.join(', ') : msg)
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

.camera-table__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.camera-table__action-buttons {
  display: flex;
  gap: 4px;
}

.camera-table__inference-status {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.inference-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
}

.inference-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
}

.inference-badge--on {
  border-color: var(--success-color);
  color: var(--success-color);
}

.inference-badge--on .inference-badge__dot {
  background: var(--success-color);
}

.inference-badge--off {
  opacity: 0.8;
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
