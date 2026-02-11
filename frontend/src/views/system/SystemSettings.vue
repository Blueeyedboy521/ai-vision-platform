<template>
  <div class="system-settings">
    <div class="page-header">
      <h1 class="page-header__title">系统设置</h1>
      <p class="page-header__subtitle">配置系统基础参数和功能选项</p>
    </div>

    <div class="settings-container">
      <!-- General Settings -->
      <section class="settings-section">
        <h3 class="settings-section__title">基础设置</h3>
        <div class="settings-items">
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">系统名称</span>
              <span class="settings-item__desc">显示在页面标题和登录页的系统名称</span>
            </div>
            <n-input v-model:value="settings.systemName" style="width: 300px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">系统 Logo</span>
              <span class="settings-item__desc">支持 PNG、JPG 格式，建议尺寸 200x60</span>
            </div>
            <n-upload :max="1" accept="image/*">
              <n-button>上传 Logo</n-button>
            </n-upload>
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">默认语言</span>
              <span class="settings-item__desc">系统界面显示语言</span>
            </div>
            <n-select v-model:value="settings.language" :options="languageOptions" style="width: 200px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">时区设置</span>
              <span class="settings-item__desc">影响系统显示和告警时间</span>
            </div>
            <n-select v-model:value="settings.timezone" :options="timezoneOptions" style="width: 300px" />
          </div>
        </div>
      </section>

      <!-- Security Settings -->
      <section class="settings-section">
        <h3 class="settings-section__title">安全设置</h3>
        <div class="settings-items">
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">登录验证码</span>
              <span class="settings-item__desc">启用后登录需要输入图形验证码</span>
            </div>
            <n-switch v-model:value="settings.enableCaptcha" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">双因素认证</span>
              <span class="settings-item__desc">启用后登录需要进行二次验证</span>
            </div>
            <n-switch v-model:value="settings.enable2FA" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">密码过期时间</span>
              <span class="settings-item__desc">用户密码定期强制更换周期</span>
            </div>
            <n-select v-model:value="settings.passwordExpiry" :options="expiryOptions" style="width: 200px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">登录失败锁定</span>
              <span class="settings-item__desc">连续登录失败次数限制</span>
            </div>
            <n-input-number v-model:value="settings.loginFailLimit" :min="3" :max="10" style="width: 150px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">会话超时</span>
              <span class="settings-item__desc">用户无操作自动登出时间（分钟）</span>
            </div>
            <n-input-number v-model:value="settings.sessionTimeout" :min="5" :max="1440" style="width: 150px" />
          </div>
        </div>
      </section>

      <!-- Storage Settings -->
      <section class="settings-section">
        <h3 class="settings-section__title">存储设置</h3>
        <div class="settings-items">
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">告警图片保留</span>
              <span class="settings-item__desc">告警截图自动清理周期</span>
            </div>
            <n-select v-model:value="settings.alarmImageRetention" :options="retentionOptions" style="width: 200px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">录像保留时间</span>
              <span class="settings-item__desc">视频录像自动清理周期</span>
            </div>
            <n-select v-model:value="settings.videoRetention" :options="retentionOptions" style="width: 200px" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">日志保留时间</span>
              <span class="settings-item__desc">操作日志自动清理周期</span>
            </div>
            <n-select v-model:value="settings.logRetention" :options="retentionOptions" style="width: 200px" />
          </div>
        </div>
      </section>

      <!-- Notification Settings -->
      <section class="settings-section">
        <h3 class="settings-section__title">通知设置</h3>
        <div class="settings-items">
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">系统告警声音</span>
              <span class="settings-item__desc">收到告警时播放提示音</span>
            </div>
            <n-switch v-model:value="settings.enableAlarmSound" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">桌面通知</span>
              <span class="settings-item__desc">允许浏览器桌面推送通知</span>
            </div>
            <n-switch v-model:value="settings.enableDesktopNotify" />
          </div>
          <div class="settings-item">
            <div class="settings-item__info">
              <span class="settings-item__label">邮件通知</span>
              <span class="settings-item__desc">系统异常时发送邮件通知管理员</span>
            </div>
            <n-switch v-model:value="settings.enableEmailNotify" />
          </div>
        </div>
      </section>

      <div class="settings-actions">
        <n-button @click="resetSettings">恢复默认</n-button>
        <n-button type="primary" @click="saveSettings">保存设置</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NSelect, NSwitch, NInputNumber, NUpload, NButton, useMessage } from 'naive-ui'

const message = useMessage()

const settings = ref({
  systemName: 'AI 视觉管理平台',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  enableCaptcha: true,
  enable2FA: false,
  passwordExpiry: 90,
  loginFailLimit: 5,
  sessionTimeout: 30,
  alarmImageRetention: 30,
  videoRetention: 7,
  logRetention: 90,
  enableAlarmSound: true,
  enableDesktopNotify: true,
  enableEmailNotify: false
})

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' }
]

const timezoneOptions = [
  { label: '(UTC+08:00) 北京, 重庆, 香港, 乌鲁木齐', value: 'Asia/Shanghai' },
  { label: '(UTC+09:00) 东京, 首尔', value: 'Asia/Tokyo' },
  { label: '(UTC+00:00) 伦敦, 都柏林', value: 'Europe/London' },
  { label: '(UTC-05:00) 纽约, 华盛顿', value: 'America/New_York' }
]

const expiryOptions = [
  { label: '永不过期', value: 0 },
  { label: '30 天', value: 30 },
  { label: '60 天', value: 60 },
  { label: '90 天', value: 90 },
  { label: '180 天', value: 180 }
]

const retentionOptions = [
  { label: '7 天', value: 7 },
  { label: '15 天', value: 15 },
  { label: '30 天', value: 30 },
  { label: '60 天', value: 60 },
  { label: '90 天', value: 90 },
  { label: '180 天', value: 180 },
  { label: '365 天', value: 365 }
]

function resetSettings() {
  settings.value = {
    systemName: 'AI 视觉管理平台',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    enableCaptcha: true,
    enable2FA: false,
    passwordExpiry: 90,
    loginFailLimit: 5,
    sessionTimeout: 30,
    alarmImageRetention: 30,
    videoRetention: 7,
    logRetention: 90,
    enableAlarmSound: true,
    enableDesktopNotify: true,
    enableEmailNotify: false
  }
  message.success('已恢复默认设置')
}

function saveSettings() {
  message.success('设置已保存')
}
</script>

<style scoped>
.system-settings {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
  margin-bottom: var(--spacing-xl);
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

.settings-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  padding-bottom: var(--spacing-xl);
}

.settings-section {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: var(--spacing-lg);
}

.settings-section__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.settings-section__title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: var(--primary-color);
  border-radius: 2px;
}

.settings-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: var(--bg-page);
}

.settings-item__info { flex: 1; }
.settings-item__label { font-weight: var(--font-weight-medium); color: var(--text-primary); display: block; margin-bottom: 4px; }
.settings-item__desc { font-size: var(--font-size-sm); color: var(--text-muted); }

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}
</style>
