<template>
  <div class="push-management">
    <!-- Page Header -->
    <div class="page-header">
      <h1 class="page-header__title">推送渠道管理</h1>
      <p class="page-header__subtitle">配置多维度的告警触达方式，确保信息及时传递</p>
    </div>

    <!-- Channel Cards -->
    <div class="channel-section">
      <div class="channel-cards">
        <!-- 钉钉推送 -->
        <div class="channel-card card-border-xl">
          <div class="channel-card__icon channel-card__icon--dingtalk">
            <n-icon :size="32"><ChatboxEllipsesOutline /></n-icon>
          </div>
          <h3 class="channel-card__title">钉钉推送</h3>
          <p class="channel-card__desc">
            通过钉钉机器人 Webhook 实现告警消息实时推送到指定的钉钉群组。
          </p>
          <div class="channel-card__status">
            <span class="status-dot status-dot--enabled"></span>
            <span class="status-text status-text--enabled">已开启</span>
          </div>
          <n-button block @click="showChannelConfig('dingtalk')">渠道配置</n-button>
        </div>

        <!-- 企业微信 -->
        <div class="channel-card card-border-xl">
          <div class="channel-card__icon channel-card__icon--wechat">
            <n-icon :size="32"><PeopleOutline /></n-icon>
          </div>
          <h3 class="channel-card__title">企业微信</h3>
          <p class="channel-card__desc">
            集成企业微信 API，支持卡片式、图文式告警展示，消息点击直达回放。
          </p>
          <div class="channel-card__status">
            <span class="status-dot status-dot--disabled"></span>
            <span class="status-text status-text--disabled">已禁用</span>
          </div>
          <n-button block type="primary" @click="enableChannel('wechat')">立即开启</n-button>
        </div>

        <!-- 邮件推送 -->
        <div class="channel-card card-border-xl">
          <div class="channel-card__icon channel-card__icon--email">
            <n-icon :size="32"><MailOutline /></n-icon>
          </div>
          <h3 class="channel-card__title">邮件推送</h3>
          <p class="channel-card__desc">
            支持 SMTP 协议，可配置多个收件人，支持 HTML 富文本格式告警邮件。
          </p>
          <div class="channel-card__status">
            <span class="status-dot status-dot--disabled"></span>
            <span class="status-text status-text--disabled">已禁用</span>
          </div>
          <n-button block type="primary" @click="enableChannel('email')">立即开启</n-button>
        </div>

        <!-- 短信推送 -->
        <div class="channel-card card-border-xl">
          <div class="channel-card__icon channel-card__icon--sms">
            <n-icon :size="32"><PhonePortraitOutline /></n-icon>
          </div>
          <h3 class="channel-card__title">短信推送</h3>
          <p class="channel-card__desc">
            对接阿里云、腾讯云短信服务，支持紧急告警短信通知，确保重要信息触达。
          </p>
          <div class="channel-card__status">
            <span class="status-dot status-dot--disabled"></span>
            <span class="status-text status-text--disabled">已禁用</span>
          </div>
          <n-button block type="primary" @click="enableChannel('sms')">立即开启</n-button>
        </div>
      </div>
    </div>

    <!-- Message Template Section -->
    <div class="template-section card-border-xl">
      <div class="template-header">
        <h2 class="template-header__title">消息模板管理</h2>
        <n-button type="primary" size="small" @click="showTemplateModal = true">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建模板
        </n-button>
      </div>

      <div class="template-list card-border-xl">
        <div 
          v-for="template in templates" 
          :key="template.id" 
          class="template-item card-border-xl"
        >
          <div class="template-item__icon">
            <n-icon :size="20" color="var(--primary-color)"><DocumentTextOutline /></n-icon>
          </div>
          <div class="template-item__info">
            <h4 class="template-item__name">{{ template.name }}</h4>
            <span class="template-item__type">{{ template.type }}</span>
          </div>
          <div class="template-item__meta">
            <span class="template-item__time">上次使用: {{ template.lastUsed }}</span>
            <div class="template-item__actions">
              <n-button text type="primary" size="small" @click="editTemplate(template)">编辑</n-button>
              <n-button text type="error" size="small" @click="deleteTemplate(template)">删除</n-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Channel Config Modal -->
    <n-modal 
      v-model:show="showConfigModal" 
      preset="card" 
      :title="configModalTitle"
      :style="{ width: '560px' }"
      :bordered="false"
    >
      <n-form :model="channelForm" label-placement="left" label-width="100">
        <n-form-item label="Webhook URL" v-if="currentChannel === 'dingtalk'">
          <n-input v-model:value="channelForm.webhook" placeholder="请输入钉钉机器人 Webhook 地址" />
        </n-form-item>
        <n-form-item label="加签密钥" v-if="currentChannel === 'dingtalk'">
          <n-input v-model:value="channelForm.secret" placeholder="请输入加签密钥（可选）" />
        </n-form-item>
        <n-form-item label="Corp ID" v-if="currentChannel === 'wechat'">
          <n-input v-model:value="channelForm.corpId" placeholder="请输入企业微信 Corp ID" />
        </n-form-item>
        <n-form-item label="Agent ID" v-if="currentChannel === 'wechat'">
          <n-input v-model:value="channelForm.agentId" placeholder="请输入应用 Agent ID" />
        </n-form-item>
        <n-form-item label="Secret" v-if="currentChannel === 'wechat'">
          <n-input v-model:value="channelForm.secret" type="password" placeholder="请输入应用 Secret" />
        </n-form-item>
        <n-form-item label="SMTP 服务器" v-if="currentChannel === 'email'">
          <n-input v-model:value="channelForm.smtpHost" placeholder="例如: smtp.qq.com" />
        </n-form-item>
        <n-form-item label="端口" v-if="currentChannel === 'email'">
          <n-input-number v-model:value="channelForm.smtpPort" placeholder="465" :min="1" :max="65535" />
        </n-form-item>
        <n-form-item label="发件邮箱" v-if="currentChannel === 'email'">
          <n-input v-model:value="channelForm.email" placeholder="请输入发件人邮箱" />
        </n-form-item>
        <n-form-item label="授权码" v-if="currentChannel === 'email'">
          <n-input v-model:value="channelForm.password" type="password" placeholder="请输入邮箱授权码" />
        </n-form-item>
        <n-form-item label="启用状态">
          <n-switch v-model:value="channelForm.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="testChannel">测试连接</n-button>
          <n-button @click="showConfigModal = false">取消</n-button>
          <n-button type="primary" @click="saveChannelConfig">保存配置</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Template Modal -->
    <n-modal 
      v-model:show="showTemplateModal" 
      preset="card" 
      :title="editingTemplate ? '编辑模板' : '新建模板'"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-form :model="templateForm" label-placement="left" label-width="100">
        <n-form-item label="模板名称">
          <n-input v-model:value="templateForm.name" placeholder="请输入模板名称" />
        </n-form-item>
        <n-form-item label="消息类型">
          <n-select 
            v-model:value="templateForm.type" 
            :options="messageTypes"
            placeholder="请选择消息类型"
          />
        </n-form-item>
        <n-form-item label="适用渠道">
          <n-checkbox-group v-model:value="templateForm.channels">
            <n-space>
              <n-checkbox value="dingtalk">钉钉</n-checkbox>
              <n-checkbox value="wechat">企业微信</n-checkbox>
              <n-checkbox value="email">邮件</n-checkbox>
              <n-checkbox value="sms">短信</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="模板内容">
          <n-input 
            v-model:value="templateForm.content" 
            type="textarea" 
            placeholder="支持变量: ${alarmType}, ${deviceName}, ${alarmTime}, ${alarmLevel}"
            :rows="5"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showTemplateModal = false">取消</n-button>
          <n-button type="primary" @click="saveTemplate">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  NButton, NIcon, NModal, NForm, NFormItem, NInput, NInputNumber,
  NSwitch, NSelect, NCheckbox, NCheckboxGroup, NSpace, useMessage 
} from 'naive-ui'
import { 
  ChatboxEllipsesOutline,
  PeopleOutline,
  MailOutline,
  PhonePortraitOutline,
  AddOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'

interface Template {
  id: string
  name: string
  type: string
  lastUsed: string
  content?: string
  channels?: string[]
}

const message = useMessage()

// Channel config
const showConfigModal = ref(false)
const currentChannel = ref('')
const channelForm = ref({
  webhook: '',
  secret: '',
  corpId: '',
  agentId: '',
  smtpHost: '',
  smtpPort: 465,
  email: '',
  password: '',
  enabled: true
})

const configModalTitle = computed(() => {
  const titles: Record<string, string> = {
    dingtalk: '钉钉推送配置',
    wechat: '企业微信配置',
    email: '邮件推送配置',
    sms: '短信推送配置'
  }
  return titles[currentChannel.value] || '渠道配置'
})

// Template data
const showTemplateModal = ref(false)
const editingTemplate = ref<Template | null>(null)
const templateForm = ref({
  name: '',
  type: null as string | null,
  channels: [] as string[],
  content: ''
})

const templates = ref<Template[]>([
  {
    id: '1',
    name: '安全告警通用模板',
    type: '卡片消息',
    lastUsed: '10分钟前'
  },
  {
    id: '2',
    name: '设备离线预警模板',
    type: '文本消息',
    lastUsed: '1小时前'
  },
  {
    id: '3',
    name: '入侵检测告警模板',
    type: '图文消息',
    lastUsed: '3小时前'
  }
])

const messageTypes = [
  { label: '文本消息', value: 'text' },
  { label: '卡片消息', value: 'card' },
  { label: '图文消息', value: 'news' },
  { label: 'Markdown', value: 'markdown' }
]

function showChannelConfig(channel: string) {
  currentChannel.value = channel
  showConfigModal.value = true
}

function enableChannel(channel: string) {
  currentChannel.value = channel
  showConfigModal.value = true
}

function testChannel() {
  message.loading('正在测试连接...')
  setTimeout(() => {
    message.success('连接测试成功')
  }, 1500)
}

function saveChannelConfig() {
  message.success('配置保存成功')
  showConfigModal.value = false
}

function editTemplate(template: Template) {
  editingTemplate.value = template
  templateForm.value = {
    name: template.name,
    type: template.type === '卡片消息' ? 'card' : template.type === '文本消息' ? 'text' : 'news',
    channels: template.channels || ['dingtalk'],
    content: template.content || ''
  }
  showTemplateModal.value = true
}

function deleteTemplate(template: Template) {
  const index = templates.value.findIndex(t => t.id === template.id)
  if (index > -1) {
    templates.value.splice(index, 1)
    message.success('模板已删除')
  }
}

function saveTemplate() {
  if (editingTemplate.value) {
    const index = templates.value.findIndex(t => t.id === editingTemplate.value!.id)
    if (index > -1) {
      templates.value[index] = {
        ...templates.value[index],
        name: templateForm.value.name,
        type: messageTypes.find(t => t.value === templateForm.value.type)?.label || '文本消息'
      }
    }
    message.success('模板更新成功')
  } else {
    templates.value.push({
      id: Date.now().toString(),
      name: templateForm.value.name,
      type: messageTypes.find(t => t.value === templateForm.value.type)?.label || '文本消息',
      lastUsed: '刚刚'
    })
    message.success('模板创建成功')
  }
  showTemplateModal.value = false
  editingTemplate.value = null
  templateForm.value = { name: '', type: null, channels: [], content: '' }
}
</script>

<style scoped>
.push-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  overflow-y: auto;
}

