<template>
  <div class="add-policy-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">新增报警策略</h1>
        <p class="page-subtitle">配置告警识别逻辑、区域过滤与多渠道自动化推送规则</p>
      </div>
      <div class="header-actions">
        <n-button type="default" size="medium" class="header-btn" @click="handleCancel">取消</n-button>
        <n-button type="primary" size="medium" class="header-btn" @click="handleSaveAndEnable">保存并启用</n-button>
      </div>
    </div>
    <!-- 页面内容 -->
    <div class="page-content">
      <div class="space-y-lg pb-xl">
        <!-- 基础信息部分 -->
        <section class="card p-xl">
          <div class="flex items-center gap-md mb-lg">
            <span class="section-indicator"></span>
            <h3 class="font-semibold text-lg">基础信息</h3>
          </div>
          <div class="grid grid-cols-12 gap-lg">
            <div class="col-span-12 md:col-span-3">
              <n-form-item label="策略 ID">
                <n-input v-model:value="policyId" readonly type="text" class="bg-page"/>
              </n-form-item>
            </div>
            <div class="col-span-12 md:col-span-5">
              <n-form-item label="策略名称" required>
                <n-input v-model:value="policyName" placeholder="例如：涂装车间火灾/烟雾告警策略"/>
              </n-form-item>
            </div>
            <div class="col-span-6 md:col-span-2">
              <n-form-item label="优先级">
                <n-select v-model:value="priority" :options="priorityOptions"/>
              </n-form-item>
            </div>
            <div class="col-span-6 md:col-span-2">
              <n-form-item label="当前状态">
                <div class="flex items-center gap-md">
                  <n-switch v-model:value="isEnabled"/>
                  <span class="text-secondary">{{ isEnabled ? '启用' : '禁用' }}</span>
                </div>
              </n-form-item>
            </div>
          </div>
        </section>

        <!-- 触发规则部分 -->
        <section class="card p-xl">
          <div class="flex items-center gap-md mb-lg">
            <span class="section-indicator"></span>
            <h3 class="font-semibold text-lg">触发规则</h3>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-xl">
            <!-- 左侧列 -->
            <div class="space-y-lg">
              <div>
                <n-form-item label="告警类别">
                  <div class="flex gap-md">
                    <n-button :type="alarmType === 'ai' ? 'primary' : 'default'" size="medium" @click="handleAlarmTypeChange('ai')">AI告警</n-button>
                    <n-button :type="alarmType === 'system' ? 'primary' : 'default'" size="medium" @click="handleAlarmTypeChange('system')">系统告警</n-button>
                  </div>
                </n-form-item>
              </div>
              <div>
                <n-form-item label="报警类型 (多选)">
                  <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                    <n-tag v-for="item in selectedAlarmTypes" :key="item" closable @close="handleRemoveAlarmType(item)">
                      {{ item }}
                    </n-tag>
                    <n-select
                      v-if="showAlarmTypeSelect"
                      v-model:value="currentAlarmType"
                      :options="currentAlarmTypeOptions"
                      placeholder="选择报警类型"
                      size="small"
                      style="width: 200px"
                      :loading="alarmType === 'ai' && loadingAlgorithms"
                      @update:value="handleAlarmTypeSelect"
                    />
                    <n-button v-else type="primary" dashed size="small" @click="showAlarmTypeSelect = true">
                      <template #icon><n-icon><Add /></n-icon></template>
                      添加
                    </n-button>
                  </div>
                </n-form-item>
              </div>
              <div>
                <n-form-item label="区域路径 (支持通配符)">
                  <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                    <n-tag v-for="item in selectedAreas" :key="item.id" closable @close="handleRemoveArea(item)">
                      {{ item.label }}
                    </n-tag>
                    <n-tree-select
                      v-if="showAreaSelect"
                      v-model:value="currentArea"
                      :options="areaTreeOptions"
                      placeholder="选择区域"
                      size="small"
                      style="width: 200px"
                      @update:value="handleAreaSelect"
                    />
                    <n-button v-else type="primary" dashed size="small" @click="showAreaSelect = true">
                      <template #icon><n-icon><Add /></n-icon></template>
                      添加
                    </n-button>
                  </div>
                </n-form-item>
              </div>
              <div>
                <n-form-item label="监控设备 (多选)">
                  <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                    <n-tag v-for="item in selectedDevices" :key="item.id" closable @close="handleRemoveDevice(item)">
                      {{ item.label }}
                    </n-tag>
                    <n-button type="primary" dashed size="small" @click="showDeviceModal = true">
                      <template #icon><n-icon><Add /></n-icon></template>
                      添加
                    </n-button>
                  </div>
                </n-form-item>
              </div>
            </div>
            <!-- 右侧列 -->
            <div class="space-y-lg">
              <div>
                <n-form-item label="报警等级过滤">
                  <div class="flex gap-lg p-sm flex-wrap">
                    <label class="flex items-center gap-sm cursor-pointer">
                      <n-checkbox v-model:checked="alarmLevels.danger" />
                      <span class="text-sm">危险 (Danger)</span>
                    </label>
                    <label class="flex items-center gap-sm cursor-pointer">
                      <n-checkbox v-model:checked="alarmLevels.critical" />
                      <span class="text-sm">严重 (Critical)</span>
                    </label>
                    <label class="flex items-center gap-sm cursor-pointer">
                      <n-checkbox v-model:checked="alarmLevels.warning" />
                      <span class="text-sm">一般 (Warning)</span>
                    </label>
                    <label class="flex items-center gap-sm cursor-pointer">
                      <n-checkbox v-model:checked="alarmLevels.info" />
                      <span class="text-sm">提示 (Info)</span>
                    </label>
                  </div>
                </n-form-item>
              </div>
              <div class="space-y-md">
                <div>
                  <n-form-item label="排除区域">
                    <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[42px] items-center">
                      <n-tag v-for="item in excludedAreas" :key="item.id" closable @close="handleRemoveExcludedArea(item)" type="default">
                        {{ item.label }}
                      </n-tag>
                      <n-tree-select
                        v-if="showExcludedAreaSelect"
                        v-model:value="currentExcludedArea"
                        :options="areaTreeOptions"
                        placeholder="选择排除区域"
                        size="small"
                        style="width: 200px"
                        @update:value="handleExcludedAreaSelect"
                      />
                      <n-button v-else type="default" dashed size="small" @click="showExcludedAreaSelect = true">
                        <template #icon><n-icon><Add /></n-icon></template>
                        排除路径
                      </n-button>
                    </div>
                  </n-form-item>
                </div>
                <div>
                  <n-form-item label="排除设备">
                    <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[42px] items-center">
                      <n-tag v-for="item in excludedDevices" :key="item.id" closable @close="handleRemoveExcludedDevice(item)" type="default">
                        {{ item.label }}
                      </n-tag>
                      <n-button type="default" dashed size="small" @click="showExcludedDeviceModal = true">
                        <template #icon><n-icon><Add /></n-icon></template>
                        排除 ID
                      </n-button>
                    </div>
                  </n-form-item>
                </div>
              </div>
              <div>
                <n-form-item label="触发时段 (24小时制)">
                  <div class="flex items-center gap-md bg-card border border-light rounded-lg p-md">
                    <n-time-picker v-model:value="timeRange.start" format="HH:mm" />
                    <span class="text-muted">至</span>
                    <n-time-picker v-model:value="timeRange.end" format="HH:mm" />
                    <n-icon class="text-muted"><TimeOutline /></n-icon>
                  </div>
                </n-form-item>
              </div>
            </div>
          </div>
        </section>

        <!-- 推送动作部分 -->
        <section class="card p-xl">
          <div class="flex items-center justify-between mb-lg">
            <div class="flex items-center gap-md">
              <span class="section-indicator"></span>
              <h3 class="font-semibold text-lg">推送动作</h3>
            </div>
            <n-button text type="primary" size="small" class="border border-primary/20 rounded-lg flex items-center gap-sm" @click="addPushAction">
              <template #icon><n-icon><Add /></n-icon></template>
              添加推送配置
            </n-button>
          </div>
          <div class="space-y-lg">
            <!-- 动作块 -->
            <div v-for="action in pushActions" :key="action.id" class="relative p-xl border border-light bg-page rounded-xl border-l-4 border-l-primary">
              <n-button text class="absolute top-lg right-lg text-muted hover:text-error" @click="removePushAction(action.id)">
                <template #icon><n-icon><TrashOutline /></n-icon></template>
              </n-button>
              <div class="grid grid-cols-12 gap-xl">
                <div class="col-span-12 md:col-span-5 space-y-lg">
                  <div>
                    <n-form-item label="推送渠道 (多选)">
                      <div class="p-md border border-light rounded-lg bg-card flex flex-wrap gap-sm min-h-[46px] items-center">
                        <n-tag v-for="item in action.channels" :key="item.value" closable @close="handleRemoveChannel(action.id, item)" :type="item.type">
                          <template #icon><n-icon size="14"><component :is="item.icon" /></n-icon></template>
                          {{ item.label }}
                        </n-tag>
                        <n-select
                          v-if="action.showChannelSelect"
                          v-model:value="action.currentChannel"
                          :options="channelOptions"
                          placeholder="选择推送渠道"
                          size="small"
                          style="width: 150px"
                          @update:value="(value) => handleChannelSelect(action.id, value)"
                        />
                        <n-button v-else type="primary" dashed size="small" @click="action.showChannelSelect = true">
                          <template #icon><n-icon><Add /></n-icon></template>
                          添加渠道
                        </n-button>
                      </div>
                    </n-form-item>
                  </div>
                  <div>
                    <n-form-item label="消息模版">
                      <n-select v-model:value="action.template" :options="templateOptions" />
                    </n-form-item>
                  </div>
                </div>
                <div class="col-span-12 md:col-span-7">
                  <div class="grid grid-cols-2 gap-lg">
                    <div>
                      <n-form-item label="静默时间 (秒)">
                        <n-input-number v-model:value="action.silenceTime" :min="0" />
                        <p class="text-xs text-muted mt-xs">相同报警在此时间内不重复发送</p>
                      </n-form-item>
                    </div>
                    <div>
                      <n-form-item label="去重关键字 (多选下拉)">
                        <n-select
                          v-model:value="action.deduplicationKeys"
                          :options="deduplicationKeyOptions"
                          multiple
                          placeholder="选择去重关键字"
                        />
                        <p class="text-xs text-muted mt-xs">用于唯一标识一条报警</p>
                      </n-form-item>
                    </div>
                    <div>
                      <n-form-item label="发送顺序">
                        <n-input-number v-model:value="action.sendOrder" :min="1" />
                        <p class="text-xs text-muted mt-xs">数字越小优先级越高</p>
                      </n-form-item>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 添加新动作触发器 -->
            <n-button type="default" dashed class="w-full py-8 rounded-xl flex flex-col items-center justify-center gap-md text-muted hover:text-primary hover:border-primary hover:bg-primary-light transition-all" @click="addPushAction">
              <n-icon size="32"><AddCircle /></n-icon>
              <span class="text-sm font-semibold">配置备用推送目标</span>
              <span class="text-xs">用于配置多级告警链路或备用通知方式</span>
            </n-button>
          </div>
        </section>
      </div>
    </div>

    <!-- 设备选择弹框 -->
    <n-modal v-model:show="showDeviceModal" preset="card" title="选择监控设备" style="width: 950px" :bordered="false">
      <div class="device-selector">
        <div class="device-selector-left">
          <div class="device-selector-title">区域树</div>
          <n-tree
            :data="deviceTreeData"
            :selected-keys="selectedDeviceTreeKeys"
            @update:selected-keys="handleDeviceTreeSelect"
            block-line
            show-line
            :default-expanded-keys="['root']"
            :theme-overrides="{
              nodeTextColor: '#555',
              nodeColorHover: 'rgba(67, 24, 255, 0.06)',
              nodeColorActive: 'rgba(67, 24, 255, 0.1)',
              lineColor: '#e5e7eb'
            }"
          />
        </div>
        <div class="device-selector-center">
          <div class="device-selector-header">
            <div class="device-selector-title">设备列表</div>
            <div class="device-count">{{ deviceTotal }} 个设备</div>
          </div>
          <div class="device-list">
            <n-skeleton v-if="loadingDevices" :rows="5" />
            <template v-else>
              <n-checkbox
                v-for="device in currentDeviceList"
                :key="device.id"
                :checked="tempSelectedDevices.some(d => d.id === device.id)"
                @update:checked="handleDeviceCheck(device.id, $event)"
                class="device-list-item"
              >
                <div class="device-info">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-meta text-xs text-muted">
                    {{ device.ip_address || '无IP' }} | 
                    {{ device.status === 'online' ? '在线' : '离线' }}
                  </div>
                </div>
              </n-checkbox>
              <div v-if="currentDeviceList.length === 0" class="device-list-empty">
                <n-empty description="该区域暂无设备" />
              </div>
            </template>
          </div>
          <div class="device-pagination">
            <n-pagination
              v-model:page="devicePage"
              v-model:page-size="devicePageSize"
              :page-sizes="[10, 20, 50]"
              :item-count="deviceTotal"
              @update:page="handleDevicePageChange"
              @update:page-size="handleDevicePageSizeChange"
            />
          </div>
        </div>
        <div class="device-selector-right">
          <div class="device-selector-title">已选择设备</div>
          <div class="selected-device-list">
            <n-tag v-for="device in tempSelectedDevices" :key="device.id" closable @close="handleRemoveTempDevice(device)" style="margin: 4px">
              {{ device.label }}
            </n-tag>
            <div v-if="tempSelectedDevices.length === 0" class="selected-device-empty text-xs text-muted">
              暂无选择
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-md">
          <n-button @click="showDeviceModal = false">取消</n-button>
          <n-button type="primary" @click="handleConfirmDevices">确定</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 排除设备选择弹框 -->
    <n-modal v-model:show="showExcludedDeviceModal" preset="card" title="选择排除设备" style="width: 900px" :bordered="false">
      <div class="device-selector">
        <div class="device-selector-left">
          <div class="device-selector-title">区域树</div>
          <n-tree
            :data="deviceTreeData"
            :selected-keys="selectedExcludedDeviceTreeKeys"
            @update:selected-keys="handleExcludedDeviceTreeSelect"
            block-line
            show-line
            :theme-overrides="{
              nodeTextColor: '#555',
              nodeColorHover: 'rgba(67, 24, 255, 0.06)',
              nodeColorActive: 'rgba(67, 24, 255, 0.1)',
              lineColor: '#e5e7eb'
            }"
          />
        </div>
        <div class="device-selector-center">
          <div class="device-selector-title">设备列表</div>
          <div class="device-list">
            <n-skeleton v-if="loadingDevices" :rows="5" />
            <template v-else>
              <n-checkbox
                v-for="device in currentExcludedDeviceList"
                :key="device.id"
                :checked="tempExcludedDevices.includes(device.id)"
                @update:checked="handleExcludedDeviceCheck(device.id, $event)"
                class="device-list-item"
              >
                <div class="device-info">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-meta text-xs text-muted">{{ device.ip_address || '无IP' }}</div>
                </div>
              </n-checkbox>
              <div v-if="currentExcludedDeviceList.length === 0" class="device-list-empty">
                <n-empty description="该区域暂无设备" />
              </div>
            </template>
          </div>
        </div>
        <div class="device-selector-right">
          <div class="device-selector-title">已选择设备</div>
          <div class="selected-device-list">
            <n-tag v-for="device in tempExcludedDevices" :key="device.id" closable @close="handleRemoveTempExcludedDevice(device)" style="margin: 4px">
              {{ device.label }}
            </n-tag>
            <div v-if="tempExcludedDevices.length === 0" class="selected-device-empty text-xs text-muted">
              暂无选择
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-md">
          <n-button @click="showExcludedDeviceModal = false">取消</n-button>
          <n-button type="primary" @click="handleConfirmExcludedDevices">确定</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NInput, NSelect, NSwitch, NCheckbox, NFormItem, NTimePicker, NInputNumber, NIcon, NTag, NModal, NTree, NTreeSelect, NEmpty, NSkeleton, useMessage } from 'naive-ui'
