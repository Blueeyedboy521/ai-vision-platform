<template>
  <div class="add-camera-page">
    <!-- Header -->
    <div class="add-camera-page__header">
      <div class="add-camera-page__header-left">
        <h1 class="add-camera-page__title">配置智能摄像头</h1>
        <span class="add-camera-page__id">ID: CAM-NEW-#{{ Date.now().toString().slice(-4) }}</span>
      </div>
      <div class="add-camera-page__header-actions">
        <n-button @click="handleCancel">取消配置</n-button>
        <n-button type="primary" @click="handleSave">
          <template #icon>
            <n-icon><SaveOutline /></n-icon>
          </template>
          保存
        </n-button>
      </div>
    </div>

    <!-- Content: 上下布局，上排左右各半，下排算法全宽 -->
    <div class="add-camera-page__content">
      <!-- 上排：左 网络与流媒体，右 实时预监 -->
      <div class="add-camera-page__top">
        <div class="add-camera-page__top-left">
          <!-- Network & Media Config -->
          <section class="config-card">
          <h3 class="config-card__title">
            <span class="config-card__indicator"></span>
            网络与流媒体配置
          </h3>
          <div class="config-card__body">
            <div class="form-field">
              <label class="form-field__label">设备显示名称</label>
              <n-input
                v-model:value="formData.name"
                placeholder="例如：西门 01 号抓拍机"
              />
            </div>
            <div class="form-field__row">
              <div class="form-field form-field--flex">
                <label class="form-field__label">管理分区</label>
                <n-tree-select
                  v-model:value="formData.location"
                  :options="areaOptions"
                  placeholder="生产 A 车间"
                  clearable
                  :default-expand-all="true"
                />
              </div>
              <div class="form-field form-field--flex">
                <label class="form-field__label">网络状态</label>
                <div 
                  class="connection-status" 
                  :class="{ 'connection-status--online': connectionStatus === 'online' }"
                >
                  <span class="connection-status__dot"></span>
                  {{ connectionStatus === 'online' ? 'ONLINE' : '未连接' }}
                </div>
              </div>
            </div>
            <div class="form-field">
              <label class="form-field__label">RTSP 流地址</label>
              <div class="form-field__group">
                <n-input
                  v-model:value="formData.rtspUrl"
                  placeholder="rtsp://admin:pwd@192.168.1.100:554/ch1"
                  class="form-field__input"
                />
                <n-button @click="testConnection" :loading="testingConnection">
                  流通性测试
                </n-button>
              </div>
            </div>
            <div v-if="streamInfo" class="stream-info">
              <span>宽 {{ streamInfo.width }} × 高 {{ streamInfo.height }}</span>
              <span v-if="streamInfo.fps"> · {{ streamInfo.fps }} fps</span>
              <span v-if="streamInfo.resolution"> · {{ streamInfo.resolution }}</span>
            </div>
            <div class="form-field__row">
              <div class="form-field form-field--flex">
                <label class="form-field__label">识别间隔(秒)</label>
                <n-input-number
                  v-model:value="formData.inferenceIntervalSec"
                  :min="1"
                  :max="3600"
                  placeholder="例如：5（每 5 秒推理一次）"
                  style="width: 100%"
                />
              </div>
            </div>
          </div>
        </section>
        </div>

        <!-- Preview Section 右上 -->
        <section class="config-card config-card--preview add-camera-page__top-right">
          <div class="config-card__header">
            <h3 class="config-card__title">
              <span class="config-card__indicator"></span>
              16:9 实时预监实况
            </h3>
            <n-button type="error" size="small" @click="captureSnapshot">
              <template #icon>
                <n-icon><CameraOutline /></n-icon>
              </template>
              抓拍
            </n-button>
          </div>
          <div class="preview">
            <div class="preview__video">
              <img
                v-if="previewImage"
                :src="previewImage"
                alt="Preview"
                class="preview__image"
              />
              <div
                v-if="props.cameraId && previewImage"
                class="preview__play-overlay"
                @click.stop="playLive"
              >
                <span class="preview__play-text">
                  {{ livePlaying ? '停止' : '播放' }}
                </span>
              </div>
              <div v-else class="preview__placeholder">
                <n-icon :size="48" class="preview__placeholder-icon">
                  <VideocamOffOutline />
                </n-icon>
                <span>等待连接...</span>
              </div>
            </div>
            <div v-if="snapshots.length > 0" class="preview__snapshots">
              <div
                v-for="(snap, index) in snapshots"
                :key="index"
                class="preview__snapshot"
              >
                <img :src="snap" alt="Snapshot" />
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- 下排：算法能力与阈值配置 宽度100% -->
      <div class="add-camera-page__bottom">
        <!-- Algorithm Config -->
        <section class="config-card add-camera-page__algorithm-section">
          <div class="config-card__header">
            <h3 class="config-card__title">
              <span class="config-card__indicator"></span>
              算法能力与阈值配置
            </h3>
            <div style="display: flex; align-items: center; gap: 12px;">
              <span class="config-card__badge">
                ACTIVE: {{ enabledAlgorithmCount }} / {{ algorithms.length }}
              </span>
              <n-button
                v-if="cameraId"
                size="small"
                type="primary"
                @click="openAddAlgorithmModal"
              >
                添加算法
              </n-button>
            </div>
          </div>

          <div class="algorithm-list">
            <div class="algorithm-list__header">
              <span class="algorithm-list__col algorithm-list__col--enable">启用</span>
              <span class="algorithm-list__col algorithm-list__col--name">算法类型</span>
              <span class="algorithm-list__col algorithm-list__col--confidence">置信度 (%)</span>
              <span class="algorithm-list__col algorithm-list__col--alarm-int">告警间隔(秒)</span>
              <span class="algorithm-list__col algorithm-list__col--strategy">告警策略</span>
              <span class="algorithm-list__col algorithm-list__col--region">检测范围</span>
              <span class="algorithm-list__col algorithm-list__col--time">时间计划</span>
              <span class="algorithm-list__col algorithm-list__col--action">操作</span>
            </div>
            <div class="algorithm-list__body">
              <div
                v-for="algo in algorithms"
                :key="algo.id"
                class="algorithm-list__row"
                :class="{ 'algorithm-list__row--enabled': algo.enabled }"
              >
                <div class="algorithm-list__col algorithm-list__col--enable">
                  <n-switch v-model:value="algo.enabled" />
                </div>
                <div class="algorithm-list__col algorithm-list__col--name">
                  <span class="algorithm-list__name">{{ algo.name }}</span>
                  <span v-if="algo.nameEn" class="algorithm-list__name-en">({{ algo.nameEn }})</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--confidence">
                  <n-slider
                    v-model:value="algo.confidence"
                    :min="0"
                    :max="100"
                    :disabled="!algo.enabled"
                    class="algorithm-list__slider"
                  />
                  <span class="algorithm-list__confidence-value">{{ algo.confidence }}%</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--alarm-int">
                  <n-input-number
                    v-model:value="algo.alarmIntervalSec"
                    :min="1"
                    :max="3600"
                    :disabled="!algo.enabled"
                    size="small"
                    placeholder="30"
                    style="width: 72px"
                  />
                </div>
                <div class="algorithm-list__col algorithm-list__col--strategy">
                  <n-button
                    v-if="algo.enabled && algo.configId && cameraId"
                    text
                    type="primary"
                    size="small"
                    @click="openAlertStrategyModal(algo)"
                  >
                    <template #icon>
                      <n-icon :size="14"><SettingsOutline /></n-icon>
                    </template>
                    {{ algo.alertConfigOverride ? '已覆盖' : '配置' }}
                  </n-button>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--region">
                  <n-button
                    v-if="algo.enabled"
                    text
                    type="primary"
                    size="small"
                    @click="configRegion(algo)"
                  >
                    <template #icon>
                      <n-icon><ScanOutline /></n-icon>
                    </template>
                    {{ algo.regionCount ? `${algo.regionCount} 个区域` : '绘制区域' }}
                  </n-button>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--time">
                  <template v-if="algo.enabled">
                    <n-popover 
                      trigger="click" 
                      placement="bottom"
                      :show="activeTimePopover === algo.id"
                      @update:show="(v) => activeTimePopover = v ? algo.id : null"
                    >
                      <template #trigger>
                        <div class="algorithm-list__time-btn">
                          <n-icon :size="14"><TimeOutline /></n-icon>
                          <span>{{ algo.timeRange || '00:00 - 23:59' }}</span>
                        </div>
                      </template>
                      <div class="time-picker-panel">
                        <div class="time-picker-panel__title">设置告警时段</div>
                        <div class="time-picker-panel__row">
                          <n-time-picker
                            v-model:value="algo.startTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('00:00')"
                          />
                          <span class="time-picker-panel__separator">至</span>
                          <n-time-picker
                            v-model:value="algo.endTime"
                            format="HH:mm"
                            :default-value="getDefaultTime('23:59')"
                          />
                        </div>
                        <div class="time-picker-panel__presets">
                          <n-button size="tiny" @click="setTimePreset(algo, '全天')">全天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '白天')">白天</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '夜间')">夜间</n-button>
                          <n-button size="tiny" @click="setTimePreset(algo, '工作时间')">工作时间</n-button>
                        </div>
                        <div class="time-picker-panel__footer">
                          <n-button size="small" type="primary" @click="confirmTimeSelection(algo)">
                            确认
                          </n-button>
                        </div>
                      </div>
                    </n-popover>
                  </template>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
                <div class="algorithm-list__col algorithm-list__col--action">
                  <n-button
                    v-if="algo.configId && cameraId"
                    text
                    type="error"
                    size="small"
                    @click="removeCameraAlgorithmConfig(algo.configId)"
                  >
                    移除
                  </n-button>
                  <span v-else class="algorithm-list__disabled">—</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- 添加算法 Modal -->
    <n-modal
      v-model:show="showAddAlgorithmModal"
      preset="card"
      title="为摄像头添加算法"
      :style="{ width: '480px' }"
      @after-enter="loadAlgorithmListForAdd"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item label="选择算法">
          <n-select
            v-model:value="addAlgorithmSelectedId"
            :options="algorithmOptionsForAdd"
            placeholder="请选择算法"
            filterable
            clearable
          />
        </n-form-item>
        <n-form-item label="置信度">
          <n-input-number
            v-model:value="addAlgorithmConfidence"
            :min="0"
            :max="1"
            :step="0.05"
            :precision="2"
            placeholder="0.9"
            style="width: 100%"
          />
          <template #feedback> 检测置信度≥此值时触发告警，建议 0.8～0.95 </template>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddAlgorithmModal = false">取消</n-button>
          <n-button type="primary" :loading="addAlgorithmSubmitting" @click="submitAddAlgorithm">
            添加
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Draw Region Modal -->
    <DrawRegionModal
      v-model:show="showDrawRegionModal"
      :image-src="previewImage || '/camera-warehouse-01.jpg'"
      :algorithm-name="currentAlgorithm?.name || ''"
      :algorithm-name-en="currentAlgorithm?.nameEn || ''"
      :existing-regions="currentAlgorithm?.regions"
      @save="handleSaveRegions"
    />

    <!-- 告警策略弹框：覆盖算法的默认告警配置，不配置则使用算法默认 -->
    <n-modal
      v-model:show="showAlertStrategyModal"
      preset="card"
      title="告警策略"
      :style="{ width: '480px' }"
      @after-enter="initAlertStrategyForm"
    >
      <n-form label-placement="left" label-width="100">
        <n-form-item label="触发方式">
          <n-radio-group v-model:value="alertStrategyForm.trigger_type">
            <n-radio-button value="instant">立即触发</n-radio-button>
            <n-radio-button value="duration">持续触发</n-radio-button>
            <n-radio-button value="count">数量触发</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="alertStrategyForm.trigger_type === 'duration'" label="持续时间(秒)">
          <n-input-number v-model:value="alertStrategyForm.duration_seconds" :min="1" style="width: 100%" />
        </n-form-item>
        <n-form-item v-if="alertStrategyForm.trigger_type === 'count'" label="数量阈值(个)">
          <n-input-number v-model:value="alertStrategyForm.count_threshold" :min="1" style="width: 100%" />
        </n-form-item>
        <n-form-item label="冷却时间(秒)">
          <n-input-number v-model:value="alertStrategyForm.cooldown_seconds" :min="0" style="width: 100%" />
          <template #feedback>同一位置重复告警的最小间隔</template>
        </n-form-item>
        <n-form-item label="告警级别">
          <n-select
            v-model:value="alertStrategyForm.alert_level"
            :options="[
              { label: '提示', value: 'info' },
              { label: '警告', value: 'warning' },
              { label: '危险', value: 'danger' }
            ]"
            style="width: 100%"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="space-between">
          <n-button @click="restoreDefaultAlertStrategy">恢复默认</n-button>
          <n-space>
            <n-button @click="showAlertStrategyModal = false">取消</n-button>
            <n-button type="primary" :loading="alertStrategySaving" @click="saveAlertStrategy">保存</n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- 实时预览弹窗 -->
    <n-modal
      v-model:show="showLivePlayer"
      preset="card"
      title="实时预览"
      :style="{ width: '960px' }"
      @after-leave="handleLivePlayerClosed"
    >
      <div style="width: 100%; aspect-ratio: 16 / 9;">
        <FlvPlayer
          v-if="livePlayUrl"
          :url="livePlayUrl"
          @fatal="handleLivePlayFatalError"
        />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NInput, NTreeSelect, NButton, NIcon, NSwitch,
  NSlider, NPopover, NTimePicker, NModal, NForm, NFormItem, NSelect, NInputNumber, NSpace,
  NRadioGroup, NRadioButton
} from 'naive-ui'
import type { TreeSelectOption } from 'naive-ui'
import {
  VideocamOffOutline,
  CameraOutline,
  SaveOutline,
  ScanOutline,
  TimeOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { useUserStore } from '@/stores/user'
import DrawRegionModal from './DrawRegionModal.vue'
import FlvPlayer from './FlvPlayer.vue'
import { getCamera, probeStream, snapshotCamera, getCameraPlayUrls, cameraLiveHeartbeat, startCamera, stopCamera } from '@/api/camera'
import {
  getCameraAlgorithmConfigs,
  addCameraAlgorithmConfig,
  deleteCameraAlgorithmConfig,
  updateCameraAlgorithmConfig,
  getAlgorithmList,
  type CameraAlgorithmConfig
} from '@/api/algorithm'
import { useMessage } from 'naive-ui'

interface Region {
  points: { x: number; y: number }[]
  color: string
  type: string
}

/** 告警策略配置（算法默认 + 摄像头可覆盖） */
interface AlertStrategyConfig {
  trigger_type: 'instant' | 'duration' | 'count'
  duration_seconds: number
  count_threshold: number
  cooldown_seconds: number
  alert_level: 'info' | 'warning' | 'danger'
}

interface Algorithm {
  id: string
  name: string
  nameEn?: string
  enabled: boolean
  confidence: number
  alarmIntervalSec: number
  alertConfigOverride?: AlertStrategyConfig | null
  effectiveAlertConfig?: AlertStrategyConfig
  regionCount?: number
  timeRange?: string
  startTime?: number
  endTime?: number
  regions?: Region[]
  configId?: string
  algorithmId?: string
}

const props = defineProps<{
  cameraId?: string | null
  areaTreeData?: any[]
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'save', data: any): void
}>()

