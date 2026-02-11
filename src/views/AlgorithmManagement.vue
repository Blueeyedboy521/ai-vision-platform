<template>
  <div class="algorithm-management">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">AI 算法模型管理</h1>
        <p class="page-header__subtitle">上架、配置、监控及优化工业视觉 AI 模型</p>
      </div>
      <div class="page-header__actions">
        <n-button type="primary" @click="showUploadModal = true">
          <template #icon>
            <n-icon><CloudUploadOutline /></n-icon>
          </template>
          模型上架
        </n-button>
      </div>
    </div>

    <!-- Algorithm Cards Grid -->
    <div class="algorithm-grid">
      <!-- Algorithm Cards -->
      <div 
        v-for="algo in algorithms" 
        :key="algo.id" 
        class="algorithm-card"
        :class="{ 'algorithm-card--disabled': algo.status === 'stopped' }"
      >
        <!-- Card Header -->
        <div class="algorithm-card__header">
          <div class="algorithm-card__icon" :style="{ background: algo.iconBg }">
            <n-icon :size="24" :color="algo.iconColor">
              <component :is="algo.icon" />
            </n-icon>
          </div>
          <div class="algorithm-card__status">
            <span 
              class="status-dot" 
              :class="`status-dot--${algo.status}`"
            ></span>
            <span class="status-text">{{ getStatusText(algo.status) }}</span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="algorithm-card__body">
          <h3 class="algorithm-card__name">{{ algo.name }}</h3>
          <p class="algorithm-card__version">版本: {{ algo.version }}</p>
        </div>

        <!-- Card Metrics -->
        <div class="algorithm-card__metrics">
          <div class="metric">
            <span class="metric__label">推理延迟</span>
            <div class="metric__value">
              <span class="metric__number">{{ algo.latency }}ms</span>
              <span class="metric__status" :class="algo.latencyStatus">{{ algo.latencyStatus === 'stable' ? '稳定' : '波动' }}</span>
            </div>
          </div>
          <div class="metric">
            <span class="metric__label">平均精度</span>
            <div class="metric__value">
              <span class="metric__number">{{ algo.accuracy }}%</span>
              <span class="metric__trend" :class="algo.accuracyTrend > 0 ? 'up' : 'down'">
                {{ algo.accuracyTrend > 0 ? '↑' : '↓' }} {{ Math.abs(algo.accuracyTrend) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Card Actions -->
        <div class="algorithm-card__actions">
          <n-button size="small" @click="showVersionHistory(algo)">版本记录</n-button>
          <n-button size="small" @click="showParamConfig(algo)">参数定义</n-button>
          <n-dropdown :options="moreOptions" @select="(key) => handleMoreAction(key, algo)">
            <n-button size="small" quaternary>
              <template #icon>
                <n-icon><EllipsisVertical /></n-icon>
              </template>
            </n-button>
          </n-dropdown>
        </div>
      </div>

      <!-- Add New Algorithm Card -->
      <div class="algorithm-card algorithm-card--add" @click="showUploadModal = true">
        <div class="add-card__content">
          <div class="add-card__icon">
            <n-icon :size="32" color="var(--text-muted)"><AddOutline /></n-icon>
          </div>
          <h3 class="add-card__title">部署新算法</h3>
          <p class="add-card__desc">支持 YOLO, PyTorch, TensorFlow 等多种模型格式</p>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <n-modal 
      v-model:show="showUploadModal" 
      preset="card" 
      title="模型上架"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-placement="left" label-width="100">
        <n-form-item label="算法名称" path="name">
          <n-input v-model:value="uploadForm.name" placeholder="请输入算法名称" />
        </n-form-item>
        <n-form-item label="算法类型" path="type">
          <n-select 
            v-model:value="uploadForm.type" 
            :options="algorithmTypes"
            placeholder="请选择算法类型"
          />
        </n-form-item>
        <n-form-item label="模型框架" path="framework">
          <n-select 
            v-model:value="uploadForm.framework" 
            :options="frameworkOptions"
            placeholder="请选择模型框架"
          />
        </n-form-item>
        <n-form-item label="版本号" path="version">
          <n-input v-model:value="uploadForm.version" placeholder="例如: V1.0.0" />
        </n-form-item>
        <n-form-item label="模型文件" path="file">
          <n-upload
            :max="1"
            accept=".pt,.pth,.onnx,.pb,.h5"
            @change="handleFileChange"
          >
            <n-button>
              <template #icon>
                <n-icon><CloudUploadOutline /></n-icon>
              </template>
              选择模型文件
            </n-button>
          </n-upload>
        </n-form-item>
        <n-form-item label="算法描述" path="description">
          <n-input 
            v-model:value="uploadForm.description" 
            type="textarea" 
            placeholder="请输入算法描述"
            :rows="3"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showUploadModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpload">确认上架</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import type { Component } from 'vue'
import { 
  NButton, NIcon, NDropdown, NModal, NForm, NFormItem, 
  NInput, NSelect, NUpload, useMessage 
} from 'naive-ui'
import { 
  CloudUploadOutline, 
  AddOutline, 
  EllipsisVertical,
  ScanOutline,
  ShieldCheckmarkOutline,
  FlameOutline,
  BodyOutline,
  AlertCircleOutline,
  EyeOutline
} from '@vicons/ionicons5'

interface Algorithm {
  id: string
  name: string
  version: string
  status: 'running' | 'stopped' | 'updating'
  icon: Component
  iconBg: string
  iconColor: string
  latency: number
  latencyStatus: 'stable' | 'fluctuating'
  accuracy: number
  accuracyTrend: number
}

const message = useMessage()
const showUploadModal = ref(false)

// Algorithm data
const algorithms = ref<Algorithm[]>([
  {
    id: '1',
    name: 'YOLOv8 目标检测',
    version: 'V1.2.0',
    status: 'running',
    icon: markRaw(ScanOutline),
    iconBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    iconColor: '#fff',
    latency: 45,
    latencyStatus: 'stable',
    accuracy: 98.2,
    accuracyTrend: 0.5
  },
  {
    id: '2',
    name: '区域入侵检测',
    version: 'V1.1.5',
    status: 'running',
    icon: markRaw(ShieldCheckmarkOutline),
    iconBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    iconColor: '#fff',
    latency: 60,
    latencyStatus: 'stable',
    accuracy: 95.5,
    accuracyTrend: 0.5
  },
  {
    id: '3',
    name: '安全帽佩戴识别',
    version: 'V2.0.1',
    status: 'stopped',
    icon: markRaw(ShieldCheckmarkOutline),
    iconBg: 'linear-gradient(135deg, #a8a8a8 0%, #888888 100%)',
    iconColor: '#fff',
    latency: 92,
    latencyStatus: 'stable',
    accuracy: 99.1,
    accuracyTrend: 0.5
  },
  {
    id: '4',
    name: '人员跌倒识别',
    version: 'V1.0.3',
    status: 'running',
    icon: markRaw(BodyOutline),
    iconBg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    iconColor: '#fff',
    latency: 120,
    latencyStatus: 'stable',
    accuracy: 92.4,
    accuracyTrend: 0.5
  },
  {
    id: '5',
    name: '烟火检测模型',
    version: 'V1.4.0',
    status: 'updating',
    icon: markRaw(FlameOutline),
    iconBg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    iconColor: '#fff',
    latency: 75,
    latencyStatus: 'stable',
    accuracy: 97,
    accuracyTrend: 0.5
  }
])

// Form data
const uploadFormRef = ref()
const uploadForm = ref({
  name: '',
  type: null,
  framework: null,
  version: '',
  file: null,
  description: ''
})

const uploadRules = {
  name: { required: true, message: '请输入算法名称', trigger: 'blur' },
  type: { required: true, message: '请选择算法类型', trigger: 'change' },
  framework: { required: true, message: '请选择模型框架', trigger: 'change' },
  version: { required: true, message: '请输入版本号', trigger: 'blur' }
}

const algorithmTypes = [
  { label: '目标检测', value: 'detection' },
  { label: '图像分类', value: 'classification' },
  { label: '语义分割', value: 'segmentation' },
  { label: '行为识别', value: 'action' },
  { label: '异常检测', value: 'anomaly' }
]

const frameworkOptions = [
  { label: 'PyTorch', value: 'pytorch' },
  { label: 'TensorFlow', value: 'tensorflow' },
  { label: 'ONNX', value: 'onnx' },
  { label: 'PaddlePaddle', value: 'paddle' },
  { label: 'OpenVINO', value: 'openvino' }
]

const moreOptions = [
  { label: '启动/停止', key: 'toggle' },
  { label: '查看详情', key: 'detail' },
  { label: '复制算法', key: 'copy' },
  { type: 'divider', key: 'd1' },
  { label: '删除', key: 'delete' }
]

function getStatusText(status: string) {
  const map: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    updating: '更新中'
  }
  return map[status] || status
}

function showVersionHistory(algo: Algorithm) {
  message.info(`查看 ${algo.name} 的版本记录`)
}

function showParamConfig(algo: Algorithm) {
  message.info(`配置 ${algo.name} 的参数`)
}

function handleMoreAction(key: string, algo: Algorithm) {
  switch (key) {
    case 'toggle':
      algo.status = algo.status === 'running' ? 'stopped' : 'running'
      message.success(algo.status === 'running' ? '算法已启动' : '算法已停止')
      break
    case 'detail':
      message.info(`查看 ${algo.name} 详情`)
      break
    case 'copy':
      message.success(`已复制 ${algo.name}`)
      break
    case 'delete':
      message.warning(`删除 ${algo.name}`)
      break
  }
}

function handleFileChange(options: any) {
  uploadForm.value.file = options.file
}

function handleUpload() {
  uploadFormRef.value?.validate((errors: any) => {
    if (!errors) {
      message.success('模型上架成功')
      showUploadModal.value = false
      // Reset form
      uploadForm.value = {
        name: '',
        type: null,
        framework: null,
        version: '',
        file: null,
        description: ''
      }
    }
  })
}
</script>

<style scoped>
.algorithm-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Page Header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  flex-shrink: 0;
}