import { Close, Add, TimeOutline, ChatbubbleOutline, MailOutline, TrashOutline, ChevronDown, AddCircle } from '@vicons/ionicons5'
import { getAreaTree, type AreaTreeNode } from '@/api/area'
import { getCameraList, type Camera, type CameraQueryParams } from '@/api/camera'
import { getNotificationEndpoints, getNotificationTemplates, type NotificationEndpoint, type NotificationTemplate } from '@/api/notification'
import { getAlgorithmList, type Algorithm } from '@/api/algorithm'

const router = useRouter()
const message = useMessage()

const handleCancel = () => {
  router.push('/push/policies')
}

const handleSaveAndEnable = () => {
  // 表单校验
  if (!policyName.value) {
    message.warning('请输入策略名称')
    return
  }
  
  if (selectedAlarmTypes.value.length === 0) {
    message.warning('请选择至少一个报警类型')
    return
  }
  
  if (!alarmLevels.danger && !alarmLevels.critical && !alarmLevels.warning && !alarmLevels.info) {
    message.warning('请至少选择一个报警等级')
    return
  }
  
  if (pushActions.value.length === 0) {
    message.warning('请至少配置一个推送动作')
    return
  }
  
  // 校验每个推送动作
  for (const action of pushActions.value) {
    if (action.channels.length === 0) {
      message.warning('请为每个推送动作配置至少一个推送渠道')
      return
    }
    if (!action.template) {
      message.warning('请为每个推送动作选择消息模版')
      return
    }
  }
  
  // 组装数据
  const data = {
    name: policyName.value,
    priority: parseInt(priority.value),
    is_enabled: isEnabled.value,
    match: {
      category: alarmType.value,
      alarm_type: selectedAlarmTypes.value,
      area_path: selectedAreas.value.map(a => a.id),
      camera_id: selectedDevices.value.map(d => d.id),
      level: Object.keys(alarmLevels).filter(key => alarmLevels[key as keyof typeof alarmLevels]),
      exclude: {
        area_path: excludedAreas.value.map(a => a.id),
        camera_id: excludedDevices.value.map(d => d.id)
      },
      time_window: {
        start: `${timeRange.start.getHours().toString().padStart(2, '0')}:${timeRange.start.getMinutes().toString().padStart(2, '0')}`,
        end: `${timeRange.end.getHours().toString().padStart(2, '0')}:${timeRange.end.getMinutes().toString().padStart(2, '0')}`
      }
    },
    actions: pushActions.value.map(action => ({
      endpoint_ids: action.channels.map(c => c.value),
      template_id: action.template,
      throttle_sec: action.silenceTime,
      dedup_key: action.deduplicationKeys.join('+'),
      push_order: action.sendOrder
    })),
    match_desc: generateMatchDesc(),
    actions_desc: generateActionsDesc()
  }
  
  console.log('策略数据:', data)
  message.success('策略保存成功并已启用')
  router.push('/push/policies')
}