// Form data
const formData = ref({
  name: '',
  location: null as string | null,
  rtspUrl: '',
  fps: null as number | null,
  resolution: null as string | null,
  inferenceIntervalSec: null as number | null
})

const message = useMessage()
const userStore = useUserStore()
const connectionStatus = ref<'online' | 'offline'>('offline')
const testingConnection = ref(false)
const streamInfo = ref<{ width: number; height: number; fps: number | null; resolution: string | null } | null>(null)
const previewImage = ref('/camera-warehouse-01.jpg')
const snapshots = ref<string[]>([])
const livePlaying = ref(false)
const showLivePlayer = ref(false)
const livePlayUrl = ref<string | null>(null)
let liveHeartbeatTimer: number | null = null

// 已配置算法（编辑时从后端加载）
const cameraAlgorithmConfigs = ref<CameraAlgorithmConfig[]>([])
const showAddAlgorithmModal = ref(false)
const algorithmOptionsForAdd = ref<{ label: string; value: string }[]>([])
const algorithmIdToModelId = ref<Record<string, string>>({})
const addAlgorithmSelectedId = ref<string | null>(null)
const addAlgorithmConfidence = ref(0.9)
const addAlgorithmSubmitting = ref(false)

// Draw Region Modal
const showDrawRegionModal = ref(false)
const currentAlgorithm = ref<Algorithm | null>(null)

