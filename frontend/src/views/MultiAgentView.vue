<template>
  <div class="multi-agent-view" @mousemove="handleMouseMove" @mouseup="stopResize" @mouseleave="stopResize">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="status-content">
        <div class="left-section">
          <!-- 标题区域 -->
          <div class="title-section">
            <h2 class="app-title">TopMat Agent</h2>
            <p class="app-subtitle">涂层材料智能研发系统</p>
          </div>
          
          <el-divider direction="vertical" />
          
          <!-- 连接状态指示器 -->
          <div class="connection-indicator" :class="{ active: isConnected }">
            <div class="connection-dot"></div>
            <span class="connection-text">{{ isConnected ? '已连接' : '未连接' }}</span>
          </div>
          
          <!-- 任务ID显示 -->
          <template v-if="currentTaskId">
            <div class="status-badge">
              <span class="badge-label">任务</span>
              <span class="badge-value">{{ currentTaskId }}</span>
            </div>
          </template>
          
          <!-- 当前Agent显示 -->
          <template v-if="currentAgent !== '等待中'">
            <div class="status-badge agent">
              <el-icon :size="14"><RibbonOutline /></el-icon>
              <span class="badge-value">{{ currentAgent }}</span>
            </div>
          </template>
          
          <!-- 错误状态指示 -->
          <template v-if="hasError">
            <div class="status-badge error" @click="showErrorDetails">
              <el-icon :size="14"><WarningOutline /></el-icon>
              <span class="badge-value">网络异常</span>
            </div>
          </template>
        </div>
        
        <div class="actions">
          <!-- 用户信息 -->
          <div class="user-info" v-if="authStore?.user">
            <div class="user-avatar">{{ (authStore?.user?.display_name || authStore?.user?.username || 'U')[0].toUpperCase() }}</div>
            <!-- <span class="user-name">{{ authStore?.user?.display_name || authStore?.user?.username }}</span> -->
            <el-button size="small" text circle @click="handleLogout">
              <el-icon :size="16"><LogOutOutline /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主工作区 -->
    <div class="workspace">
      <!-- 左侧：表单（可收起） -->
      <div 
        class="left-panel-wrapper" 
        :class="{ collapsed: leftPanelCollapsed }"
        :style="{ width: leftPanelCollapsed ? '0' : `${leftPanelWidth}px` }"
      >
        <!-- 收起时的展开按钮 -->
        <div class="collapsed-toggle" v-if="leftPanelCollapsed" @click="leftPanelCollapsed = false">
          <el-icon :size="16"><ChevronForwardOutline /></el-icon>
        </div>
        
        <!-- 展开时的面板 -->
        <div class="left-panel" v-show="!leftPanelCollapsed">
          <div class="panel-toggle" @click="leftPanelCollapsed = true">
            <el-icon :size="16"><ChevronBackOutline /></el-icon>
          </div>
          <div class="panel-content">
            <LeftPanel
              :disabled="currentTaskId !== null"
              @submit="handleFormSubmit"
            />
          </div>
        </div>
      </div>
      
      <!-- 左侧调整手柄 -->
      <div 
        class="resize-handle left" 
        v-if="!leftPanelCollapsed"
        @mousedown.prevent="startResizeLeft"
      >
        <div class="handle-line"></div>
      </div>
      
      <!-- 中间：对话面板 -->
      <div class="center-panel">
        <ChatPanel
          :messages="messages"
          :current-agent="currentAgent"
          :is-agent-typing="isAgentTyping"
          :is-generating="isAgentTyping"
          @send-message="handleSendMessage"
          @stop-generate="handleStopGenerate"
        />
      </div>
      
      <!-- 右侧调整手柄 -->
      <div 
        class="resize-handle right" 
        @mousedown.prevent="startResizeRight"
      >
        <div class="handle-line"></div>
      </div>
      
      <!-- 右侧：结果展示 -->
      <div 
        class="right-panel"
        :style="{ width: `${rightPanelWidth}px` }"
      >
        <ResultsPanel 
          :results="results"
          @clear="clearResults"
          @select-optimization="handleOptimizationSelect"
          @experiment-submit="handleExperimentSubmit"
          @experiment-cancel="handleExperimentCancel"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElTabs, ElTabPane, ElTag, ElMessage, ElButton, ElIcon, ElDivider } from 'element-plus'