// 生成匹配条件描述
function generateMatchDesc(): string {
  const parts: string[] = []
  
  parts.push(alarmType.value === 'ai' ? 'AI告警' : '系统告警')
  
  // 报警类型
  if (selectedAlarmTypes.value.length > 0) {
    const typeLabels = selectedAlarmTypes.value.map(typeId => {
      const option = aiAlarmTypes.value.find(opt => opt.value === typeId) || 
                    systemAlarmTypes.find(opt => opt.value === typeId)
      return option ? option.label : typeId
    })
    parts.push(`类型: ${typeLabels.join('、')}`)
  }
  
  // 区域
  if (selectedAreas.value.length > 0) {
    parts.push(`区域: ${selectedAreas.value.map(a => a.label).join('、')}`)
  }
  
  // 设备
  if (selectedDevices.value.length > 0) {
    parts.push(`设备: ${selectedDevices.value.map(d => d.label).join('、')}`)
  }
  
  // 报警等级（使用中文标签）
  const levelLabels: string[] = []
  if (alarmLevels.danger) levelLabels.push('危险')
  if (alarmLevels.critical) levelLabels.push('严重')
  if (alarmLevels.warning) levelLabels.push('一般')
  if (alarmLevels.info) levelLabels.push('提示')
  if (levelLabels.length > 0) {
    parts.push(`等级: ${levelLabels.join('、')}`)
  }
  
  // 排除区域
  if (excludedAreas.value.length > 0) {
    parts.push(`排除区域: ${excludedAreas.value.map(a => a.label).join('、')}`)
  }
  
  // 排除设备
  if (excludedDevices.value.length > 0) {
    parts.push(`排除设备: ${excludedDevices.value.map(d => d.label).join('、')}`)
  }
  
  // 触发时段
  const startTime = `${timeRange.start.getHours().toString().padStart(2, '0')}:${timeRange.start.getMinutes().toString().padStart(2, '0')}`
  const endTime = `${timeRange.end.getHours().toString().padStart(2, '0')}:${timeRange.end.getMinutes().toString().padStart(2, '0')}`
  parts.push(`时段: ${startTime}-${endTime}`)
  
  return parts.join(' | ')
}