// 告警策略弹框
const showAlertStrategyModal = ref(false)
const currentAlertStrategyAlgo = ref<Algorithm | null>(null)
const alertStrategySaving = ref(false)
const alertStrategyForm = ref<AlertStrategyConfig>({
  trigger_type: 'instant',
  duration_seconds: 0,
  count_threshold: 0,
  cooldown_seconds: 30,
  alert_level: 'warning'
})

function openAlertStrategyModal(algo: Algorithm) {
  currentAlertStrategyAlgo.value = algo
  showAlertStrategyModal.value = true
}

function initAlertStrategyForm() {
  const algo = currentAlertStrategyAlgo.value
  if (!algo) return
  const cfg = algo.effectiveAlertConfig || {
    trigger_type: 'instant' as const,
    duration_seconds: 0,
    count_threshold: 0,
    cooldown_seconds: 30,
    alert_level: 'warning' as const
  }
  alertStrategyForm.value = {
    trigger_type: cfg.trigger_type || 'instant',
    duration_seconds: cfg.duration_seconds ?? 0,
    count_threshold: cfg.count_threshold ?? 0,
    cooldown_seconds: cfg.cooldown_seconds ?? 30,
    alert_level: cfg.alert_level || 'warning'
  }
}

async function saveAlertStrategy() {
  const algo = currentAlertStrategyAlgo.value
  const cameraId = props.cameraId
  if (!algo?.configId || !cameraId) return
  alertStrategySaving.value = true
  try {
    await updateCameraAlgorithmConfig(cameraId, algo.configId, {
      alert_config: { ...alertStrategyForm.value }
    })
    message.success('告警策略已保存')
    showAlertStrategyModal.value = false
    await loadCameraAlgorithmConfigs(cameraId)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '保存失败')
  } finally {
    alertStrategySaving.value = false
  }
}

