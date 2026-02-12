<template>
  <div class="algorithm-management">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-header__title">AI 模型管理</h1>
        <p class="page-header__subtitle">管理 AI 模型及其检测能力（算法）配置</p>
      </div>
      <div class="page-header__actions">
        <n-button type="primary" @click="openModelModal()">
          <template #icon>
            <n-icon><CloudUploadOutline /></n-icon>
          </template>
          模型上架
        </n-button>
      </div>
    </div>

    <!-- Model Cards Grid -->
    <div class="model-grid">
      <!-- Model Cards -->
      <div 
        v-for="model in models" 
        :key="model.id" 
        class="model-card"
        :class="{ 'model-card--disabled': !model.is_enabled }"
      >
        <!-- Card Header -->
        <div class="model-card__header">
          <div class="model-card__icon" :style="{ background: getModelIconBg(model.model_type) }">
            <n-icon :size="24" color="#fff">
              <component :is="getModelIcon(model.model_type)" />
            </n-icon>
          </div>
          <div class="model-card__status">
            <span 
              class="status-dot" 
              :class="model.is_enabled ? 'status-dot--running' : 'status-dot--stopped'"
            ></span>
            <span class="status-text">{{ model.is_enabled ? '已启用' : '已停用' }}</span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="model-card__body">
          <h3 class="model-card__name">{{ model.name }}</h3>
          <p class="model-card__code">编码: {{ model.code }}</p>
          <p class="model-card__version">版本: {{ model.version || 'V1.0.0' }}</p>
        </div>

        <!-- Classes Tags -->
        <div class="model-card__classes">
          <span class="classes-label">支持类别:</span>
          <div class="classes-tags">
            <n-tag 
              v-for="cls in model.classes.slice(0, 3)" 
              :key="cls" 
              size="small" 
              type="info"
            >
              {{ cls }}
            </n-tag>
            <n-tag v-if="model.classes.length > 3" size="small" type="default">
              +{{ model.classes.length - 3 }}
            </n-tag>
          </div>
        </div>

        <!-- Card Metrics -->
        <div class="model-card__metrics">
          <div class="metric">
            <span class="metric__label">检测能力</span>
            <span class="metric__value">{{ model.algorithm_count || 0 }} 个</span>
          </div>
          <div class="metric">
            <span class="metric__label">显存占用</span>
            <span class="metric__value">{{ model.gpu_memory_mb || '-' }} MB</span>
          </div>
          <div class="metric">
            <span class="metric__label">推理延迟</span>
            <span class="metric__value">{{ model.inference_ms || '-' }} ms</span>
          </div>
        </div>

        <!-- Card Actions -->
        <div class="model-card__actions">
          <n-button size="small" type="primary" @click="openAlgorithmConfig(model)">
            <template #icon>
              <n-icon><SettingsOutline /></n-icon>
            </template>
            配置算法
          </n-button>
          <n-button size="small" @click="openModelModal(model)">编辑</n-button>
          <n-dropdown :options="moreOptions" @select="(key) => handleMoreAction(key, model)">
            <n-button size="small" quaternary>
              <template #icon>
                <n-icon><EllipsisVertical /></n-icon>
              </template>
            </n-button>
          </n-dropdown>
        </div>
      </div>

      <!-- Add New Model Card -->
      <div class="model-card model-card--add" @click="openModelModal()">
        <div class="add-card__content">
          <div class="add-card__icon">
            <n-icon :size="32" color="var(--text-muted)"><AddOutline /></n-icon>
          </div>
          <h3 class="add-card__title">上架新模型</h3>
          <p class="add-card__desc">支持 YOLO, PyTorch, ONNX, TensorRT 等格式</p>
        </div>
      </div>
    </div>

    <!-- Model Upload/Edit Modal -->
    <n-modal 
      v-model:show="showModelModal" 
      preset="card" 
      :title="editingModel ? '编辑模型' : '模型上架'"
      :style="{ width: '680px' }"
      :bordered="false"
    >
      <n-form 
        ref="modelFormRef" 
        :model="modelForm" 
        :rules="modelRules" 
        label-placement="left" 
        label-width="100"
      >
        <n-form-item label="模型名称" path="name">
          <n-input v-model:value="modelForm.name" placeholder="请输入模型名称" />
        </n-form-item>
        <n-form-item label="模型编码" path="code">
          <n-input 
            v-model:value="modelForm.code" 
            placeholder="唯一标识，如: yolo_safety_v1"
            :disabled="!!editingModel"
          />
        </n-form-item>
        <n-form-item label="模型类型" path="model_type">
          <n-select 
            v-model:value="modelForm.model_type" 
            :options="modelTypeOptions"
            placeholder="请选择模型类型"
          />
        </n-form-item>
        <n-form-item label="版本号" path="version">
          <n-input v-model:value="modelForm.version" placeholder="例如: V1.0.0" />
        </n-form-item>
        <n-form-item label="模型文件" path="model_path">
          <n-input-group>
            <n-input 
              v-model:value="modelForm.model_path" 
              placeholder="模型文件路径，如: models/yolo_v8.pt"
              style="flex: 1"
            />
            <n-upload
              :show-file-list="false"
              :max="1"
              accept=".pt,.pth,.onnx,.pb,.h5,.engine"
              @change="handleFileUpload"
            >
              <n-button>
                <template #icon>
                  <n-icon><CloudUploadOutline /></n-icon>
                </template>
                上传
              </n-button>
            </n-upload>
          </n-input-group>
        </n-form-item>
        <n-form-item label="检测类别" path="classes">
          <n-dynamic-tags v-model:value="modelForm.classes" />
          <template #feedback>
            <span class="form-tip">输入模型支持的所有检测类别，按回车添加</span>
          </template>
        </n-form-item>
        <n-form-item label="显存占用" path="gpu_memory_mb">
          <n-input-number 
            v-model:value="modelForm.gpu_memory_mb" 
            placeholder="预估显存占用 (MB)"
            :min="0"
            style="width: 100%"
          >
            <template #suffix>MB</template>
          </n-input-number>
        </n-form-item>
        <n-form-item label="推理时间" path="inference_ms">
          <n-input-number 
            v-model:value="modelForm.inference_ms" 
            placeholder="预估推理时间 (ms)"
            :min="0"
            style="width: 100%"
          >
            <template #suffix>ms</template>
          </n-input-number>
        </n-form-item>
        <n-form-item label="模型描述" path="description">
          <n-input 
            v-model:value="modelForm.description" 
            type="textarea" 
            placeholder="请输入模型描述"
            :rows="2"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showModelModal = false">取消</n-button>
          <n-button type="primary" @click="handleModelSubmit" :loading="modelSubmitting">
            {{ editingModel ? '保存修改' : '确认上架' }}
          </n-button>
        </div>
      </template>
    </n-modal>

    <!-- Algorithm Configuration Modal -->
    <n-modal 
      v-model:show="showAlgorithmModal" 
      preset="card" 
      :title="`配置检测能力 - ${selectedModel?.name || ''}`"
      :style="{ width: '900px' }"
      :bordered="false"
    >
      <div class="algorithm-config">
        <!-- Algorithm List -->
        <div class="algorithm-list">
          <div class="algorithm-list__header">
            <h4>已配置的检测能力</h4>
            <n-button size="small" type="primary" @click="openAlgorithmForm()">
              <template #icon>
                <n-icon><AddOutline /></n-icon>
              </template>
              新增检测能力
            </n-button>
          </div>
          
          <n-empty v-if="!algorithms.length" description="暂无检测能力，点击上方按钮添加" />
          
          <div v-else class="algorithm-items">
            <div 
              v-for="algo in algorithms" 
              :key="algo.id" 
              class="algorithm-item"
              :class="{ 'algorithm-item--disabled': !algo.is_enabled }"
            >
              <div class="algorithm-item__info">
                <div class="algorithm-item__name">
                  {{ algo.name }}
                  <n-tag size="small" :type="algo.is_enabled ? 'success' : 'default'">
                    {{ algo.is_enabled ? '启用' : '停用' }}
                  </n-tag>
                </div>
                <div class="algorithm-item__code">编码: {{ algo.code }}</div>
                <div class="algorithm-item__classes">
                  <span>检测类别:</span>
                  <n-tag 
                    v-for="cls in algo.target_classes" 
                    :key="cls" 
                    size="tiny" 
                    type="info"
                  >
                    {{ cls }}
                  </n-tag>
                </div>
                <div class="algorithm-item__config">
                  <span>置信度: {{ algo.default_confidence }}</span>
                  <span>告警级别: {{ getAlertLevelText(algo.alert_config?.alert_level) }}</span>
                  <span>触发方式: {{ getTriggerTypeText(algo.alert_config?.trigger_type) }}</span>
                </div>
              </div>
              <div class="algorithm-item__actions">
                <n-button size="small" @click="openAlgorithmForm(algo)">编辑</n-button>
                <n-button size="small" @click="toggleAlgorithm(algo)">
                  {{ algo.is_enabled ? '停用' : '启用' }}
                </n-button>
                <n-popconfirm @positive-click="deleteAlgorithm(algo)">
                  <template #trigger>
                    <n-button size="small" type="error" quaternary>删除</n-button>
                  </template>
                  确定要删除此检测能力吗？
                </n-popconfirm>
              </div>
            </div>
          </div>
        </div>
      </div>
    </n-modal>

    <!-- Algorithm Form Modal -->
    <n-modal 
      v-model:show="showAlgorithmFormModal" 
      preset="card" 
      :title="editingAlgorithm ? '编辑检测能力' : '新增检测能力'"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-form 
        ref="algorithmFormRef" 
        :model="algorithmForm" 
        :rules="algorithmRules" 
        label-placement="left" 
        label-width="100"
      >
        <n-form-item label="能力名称" path="name">
          <n-input v-model:value="algorithmForm.name" placeholder="如: 人员入侵检测" />
        </n-form-item>
        <n-form-item label="能力编码" path="code">
          <n-input 
            v-model:value="algorithmForm.code" 
            placeholder="唯一标识，如: person_intrusion"
            :disabled="!!editingAlgorithm"
          />
        </n-form-item>
        <n-form-item label="检测类别" path="target_classes">
          <n-select
            v-model:value="algorithmForm.target_classes"
            multiple
            :options="availableClassOptions"
            placeholder="选择要检测的类别"
          />
          <template #feedback>
            <span class="form-tip">从模型支持的类别中选择此检测能力需要的类别</span>
          </template>
        </n-form-item>
        <n-form-item label="置信度阈值" path="default_confidence">
          <n-slider 
            v-model:value="algorithmForm.default_confidence" 
            :min="0.1" 
            :max="1" 
            :step="0.05"
            :format-tooltip="(v) => `${(v * 100).toFixed(0)}%`"
          />
          <n-input-number 
            v-model:value="algorithmForm.default_confidence" 
            :min="0.1" 
            :max="1" 
            :step="0.05"
            size="small"
            style="width: 100px; margin-left: 16px"
          />
        </n-form-item>
        
        <n-divider>告警配置</n-divider>
        
        <n-form-item label="触发方式" path="alert_config.trigger_type">
          <n-radio-group v-model:value="algorithmForm.alert_config.trigger_type">
            <n-radio-button value="instant">立即触发</n-radio-button>
            <n-radio-button value="duration">持续触发</n-radio-button>
            <n-radio-button value="count">数量触发</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item 
          v-if="algorithmForm.alert_config.trigger_type === 'duration'" 
          label="持续时间"
        >
          <n-input-number 
            v-model:value="algorithmForm.alert_config.duration_seconds" 
            :min="1"
            style="width: 100%"
          >
            <template #suffix>秒</template>
          </n-input-number>
        </n-form-item>
        <n-form-item 
          v-if="algorithmForm.alert_config.trigger_type === 'count'" 
          label="数量阈值"
        >
          <n-input-number 
            v-model:value="algorithmForm.alert_config.count_threshold" 
            :min="1"
            style="width: 100%"
          >
            <template #suffix>个</template>
          </n-input-number>
        </n-form-item>
        <n-form-item label="告警级别" path="alert_config.alert_level">
          <n-select 
            v-model:value="algorithmForm.alert_config.alert_level"
            :options="alertLevelOptions"
          />
        </n-form-item>
        <n-form-item label="冷却时间" path="alert_config.cooldown_seconds">
          <n-input-number 
            v-model:value="algorithmForm.alert_config.cooldown_seconds" 
            :min="0"
            style="width: 100%"
          >
            <template #suffix>秒</template>
          </n-input-number>
          <template #feedback>
            <span class="form-tip">同一位置重复告警的最小间隔时间</span>
          </template>
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input 
            v-model:value="algorithmForm.description" 
            type="textarea" 
            placeholder="检测能力描述"
            :rows="2"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showAlgorithmFormModal = false">取消</n-button>
          <n-button type="primary" @click="handleAlgorithmSubmit" :loading="algorithmSubmitting">
            {{ editingAlgorithm ? '保存修改' : '确认添加' }}
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted } from 'vue'
import type { Component } from 'vue'
import { 
  NButton, NIcon, NDropdown, NModal, NForm, NFormItem, 
  NInput, NSelect, NUpload, NTag, NDynamicTags, NInputNumber,
  NInputGroup, NSlider, NDivider, NRadioGroup, NRadioButton,
  NPopconfirm, NEmpty, useMessage 
} from 'naive-ui'
import { 
  CloudUploadOutline, 
  AddOutline, 
  EllipsisVertical,
  SettingsOutline,
  CubeOutline,
  HardwareChipOutline,
  SpeedometerOutline
} from '@vicons/ionicons5'

