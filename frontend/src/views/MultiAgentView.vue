<template>
  <div class="multi-agent-view">
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
          <div class="connection-indicator">
            <div :class="['connection-dot', { active: isConnected }]"></div>
            <span :class="['connection-text', { active: isConnected }]">
              {{ isConnected ? '已连接' : '未连接' }}
            </span>
          </div>
          
          <!-- 任务ID显示 -->
          <template v-if="currentTaskId">
            <el-divider direction="vertical" />
            <div class="task-indicator">
              <span class="task-label">任务</span>
              <span class="task-id">{{ currentTaskId }}</span>
            </div>
          </template>
          
          <!-- 当前Agent显示 -->
          <template v-if="currentAgent !== '等待中'">
            <el-divider direction="vertical" />
            <div class="agent-indicator">
              <el-icon :size="14"><RibbonOutline /></el-icon>
              <span class="agent-name">{{ currentAgent }}</span>
            </div>
          </template>
        </div>
        
        <div class="actions">
          <!-- 用户信息 -->
          <div class="user-info" v-if="authStore?.user">
            <span class="user-name">{{ authStore?.user?.display_name || authStore?.user?.username }}</span>
            <el-button size="small" text @click="handleLogout">退出</el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主工作区 -->
    <div class="workspace">
      <!-- 左侧：表单（可收起） -->
      <div class="left-panel-wrapper" :class="{ collapsed: leftPanelCollapsed }">
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
      
      <!-- 中间：对话面板 -->
      <div class="center-panel">
        <ChatPanel
          :messages="messages"
          :current-agent="currentAgent"
          :is-agent-typing="isAgentTyping"
          :can-send-message="canSendMessage"
          @send-message="handleSendMessage"
        />
      </div>
      
      <!-- 右侧：结果展示 -->
      <div class="right-panel">
        <ResultsPanel 
          :results="results"
          @clear="clearResults"
          @select-optimization="handleOptimizationSelect"
          @experiment-submit="handleExperimentSubmit"
          @experiment-cancel="handleExperimentCancel"
        />
        
        <!-- ✅ 所有用户操作都移到右侧面板，不再使用中间的悬浮层 -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElTabs, ElTabPane, ElTag, ElMessage, ElButton, ElIcon, ElDivider } from 'element-plus'
import { RibbonOutline, ChevronBackOutline, ChevronForwardOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth'
import { useMultiAgent } from '../composables/useMultiAgent'

import LeftPanel from '../components/layout/LeftPanel.vue'
import ChatPanel from '../components/chat/ChatPanel.vue'
import ResultsPanel from '../components/results/ResultsPanel.vue'

const authStore = useAuthStore()

// 左侧面板收起状态
const leftPanelCollapsed = ref(false)

// 使用多Agent composable
const {
  connect,
  disconnect,
  isConnected,
  currentAgent,
  currentTaskId,
  isAgentTyping,
  messages,
  results,
  p1Content,
  p2Content,
  p3Content,
  comprehensiveRecommendation,
  canSendMessage,
  showOptimizationSelector,
  showExperimentInput,
  startAgentTask,
  sendMessage,
  selectOptimization,
  submitExperiment,
  clearResults,
  validationResult,
  performancePrediction,
  integratedAnalysis,
  experimentWorkorder,
  activeTab
} = useMultiAgent()

// 表单提交
const handleFormSubmit = (formData) => {
  startAgentTask(formData)
  ElMessage.success('任务已提交，Agent正在处理...')
}

// 发送对话消息
const handleSendMessage = (message) => {
  sendMessage(message)
}

// 选择优化方案
const handleOptimizationSelect = (option) => {
  selectOptimization(option)
  ElMessage.success(`已选择 ${option}，正在生成工单...`)
  
  // 移除优化方案选择器（与实验输入表单相同处理）
  results.value = results.value.filter(r => r.type !== 'optimization')
}

// 提交实验结果
const handleExperimentSubmit = (data) => {
  submitExperiment(data)
  
  if (data.continue_iteration) {
    ElMessage.success('开始新一轮迭代...')
  } else {
    ElMessage.success('优化流程已完成！')
  }
  
  // 移除实验输入表单
  results.value = results.value.filter(r => r.type !== 'experiment_input')
}

// 取消实验结果输入
const handleExperimentCancel = () => {
  // 移除实验输入表单
  results.value = results.value.filter(r => r.type !== 'experiment_input')
  ElMessage.info('已取消实验数据录入')
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
}

// 监听数据更新，自动切换标签页
watch([validationResult, performancePrediction, integratedAnalysis, p1Content, experimentWorkorder], 
  ([validation, performance, analysis, p1, workorder]) => {
    if (workorder && !showExperimentInput.value) {
      activeTab.value = 'workorder'
    } else if (p1) {
      activeTab.value = 'optimization'
    } else if (analysis) {
      activeTab.value = 'analysis'
    } else if (performance) {
      activeTab.value = 'performance'
    } else if (validation) {
      activeTab.value = 'validation'
    }
  }
)

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
})