async function restoreDefaultAlertStrategy() {
  const algo = currentAlertStrategyAlgo.value
  const cameraId = props.cameraId
  if (!algo?.configId || !cameraId) return
  alertStrategySaving.value = true
  try {
    await updateCameraAlgorithmConfig(cameraId, algo.configId, {
      alert_config: null
    })
    message.success('已恢复为算法默认配置')
    showAlertStrategyModal.value = false
    await loadCameraAlgorithmConfigs(cameraId)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '恢复失败')
  } finally {
    alertStrategySaving.value = false
  }
}

// Time Popover
const activeTimePopover = ref<string | null>(null)

// Area options
const areaOptions = computed<TreeSelectOption[]>(() => {
  if (props.areaTreeData && props.areaTreeData.length > 0) {
    return convertToTreeSelectOptions(props.areaTreeData)
  }
  return [
    {
      key: 'main-park',
      label: '主园区',
      children: [
        { key: 'a-warehouse', label: 'A栋仓库' },
        { key: 'b-office', label: 'B区办公楼' },
        { key: 'security-center', label: '安防中心' }
      ]
    },
    {
      key: 'material-yard',
      label: '物料堆场',
      children: [
        { key: 'yard-a', label: '堆场A区' },
        { key: 'yard-b', label: '堆场B区' }
      ]
    }
  ]
})