// Types
interface AlertConfig {
  trigger_type: 'instant' | 'duration' | 'count'
  duration_seconds: number
  count_threshold: number
  cooldown_seconds: number
  alert_level: 'info' | 'warning' | 'danger'
}

interface Algorithm {
  id: string
  name: string
  code: string
  model_id: string
  target_classes: string[]
  default_confidence: number
  alert_config: AlertConfig
  description?: string
  is_enabled: boolean
}

interface Model {
  id: string
  name: string
  code: string
  model_type: string
  model_path: string
  classes: string[]
  version?: string
  gpu_memory_mb?: number
  inference_ms?: number
  description?: string
  is_enabled: boolean
  algorithm_count: number
  algorithms?: Algorithm[]
}

const message = useMessage()

// Models data
const models = ref<Model[]>([
  {
    id: '10000000000000000000000000000001',
    name: '安全生产检测模型',
    code: 'yolo_safety_v1',
    model_type: 'yolo',
    model_path: 'models/yolo_safety_v1.pt',
    classes: ['person', 'helmet', 'no_helmet', 'vest', 'no_vest'],
    version: 'V1.2.0',
    gpu_memory_mb: 500,
    inference_ms: 30,
    description: '检测人员、安全帽、反光衣',
    is_enabled: true,
    algorithm_count: 3
  },
  {
    id: '10000000000000000000000000000002',
    name: '烟火检测模型',
    code: 'fire_smoke_v1',
    model_type: 'yolo',
    model_path: 'models/fire_smoke_v1.pt',
    classes: ['fire', 'smoke'],
    version: 'V1.4.0',
    gpu_memory_mb: 300,
    inference_ms: 25,
    description: '检测明火和烟雾',
    is_enabled: true,
    algorithm_count: 1
  }
])

