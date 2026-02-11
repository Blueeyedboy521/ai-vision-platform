<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="login-bg__gradient"></div>
      <div class="login-bg__pattern"></div>
    </div>
    
    <div class="login-container">
      <!-- Left: Branding -->
      <div class="login-branding">
        <div class="login-branding__content">
          <div class="login-branding__logo">
            <svg width="48" height="48" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="6" fill="#4318FF" />
              <path d="M8 10h4v8H8V10zm8 0h4v8h-4V10z" fill="white" opacity="0.9" />
              <path d="M12 8h4v12h-4V8z" fill="white" />
            </svg>
            <h1 class="login-branding__title">AI 视觉管理平台</h1>
          </div>
          <p class="login-branding__desc">
            新一代智能视觉分析平台，为企业提供全方位的视频监控、AI算法管理及智能告警解决方案
          </p>
          <div class="login-branding__features">
            <div class="feature-item">
              <n-icon :size="20" color="#4318FF"><VideocamOutline /></n-icon>
              <span>智能视频监控</span>
            </div>
            <div class="feature-item">
              <n-icon :size="20" color="#4318FF"><SparklesOutline /></n-icon>
              <span>AI 算法管理</span>
            </div>
            <div class="feature-item">
              <n-icon :size="20" color="#4318FF"><NotificationsOutline /></n-icon>
              <span>实时告警推送</span>
            </div>
            <div class="feature-item">
              <n-icon :size="20" color="#4318FF"><ShieldCheckmarkOutline /></n-icon>
              <span>安全权限管理</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Login Form -->
      <div class="login-form-wrapper">
        <div class="login-form">
          <h2 class="login-form__title">欢迎登录</h2>
          <p class="login-form__subtitle">请输入您的账号信息</p>

          <n-form ref="formRef" :model="formData" :rules="rules" class="login-form__content">
            <n-form-item path="username" label="用户名">
              <n-input 
                v-model:value="formData.username" 
                placeholder="请输入用户名"
                size="large"
              >
                <template #prefix>
                  <n-icon :size="18" color="#9ca3af"><PersonOutline /></n-icon>
                </template>
              </n-input>
            </n-form-item>

            <n-form-item path="password" label="密码">
              <n-input 
                v-model:value="formData.password" 
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password-on="click"
              >
                <template #prefix>
                  <n-icon :size="18" color="#9ca3af"><LockClosedOutline /></n-icon>
                </template>
              </n-input>
            </n-form-item>

            <n-form-item v-if="showCaptcha" path="captcha" label="验证码">
              <div class="captcha-row">
                <n-input 
                  v-model:value="formData.captcha" 
                  placeholder="请输入验证码"
                  size="large"
                />
                <div class="captcha-image" @click="refreshCaptcha">
                  <span>{{ captchaText }}</span>
                </div>
              </div>
            </n-form-item>

            <div class="login-form__options">
              <n-checkbox v-model:checked="formData.remember">记住密码</n-checkbox>
              <a href="#" class="forgot-link">忘记密码？</a>
            </div>

            <n-button 
              type="primary" 
              block 
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </n-button>
          </n-form>

          <div class="login-form__footer">
            <span>© 2024 AI Vision Platform. All rights reserved.</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, NCheckbox, NIcon, useMessage } from 'naive-ui'
import { 
  PersonOutline, 
  LockClosedOutline, 
  VideocamOutline,
  NotificationsOutline,
  ShieldCheckmarkOutline,
  SparklesOutline
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const formRef = ref()
const loading = ref(false)
const showCaptcha = ref(true)
const captchaText = ref('ABCD')

const formData = ref({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
  captcha: { required: true, message: '请输入验证码', trigger: 'blur' }
}

function refreshCaptcha() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  captchaText.value = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    // Simulate login request
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Demo: accept any username/password
    if (formData.value.username && formData.value.password) {
      // Store user info
      localStorage.setItem('user', JSON.stringify({
        username: formData.value.username,
        name: formData.value.username === 'admin' ? '系统管理员' : formData.value.username,
        role: formData.value.username === 'admin' ? '超级管理员' : '普通用户',
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${formData.value.username}`
      }))
      localStorage.setItem('token', 'demo-token-' + Date.now())
      
      message.success('登录成功')
      router.push('/dashboard')
    } else {
      message.error('用户名或密码错误')
    }
  } catch (error) {
    // Validation failed
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.login-bg__gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #4318FF 100%);
}

.login-bg__pattern {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.login-container {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  max-width: 1000px;
  min-height: 600px;
  margin: 20px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

/* Branding Section */
.login-branding {
  flex: 1;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 48px;
  display: flex;
  align-items: center;
  color: #fff;
}

.login-branding__content {
  max-width: 400px;
}

.login-branding__logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.login-branding__title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.login-branding__desc {
  font-size: 15px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 32px;
}

.login-branding__features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

/* Login Form */
.login-form-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: #fff;
}

.login-form {
  width: 100%;
  max-width: 360px;
}

.login-form__title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.login-form__subtitle {
  font-size: 14px;
  color: #9ca3af;
  margin: 0 0 32px;
}

.login-form__content {
  margin-bottom: 24px;
}

.captcha-row {
  display: flex;
  gap: 12px;
}

.captcha-row :deep(.n-input) {
  flex: 1;
}

.captcha-image {
  width: 120px;
  height: 40px;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.captcha-image span {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #374151;
  font-family: monospace;
  text-decoration: line-through;
  text-decoration-color: rgba(67, 24, 255, 0.3);
}

.login-form__options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.forgot-link {
  font-size: 13px;
  color: #4318FF;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.login-form__footer {
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 32px;
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    max-width: 400px;
  }
  
  .login-branding {
    padding: 32px;
  }
  
  .login-branding__features {
    grid-template-columns: 1fr;
  }
}
</style>