// 生成动作描述
function generateActionsDesc(): string {
  const actionDescs = pushActions.value.map(action => {
    const channelNames = action.channels.map(c => c.label).join('、')
    const templateName = templateOptions.value.find(t => t.value === action.template)?.label || action.template
    return `渠道: ${channelNames} | 模版: ${templateName} | 静默: ${action.silenceTime}s`
  })
  return actionDescs.join('; ')
}

const policyId = ref('STRAT-20231024-001')
const policyName = ref('')
const priority = ref('1')
const isEnabled = ref(true)

const priorityOptions = [
  { label: '1 (最高)', value: '1' },
  { label: '2', value: '2' },
  { label: '3', value: '3' },
  { label: '4', value: '4' },
  { label: '5 (最低)', value: '5' }
]

const alarmType = ref('ai')

const aiAlarmTypes = ref<any[]>([])
const loadingAlgorithms = ref(false)

const systemAlarmTypes = [
  { label: '设备离线', value: '设备离线' },
  { label: '存储异常', value: '存储异常' },
  { label: '网络异常', value: '网络异常' },
  { label: '系统错误', value: '系统错误' }
]

const currentAlarmTypeOptions = computed(() => {
  return alarmType.value === 'ai' ? aiAlarmTypes.value : systemAlarmTypes
})