// Algorithms for selected model
const algorithms = ref<Algorithm[]>([])

// Model Modal
const showModelModal = ref(false)
const editingModel = ref<Model | null>(null)
const modelSubmitting = ref(false)
const modelFormRef = ref()
const modelForm = ref({
  name: '',
  code: '',
  model_type: null as string | null,
  model_path: '',
  classes: [] as string[],
  version: '',
  gpu_memory_mb: null as number | null,
  inference_ms: null as number | null,
  description: ''
})

const modelRules = {
  name: { required: true, message: '请输入模型名称', trigger: 'blur' },
  code: { required: true, message: '请输入模型编码', trigger: 'blur' },
  model_type: { required: true, message: '请选择模型类型', trigger: 'change' },
  model_path: { required: true, message: '请输入模型文件路径', trigger: 'blur' },
  classes: { 
    type: 'array', 
    required: true, 
    min: 1,
    message: '请至少添加一个检测类别', 
    trigger: 'change' 
  }
}

const modelTypeOptions = [
  { label: 'YOLO', value: 'yolo' },
  { label: 'ONNX', value: 'onnx' },
  { label: 'TensorRT', value: 'tensorrt' },
  { label: 'PyTorch', value: 'pytorch' },
  { label: '自定义', value: 'custom' }
]

