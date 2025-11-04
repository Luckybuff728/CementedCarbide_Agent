/**
 * 工作流状态管理Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWorkflowStore = defineStore('workflow', () => {
  // ========== 状态定义 ==========
  
  // 连接状态
  const isConnected = ref(false)
  const isProcessing = ref(false)
  
  // 当前节点
  const currentNode = ref('')
  const currentNodeTitle = ref('')
  
  // 流程步骤列表
  const processSteps = ref([])
  
  // 节点折叠状态
  const collapsedNodes = ref({})
  
  // P1/P2/P3优化内容（独立存储，避免并行冲突）
  const p1Content = ref('')
  const p2Content = ref('')
  const p3Content = ref('')
  
  // 综合建议
  const comprehensiveRecommendation = ref('')
  
  // 分析结果
  const performancePrediction = ref(null)
  const historicalComparison = ref(null)
  const integratedAnalysis = ref(null)
  const experimentWorkorder = ref(null)
  
  // 用户选择
  const selectedOptimization = ref(null)
  const showOptimizationSelection = ref(false)
  
  // ========== 计算属性 ==========
  
  // 已完成的节点列表
  const completedNodes = computed(() => {
    return processSteps.value
      .filter(step => step.status === 'completed')
      .map(step => step.nodeId)
  })
  
  // 是否有分析结果
  const hasResults = computed(() => {
    return performancePrediction.value !== null ||
           historicalComparison.value !== null ||
           integratedAnalysis.value !== null
  })
  
  // 是否显示优化方案
  const showOptimizationSummary = computed(() => {
    return p1Content.value || p2Content.value || p3Content.value
  })
  
  // ========== 方法 ==========
  
  // 添加流程步骤
  const addProcessStep = (step) => {
    const existingStep = processSteps.value.find(s => s.nodeId === step.nodeId)
    if (existingStep) {
      existingStep.status = step.status
      existingStep.content = step.content
      if (step.timestamp) existingStep.timestamp = step.timestamp
    } else {
      processSteps.value.push({
        id: Date.now().toString(),
        nodeId: step.nodeId,
        status: step.status || 'pending',
        content: step.content || '',
        timestamp: step.timestamp || new Date().toISOString()
      })
      // 新增节点默认展开
      collapsedNodes.value[step.nodeId] = false
    }
  }
  
  // 更新节点状态
  const updateNodeStatus = (nodeId, status) => {
    const step = processSteps.value.find(s => s.nodeId === nodeId)
    if (step) {
      step.status = status
    }
  }
  
  // 切换节点折叠状态
  const toggleNodeCollapse = (nodeId) => {
    collapsedNodes.value[nodeId] = !collapsedNodes.value[nodeId]
  }
  
  // 展开所有节点
  const expandAll = () => {
    Object.keys(collapsedNodes.value).forEach(key => {
      collapsedNodes.value[key] = false
    })
  }
  
  // 收起所有节点
  const collapseAll = () => {
    Object.keys(collapsedNodes.value).forEach(key => {
      collapsedNodes.value[key] = true
    })
  }
  
  // 智能收起：完成的节点自动收起
  const autoCollapseCompleted = () => {
    processSteps.value.forEach(step => {
      if (step.status === 'completed' && step.nodeId !== currentNode.value) {
        collapsedNodes.value[step.nodeId] = true
      }
    })
  }
  
  // 清空所有数据
  const reset = () => {
    processSteps.value = []
    collapsedNodes.value = {}
    currentNode.value = ''
    currentNodeTitle.value = ''
    isProcessing.value = false
    p1Content.value = ''
    p2Content.value = ''
    p3Content.value = ''
    comprehensiveRecommendation.value = ''
    performancePrediction.value = null
    historicalComparison.value = null
    integratedAnalysis.value = null
    experimentWorkorder.value = null
    selectedOptimization.value = null
    showOptimizationSelection.value = false
  }
  
  return {
    // 状态
    isConnected,
    isProcessing,
    currentNode,
    currentNodeTitle,
    processSteps,
    collapsedNodes,
    p1Content,
    p2Content,
    p3Content,
    comprehensiveRecommendation,
    performancePrediction,
    historicalComparison,
    integratedAnalysis,
    experimentWorkorder,
    selectedOptimization,
    showOptimizationSelection,
    // 计算属性
    completedNodes,
    hasResults,
    showOptimizationSummary,
    // 方法
    addProcessStep,
    updateNodeStatus,
    toggleNodeCollapse,
    expandAll,
    collapseAll,
    autoCollapseCompleted,
    reset
  }
})
