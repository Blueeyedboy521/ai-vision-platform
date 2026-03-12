<template>
  <div class="push-management">
    <!-- Page Header -->
    <div class="page-header">
      <h1 class="page-header__title">通道配置</h1>
      <p class="page-header__subtitle">配置多维度的告警触达方式，确保信息及时传递</p>
      <div class="page-header__actions">
        <n-button type="primary" @click="showAddModal = true">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新增通道
        </n-button>
      </div>
    </div>

    <!-- Channel Cards -->
    <div class="channel-section">
      <div class="channel-cards">
        <div 
          v-for="channel in channels" 
          :key="channel.id" 
          class="channel-card card-border-xl"
        >
          <div class="channel-card__icon" :class="`channel-card__icon--${channel.type}`">
            <n-icon :size="32"><ChatboxEllipsesOutline v-if="channel.type === 'dingtalk'" /><PeopleOutline v-else /></n-icon>
          </div>
          <h3 class="channel-card__title">{{ channel.name }}</h3>
          <p class="channel-card__desc">
            {{ channel.type === 'dingtalk' ? '钉钉机器人' : '企业微信机器人' }} 通道
          </p>
          <div class="channel-card__status">
            <span class="status-dot" :class="channel.isEnabled ? 'status-dot--enabled' : 'status-dot--disabled'"></span>
            <span class="status-text" :class="channel.isEnabled ? 'status-text--enabled' : 'status-text--disabled'">
              {{ channel.isEnabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          <div class="channel-card__meta">
            <span class="channel-card__webhook">{{ maskWebhook(channel.webhook) }}</span>
          </div>
          <div class="channel-card__actions">
            <n-switch 
              v-model:value="channel.isEnabled" 
              @update:value="updateChannelStatus(channel)"
              style="margin-right: 12px"
            />
            <n-button text type="primary" size="small" @click="editChannel(channel)">编辑</n-button>
            <n-button text type="error" size="small" @click="deleteChannel(channel)">删除</n-button>
          </div>
        </div>
        <div v-if="channels.length === 0" class="empty-state">
          <n-empty description="暂无通道数据" />
        </div>
      </div>
    </div>

    <!-- Add/Edit Channel Modal -->
    <n-modal 
      v-model:show="showAddModal" 
      preset="card" 
      :title="editingChannel ? '编辑通道' : '新增通道'"
      :style="{ width: '560px' }"
      :bordered="false"
    >
      <n-form :model="channelForm" label-placement="left" label-width="100">
        <n-form-item label="通道名称" required>
          <n-input v-model:value="channelForm.name" placeholder="请输入通道名称" />
        </n-form-item>
        <n-form-item label="通道类型" required>
          <n-select 
            v-model:value="channelForm.type" 
            :options="channelTypes"
            placeholder="请选择通道类型"
          />
        </n-form-item>
        <n-form-item label="Webhook URL" required>
          <n-input v-model:value="channelForm.webhook" placeholder="请输入机器人 Webhook 地址" />
        </n-form-item>
        <n-form-item label="加签密钥">
          <n-input v-model:value="channelForm.secret" placeholder="请输入加签密钥（可选）" />
        </n-form-item>
        <n-form-item label="启用状态">
          <n-switch v-model:value="channelForm.isEnabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="testChannel">测试连接</n-button>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="saveChannel">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  NButton, NIcon, NModal, NForm, NFormItem, NInput, NSwitch, NSelect, 
  NEmpty, useMessage 
} from 'naive-ui'
import { 
  AddOutline, ChatboxEllipsesOutline, PeopleOutline
} from '@vicons/ionicons5'

interface Channel {
  id: string
  name: string
  type: 'dingtalk' | 'wechat'
  webhook: string
  secret?: string
  isEnabled: boolean
}

const message = useMessage()

// Channel data
const channels = ref<Channel[]>([
  {
    id: '1',
    name: '监控告警群',
    type: 'dingtalk',
    webhook: 'https://oapi.dingtalk.com/robot/send?access_token=1234567890abcdef1234567890abcdef',
    secret: 'SEC1234567890abcdef1234567890abcdef',
    isEnabled: true
  },
  {
    id: '2',
    name: '安保通知群',
    type: 'wechat',
    webhook: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1234567890abcdef1234567890abcdef',
    isEnabled: false
  }
])

// Form data
const showAddModal = ref(false)
const editingChannel = ref<Channel | null>(null)
const channelForm = ref({
  name: '',
  type: 'dingtalk' as 'dingtalk' | 'wechat',
  webhook: '',
  secret: '',
  isEnabled: true
})

// Channel types
const channelTypes = [
  { label: '钉钉机器人', value: 'dingtalk' },
  { label: '企业微信机器人', value: 'wechat' }
]

// Methods
function editChannel(channel: Channel) {
  editingChannel.value = channel
  channelForm.value = {
    name: channel.name,
    type: channel.type,
    webhook: channel.webhook,
    secret: channel.secret || '',
    isEnabled: channel.isEnabled
  }
  showAddModal.value = true
}

function deleteChannel(channel: Channel) {
  const index = channels.value.findIndex(c => c.id === channel.id)
  if (index > -1) {
    channels.value.splice(index, 1)
    message.success('通道已删除')
  }
}

function saveChannel() {
  if (!channelForm.value.name || !channelForm.value.webhook) {
    message.error('请填写完整的通道信息')
    return
  }
  
  if (editingChannel.value) {
    const index = channels.value.findIndex(c => c.id === editingChannel.value!.id)
    if (index > -1) {
      channels.value[index] = {
        ...channels.value[index],
        name: channelForm.value.name,
        type: channelForm.value.type,
        webhook: channelForm.value.webhook,
        secret: channelForm.value.secret,
        isEnabled: channelForm.value.isEnabled
      }
    }
    message.success('通道更新成功')
  } else {
    channels.value.push({
      id: Date.now().toString(),
      name: channelForm.value.name,
      type: channelForm.value.type,
      webhook: channelForm.value.webhook,
      secret: channelForm.value.secret,
      isEnabled: channelForm.value.isEnabled
    })
    message.success('通道创建成功')
  }
  
  showAddModal.value = false
  editingChannel.value = null
  channelForm.value = {
    name: '',
    type: 'dingtalk',
    webhook: '',
    secret: '',
    isEnabled: true
  }
}

function updateChannelStatus(channel: Channel) {
  message.success(channel.isEnabled ? '通道已启用' : '通道已禁用')
}

function testChannel() {
  message.success('测试消息已发送，请检查对应通道')
}

function maskWebhook(webhook: string): string {
  // 只显示域名和部分路径，隐藏敏感信息
  const match = webhook.match(/^(https?:\/\/[^/]+\/[^?]+)\?.*$/)
  if (match) {
    return match[1] + '?***'
  }
  return webhook
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
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
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
  margin: 0;
}

.page-header__actions {
  margin-top: var(--spacing-sm);
}

/* Channel Section */
.channel-section {
  flex: 1;
  min-height: 0;
}

.channel-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.channel-card {
  background: var(--bg-card);
  padding: var(--spacing-xl);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: all 0.3s ease;
}

.channel-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.1);
}

.channel-card__icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.channel-card__icon--dingtalk {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
}

.channel-card__icon--wechat {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
}

.channel-card__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.channel-card__desc {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
  flex: 1;
}

.channel-card__status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
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
  font-weight: var(--font-weight-medium);
}

.status-text--enabled {
  color: #22c55e;
}

.status-text--disabled {
  color: var(--text-muted);
}

.channel-card__meta {
  margin-bottom: var(--spacing-sm);
}

.channel-card__webhook {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  word-break: break-all;
}

.channel-card__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  padding: var(--spacing-3xl) var(--spacing-xl);
  text-align: center;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* Scrollbar */
.push-management::-webkit-scrollbar {
  width: 6px;
}

.push-management::-webkit-scrollbar-track {
  background: transparent;
}

.push-management::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.push-management::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Responsive */
@media (max-width: 768px) {
  .channel-cards {
    grid-template-columns: 1fr;
  }
}
</style>