// Algorithm Config Modal
const showAlgorithmModal = ref(false)
const selectedModel = ref<Model | null>(null)

// Algorithm Form Modal
const showAlgorithmFormModal = ref(false)
const editingAlgorithm = ref<Algorithm | null>(null)
const algorithmSubmitting = ref(false)
const algorithmFormRef = ref()
const algorithmForm = ref({
  name: '',
  code: '',
  target_classes: [] as string[],
  default_confidence: 0.5,
  alert_config: {
    trigger_type: 'instant' as 'instant' | 'duration' | 'count',
    duration_seconds: 3,
    count_threshold: 1,
    cooldown_seconds: 30,
    alert_level: 'warning' as 'info' | 'warning' | 'danger'
  },
  description: ''
})

const algorithmRules = {
  name: { required: true, message: '请输入能力名称', trigger: 'blur' },
  code: { required: true, message: '请输入能力编码', trigger: 'blur' },
  target_classes: { 
    type: 'array', 
    required: true, 
    min: 1,
    message: '请至少选择一个检测类别', 
    trigger: 'change' 
  }
}

const alertLevelOptions = [
  { label: '提示 (Info)', value: 'info' },
  { label: '警告 (Warning)', value: 'warning' },
  { label: '危险 (Danger)', value: 'danger' }
]