function convertToTreeSelectOptions(nodes: any[]): TreeSelectOption[] {
  return nodes.map(node => ({
    key: node.key,
    label: node.label,
    children: node.children ? convertToTreeSelectOptions(node.children) : undefined
  }))
}

// Algorithms：新增摄像头时为空；编辑时从后端摄像头算法配置加载
const algorithms = ref<Algorithm[]>([])

const enabledAlgorithmCount = computed(() => 
  algorithms.value.filter(a => a.enabled).length
)

async function testConnection() {
  if (!formData.value.rtspUrl?.trim()) {
    message.warning('请先填写 RTSP 流地址')
    return
  }
  testingConnection.value = true
  streamInfo.value = null
  try {
    const res = await probeStream({
      rtsp_url: formData.value.rtspUrl,
    })
    const data = (res.data as any)?.data ?? res.data
    if (data?.width != null && data?.height != null) {
      streamInfo.value = {
        width: data.width,
        height: data.height,
        fps: data.fps ?? null,
        resolution: data.resolution ?? null
      }
      formData.value.fps = data.fps ?? null
      formData.value.resolution = data.resolution ?? null
      connectionStatus.value = 'online'
      message.success('流通性测试成功')
    } else {
      connectionStatus.value = 'offline'
      message.error((res.data as any)?.detail || '探测失败')
    }
  } catch (e: any) {
    connectionStatus.value = 'offline'
    message.error(e?.response?.data?.detail || e?.message || '流通性测试失败')
  } finally {
    testingConnection.value = false
  }
}

async function captureSnapshot() {
  if (props.cameraId) {
    try {
      const res = await snapshotCamera(props.cameraId)
      const data = (res.data as any)?.data ?? res.data
      const url = data?.snapshot_url
      if (url) {
        const base = import.meta.env.VITE_API_BASE_URL || ''
        if (typeof url === 'string' && (url.startsWith('http://') || url.startsWith('https://'))) {
          previewImage.value = url
        } else {
          previewImage.value = base + url
        }
        snapshots.value = [previewImage.value]
        message.success('抓拍已保存，列表将显示为缩略图')
      }
    } catch (e: any) {
      message.error(e?.response?.data?.detail || e?.message || '抓拍失败')
    }
  } else {
    if (snapshots.value.length < 4) {
      snapshots.value.push(previewImage.value || '/camera-lobby-01.jpg')
    }
  }
}

async function playLive() {
  if (!props.cameraId) return
  try {
    if (livePlaying.value) {
      await stopCamera(props.cameraId)
      livePlaying.value = false
      showLivePlayer.value = false
      livePlayUrl.value = null
      if (liveHeartbeatTimer !== null) {
        window.clearInterval(liveHeartbeatTimer)
        liveHeartbeatTimer = null
      }
      message.success('已停止直播')
      return
    }

    // 启动摄像头 Pipeline
    await startCamera(props.cameraId)
    const res = await getCameraPlayUrls(props.cameraId)
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
    livePlayUrl.value = flvUrl
    showLivePlayer.value = true
    livePlaying.value = true

    // 启动心跳
    if (liveHeartbeatTimer !== null) {
      window.clearInterval(liveHeartbeatTimer)
    }
    liveHeartbeatTimer = window.setInterval(() => {
      if (!props.cameraId) return
      cameraLiveHeartbeat(props.cameraId).catch(() => {
        // 心跳失败暂时忽略
      })
    }, 60000)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '启动播放失败')
  }
}

function handleLivePlayerClosed() {
  livePlayUrl.value = null
  if (props.cameraId && livePlaying.value) {
    stopCamera(props.cameraId).catch(() => {})
  }
  livePlaying.value = false
  if (liveHeartbeatTimer !== null) {
    window.clearInterval(liveHeartbeatTimer)
    liveHeartbeatTimer = null
  }
}

function handleLivePlayFatalError() {
  message.error('30 秒内未能播放该摄像头的流，请稍后重试')
  showLivePlayer.value = false
}

function configRegion(algo: Algorithm) {
  currentAlgorithm.value = algo
  showDrawRegionModal.value = true
}

function handleSaveRegions(regions: Region[]) {
  if (currentAlgorithm.value) {
    currentAlgorithm.value.regions = regions
    currentAlgorithm.value.regionCount = regions.length
    // 将前端 Region 转成后端期望的二维点数组并持久化
    const cameraId = props.cameraId
    const configId = currentAlgorithm.value.configId || currentAlgorithm.value.id
    if (cameraId && configId) {
      const payloadRegions: number[][][] = regions.map((r) =>
        r.points.map((p) => [p.x, p.y])
      )
      updateCameraAlgorithmConfig(cameraId, configId, {
        regions: payloadRegions,
      }).catch(() => {
        // 若更新失败，先不打断前端体验
      })
    }
  }
}