.page-header__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.page-header__subtitle {
  font-size: var(--font-size-base);
  color: var(--text-muted);
  margin: var(--spacing-xs) 0 0;
}

/* Algorithm Grid */
.algorithm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
  flex: 1;
  overflow-y: auto;
  padding-bottom: var(--spacing-lg);
  align-content: start;
}

/* Algorithm Card */
.algorithm-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: all 0.3s ease;
  height: 280px;
  max-height: 280px;
}

.algorithm-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgba(67, 24, 255, 0.12);
}

.algorithm-card--disabled {
  opacity: 0.7;
}

.algorithm-card--disabled:hover {
  transform: none;
  box-shadow: none;
}

/* Card Header */
.algorithm-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.algorithm-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.algorithm-card__status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--running {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}

.status-dot--stopped {
  background: #9ca3af;
}

.status-dot--updating {
  background: #f59e0b;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  color: var(--text-muted);
}

/* Card Body */
.algorithm-card__body {
  flex: 1;
}

.algorithm-card__name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs);
}

.algorithm-card__version {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin: 0;
}

/* Card Metrics */
.algorithm-card__metrics {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.metric {
  flex: 1;
}

.metric__label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  display: block;
  margin-bottom: var(--spacing-xs);
}

.metric__value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.metric__number {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.metric__status {
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.metric__status.stable {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.metric__status.fluctuating {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.metric__trend {
  font-size: var(--font-size-xs);
}

.metric__trend.up {
  color: #22c55e;
}

.metric__trend.down {
  color: #ef4444;
}

/* Card Actions */
.algorithm-card__actions {
  display: flex;
  gap: var(--spacing-sm);
}

.algorithm-card__actions .n-button:first-child,
.algorithm-card__actions .n-button:nth-child(2) {
  flex: 1;
}

/* Add Card */
.algorithm-card--add {
  border: 2px dashed var(--border-color);
  background: transparent;
  cursor: pointer;
  height: 280px;
  max-height: 280px;
  justify-content: center;
  align-items: center;
}

.algorithm-card--add:hover {
  border-color: var(--primary-color);
  background: rgba(67, 24, 255, 0.02);
}

.add-card__content {
  text-align: center;
}

.add-card__icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-md);
}

.add-card__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs);
}

.add-card__desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin: 0;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* Scrollbar */
.algorithm-grid::-webkit-scrollbar {
  width: 6px;
}

.algorithm-grid::-webkit-scrollbar-track {
  background: transparent;
}

.algorithm-grid::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.algorithm-grid::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