// Computed
const availableClassOptions = computed(() => {
  if (!selectedModel.value) return []
  return selectedModel.value.classes.map(cls => ({
    label: cls,
    value: cls
  }))
})

// More options dropdown
const moreOptions = [
  { label: '启用/停用', key: 'toggle' },
  { label: '查看详情', key: 'detail' },
  { type: 'divider', key: 'd1' },
  { label: '删除', key: 'delete' }
]

// Helper functions
function getModelIcon(type: string): Component {
  const icons: Record<string, Component> = {
    yolo: markRaw(SpeedometerOutline),
    onnx: markRaw(HardwareChipOutline),
    tensorrt: markRaw(HardwareChipOutline),
    pytorch: markRaw(CubeOutline),
    custom: markRaw(CubeOutline)
  }
  return icons[type] || markRaw(CubeOutline)
}

function getModelIconBg(type: string): string {
  const bgs: Record<string, string> = {
    yolo: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    onnx: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    tensorrt: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    pytorch: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    custom: 'linear-gradient(135deg, #a8a8a8 0%, #888888 100%)'
  }
  return bgs[type] || bgs.custom
}

function getAlertLevelText(level?: string): string {
  const map: Record<string, string> = {
    info: '提示',
    warning: '警告',
    danger: '危险'
  }
  return map[level || 'warning'] || level || '-'
}

function getTriggerTypeText(type?: string): string {
  const map: Record<string, string> = {
    instant: '立即',
    duration: '持续',
    count: '数量'
  }
  return map[type || 'instant'] || type || '-'
}

// Model operations
function openModelModal(model?: Model) {
  editingModel.value = model || null
  if (model) {
    modelForm.value = {
      name: model.name,
      code: model.code,
      model_type: model.model_type,
      model_path: model.model_path,
      classes: [...model.classes],
      version: model.version || '',
      gpu_memory_mb: model.gpu_memory_mb || null,
      inference_ms: model.inference_ms || null,
      description: model.description || ''
    }
  } else {
    modelForm.value = {
      name: '',
      code: '',
      model_type: null,
      model_path: '',
      classes: [],
      version: '',
      gpu_memory_mb: null,
      inference_ms: null,
      description: ''
    }
  }
  showModelModal.value = true
}

function handleFileUpload(options: any) {
  if (options.file?.name) {
    modelForm.value.model_path = `models/${options.file.name}`
  }
}

