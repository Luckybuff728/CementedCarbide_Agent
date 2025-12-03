<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2 class="title">CementedCarbide Agent {{ isRegister ? '注册' : '登录' }}</h2>
      <el-form @submit.prevent="handleSubmit">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item v-if="isRegister">
          <el-input v-model="displayName" placeholder="显示名称（可选）" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            :placeholder="isRegister ? '设置密码' : '密码'"
            autocomplete="current-password"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="auth.loading" native-type="submit" style="width: 100%">
            {{ isRegister ? '注册' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="switch-mode">
        <span v-if="isRegister">
          已有账号？
          <a href="javascript:void(0)" @click="switchMode">去登录</a>
        </span>
        <span v-else>
          还没有账号？
          <a href="javascript:void(0)" @click="switchMode">去注册</a>
        </span>
      </div>
      <div class="wechat-placeholder">
        <span>或使用微信扫码登录（待接入）</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const username = ref('')
const password = ref('')
const displayName = ref('')
const isRegister = ref(false)

const handleSubmit = async () => {
  if (!username.value || !password.value) return
  if (isRegister.value) {
    await auth.register(username.value, password.value, displayName.value)
    // 注册成功后切回登录模式
    isRegister.value = false
  } else {
    await auth.login(username.value, password.value)
  }
}

const switchMode = () => {
  isRegister.value = !isRegister.value
}
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 50%, #fef3c7 100%);
}

.login-card {
  width: 360px;
  padding: 32px 28px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.25);
}

.title {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  color: #111827;
}

.switch-mode {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

.switch-mode a {
  color: #2563eb;
  cursor: pointer;
}

.wechat-placeholder {
  margin-top: 12px;
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}
</style>