import { RibbonOutline, ChevronBackOutline, ChevronForwardOutline, LogOutOutline, WarningOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth'
import { useMultiAgent } from '../composables/useMultiAgent'

import LeftPanel from '../components/panels/LeftPanel.vue'
import ChatPanel from '../components/panels/ChatPanel.vue'
import ResultsPanel from '../components/panels/ResultsPanel.vue'

const authStore = useAuthStore()

// 左侧面板收起状态
const leftPanelCollapsed = ref(false)

// 布局调整状态
const leftPanelWidth = ref(340)
const rightPanelWidth = ref(480)
const isResizingLeft = ref(false)
const isResizingRight = ref(false)

const startResizeLeft = () => {
  isResizingLeft.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const startResizeRight = () => {
  isResizingRight.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleMouseMove = (e) => {
  if (isResizingLeft.value) {
    const newWidth = e.clientX - 16 // 减去padding
    if (newWidth >= 280 && newWidth <= 600) {
      leftPanelWidth.value = newWidth
    }
  }
  
  if (isResizingRight.value) {
    const newWidth = window.innerWidth - e.clientX - 16 // 减去padding
    if (newWidth >= 350 && newWidth <= 800) {
      rightPanelWidth.value = newWidth
    }
  }
}

const stopResize = () => {
  if (isResizingLeft.value || isResizingRight.value) {
    isResizingLeft.value = false
    isResizingRight.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
}

// 使用对话式多Agent composable
const {
  connect,
  disconnect,
  isConnected,
  sessionId,
  currentAgent,
  isAgentTyping,
  activeTool,
  statusText,
  messages,
  results,
  validationResult,
  performancePrediction,
  optimizationResults,
  experimentWorkorder,
  sessionParams,
  sendMessage,
  startWithParams,
  clearSession,
  clearResults,
  stopGenerate,
  hasError,
  lastError
} = useMultiAgent()

// 兼容旧版变量名
const currentTaskId = sessionId

// 表单提交 - 使用新版对话式 API
const handleFormSubmit = (formData) => {
  startWithParams(formData)
  ElMessage.success('参数已提交，助手正在分析...')
}

// 发送对话消息
const handleSendMessage = (message) => {
  sendMessage(message)
}

// 终止生成
const handleStopGenerate = () => {
  stopGenerate()
}

// 选择优化方案 - 对话式系统通过消息处理
const handleOptimizationSelect = (option) => {
  // 在对话式系统中，通过发送消息来选择方案
  sendMessage(`我选择 ${option} 优化方案，请帮我生成实验工单`)
  ElMessage.success(`已选择 ${option}`)
  
  // 移除优化方案选择器
  results.value = results.value.filter(r => r.type !== 'optimization')
}

// 提交实验结果 - 对话式系统通过消息处理
const handleExperimentSubmit = (data) => {
  // 解构数据（ExperimentInputCard 发出的格式）
  const { experiment_data, continue_iteration } = data
  const { hardness, elastic_modulus, adhesion_strength, wear_rate, notes } = experiment_data
  
  // 构建实验结果消息
  let resultMsg = `实验完成，测试结果：硬度 ${hardness} GPa，弹性模量 ${elastic_modulus} GPa，结合力 ${adhesion_strength} N`
  if (wear_rate) {
    resultMsg += `，磨损率 ${wear_rate} mm³/Nm`
  }
  if (notes) {
    resultMsg += `。备注：${notes}`
  }
  resultMsg += continue_iteration ? '。请分析结果并继续优化。' : '。请分析最终结果。'
  
  sendMessage(resultMsg)
  
  ElMessage.success(continue_iteration ? '数据已提交，正在分析...' : '数据已提交，正在生成最终报告...')
  
  // 移除实验输入表单
  results.value = results.value.filter(r => r.type !== 'experiment_input')
}

// 取消实验结果输入
const handleExperimentCancel = () => {
  results.value = results.value.filter(r => r.type !== 'experiment_input')
  ElMessage.info('已取消实验数据录入')
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
}

// 显示错误详情
const showErrorDetails = () => {
  if (lastError.value) {
    ElMessage({
      type: 'warning',
      message: lastError.value.user_message || '系统遇到临时问题',
      duration: 5000,
      showClose: true
    })
  }
}

// 对话式系统：监听结果列表变化，自动滚动到最新
watch(results, (newResults) => {
  if (newResults.length > 0) {
    console.log('[ChatView] 新结果:', newResults[newResults.length - 1].type)
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  authStore.init()
  
  // ✅ 测试模式：刷新页面时清空旧任务，重新开始
  console.log('[测试模式] 刷新页面，清理旧状态')
  clearResults()  // 清空结果
  // 注意：不清理messages，保留对话历史供参考
  
  // 初始化时只建立一次连接
  if (authStore.isAuthenticated && !isConnected.value) {
    console.log('[MultiAgentView] 初始连接')
    connect(authStore.token)
    ElMessage.success('欢迎使用 TopMat Agent 多智能体系统')
  }
  
  // 添加全局事件监听，防止拖出iframe或窗口时卡住
  window.addEventListener('mouseup', stopResize)
})

onUnmounted(() => {
  console.log('[MultiAgentView] 组件卸载，断开连接')
  disconnect()
  window.removeEventListener('mouseup', stopResize)
})

// 监听认证状态变化（避免重复连接）
let isConnecting = false
watch(() => authStore.isAuthenticated, (authed) => {
  if (authed && !isConnected.value && !isConnecting) {
    isConnecting = true
    console.log('[MultiAgentView] 认证成功，建立连接')
    connect(authStore.token)
    // 延迟重置标志，避免快速重复调用
    setTimeout(() => { isConnecting = false }, 1000)
  } else if (!authed && isConnected.value) {
    console.log('[MultiAgentView] 认证失效，断开连接')
    disconnect()
    isConnecting = false
  }
})
</script>

<style scoped>
.multi-agent-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f4f9; /* Gemini 风格背景 */
  color: #1f1f1f;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* 顶部状态栏 - 极简风格 */
.status-bar {
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e1e4e8;
  display: flex;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.status-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

/* 标题区域 */
.title-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.app-subtitle {
  margin: 0;
  font-size: 12px;
  color: #5f6368;
  line-height: 1.2;
}

/* 连接状态 */
.connection-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  color: #5f6368;
  background: #f1f3f4;
}

.connection-indicator.active {
  background: #e6f4ea;
  color: #137333;
}

.connection-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

/* 状态徽章 */
.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #f1f3f4;
  border-radius: 16px;
  font-size: 12px;
  color: #3c4043;
}

.status-badge.agent {
  background: #e8f0fe;
  color: #1967d2;
}

.status-badge.error {
  background: #fce8e6;
  color: #c5221f;
  cursor: pointer;
  animation: pulse-error 2s ease-in-out infinite;
}

.status-badge.error:hover {
  background: #f8d7da;
}

@keyframes pulse-error {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.badge-label {
  color: #5f6368;
  font-weight: 500;
}

.badge-value {
  font-family: 'Consolas', monospace;
  font-weight: 600;
}

/* 分割线 */
:deep(.el-divider--vertical) {
  height: 24px;
  margin: 0;
  border-color: #dfe1e5;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1967d2;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

/* 工作区布局 */
.workspace {
  flex: 1;
  display: flex;
  padding: 16px;
  overflow: hidden;
  gap: 0; /* 由resize-handle充当gap */
}

/* 调整手柄 */
.resize-handle {
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: col-resize;
  flex-shrink: 0;
  transition: all 0.2s;
}

.resize-handle:hover .handle-line {
  background: #1967d2;
  opacity: 1;
}

.handle-line {
  width: 4px;
  height: 40px;
  background: #dadce0;
  border-radius: 2px;
  transition: all 0.2s;
}

/* 左侧面板容器 */
.left-panel-wrapper {
  flex-shrink: 0;
  position: relative;
  transition: width 0.1s ease-out; /* 拖动时需要快速响应 */
  display: flex;
  flex-direction: column;
}

.left-panel-wrapper.collapsed {
  width: 0 !important;
  transition: width 0.3s ease;
}

/* 收起时的展开按钮 */
.collapsed-toggle {
  position: absolute;
  top: 20px;
  left: 0;
  width: 32px;
  height: 32px;
  background: #ffffff;
  border: 1px solid #dadce0;
  border-radius: 0 16px 16px 0;
  border-left: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  color: #5f6368;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.collapsed-toggle:hover {
  background: #f8f9fa;
  color: #1967d2;
}

/* 展开时的面板 */
.left-panel {
  flex: 1;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dadce0; /* 轻微边框 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-toggle {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  background: #fff;
  border: 1px solid #dadce0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  color: #5f6368;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.panel-toggle:hover {
  background: #f8f9fa;
  color: #1967d2;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  /* padding: 16px; 由内部组件决定padding */
  height: 100%;
}

.center-panel {
  flex: 1;
  min-width: 0; /* 防止flex子项溢出 */
  display: flex;
  flex-direction: column;
  background: transparent;
}

.right-panel {
  flex-shrink: 0;
  background: transparent; /* 内部ResultPanel会有背景 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 滚动条样式统一 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #dadce0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #bdc1c6;
}
</style>