async function handleModelSubmit() {
  try {
    await modelFormRef.value?.validate()
    modelSubmitting.value = true
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (editingModel.value) {
      // Update existing model
      const idx = models.value.findIndex(m => m.id === editingModel.value!.id)
      if (idx !== -1) {
        models.value[idx] = {
          ...models.value[idx],
          ...modelForm.value
        }
      }
      message.success('模型更新成功')
    } else {
      // Create new model
      const newModel: Model = {
        id: Date.now().toString().padStart(32, '0'),
        name: modelForm.value.name,
        code: modelForm.value.code,
        model_type: modelForm.value.model_type!,
        model_path: modelForm.value.model_path,
        classes: modelForm.value.classes,
        version: modelForm.value.version,
        gpu_memory_mb: modelForm.value.gpu_memory_mb || undefined,
        inference_ms: modelForm.value.inference_ms || undefined,
        description: modelForm.value.description,
        is_enabled: true,
        algorithm_count: 0
      }
      models.value.push(newModel)
      message.success('模型上架成功')
    }
    
    showModelModal.value = false
  } catch (e) {
    // Validation failed
  } finally {
    modelSubmitting.value = false
  }
}

function handleMoreAction(key: string, model: Model) {
  switch (key) {
    case 'toggle':
      model.is_enabled = !model.is_enabled
      message.success(model.is_enabled ? '模型已启用' : '模型已停用')
      break
    case 'detail':
      openAlgorithmConfig(model)
      break
    case 'delete':
      const idx = models.value.findIndex(m => m.id === model.id)
      if (idx !== -1) {
        models.value.splice(idx, 1)
        message.success('模型已删除')
      }
      break
  }
}

// Algorithm operations
function openAlgorithmConfig(model: Model) {
  selectedModel.value = model
  // Load algorithms for this model (mock data)
  algorithms.value = [
    {
      id: '20000000000000000000000000000001',
      name: '人员入侵检测',
      code: 'person_intrusion',
      model_id: model.id,
      target_classes: ['person'],
      default_confidence: 0.5,
      alert_config: {
        trigger_type: 'instant',
        duration_seconds: 0,
        count_threshold: 0,
        cooldown_seconds: 30,
        alert_level: 'danger'
      },
      is_enabled: true
    },
    {
      id: '20000000000000000000000000000002',
      name: '安全帽检测',
      code: 'helmet_detection',
      model_id: model.id,
      target_classes: ['no_helmet'],
      default_confidence: 0.6,
      alert_config: {
        trigger_type: 'duration',
        duration_seconds: 3,
        count_threshold: 0,
        cooldown_seconds: 60,
        alert_level: 'danger'
      },
      is_enabled: true
    },
    {
      id: '20000000000000000000000000000003',
      name: '反光衣检测',
      code: 'vest_detection',
      model_id: model.id,
      target_classes: ['no_vest'],
      default_confidence: 0.6,
      alert_config: {
        trigger_type: 'instant',
        duration_seconds: 0,
        count_threshold: 0,
        cooldown_seconds: 60,
        alert_level: 'warning'
      },
      is_enabled: true
    }
  ].filter(algo => algo.model_id === model.id)
  
  showAlgorithmModal.value = true
}

function openAlgorithmForm(algo?: Algorithm) {
  editingAlgorithm.value = algo || null
  if (algo) {
    algorithmForm.value = {
      name: algo.name,
      code: algo.code,
      target_classes: [...algo.target_classes],
      default_confidence: algo.default_confidence,
      alert_config: { ...algo.alert_config },
      description: algo.description || ''
    }
  } else {
    algorithmForm.value = {
      name: '',
      code: '',
      target_classes: [],
      default_confidence: 0.5,
      alert_config: {
        trigger_type: 'instant',
        duration_seconds: 3,
        count_threshold: 1,
        cooldown_seconds: 30,
        alert_level: 'warning'
      },
      description: ''
    }
  }
  showAlgorithmFormModal.value = true
}

