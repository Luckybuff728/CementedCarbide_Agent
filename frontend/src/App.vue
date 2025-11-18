<script setup>
import { ref, onMounted, onUnmounted, watch, provide } from 'vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from './stores/workflow'
import { useWebSocket } from './composables/useWebSocket'
import { useWorkflowHandler } from './composables/useWorkflowHandler'
import { useLayoutManager } from './composables/useLayoutManager'
import { WS_ENDPOINTS } from './config'
import { useAuthStore } from './stores/auth'

import ErrorBoundary from './components/layout/ErrorBoundary.vue'
import StatusBar from './components/layout/StatusBar.vue'
import LeftPanel from './components/layout/LeftPanel.vue'
import CenterPanel from './components/layout/CenterPanel.vue'
import RightPanel from './components/layout/RightPanel.vue'
import LoginPanel from './components/auth/LoginPanel.vue'

// ==================== 初始化 ====================
const workflowStore = useWorkflowStore()
const authStore = useAuthStore()

// WebSocket管理
const { 
  connect, 
  send, 
  disconnect, 
  reconnect, 
  isConnected, 
  connectionState, 
  reconnectAttempts,
  setLongTaskStatus
} = useWebSocket()

// 工作流消息处理
const { handleWebSocketMessage } = useWorkflowHandler(setLongTaskStatus)

// 布局管理（支持基础响应式 + 拖拽调整）
const { leftWidth, rightWidth, startResize, applyResponsiveWidth } = useLayoutManager()

// 向子组件provide连接状态
provide('connectionState', connectionState)
provide('reconnectAttempts', reconnectAttempts)
provide('reconnect', reconnect)

// 中间面板引用（用于滚动控制）
const centerPanelRef = ref(null)

// ==================== 状态监听 ====================
watch(isConnected, (connected) => {
  workflowStore.isConnected = connected
})

// WebSocket 与登录状态联动
watch(
  () => authStore.isAuthenticated,
  (authed) => {
    if (authed) {
      const url = `${WS_ENDPOINTS.coating}?token=${authStore.token}`
      connect(url, handleWebSocketMessage)
    } else {
      disconnect()
    }
  },
  { immediate: true }
)

// ==================== 事件处理器 ====================

/**
 * 表单提交处理
 */
const handleFormSubmit = (formData) => {
  workflowStore.reset()
  workflowStore.isProcessing = true
  
  send({
    type: 'start_workflow',
    data: formData
  })
  
  ElMessage.success('已提交，开始分析...')
}

/**
 * 优化方案选择处理
 */
const handleOptimizationSelect = (option) => {
  workflowStore.selectedOptimization = option
  workflowStore.showOptimizationSelection = false
  workflowStore.isProcessing = true
  
  send({
    type: 'select_optimization',
    selected_option: option
  })
  
  ElMessage.success(`已选择 ${option}，正在生成工单...`)
}

/**
 * 实验数据提交处理
 */
const handleExperimentSubmit = (data) => {
  console.log('[实验数据提交]', data)
  
  workflowStore.experimentResults = data.experiment_data
  workflowStore.showExperimentInput = false
  workflowStore.isWaitingExperiment = false
  
  // 根据用户选择设置处理状态
  if (data.continue_iteration) {
    // 继续迭代：设置为正在处理
    workflowStore.isProcessing = true
  } else {
    // 完成迭代：等待后端确认后再结束处理
    console.log('[完成迭代] 等待后端确认结束')
    // 保持 isProcessing 为 true，等待 optimization_completed 消息
    workflowStore.isProcessing = true
  }
  
  // 记录当前轮次的完整快照到历史
  workflowStore.recordIteration({
    iteration: workflowStore.currentIteration,
    selected_optimization: workflowStore.selectedOptimization,
    experiment_results: data.experiment_data,
    timestamp: new Date().toISOString(),
    snapshot: {
      processSteps: JSON.parse(JSON.stringify(workflowStore.processSteps)),
      p1Content: workflowStore.p1Content,
      p2Content: workflowStore.p2Content,
      p3Content: workflowStore.p3Content,
      comprehensiveRecommendation: workflowStore.comprehensiveRecommendation,
      validationResult: workflowStore.validationResult ?
        JSON.parse(JSON.stringify(workflowStore.validationResult)) : null,
      topphiResult: workflowStore.topphiResult ?
        JSON.parse(JSON.stringify(workflowStore.topphiResult)) : null,
      performancePrediction: workflowStore.performancePrediction ? 
        JSON.parse(JSON.stringify(workflowStore.performancePrediction)) : null,
      historicalComparison: workflowStore.historicalComparison ?
        JSON.parse(JSON.stringify(workflowStore.historicalComparison)) : null,
      integratedAnalysis: workflowStore.integratedAnalysis ?
        JSON.parse(JSON.stringify(workflowStore.integratedAnalysis)) : null,
      experimentWorkorder: workflowStore.experimentWorkorder
    }
  })
  
  send({
    type: 'submit_experiment_results',
    data: {
      experiment_data: data.experiment_data,
      continue_iteration: data.continue_iteration
    }
  })
  
  const message = data.continue_iteration 
    ? `实验数据已提交，正在开始第${workflowStore.currentIteration + 1}轮优化...` 
    : '实验数据已提交，正在结束优化流程...'
  ElMessage.success(message)
}

