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
  const validationResult = ref(null)  // 验证结果（包含错误信息）
  const topphiResult = ref(null)  // TopPhi相场模拟结果（包含VTK数据）
  const performancePrediction = ref(null)
  const historicalComparison = ref(null)
  const integratedAnalysis = ref(null)
  const experimentWorkorder = ref(null)
  
  // 用户选择
  const selectedOptimization = ref(null)
  const showOptimizationSelection = ref(false)
  
  // 迭代优化
  const iterationHistory = ref([])
  const currentIteration = ref(1)
  const showExperimentInput = ref(false)
  const experimentResults = ref(null)
  const isWaitingExperiment = ref(false)
  
  // 历史查看模式
  const viewMode = ref('current')  // 'current' | 'history'
  const viewingIteration = ref(null)  // 正在查看的历史轮次
  
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

  // ========== 显示层计算属性（隔离当前和历史） ==========
  
  // 获取当前显示的快照（历史或当前）
  const currentDisplaySnapshot = computed(() => {
    if (viewMode.value === 'history' && viewingIteration.value) {
      const history = iterationHistory.value.find(h => h.iteration === viewingIteration.value)
      return history?.snapshot || null
    }
    return null
  })
  
  // 显示用的流程步骤（自动切换数据源）
  const displayProcessSteps = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.processSteps : processSteps.value
  })
  
  // 显示用的优化内容
  const displayP1Content = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.p1Content : p1Content.value
  })
  
  const displayP2Content = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.p2Content : p2Content.value
  })
  
  const displayP3Content = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.p3Content : p3Content.value
  })
  
  const displayComprehensiveRecommendation = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.comprehensiveRecommendation : comprehensiveRecommendation.value
  })
  
  // 显示用的分析结果
  const displayValidationResult = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.validationResult : validationResult.value
  })
  
  const displayTopphiResult = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.topphiResult : topphiResult.value
  })
  
  const displayPerformancePrediction = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.performancePrediction : performancePrediction.value
  })
  
  const displayHistoricalComparison = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.historicalComparison : historicalComparison.value
  })
  
  const displayIntegratedAnalysis = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.integratedAnalysis : integratedAnalysis.value
  })
  
  const displayExperimentWorkorder = computed(() => {
    const snapshot = currentDisplaySnapshot.value
    return snapshot ? snapshot.experimentWorkorder : experimentWorkorder.value
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
    validationResult.value = null
    topphiResult.value = null
    performancePrediction.value = null
    historicalComparison.value = null
    integratedAnalysis.value = null
    experimentWorkorder.value = null
    selectedOptimization.value = null
    showOptimizationSelection.value = false
    iterationHistory.value = []
    currentIteration.value = 1
    showExperimentInput.value = false
    experimentResults.value = null
    isWaitingExperiment.value = false
  }
  
  // 记录迭代数据
  const recordIteration = (record) => {
    iterationHistory.value.push(record)
  }
  
  // 清空迭代数据
  const clearIteration = () => {
    iterationHistory.value = []
    currentIteration.value = 1
    experimentResults.value = null
  }
  
  // 开始新一轮迭代 - 清空当前流程内容
  const startNewIteration = (iteration) => {
    console.log(`[迭代管理] 开始第 ${iteration} 轮迭代，清空当前流程`)
    
    // ✅ 关键修复：强制切换回current模式
    if (viewMode.value === 'history') {
      console.log('[迭代管理] 从历史模式切换回当前模式')
      viewMode.value = 'current'
      viewingIteration.value = null
    }
    
    // 清空流程步骤（保留迭代历史，那里有上一轮的完整记录）
    processSteps.value = []
    
    // 清空优化内容
    p1Content.value = ''
    p2Content.value = ''
    p3Content.value = ''
    comprehensiveRecommendation.value = ''
    
    // 清空分析结果（重要！）
    topphiResult.value = null
    performancePrediction.value = null
    historicalComparison.value = null
    integratedAnalysis.value = null
    
    // 清空实验工单
    experimentWorkorder.value = null
    
    // 清空选择状态
    showOptimizationSelection.value = false
    showExperimentInput.value = false
    selectedOptimization.value = null
    
    // 重置处理状态
    isProcessing.value = true
    currentNode.value = ''
    
    console.log('[迭代管理] 流程已清空，已切换到当前模式，准备开始新流程')
  }
  
  // 切换到历史查看模式（简化版 - 只改标志位）
  const viewHistoryIteration = (iteration) => {
    console.log(`[历史查看] 切换到第 ${iteration} 轮历史`)
    
    // 验证历史记录存在
    const history = iterationHistory.value.find(h => h.iteration === iteration)
    if (!history || !history.snapshot) {
      console.warn(`[历史查看] 未找到第 ${iteration} 轮的快照数据`)
      return
    }
    
    // 只需要切换模式标志位，显示层会自动通过computed切换数据源
    viewMode.value = 'history'
    viewingIteration.value = iteration
    
    console.log('[历史查看] 已切换到历史模式，显示第', iteration, '轮快照')
  }
  
  // 返回当前轮次（简化版 - 只改标志位）
  const returnToCurrent = () => {
    console.log('[历史查看] 返回当前轮次')
    
    // 只需要切换回当前模式，显示层会自动切换到当前数据
    viewMode.value = 'current'
    viewingIteration.value = null
    
    console.log('[历史查看] 已返回当前轮次')
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
    validationResult,
    topphiResult,
    performancePrediction,
    historicalComparison,
    integratedAnalysis,
    experimentWorkorder,
    selectedOptimization,
    showOptimizationSelection,
    iterationHistory,
    currentIteration,
    showExperimentInput,
    experimentResults,
    isWaitingExperiment,
    viewMode,
    viewingIteration,
    // 计算属性
    completedNodes,
    hasResults,
    showOptimizationSummary,
    // 显示层计算属性（供UI使用）
    displayProcessSteps,
    displayP1Content,
    displayP2Content,
    displayP3Content,
    displayComprehensiveRecommendation,
    displayValidationResult,
    displayTopphiResult,
    displayPerformancePrediction,
    displayHistoricalComparison,
    displayIntegratedAnalysis,
    displayExperimentWorkorder,
    // 方法
    addProcessStep,
    updateNodeStatus,
    toggleNodeCollapse,
    expandAll,
    collapseAll,
    autoCollapseCompleted,
    reset,
    recordIteration,
    clearIteration,
    startNewIteration,
    viewHistoryIteration,
    returnToCurrent
  }
})