/* Page Header */
.page-header {
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

/* Channel Section */
.channel-section {
  flex-shrink: 0;
}

.channel-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.channel-card {
  background: var(--bg-card);
  padding: var(--spacing-xl);
  text-align: center;
  transition: all 0.3s ease;
}

.channel-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.1);
}

.channel-card__icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-md);
}

.channel-card__icon--dingtalk {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  color: #fff;
}

.channel-card__icon--wechat {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  color: #fff;
}

.channel-card__icon--email {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  color: #fff;
}

.channel-card__icon--sms {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: #fff;
}

.channel-card__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm);
}

.channel-card__desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0 0 var(--spacing-md);
  min-height: 48px;
}

.channel-card__status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--enabled {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}

.status-dot--disabled {
  background: #9ca3af;
}

.status-text {
  font-size: var(--font-size-sm);
}

.status-text--enabled {
  color: #22c55e;
}

.status-text--disabled {
  color: var(--text-muted);
}

/* Template Section */
.template-section {
  background: var(--bg-card);
  padding: var(--spacing-xl);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.template-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  flex-shrink: 0;
}

.template-header__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.template-header__title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: var(--primary-color);
  border-radius: 2px;
}

.template-list {
  flex: 1;
  overflow-y: auto;
}

.template-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-lg);
  transition: background 0.2s;
}

.template-item:hover {
  background: var(--bg-hover);
}

.template-item__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(67, 24, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.template-item__info {
  flex: 1;
  min-width: 0;
}

.template-item__name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin: 0 0 2px;
}

.template-item__type {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.template-item__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-xs);
}

.template-item__time {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.template-item__actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* Modal Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* Scrollbar */
.push-management::-webkit-scrollbar,
.template-list::-webkit-scrollbar {
  width: 6px;
}

.push-management::-webkit-scrollbar-track,
.template-list::-webkit-scrollbar-track {
  background: transparent;
}

.push-management::-webkit-scrollbar-thumb,
.template-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.push-management::-webkit-scrollbar-thumb:hover,
.template-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Responsive */
@media (max-width: 900px) {
  .channel-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .channel-cards {
    grid-template-columns: 1fr;
  }
}
</style>