const selectedAlarmTypes = ref<string[]>([])
const showAlarmTypeSelect = ref(false)
const currentAlarmType = ref(null)

// 加载算法列表作为AI告警类型
async function loadAlgorithms() {
  loadingAlgorithms.value = true
  try {
    const response = await getAlgorithmList({ is_enabled: true })
    if (response.data && response.data.data && response.data.data.items) {
      aiAlarmTypes.value = response.data.data.items.map((algo: Algorithm) => ({
        label: `${algo.model_name || '未知模型'}-${algo.name}`,
        value: algo.id
      }))
    } else {
      // 使用默认AI告警类型
      aiAlarmTypes.value = [
        { label: '火灾识别', value: '火灾识别' },
        { label: '烟雾检测', value: '烟雾检测' },
        { label: '人员入侵', value: '人员入侵' },
        { label: '安全帽检测', value: '安全帽检测' },
        { label: '反光衣检测', value: '反光衣检测' }
      ]
    }
  } catch (error: any) {
    console.error('加载算法列表失败:', error)
    message.error('加载算法列表失败')
    // 使用默认AI告警类型
    aiAlarmTypes.value = [
      { label: '火灾识别', value: '火灾识别' },
      { label: '烟雾检测', value: '烟雾检测' },
      { label: '人员入侵', value: '人员入侵' },
      { label: '安全帽检测', value: '安全帽检测' },
      { label: '反光衣检测', value: '反光衣检测' }
    ]
  } finally {
    loadingAlgorithms.value = false
  }
}

const handleAlarmTypeChange = (type: string) => {
  alarmType.value = type
  selectedAlarmTypes.value = []
  showAlarmTypeSelect.value = false
  currentAlarmType.value = null
}

const handleAlarmTypeSelect = (value: string) => {
  if (value && !selectedAlarmTypes.value.includes(value)) {
    selectedAlarmTypes.value.push(value)
  }
  showAlarmTypeSelect.value = false
  currentAlarmType.value = null
}

const handleRemoveAlarmType = (item: string) => {
  selectedAlarmTypes.value = selectedAlarmTypes.value.filter(i => i !== item)
}

// 区域树数据和加载状态
const areaTreeOptions = ref<any[]>([])
const loadingAreas = ref(false)
const selectedAreas = ref<{id: string, label: string}[]>([])
const showAreaSelect = ref(false)
const currentArea = ref(null)

// 将后端区域数据转换为树形结构
function convertToTreeOption(node: AreaTreeNode, parentPath: string = ''): any {
  const path = parentPath ? `${parentPath}/${node.id}` : `/${node.id}`
  const option: any = {
    key: node.id,
    label: node.name,
    value: path,
    fullPath: path,
    name: node.name
  }
  if (node.children && node.children.length > 0) {
    option.children = node.children.map(child => convertToTreeOption(child, path))
  }
  return option
}

// 加载区域树数据
async function loadAreaTree() {
  loadingAreas.value = true
  try {
    const response = await getAreaTree()
    if (response.data.data) {
      areaTreeOptions.value = response.data.data.map((node: AreaTreeNode) => convertToTreeOption(node))
    }
  } catch (error: any) {
    console.error('加载区域树失败:', error)
    message.error('加载区域树失败')
    // 如果 API 失败，使用默认数据
    areaTreeOptions.value = [
      {
        label: '默认园区',
        key: 'default-area',
        value: '/default-area',
        fullPath: '/default-area',
        name: '默认园区',
        children: []
      }
    ]
  } finally {
    loadingAreas.value = false
  }
}

// 递归查找区域信息
function findAreaInfo(path: string, nodes: any[] = areaTreeOptions.value): {id: string, label: string} | null {
  for (const node of nodes) {
    if (node.value === path) return { id: path, label: node.label }
    if (node.children) {
      const found = findAreaInfo(path, node.children)
      if (found) return found
    }
  }
  return null
}

