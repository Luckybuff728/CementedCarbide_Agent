<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">出错了</h2>
      <p class="error-message">{{ errorMessage }}</p>
      
      <div class="error-details" v-if="showDetails">
        <pre class="error-stack">{{ errorStack }}</pre>
      </div>
      
      <div class="error-actions">
        <button class="btn-primary" @click="handleReload">
          刷新页面
        </button>
        <button class="btn-secondary" @click="handleToggleDetails">
          {{ showDetails ? '隐藏详情' : '显示详情' }}
        </button>
        <button class="btn-secondary" @click="handleReport">
          报告问题
        </button>
      </div>
      
      <div class="error-tips">
        <p>如果问题持续存在，请尝试：</p>
        <ul>
          <li>清除浏览器缓存</li>
          <li>使用无痕模式</li>
          <li>联系技术支持</li>
        </ul>
      </div>
    </div>
  </div>
  
  <div v-else class="error-boundary-content">
    <slot />
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { ElMessage } from 'element-plus'

// 错误状态
const hasError = ref(false)
const errorMessage = ref('')
const errorStack = ref('')
const showDetails = ref(false)

// 捕获组件错误
onErrorCaptured((err, instance, info) => {
  hasError.value = true
  errorMessage.value = err.message || '未知错误'
  errorStack.value = `${err.stack}\n\n组件信息: ${info}`
  
  // 记录到控制台
  console.error('[ErrorBoundary] 捕获到错误:', {
    error: err,
    component: instance,
    info: info
  })
  
  // 可选：发送到错误监控服务（如Sentry）
  // sendErrorToMonitoring(err, instance, info)
  
  // 阻止错误继续传播
  return false
})

// 刷新页面
const handleReload = () => {
  window.location.reload()
}

// 切换详情显示
const handleToggleDetails = () => {
  showDetails.value = !showDetails.value
}

// 报告问题
const handleReport = () => {
  const errorReport = {
    message: errorMessage.value,
    stack: errorStack.value,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    url: window.location.href
  }
  
  // 复制错误信息到剪贴板
  const reportText = JSON.stringify(errorReport, null, 2)
  navigator.clipboard.writeText(reportText).then(() => {
    ElMessage.success('错误信息已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制错误详情')
  })
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #fef3c7 0%, #fca5a5 100%);
  padding: 24px;
}

.error-container {
  max-width: 600px;
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 16px;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 12px 0;
}

.error-message {
  font-size: 16px;
  color: #4b5563;
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.error-details {
  margin: 24px 0;
  text-align: left;
}

.error-stack {
  background: #1f2937;
  color: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.error-tips {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  text-align: left;
}

.error-tips p {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.error-tips ul {
  margin: 0;
  padding-left: 20px;
}

.error-tips li {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.8;
}

/* 错误边界内容容器 */
.error-boundary-content {
  width: 100%;
  height: 100%;
}
</style>