/**
 * 节点跳转处理
 */
const handleJumpToNode = (nodeId) => {
  if (centerPanelRef.value) {
    centerPanelRef.value.scrollToNode(nodeId)
  }
}

/**
 * 导出处理
 */
const handleExport = () => {
  try {
    const exportData = {
      timestamp: new Date().toISOString(),
      processSteps: workflowStore.processSteps,
      performancePrediction: workflowStore.performancePrediction,
      historicalComparison: workflowStore.historicalComparison,
      integratedAnalysis: workflowStore.integratedAnalysis,
      p1Content: workflowStore.p1Content,
      p2Content: workflowStore.p2Content,
      p3Content: workflowStore.p3Content,
      comprehensiveRecommendation: workflowStore.comprehensiveRecommendation,
      experimentWorkorder: workflowStore.experimentWorkorder
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `topmat_analysis_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('数据已导出')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

/**
 * 清空处理（由StatusBar组件处理）
 */
const handleClear = () => {}

// ==================== 生命周期 ====================

// 窗口尺寸变化时，按比例更新左右面板宽度
const handleWindowResize = () => {
  if (typeof window === 'undefined') return
  applyResponsiveWidth(window.innerWidth)
}

onMounted(() => {
  authStore.init()
  handleWindowResize()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleWindowResize)
  }
})

onUnmounted(() => {
  disconnect()
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleWindowResize)
  }
})
</script>

<template>
  <ErrorBoundary>
    <LoginPanel v-if="!authStore.isAuthenticated" />
    <div v-else class="app-container">
      <!-- 顶部状态栏 -->
      <StatusBar 
        @jump-to-node="handleJumpToNode"
        @export="handleExport"
        @clear="handleClear"
      />
      
      <!-- 主工作区 - 三段式布局 -->
      <div class="main-workspace">
      <!-- 左侧表单 -->
      <LeftPanel 
        :style="{ width: `${leftWidth}px` }"
        @submit="handleFormSubmit"
      />
      
      <!-- 左侧拖动条 -->
      <div 
        class="resizer left-resizer"
        @mousedown="startResize($event, 'left')"
      ></div>
      
      <!-- 中间流程展示 -->
      <CenterPanel 
        ref="centerPanelRef"
        :style="{ flex: 1 }"
      />
      
      <!-- 右侧拖动条 -->
      <div 
        class="resizer right-resizer"
        @mousedown="startResize($event, 'right')"
      ></div>
      
      <!-- 右侧结果摘要 -->
      <RightPanel 
        :style="{ width: `${rightWidth}px` }"
        @optimization-select="handleOptimizationSelect"
        @jump-to-node="handleJumpToNode"
        @experiment-submit="handleExperimentSubmit"
      />
    </div>
    </div>
  </ErrorBoundary>
</template>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

.main-workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 拖动条样式 */
.resizer {
  width: 4px;
  background: var(--border-color);
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
}

.resizer:hover {
  background: var(--primary);
}

.resizer::before {
  content: '';
  position: absolute;
  left: -2px;
  right: -2px;
  top: 0;
  bottom: 0;
}

.left-resizer:hover,
.right-resizer:hover {
  background: var(--primary);
  width: 4px;
}
</style>