const handleAreaSelect = (value: string) => {
  if (value && !selectedAreas.value.find(a => a.id === value)) {
    const areaInfo = findAreaInfo(value)
    if (areaInfo) {
      selectedAreas.value.push(areaInfo)
    }
  }
  showAreaSelect.value = false
  currentArea.value = null
}

const handleRemoveArea = (item: any) => {
  selectedAreas.value = selectedAreas.value.filter(i => i.id !== item.id)
}

// 设备数据和加载状态
const deviceTreeData = ref<any[]>([])
const allDevices = ref<Camera[]>([])
const loadingDevices = ref(false)
const loadingDeviceTree = ref(false)

const selectedDevices = ref<{id: string, label: string}[]>([])
const showDeviceModal = ref(false)
const selectedDeviceTreeKeys = ref<string[]>([])
const tempSelectedDevices = ref<{id: string, label: string}[]>([])

// 分页相关
const devicePage = ref(1)
const devicePageSize = ref(10)
const deviceTotal = ref(0)

// 加载设备列表
async function loadCameras(areaId?: string, page: number = 1) {
  loadingDevices.value = true
  try {
    const params: CameraQueryParams = {
      page: page,
      page_size: devicePageSize.value
    }
    if (areaId) {
      params.area_id = areaId
    }
    const response = await getCameraList(params)
    if (response.data && response.data.data) {
      allDevices.value = response.data.data.items || []
      deviceTotal.value = response.data.data.total || 0
    } else {
      allDevices.value = []
      deviceTotal.value = 0
    }
  } catch (error: any) {
    console.error('加载设备列表失败:', error)
    message.error('加载设备列表失败')
    allDevices.value = []
    deviceTotal.value = 0
  } finally {
    loadingDevices.value = false
  }
}

const currentDeviceList = computed(() => {
  if (selectedDeviceTreeKeys.value.length === 0) {
    return allDevices.value
  }
  const selectedKey = selectedDeviceTreeKeys.value[0]
  return allDevices.value.filter(device => device.area_id === selectedKey)
})

const handleDeviceTreeSelect = async (keys: string[]) => {
  selectedDeviceTreeKeys.value = keys
  devicePage.value = 1 // 重置分页
  if (keys.length > 0) {
    await loadCameras(keys[0], 1)
  } else {
    await loadCameras(undefined, 1)
  }
}

const handleDeviceCheck = (deviceId: string, checked: boolean) => {
  const device = allDevices.value.find(d => d.id === deviceId)
  if (!device) return
  
  if (checked && !tempSelectedDevices.value.some(d => d.id === deviceId)) {
    tempSelectedDevices.value.push({
      id: deviceId,
      label: device.name
    })
  } else if (!checked) {
    tempSelectedDevices.value = tempSelectedDevices.value.filter(d => d.id !== deviceId)
  }
}

const handleRemoveTempDevice = (device: any) => {
  tempSelectedDevices.value = tempSelectedDevices.value.filter(d => d.id !== device.id)
}

// 设备分页处理
const handleDevicePageChange = async (page: number) => {
  devicePage.value = page
  if (selectedDeviceTreeKeys.value.length > 0) {
    await loadCameras(selectedDeviceTreeKeys.value[0], page)
  } else {
    await loadCameras(undefined, page)
  }
}

const handleDevicePageSizeChange = async (pageSize: number) => {
  devicePageSize.value = pageSize
  devicePage.value = 1
  if (selectedDeviceTreeKeys.value.length > 0) {
    await loadCameras(selectedDeviceTreeKeys.value[0], 1)
  } else {
    await loadCameras(undefined, 1)
  }
}

const handleConfirmDevices = () => {
  const existingIds = selectedDevices.value.map(d => d.id)
  tempSelectedDevices.value.forEach(device => {
    if (!existingIds.includes(device.id)) {
      selectedDevices.value.push(device)
    }
  })
  tempSelectedDevices.value = []
  showDeviceModal.value = false
}

const handleRemoveDevice = (item: any) => {
  selectedDevices.value = selectedDevices.value.filter(i => i.id !== item.id)
}

const alarmLevels = reactive({
  danger: true,
  critical: true,
  warning: false,
  info: false
})

const excludedAreas = ref<{id: string, label: string}[]>([])
const showExcludedAreaSelect = ref(false)
const currentExcludedArea = ref(null)

const handleExcludedAreaSelect = (value: string) => {
  if (value && !excludedAreas.value.find(a => a.id === value)) {
    const areaInfo = findAreaInfo(value)
    if (areaInfo) {
      excludedAreas.value.push(areaInfo)
    }
  }
  showExcludedAreaSelect.value = false
  currentExcludedArea.value = null
}

const handleRemoveExcludedArea = (item: any) => {
  excludedAreas.value = excludedAreas.value.filter(i => i.id !== item.id)
}

const excludedDevices = ref<{id: string, label: string}[]>([])
const showExcludedDeviceModal = ref(false)
const selectedExcludedDeviceTreeKeys = ref<string[]>([])
const tempExcludedDevices = ref<{id: string, label: string}[]>([])

const currentExcludedDeviceList = computed(() => {
  if (selectedExcludedDeviceTreeKeys.value.length === 0) {
    return allDevices.value
  }
  const selectedKey = selectedExcludedDeviceTreeKeys.value[0]
  return allDevices.value.filter(device => device.area_id === selectedKey)
})