onUnmounted(() => {
  console.log('[MultiAgentView] 组件卸载，断开连接')
  disconnect()
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
  background: #f8f9fa;
}

/* 优化后的顶部状态栏 - 参考StatusBar设计 */
.status-bar {
  min-height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  align-items: center;
  padding: 8px 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 10;
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
  gap: 16px;
  flex: 1;
  overflow-x: auto;
}

/* 标题区域 */
.title-section {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding-right: 8px;
}

.app-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #0d0d0d;
  line-height: 1.5;
}

.app-subtitle {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

/* 连接状态指示器 */
.connection-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 6px;
  background: #fafafa;
}

.connection-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
  transition: all 0.3s;
}

.connection-dot.active {
  background: #2d2d2d;
  box-shadow: 0 0 6px rgba(45, 45, 45, 0.4);
  animation: pulse-dark 2s ease-in-out infinite;
}

.connection-text {
  font-size: 12px;
  font-weight: 500;
  color: #999;
  transition: color 0.3s;
}

.connection-text.active {
  color: #2d2d2d;
}

@keyframes pulse-dark {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 任务指示器 */
.task-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #f4f4f4;
  border-radius: 6px;
}

.task-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.task-id {
  font-size: 12px;
  color: #0d0d0d;
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 500;
}

/* Agent指示器 */
.agent-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #f4f4f4;
  border-radius: 6px;
}

.agent-name {
  font-size: 12px;
  color: #2d2d2d;
  font-weight: 500;
}

/* 分割线样式 */
:deep(.el-divider--vertical) {
  height: 24px;
  margin: 0;
  border-color: #e5e5e5;
}

/* 右侧操作区 */
.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.actions :deep(.el-button) {
  border-radius: 6px;
}

/* 工作区布局 */
.workspace {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 左侧面板容器 */
.left-panel-wrapper {
  flex-shrink: 0;
  position: relative;
  transition: all 0.3s ease;
}

.left-panel-wrapper.collapsed {
  width: 0;
}

/* 收起时的展开按钮 */
.collapsed-toggle {
  position: absolute;
  top: 12px;
  left: 0;
  width: 28px;
  height: 28px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 0 8px 8px 0;
  border-left: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  transition: all 0.2s;
  color: #666;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.06);
}

.collapsed-toggle:hover {
  background: #f5f5f5;
  color: #333;
  width: 32px;
}

/* 展开时的面板 */
.left-panel {
  width: 340px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-toggle {
  position: absolute;
  top: 12px;
  right: -12px;
  width: 24px;
  height: 24px;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  color: #666;
}

.panel-toggle:hover {
  background: #f5f5f5;
  color: #333;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

.center-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.right-panel {
  width: 480px;
  flex-shrink: 0;
  overflow-y: auto;
}

.optimization-content {
  padding: 0;
}

.optimization-preview {
  padding: 16px;
  background: white;
  border-radius: 8px;
}

/* 优化标签页样式 */
:deep(.el-tabs--border-card) {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  height: 100%;
  background: #ffffff;
}

:deep(.el-tabs__header) {
  background: #fafafa;
  border-bottom: 1px solid #e5e5e5;
  margin: 0;
  padding: 12px 16px 0;
  border-radius: 12px 12px 0 0;
}

:deep(.el-tabs__item) {
  color: #666;
  font-size: 14px;
  font-weight: 500;
  padding: 0 16px;
  height: 40px;
  line-height: 40px;
  border: none;
  transition: all 0.2s;
}

:deep(.el-tabs__item:hover) {
  color: #0d0d0d;
}

:deep(.el-tabs__item.is-active) {
  color: #0d0d0d;
  background: #ffffff;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
}

:deep(.el-tabs__content) {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(100vh - 220px);
}

/* 滚动条样式统一 */
.left-panel::-webkit-scrollbar,
.right-panel::-webkit-scrollbar,
:deep(.el-tabs__content)::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track,
.right-panel::-webkit-scrollbar-track,
:deep(.el-tabs__content)::-webkit-scrollbar-track {
  background: transparent;
}

.left-panel::-webkit-scrollbar-thumb,
.right-panel::-webkit-scrollbar-thumb,
:deep(.el-tabs__content)::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.left-panel::-webkit-scrollbar-thumb:hover,
.right-panel::-webkit-scrollbar-thumb:hover,
:deep(.el-tabs__content)::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 悬浮overlay样式 */
/* ✅ 所有用户操作都在右侧面板，不再需要中间的悬浮层样式 */
</style>


