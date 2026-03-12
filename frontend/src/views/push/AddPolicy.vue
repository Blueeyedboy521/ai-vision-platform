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
                  <n-button :type="alarmType === 'ai' ? 'primary' : 'default'" size="medium" @click="alarmType = 'ai'">AI告警</n-button>
                  <n-button :type="alarmType === 'system' ? 'primary' : 'default'" size="medium" @click="alarmType = 'system'">系统告警</n-button>
                </div>
              </n-form-item>
            </div>
            <div>
              <n-form-item label="报警类型 (多选)">
                <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                  <n-tag closable on-close="() => {}">火灾识别</n-tag>
                  <n-tag closable on-close="() => {}">烟雾检测</n-tag>
                  <n-button type="primary" dashed size="small">
                    <template #icon><n-icon><Add /></n-icon></template>
                    添加
                  </n-button>
                </div>
              </n-form-item>
            </div>
            <div>
              <n-form-item label="区域路径 (支持通配符)">
                <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                  <n-tag closable on-close="() => {}">/一分厂/冲压/A1*</n-tag>
                  <n-button type="primary" dashed size="small">
                    <template #icon><n-icon><Add /></n-icon></template>
                    添加
                  </n-button>
                </div>
              </n-form-item>
            </div>
            <div>
              <n-form-item label="监控设备 (多选)">
                <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[46px] items-center">
                  <n-tag closable on-close="() => {}">CAM-SOUTH-001</n-tag>
                  <n-tag closable on-close="() => {}">CAM-WEST-042</n-tag>
                  <n-button type="primary" dashed size="small">
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
                <div class="flex gap-lg p-sm">
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
                </div>
              </n-form-item>
            </div>
            <div class="space-y-md">
              <div>
                <n-form-item label="排除区域">
                  <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[42px] items-center">
                    <n-tag closable on-close="() => {}" type="default">/DEBUG/*</n-tag>
                    <n-button type="default" dashed size="small">
                      <template #icon><n-icon><Add /></n-icon></template>
                      排除路径
                    </n-button>
                  </div>
                </n-form-item>
              </div>
              <div>
                <n-form-item label="排除设备">
                  <div class="p-md border border-light rounded-lg bg-page flex flex-wrap gap-sm min-h-[42px] items-center">
                    <n-tag closable on-close="() => {}" type="default">#CAM-TEST-02</n-tag>
                    <n-button type="default" dashed size="small">
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
          <n-button text type="primary" size="small" class="border border-primary\/20 rounded-lg flex items-center gap-sm">
            <template #icon><n-icon><Add /></n-icon></template>
            添加推送配置
          </n-button>
        </div>
        <div class="space-y-lg">
          <!-- 动作块 1 -->
          <div class="relative p-xl border border-light bg-page rounded-xl border-l-4 border-l-primary">
            <n-button text class="absolute top-lg right-lg text-muted hover:text-error">
              <template #icon><n-icon><TrashOutline /></n-icon></template>
            </n-button>
            <div class="grid grid-cols-12 gap-xl">
              <div class="col-span-12 md:col-span-5 space-y-lg">
                <div>
                  <n-form-item label="推送渠道 (多选)">
                    <div class="p-md border border-light rounded-lg bg-card flex flex-wrap gap-sm min-h-[46px] items-center">
                      <n-tag closable on-close="() => {}" type="primary">
                        <template #icon><n-icon size="14"><ChatbubbleOutline /></n-icon></template>
                        钉钉机器人
                      </n-tag>
                      <n-tag closable on-close="() => {}" type="success">
                        <template #icon><n-icon size="14"><MailOutline /></n-icon></template>
                        邮件网关
                      </n-tag>
                      <n-button type="primary" dashed size="small">
                        <template #icon><n-icon><Add /></n-icon></template>
                        添加渠道
                      </n-button>
                    </div>
                  </n-form-item>
                </div>
                <div>
                  <n-form-item label="消息模版">
                    <n-select v-model:value="template" :options="templateOptions" />
                  </n-form-item>
                </div>
              </div>
              <div class="col-span-12 md:col-span-7">
                <div class="grid grid-cols-2 gap-lg">
                  <div>
                    <n-form-item label="静默时间 (秒)">
                      <n-input-number v-model:value="silenceTime" :min="0" />
                      <p class="text-xs text-muted mt-xs">相同报警在此时间内不重复发送</p>
                    </n-form-item>
                  </div>
                  <div>
                    <n-form-item label="去重关键字 (多选下拉)">
                      <div class="p-md border border-light rounded-lg bg-card flex flex-wrap gap-sm min-h-[40px] items-center">
                        <n-tag closable on-close="() => {}" type="default" class="font-mono">camera_id</n-tag>
                        <n-tag closable on-close="() => {}" type="default" class="font-mono">event_type</n-tag>
                        <n-button text class="ml-auto text-muted">
                          <template #icon><n-icon><ChevronDown /></n-icon></template>
                        </n-button>
                      </div>
                      <p class="text-xs text-muted mt-xs">用于唯一标识一条报警</p>
                    </n-form-item>
                  </div>
                  <div>
                    <n-form-item label="发送顺序">
                      <n-input-number v-model:value="sendOrder" :min="1" />
                      <p class="text-xs text-muted mt-xs">数字越小优先级越高</p>
                    </n-form-item>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 添加新动作触发器 -->
          <n-button type="default" dashed class="w-full py-8 rounded-xl flex flex-col items-center justify-center gap-md text-muted hover:text-primary hover:border-primary hover:bg-primary-light transition-all">
            <n-icon size="32"><AddCircle /></n-icon>
            <span class="text-sm font-semibold">配置备用推送目标</span>
            <span class="text-xs">用于配置多级告警链路或备用通知方式</span>
          </n-button>
        </div>
      </section>
    </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NInput, NSelect, NSwitch, NCheckbox, NFormItem, NTimePicker, NInputNumber, NIcon, NTag, useMessage } from 'naive-ui'
import { Close, Add, TimeOutline, ChatbubbleOutline, MailOutline, TrashOutline, ChevronDown, AddCircle } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

// 取消
const handleCancel = () => {
  router.push('/push/policy-management')
}

// 保存并启用
const handleSaveAndEnable = () => {
  message.success('策略保存成功并已启用')
  router.push('/push/policy-management')
}

// 基础信息
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

// 触发规则
const alarmType = ref('ai')
const alarmLevels = reactive({
  danger: true,
  critical: true,
  warning: false
})
const timeRange = reactive({
  start: new Date(),
  end: new Date()
})

// 初始化时间为00:00和23:59
const initTime = () => {
  const startDate = new Date()
  startDate.setHours(0, 0, 0, 0)
  
  const endDate = new Date()
  endDate.setHours(23, 59, 59, 999)
  
  timeRange.start = startDate
  timeRange.end = endDate
}

// 初始化时间
initTime()

// 推送动作
const template = ref('template1')
const templateOptions = [
  { label: '【紧急】工业园区火灾告警模版 v2', value: 'template1' },
  { label: '【常规】设备运行异常预警', value: 'template2' },
  { label: '自定义模版...', value: 'template3' }
]
const silenceTime = ref(300)
const sendOrder = ref(1)
</script>

<style scoped>
/* 页面布局 */
.add-policy-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  overflow: hidden;
}

/* 页面标题 */
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

/* 页面内容 */
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

/* 页面特定样式 */
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

/* 响应式 */
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
}
</style>