const handleExcludedDeviceTreeSelect = async (keys: string[]) => {
  selectedExcludedDeviceTreeKeys.value = keys
  if (keys.length > 0) {
    await loadCameras(keys[0])
  } else {
    await loadCameras()
  }
}

const handleExcludedDeviceCheck = (deviceId: string, checked: boolean) => {
  const device = allDevices.value.find(d => d.id === deviceId)
  if (!device) return
  
  if (checked && !tempExcludedDevices.value.find(d => d.id === deviceId)) {
    tempExcludedDevices.value.push({
      id: deviceId,
      label: device.name
    })
  } else if (!checked) {
    tempExcludedDevices.value = tempExcludedDevices.value.filter(d => d.id !== deviceId)
  }
}

const handleRemoveTempExcludedDevice = (device: any) => {
  tempExcludedDevices.value = tempExcludedDevices.value.filter(d => d.id !== device.id)
}

const handleConfirmExcludedDevices = () => {
  const existingIds = excludedDevices.value.map(d => d.id)
  tempExcludedDevices.value.forEach(device => {
    if (!existingIds.includes(device.id)) {
      excludedDevices.value.push(device)
    }
  })
  tempExcludedDevices.value = []
  showExcludedDeviceModal.value = false
}

const handleRemoveExcludedDevice = (item: any) => {
  excludedDevices.value = excludedDevices.value.filter(i => i.id !== item.id)
}

// 推送动作数组
const pushActions = ref<any[]>([
  {
    id: 1,
    channels: [] as any[],
    template: 'template1',
    silenceTime: 300,
    sendOrder: 1,
    deduplicationKeys: [] as string[],
    showChannelSelect: false,
    currentChannel: null
  }
])

// 通道和模板数据
const channelOptions = ref<any[]>([])
const templateOptions = ref<any[]>([])
const loadingChannels = ref(false)
const loadingTemplates = ref(false)

// 加载通道列表
async function loadChannels() {
  loadingChannels.value = true
  try {
    const response = await getNotificationEndpoints()
    if (response.data && response.data.data) {
      channelOptions.value = response.data.data.map((item: NotificationEndpoint) => ({
        id: item.id,
        label: item.name,
        value: item.id,
        provider: item.provider,
        type: item.provider === 'dingtalk_bot' || item.provider === 'wechat' ? 'primary' : 'success',
        icon: item.provider === 'dingtalk_bot' || item.provider === 'wechat' ? ChatbubbleOutline : MailOutline
      }))
    }
  } catch (error: any) {
    console.error('加载通道列表失败:', error)
    message.error('加载通道列表失败')
    channelOptions.value = []
  } finally {
    loadingChannels.value = false
  }
}

// 加载模板列表
async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const response = await getNotificationTemplates()
    if (response.data && response.data.data) {
      templateOptions.value = response.data.data.map((item: NotificationTemplate) => ({
        label: item.name,
        value: item.id
      }))
      // 设置默认模板
      if (templateOptions.value.length > 0 && pushActions.value.length > 0) {
        pushActions.value.forEach(action => {
          if (!action.template) {
            action.template = templateOptions.value[0].value
          }
        })
      }
    }
  } catch (error: any) {
    console.error('加载模板列表失败:', error)
    message.error('加载模板列表失败')
    templateOptions.value = []
  } finally {
    loadingTemplates.value = false
  }
}

// 添加推送动作
const addPushAction = () => {
  pushActions.value.push({
    id: pushActions.value.length + 1,
    channels: [] as any[],
    template: templateOptions.value[0]?.value || '',
    silenceTime: 300,
    sendOrder: pushActions.value.length + 1,
    deduplicationKeys: [] as string[],
    showChannelSelect: false,
    currentChannel: null
  })
}

// 删除推送动作
const removePushAction = (id: number) => {
  if (pushActions.value.length > 1) {
    pushActions.value = pushActions.value.filter(action => action.id !== id)
    // 更新发送顺序
    pushActions.value.forEach((action, index) => {
      action.sendOrder = index + 1
    })
  } else {
    message.warning('至少需要保留一个推送动作')
  }
}

// 处理渠道选择
const handleChannelSelect = (actionId: number, value: string) => {
  const action = pushActions.value.find(a => a.id === actionId)
  if (action) {
    const channel = channelOptions.value.find(c => c.value === value)
    if (channel && !action.channels.find((c: any) => c.value === value)) {
      action.channels.push(channel)
    }
    action.showChannelSelect = false
    action.currentChannel = null
  }
}

// 处理渠道移除
const handleRemoveChannel = (actionId: number, item: any) => {
  const action = pushActions.value.find(a => a.id === actionId)
  if (action) {
    action.channels = action.channels.filter(c => c.value !== item.value)
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadAreaTree()
  deviceTreeData.value = areaTreeOptions.value
  await loadCameras(undefined, 1)
  await loadChannels()
  await loadTemplates()
  await loadAlgorithms()
})

const timeRange = reactive({
  start: new Date(),
  end: new Date()
})

const initTime = () => {
  const startDate = new Date()
  startDate.setHours(0, 0, 0, 0)
  
  const endDate = new Date()
  endDate.setHours(23, 59, 59, 999)
  
  timeRange.start = startDate
  timeRange.end = endDate
}

initTime()