// Time handling
function getDefaultTime(time: string): number {
  const [hours, minutes] = time.split(':').map(Number)
  return (hours * 60 + minutes) * 60 * 1000
}

function formatTime(timestamp: number | undefined): string {
  if (timestamp === undefined) return '00:00'
  const totalMinutes = Math.floor(timestamp / 60000)
  const hours = Math.floor(totalMinutes / 60) % 24
  const minutes = totalMinutes % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
}

function setTimePreset(algo: Algorithm, preset: string) {
  const idx = algorithms.value.findIndex(a => a.id === algo.id)
  if (idx === -1) return
  
  let startTime = 0
  let endTime = getDefaultTime('23:59')
  
  switch (preset) {
    case '全天':
      startTime = 0
      endTime = getDefaultTime('23:59')
      break
    case '白天':
      startTime = getDefaultTime('06:00')
      endTime = getDefaultTime('18:00')
      break
    case '夜间':
      startTime = getDefaultTime('18:00')
      endTime = getDefaultTime('06:00')
      break
    case '工作时间':
      startTime = getDefaultTime('08:00')
      endTime = getDefaultTime('18:00')
      break
  }
  
  // Update using array index for proper reactivity
  algorithms.value[idx].startTime = startTime
  algorithms.value[idx].endTime = endTime
  algorithms.value[idx].timeRange = `${formatTime(startTime)} - ${formatTime(endTime)}`
}

function confirmTimeSelection(algo: Algorithm) {
  const idx = algorithms.value.findIndex(a => a.id === algo.id)
  if (idx === -1) return
  
  // Update timeRange when confirm button is clicked using array index
  const startTime = algorithms.value[idx].startTime
  const endTime = algorithms.value[idx].endTime
  algorithms.value[idx].timeRange = `${formatTime(startTime)} - ${formatTime(endTime)}`
  activeTimePopover.value = null
}

async function loadCameraDetail(id: string) {
  try {
    const res = await getCamera(id)
    const c = (res.data as any)?.data ?? res.data
    if (!c) return
    // 网络状态使用 Redis 在线状态（后端从 camera:online:{id} 读取）
    connectionStatus.value = (c.online === true) ? 'online' : 'offline'
    formData.value = {
      name: c.name ?? '',
      location: c.area_id ?? null,
      rtspUrl: c.rtsp_url ?? '',
      fps: c.fps ?? null,
      resolution: c.resolution ?? null,
      inferenceIntervalSec: (c as any).inference_interval_sec ?? null
    }
    if (c.snapshot_url) {
      const base = import.meta.env.VITE_API_BASE_URL || ''
      const raw = c.snapshot_url as string
      if (raw.startsWith('http://') || raw.startsWith('https://')) {
        previewImage.value = raw
      } else {
        previewImage.value = base + raw
      }
    }
    if (c.fps != null || c.resolution) {
      streamInfo.value = {
        width: 0,
        height: 0,
        fps: c.fps ?? null,
        resolution: c.resolution ?? null
      }
      if (c.resolution && typeof c.resolution === 'string' && c.resolution.includes('x')) {
        const [w, h] = c.resolution.split('x').map(Number)
        if (!isNaN(w) && !isNaN(h)) {
          streamInfo.value!.width = w
          streamInfo.value!.height = h
        }
      }
    }
    if (props.cameraId) await loadCameraAlgorithmConfigs(props.cameraId)
  } catch (e) {
    console.error('加载摄像头详情失败', e)
  }
}

async function loadCameraAlgorithmConfigs(cameraId: string) {
  try {
    const res = await getCameraAlgorithmConfigs(cameraId)
    const data = (res.data as any)?.data ?? res.data
    cameraAlgorithmConfigs.value = Array.isArray(data) ? data : []
    // 同步到下方算法能力列表，让每个已配置算法在下面出现一行
    syncAlgorithmsFromConfigs()
  } catch (e) {
    console.error('加载摄像头算法配置失败', e)
    cameraAlgorithmConfigs.value = []
    // 加载失败保持现有 algorithms 配置
  }
}

function openAddAlgorithmModal() {
  addAlgorithmSelectedId.value = null
  addAlgorithmConfidence.value = 0.9
  showAddAlgorithmModal.value = true
}

async function loadAlgorithmListForAdd() {
  try {
    const res = await getAlgorithmList({ page: 1, page_size: 100 })
    const raw = res.data as any
    const list = Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []
    const map: Record<string, string> = {}
    algorithmOptionsForAdd.value = list.map((a: any) => {
      if (a.model_id) map[a.id] = a.model_id
      return { label: `${a.name} (${a.code || a.id})`, value: a.id }
    })
    algorithmIdToModelId.value = map
  } catch (e) {
    console.error('加载算法列表失败', e)
    algorithmOptionsForAdd.value = []
  }
}