async function handleAlgorithmSubmit() {
  try {
    await algorithmFormRef.value?.validate()
    algorithmSubmitting.value = true
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (editingAlgorithm.value) {
      // Update existing
      const idx = algorithms.value.findIndex(a => a.id === editingAlgorithm.value!.id)
      if (idx !== -1) {
        algorithms.value[idx] = {
          ...algorithms.value[idx],
          ...algorithmForm.value
        }
      }
      message.success('检测能力更新成功')
    } else {
      // Create new
      const newAlgo: Algorithm = {
        id: Date.now().toString().padStart(32, '0'),
        name: algorithmForm.value.name,
        code: algorithmForm.value.code,
        model_id: selectedModel.value!.id,
        target_classes: algorithmForm.value.target_classes,
        default_confidence: algorithmForm.value.default_confidence,
        alert_config: algorithmForm.value.alert_config,
        description: algorithmForm.value.description,
        is_enabled: true
      }
      algorithms.value.push(newAlgo)
      
      // Update model's algorithm count
      const modelIdx = models.value.findIndex(m => m.id === selectedModel.value!.id)
      if (modelIdx !== -1) {
        models.value[modelIdx].algorithm_count++
      }
      
      message.success('检测能力添加成功')
    }
    
    showAlgorithmFormModal.value = false
  } catch (e) {
    // Validation failed
  } finally {
    algorithmSubmitting.value = false
  }
}

function toggleAlgorithm(algo: Algorithm) {
  algo.is_enabled = !algo.is_enabled
  message.success(algo.is_enabled ? '检测能力已启用' : '检测能力已停用')
}

function deleteAlgorithm(algo: Algorithm) {
  const idx = algorithms.value.findIndex(a => a.id === algo.id)
  if (idx !== -1) {
    algorithms.value.splice(idx, 1)
    
    // Update model's algorithm count
    const modelIdx = models.value.findIndex(m => m.id === selectedModel.value!.id)
    if (modelIdx !== -1) {
      models.value[modelIdx].algorithm_count = Math.max(0, models.value[modelIdx].algorithm_count - 1)
    }
    
    message.success('检测能力已删除')
  }
}

// Init
onMounted(() => {
  // Load models from API
})
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

/* Model Grid */
.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--spacing-lg);
  flex: 1;
  overflow-y: auto;
  padding-bottom: var(--spacing-lg);
  align-content: start;
}

/* Model Card */
.model-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: all 0.3s ease;
}

.model-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgba(67, 24, 255, 0.12);
}

.model-card--disabled {
  opacity: 0.7;
}

.model-card--disabled:hover {
  transform: none;
  box-shadow: none;
}

/* Card Header */
.model-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.model-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-card__status {
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

.status-text {
  color: var(--text-muted);
}

/* Card Body */
.model-card__body {
  flex: 1;
  min-height: 60px;
}

.model-card__name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs);
}

.model-card__code,
.model-card__version {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin: 0;
}

/* Classes Tags */
.model-card__classes {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  padding: var(--spacing-sm) 0;
}

.classes-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.classes-tags {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

/* Card Metrics */
.model-card__metrics {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.metric {
  flex: 1;
  text-align: center;
}

.metric__label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  display: block;
  margin-bottom: var(--spacing-xs);
}

.metric__value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

/* Card Actions */
.model-card__actions {
  display: flex;
  gap: var(--spacing-sm);
}

.model-card__actions .n-button:first-child {
  flex: 1;
}

/* Add Card */
.model-card--add {
  border: 2px dashed var(--border-color);
  background: transparent;
  cursor: pointer;
  justify-content: center;
  align-items: center;
  min-height: 320px;
}

.model-card--add:hover {
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

/* Form tip */
.form-tip {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

/* Algorithm Config */
.algorithm-config {
  min-height: 400px;
}

.algorithm-list__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.algorithm-list__header h4 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.algorithm-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.algorithm-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-md);
  background: var(--bg-hover);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.algorithm-item--disabled {
  opacity: 0.6;
}

.algorithm-item__info {
  flex: 1;
}

.algorithm-item__name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.algorithm-item__code {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin-bottom: var(--spacing-xs);
}

.algorithm-item__classes {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.algorithm-item__classes .n-tag {
  margin-left: var(--spacing-xs);
}

.algorithm-item__config {
  display: flex;
  gap: var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.algorithm-item__actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

/* Scrollbar */
.model-grid::-webkit-scrollbar {
  width: 6px;
}

.model-grid::-webkit-scrollbar-track {
  background: transparent;
}

.model-grid::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.model-grid::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