const deduplicationKeyOptions = [
  { label: '摄像头 (camera_id)', value: 'camera_id' },
  { label: '区域 (area_id)', value: 'area_id' },
  { label: '算法 (algorithm_id)', value: 'algorithm_id' },
  { label: '告警类型 (alarm_type)', value: 'alarm_type' }
]
</script>

<style scoped>
.add-policy-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 0 var(--spacing-lg);
  height: 64px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
}

.page-header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.header-btn {
  min-width: 100px;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding-top: var(--spacing-lg);
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) var(--bg-page);
}

.page-content::-webkit-scrollbar {
  width: 6px;
}

.page-content::-webkit-scrollbar-track {
  background: var(--bg-page);
}

.page-content::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 3px;
}

.page-content::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-muted);
}

.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-cols-12 {
  grid-template-columns: repeat(12, minmax(0, 1fr));
}

.col-span-12 {
  grid-column: span 12 / span 12;
}

.col-span-6 {
  grid-column: span 6 / span 6;
}

.md\:col-span-2 {
  grid-column: span 2 / span 2;
}

.md\:col-span-3 {
  grid-column: span 3 / span 3;
}

.md\:col-span-5 {
  grid-column: span 5 / span 5;
}

.md\:col-span-7 {
  grid-column: span 7 / span 7;
}

.md\:grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.space-y-lg > * + * {
  margin-top: var(--spacing-lg);
}

.space-y-md > * + * {
  margin-top: var(--spacing-md);
}

.space-y-sm > * + * {
  margin-top: var(--spacing-sm);
}

.gap-xl {
  gap: var(--spacing-xl);
}

.gap-lg {
  gap: var(--spacing-lg);
}

.gap-md {
  gap: var(--spacing-md);
}

.gap-sm {
  gap: var(--spacing-sm);
}

.mt-xs {
  margin-top: var(--spacing-xs);
}

.mt-sm {
  margin-top: var(--spacing-sm);
}

.mt-lg {
  margin-top: var(--spacing-lg);
}

.mb-lg {
  margin-bottom: var(--spacing-lg);
}

.pb-xl {
  padding-bottom: var(--spacing-xl);
}

.p-xl {
  padding: var(--spacing-xl);
}

.p-lg {
  padding: var(--spacing-lg);
}

.p-md {
  padding: var(--spacing-md);
}

.p-sm {
  padding: var(--spacing-sm);
}

.px-sm {
  padding-left: var(--spacing-sm);
  padding-right: var(--spacing-sm);
}

.py-xs {
  padding-top: var(--spacing-xs);
  padding-bottom: var(--spacing-xs);
}

.min-h-\[42px\] {
  min-height: 42px;
}

.min-h-\[46px\] {
  min-height: 46px;
}

.ml-auto {
  margin-left: auto;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.top-lg {
  top: var(--spacing-lg);
}

.right-lg {
  right: var(--spacing-lg);
}

.border-l-4 {
  border-left-width: 4px;
}

.border-l-primary {
  border-left-color: var(--primary-color);
}

.text-xs {
  font-size: var(--font-size-xs);
}

.text-sm {
  font-size: var(--font-size-sm);
}

.text-lg {
  font-size: var(--font-size-lg);
}

.font-semibold {
  font-weight: var(--font-weight-semibold);
}

.font-mono {
  font-family: var(--font-mono);
}

.italic {
  font-style: italic;
}

.uppercase {
  text-transform: uppercase;
}

.device-selector {
  display: flex;
  gap: var(--spacing-md);
  height: 500px;
}

.device-selector-left {
  width: 200px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  overflow-y: auto;
  background: var(--bg-card);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.device-selector-center {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.device-selector-right {
  width: 200px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  overflow-y: auto;
  background: var(--bg-card);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.device-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.device-selector-title {
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.device-count {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.device-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.device-list-item {
  width: 100%;
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  transition: all var(--transition-normal);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
}

.device-list-item:hover {
  background: var(--bg-hover);
  border-color: var(--primary-color);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.device-meta {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}

.device-list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-muted);
  background: var(--bg-page);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
}

.device-pagination {
  border-top: 1px solid var(--border-color);
  padding-top: var(--spacing-md);
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.selected-device-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  max-height: 400px;
  overflow-y: auto;
}

.selected-device-empty {
  text-align: center;
  padding: var(--spacing-md) 0;
  color: var(--text-muted);
  background: var(--bg-page);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
  margin-top: var(--spacing-sm);
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.device-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.device-meta {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.device-list-empty {
  padding: var(--spacing-xl);
  display: flex;
  justify-content: center;
  align-items: center;
}

.selected-device-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.selected-device-empty {
  padding: var(--spacing-lg);
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
}

@media (max-width: 768px) {
  .page-header {
    padding: 0 var(--spacing-md);
    flex-direction: column;
    height: auto;
    padding: var(--spacing-md);
    gap: var(--spacing-md);
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .page-content {
    padding: var(--spacing-md);
  }
  
  .grid-cols-12 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .col-span-6,
  .md\:col-span-2,
  .md\:col-span-3,
  .md\:col-span-5,
  .md\:col-span-7 {
    grid-column: span 12 / span 12;
  }
  
  .md\:grid-cols-2 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .device-selector {
    flex-direction: column;
    height: auto;
  }
  
  .device-selector-left,
  .device-selector-center,
  .device-selector-right {
    width: 100%;
    max-height: 200px;
  }
}
</style>