async function submitAddAlgorithm() {
  const cameraId = props.cameraId
  const algorithmId = addAlgorithmSelectedId.value
  if (!cameraId || !algorithmId) {
    message.warning('请选择算法')
    return
  }
  const modelId = algorithmIdToModelId.value[algorithmId]
  if (!modelId) {
    message.error('未获取到该算法的模型 ID')
    return
  }
  addAlgorithmSubmitting.value = true
  try {
    await addCameraAlgorithmConfig(cameraId, {
      camera_id: cameraId,
      algorithm_id: algorithmId,
      model_id: modelId,
      confidence: addAlgorithmConfidence.value,
      is_enabled: true
    })
    message.success('已添加算法配置')
    showAddAlgorithmModal.value = false
    await loadCameraAlgorithmConfigs(cameraId)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '添加失败')
  } finally {
    addAlgorithmSubmitting.value = false
  }
}

async function removeCameraAlgorithmConfig(configId: string) {
  const cameraId = props.cameraId
  if (!cameraId) return
  try {
    await deleteCameraAlgorithmConfig(cameraId, configId)
    message.success('已移除')
    await loadCameraAlgorithmConfigs(cameraId)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || e?.message || '移除失败')
  }
}

// 根据后端返回的摄像头算法配置，刷新下方算法能力列表
function syncAlgorithmsFromConfigs() {
  if (!props.cameraId) return
  const configs = cameraAlgorithmConfigs.value
  if (!configs || configs.length === 0) {
    algorithms.value = []
    return
  }
  algorithms.value = configs.map((cfg, idx) => {
    const rawRegions = (cfg as any).regions as number[][][] | undefined
    // 将后端 regions 转成前端 Region 结构（颜色和类型在前端生成）
    const uiRegions: Region[] = (rawRegions || []).map((poly, polyIndex) => ({
      points: poly.map((p) => ({ x: p[0], y: p[1] })),
      color: ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899'][polyIndex % 6],
      type: polyIndex % 2 === 0 ? '入侵区' : '排查区',
    }))
    const conf =
      (cfg as any).effective_confidence ??
      (cfg as any).confidence ??
      0.9
    const alarmSec = (cfg as any).alarm_interval_sec ?? 30
    const rawAlert = (cfg as any).alert_config as Record<string, unknown> | null | undefined
    const rawEffective = (cfg as any).effective_alert_config as Record<string, unknown> | undefined
    const toStrategy = (r: Record<string, unknown> | null | undefined): AlertStrategyConfig | undefined => {
      if (!r || typeof r !== 'object') return undefined
      return {
        trigger_type: (r.trigger_type as any) || 'instant',
        duration_seconds: Number(r.duration_seconds) || 0,
        count_threshold: Number(r.count_threshold) || 0,
        cooldown_seconds: Number(r.cooldown_seconds) || 30,
        alert_level: (r.alert_level as any) || 'warning'
      }
    }
    return {
      id: cfg.id,
      configId: cfg.id,
      algorithmId: cfg.algorithm_id,
      name: cfg.algorithm_name || cfg.algorithm_id,
      enabled: cfg.is_enabled,
      confidence: Math.round(conf * 100),
      alarmIntervalSec: alarmSec,
      alertConfigOverride: rawAlert ? toStrategy(rawAlert) ?? undefined : null,
      effectiveAlertConfig: toStrategy(rawEffective || rawAlert),
      regionCount: uiRegions.length,
      timeRange: '00:00 - 23:59',
      startTime: 0,
      endTime: getDefaultTime('23:59'),
      regions: uiRegions,
    } as Algorithm
  })
}

onMounted(() => {
  if (props.cameraId) {
    loadCameraDetail(props.cameraId)
  }
})

watch(() => props.cameraId, (id) => {
  if (id) loadCameraDetail(id)
  else {
    formData.value = { name: '', location: null, rtspUrl: '', fps: null, resolution: null, inferenceIntervalSec: null }
    streamInfo.value = null
    previewImage.value = '/camera-warehouse-01.jpg'
    snapshots.value = []
    cameraAlgorithmConfigs.value = []
    algorithms.value = []
  }
})

function handleCancel() {
  emit('cancel')
}

async function handleSave() {
  const data = {
    ...formData.value,
    rtspUrl: formData.value.rtspUrl,
    fps: formData.value.fps ?? undefined,
    resolution: formData.value.resolution ?? undefined,
    inferenceIntervalSec: formData.value.inferenceIntervalSec ?? undefined,
    algorithms: algorithms.value.filter(a => a.enabled)
  }

  // 若是编辑已有摄像头，则在保存前将算法状态/置信度同步到后端 CameraAlgorithm 配置
  const cameraId = props.cameraId
  if (cameraId) {
    const updatePromises: Promise<unknown>[] = []
    for (const algo of algorithms.value) {
      if (!algo.configId) continue
      // 将 0-100 的置信度转换为 0-1 发送给后端
      const payload: {
        confidence?: number
        is_enabled?: boolean
        alarm_interval_sec?: number
      } = {
        confidence: algo.confidence / 100,
        is_enabled: algo.enabled,
        alarm_interval_sec: Math.max(1, Math.min(3600, algo.alarmIntervalSec ?? 30))
      }
      updatePromises.push(
        updateCameraAlgorithmConfig(cameraId, algo.configId, payload)
      )
    }
    try {
      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
    } catch (e) {
      console.error('更新摄像头算法配置失败', e)
      // 不中断主流程，仍然继续保存摄像头基本信息
    }
    ;(data as any).id = cameraId
  }

  emit('save', data)
}
</script>

<style scoped>
.add-camera-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

/* Header */
.add-camera-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.add-camera-page__header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.add-camera-page__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.add-camera-page__id {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.add-camera-page__header-actions {
  display: flex;
  gap: var(--spacing-md);
}

/* Content: 上排左右 50/50，下排算法全宽 */
.add-camera-page__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-xl);
  overflow-y: auto;
}

.add-camera-page__top {
  display: flex;
  gap: var(--spacing-xl);
  flex: 0 0 auto;
}

.add-camera-page__top-left {
  flex: 1;
  min-width: 0;
  max-width: 50%;
}

.add-camera-page__top-right {
  flex: 1;
  min-width: 0;
  max-width: 50%;
}

.add-camera-page__bottom {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.add-camera-page__algorithm-section {
  width: 100%;
}

/* Config Card */
.config-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
}

.config-card--preview {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.config-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.config-card__title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.config-card__indicator {
  width: 4px;
  height: 16px;
  background: var(--primary-color);
  border-radius: var(--radius-xs);
}

.config-card__badge {
  font-size: var(--font-size-sm);
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
}

.form-field--row { display: flex; gap: 1rem; flex-wrap: wrap; }
.form-field--flex { flex: 1; min-width: 120px; }
.stream-info { margin-top: 0.5rem; font-size: 12px; color: var(--text-muted, #666); }
.algo-config-empty { padding: 12px 0; }
.algo-config-list { list-style: none; margin: 0; padding: 0; }
.algo-config-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--border-color, #eee); }
.algo-config-item:last-child { border-bottom: none; }
.algo-config-name { flex: 1; font-weight: 500; }
.algo-config-confidence { font-size: 12px; color: var(--text-muted, #666); }
.config-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

/* Form Fields */
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-field--flex {
  flex: 1;
}

.form-field__row {
  display: flex;
  gap: var(--spacing-lg);
}

.form-field__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
}

.form-field__group {
  display: flex;
  gap: var(--spacing-sm);
}

.form-field__input {
  flex: 1;
}

/* Connection Status */
.connection-status {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.connection-status--online {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: var(--success-color);
}

.connection-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

/* Preview */
.preview {
  flex: 1;
  margin-top: var(--spacing-md);
  display: flex;
  flex-direction: column;
}

.preview__video {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #1a1a2e;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.preview__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-sm);
  color: var(--text-muted);
}

.preview__snapshots {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.preview__snapshot {
  width: 60px;
  height: 45px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--border-color);
}

.preview__snapshot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Algorithm List */
.algorithm-list {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-top: var(--spacing-md);
}

.algorithm-list__header {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.algorithm-list__body {
  max-height: 320px;
  overflow-y: auto;
}

.algorithm-list__row {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-normal);
}

.algorithm-list__row:last-child {
  border-bottom: none;
}

.algorithm-list__row:hover {
  background: var(--bg-card);
}

.algorithm-list__row--enabled {
  background: rgba(67, 24, 255, 0.02);
}

.algorithm-list__col {
  display: flex;
  align-items: center;
}

.algorithm-list__col--enable {
  width: 50px;
  flex-shrink: 0;
}

.algorithm-list__col--name {
  flex: 1.5;
  gap: var(--spacing-xs);
}

.algorithm-list__col--confidence {
  flex: 1.2;
  gap: var(--spacing-sm);
}

.algorithm-list__col--interval,
.algorithm-list__col--alarm-int {
  width: 100px;
  flex-shrink: 0;
  gap: 4px;
}

.algorithm-list__hint {
  font-size: 10px;
  color: var(--error-color, #d03050);
  white-space: nowrap;
}

.algorithm-list__col--strategy {
  width: 90px;
  flex-shrink: 0;
}

.algorithm-list__col--region {
  flex: 1;
}

.algorithm-list__col--time {
  flex: 1;
}

.algorithm-list__col--action {
  width: 80px;
  flex-shrink: 0;
  justify-content: flex-end;
}

.algorithm-list__name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.algorithm-list__name-en {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.algorithm-list__slider {
  width: 80px;
}

.algorithm-list__confidence-value {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  min-width: 36px;
}

.algorithm-list__disabled {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.algorithm-list__time-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.algorithm-list__time-btn:hover {
  border-color: var(--primary-color);
}

/* Time Picker Panel */
.time-picker-panel {
  padding: var(--spacing-sm);
  min-width: 280px;
}

.time-picker-panel__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.time-picker-panel__row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.time-picker-panel__separator {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.time-picker-panel__presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
}

.time-picker-panel__footer {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
}

/* Responsive */
@media (max-width: 1000px) {
  .add-camera-page__content {
    flex-direction: column;
  }

  .add-camera-page__left {
    flex: none;
    max-width: none;
  }
}
</style>
