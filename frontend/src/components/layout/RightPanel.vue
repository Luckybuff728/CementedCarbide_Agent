<template>
  <div class="right-panel" ref="rightPanelRef" @scroll="handlePanelScroll">
    <!-- 空状态展示 -->
    <EmptyStateCard v-if="!hasAnyContent" />
    
    <!-- 参数验证摘要 -->
    <ValidationSummaryCard
      v-if="hasValidationResult"
      :validation-result="workflowStore.displayValidationResult"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- TopPhi相场模拟 -->
    <TopPhiResultCard
      v-if="hasTopPhiResult"
      :topphi-result="workflowStore.displayTopphiResult"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- ML性能预测 -->
    <PerformancePredictionCard
      v-if="hasMlPrediction"
      :prediction="workflowStore.displayPerformancePrediction"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- 历史对比 -->
    <HistoricalComparisonCard
      v-if="hasHistoricalComparison"
      :comparison="workflowStore.displayHistoricalComparison"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- 根因分析 -->
    <IntegratedAnalysisCard
      v-if="hasIntegratedAnalysis"
      :analysis="workflowStore.displayIntegratedAnalysis"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- 优化方案选择器 -->
    <OptimizationSelector
      v-if="workflowStore.showOptimizationSelection"
      :p1-content="workflowStore.displayP1Content"
      :p2-content="workflowStore.displayP2Content"
      :p3-content="workflowStore.displayP3Content"
      :comprehensive-recommendation="workflowStore.displayComprehensiveRecommendation"
      @select="handleOptimizationSelect"
    />
    
    <!-- 实验工单摘要 -->
    <WorkorderSummaryCard
      v-if="hasWorkorder"
      :workorder="workflowStore.displayExperimentWorkorder"
      :selected-optimization="workflowStore.selectedOptimization"
      @download="downloadWorkorder"
      @jump-to-node="handleJumpToNode"
    />
    
    <!-- 实验数据输入 -->
    <ExperimentInputCard
      v-if="workflowStore.showExperimentInput"
      :iteration="workflowStore.currentIteration"
      :historical-best="getHistoricalBest()"
      @submit="handleExperimentSubmit"
      @cancel="handleExperimentCancel"
    />
    
    <!-- 迭代历史 -->
    <IterationHistoryPanel
      v-if="workflowStore.iterationHistory.length > 0"
      :history="workflowStore.iterationHistory"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { ElMessage } from 'element-plus'

// 导入所有卡片组件
import EmptyStateCard from '../cards/EmptyStateCard.vue'
import ValidationSummaryCard from '../cards/ValidationSummaryCard.vue'
import TopPhiResultCard from '../cards/TopPhiResultCard.vue'
import PerformancePredictionCard from '../cards/PerformancePredictionCard.vue'
import HistoricalComparisonCard from '../cards/result/HistoricalComparisonCard.vue'
import IntegratedAnalysisCard from '../cards/result/IntegratedAnalysisCard.vue'
import OptimizationSelector from '../cards/OptimizationSelector.vue'
import WorkorderSummaryCard from '../cards/result/WorkorderSummaryCard.vue'
import ExperimentInputCard from '../experiment/ExperimentInputCard.vue'
import IterationHistoryPanel from '../experiment/IterationHistoryPanel.vue'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['optimization-select', 'jump-to-node', 'experiment-submit'])

const rightPanelRef = ref(null)
const autoScrollEnabled = ref(true)

// ==================== 计算属性 ====================

// 判断是否有任何内容
const hasAnyContent = computed(() => {
  return workflowStore.displayValidationResult ||
         workflowStore.displayTopphiResult ||
         workflowStore.displayPerformancePrediction ||
         workflowStore.displayHistoricalComparison ||
         workflowStore.displayIntegratedAnalysis ||
         workflowStore.showOptimizationSelection ||
         workflowStore.displayExperimentWorkorder ||
         workflowStore.showExperimentInput ||
         workflowStore.iterationHistory.length > 0
})

// 是否有验证结果
const hasValidationResult = computed(() => {
  const step = workflowStore.displayProcessSteps.find(s => s.nodeId === 'input_validation')
  return step && (step.status === 'completed' || step.status === 'error')
})

// 是否有TopPhi结果
const hasTopPhiResult = computed(() => {
  return workflowStore.displayTopphiResult !== null
})

// 是否有ML预测
const hasMlPrediction = computed(() => {
  const step = workflowStore.displayProcessSteps.find(s => s.nodeId === 'ml_prediction')
  return step && step.status === 'completed'
})

// 是否有历史对比
const hasHistoricalComparison = computed(() => {
  return workflowStore.displayHistoricalComparison !== null
})

// 是否有根因分析
const hasIntegratedAnalysis = computed(() => {
  return workflowStore.displayIntegratedAnalysis !== null
})

// 是否有工单
const hasWorkorder = computed(() => {
  const workorder = workflowStore.displayExperimentWorkorder
  const step = workflowStore.displayProcessSteps.find(s => s.nodeId === 'experiment_workorder')
  const hasFinalData = workorder && typeof workorder === 'object'
  const isCompleted = step && step.status === 'completed'
  return hasFinalData && isCompleted
})

// ==================== 事件处理 ====================

// 跳转到节点
const handleJumpToNode = (nodeId) => {
  emit('jump-to-node', nodeId)
}

// 处理优化方案选择
const handleOptimizationSelect = (option) => {
  workflowStore.selectedOptimization = option
  workflowStore.showOptimizationSelection = false
  emit('optimization-select', option)
}

// 处理实验数据提交
const handleExperimentSubmit = (data) => {
  emit('experiment-submit', data)
}

// 取消实验输入
const handleExperimentCancel = () => {
  workflowStore.showExperimentInput = false
}

// 下载工单（生成PDF）
const downloadWorkorder = async () => {
  if (!workflowStore.displayExperimentWorkorder) {
    ElMessage.warning('没有可下载的工单')
    return
  }
  
  try {
    const workorder = workflowStore.displayExperimentWorkorder
    
    // 检查工单数据类型
    if (typeof workorder === 'object' && workorder.content) {
      // 结构化数据：提取字段
      const markdownContent = workorder.content || ''
      const workorderNumber = workorder.workorder_id || workorder.experiment_id || `WO${Date.now()}`
      const solutionName = workorder.solution_name || 'TiAlN涂层优化实验'
      
      // 导入PDF生成器并生成PDF
      const { generateWorkorderPDF } = await import('../../utils/pdfExporter.js')
      const fileName = await generateWorkorderPDF(markdownContent, workorderNumber, solutionName)
      ElMessage.success(`工单已导出为 ${fileName}`)
    } else if (typeof workorder === 'string') {
      // 兼容旧格式：字符串类型
      const { generateWorkorderPDF } = await import('../../utils/pdfExporter.js')
      const fileName = await generateWorkorderPDF(workorder, `WO${Date.now()}`, 'TiAlN涂层优化实验')
      ElMessage.success(`工单已导出为 ${fileName}`)
    } else {
      // 降级方案：下载JSON
      console.warn('[下载工单] 未知的数据格式，降级为JSON下载')
      const content = JSON.stringify(workorder, null, 2)
      const blob = new Blob([content], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `workorder_${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('工单下载成功（JSON格式）')
    }
  } catch (error) {
    console.error('[RightPanel] 下载工单失败:', error)
    ElMessage.error(`下载工单失败: ${error.message}`)
  }
}

// 获取历史最佳结果（按4个核心性能指标返回）
const getHistoricalBest = () => {
  if (workflowStore.currentIteration > 1 && workflowStore.iterationHistory.length > 0) {
    const lastIteration = workflowStore.iterationHistory[workflowStore.iterationHistory.length - 1]
    if (lastIteration && lastIteration.experiment_results) {
      const results = lastIteration.experiment_results
      return {
        hardness: results.hardness,
        elastic_modulus: results.elastic_modulus,
        wear_rate: results.wear_rate,
        adhesion_strength: results.adhesion_strength
      }
    }
  }
  return null
}

// ==================== 自动滚动控制 ====================

// 处理面板滚动
const handlePanelScroll = () => {
  if (!rightPanelRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = rightPanelRef.value
  const nearBottom = scrollHeight - scrollTop - clientHeight < 100
  autoScrollEnabled.value = nearBottom
}

// 滚动到底部
const scrollToBottom = () => {
  if (!rightPanelRef.value || !autoScrollEnabled.value) return
  
  nextTick(() => {
    if (rightPanelRef.value) {
      rightPanelRef.value.scrollTop = rightPanelRef.value.scrollHeight
    }
  })
}

// 监听内容变化，自动滚动
watch(
  () => [
    workflowStore.displayValidationResult,
    workflowStore.displayTopphiResult,
    workflowStore.displayPerformancePrediction,
    workflowStore.displayHistoricalComparison,
    workflowStore.displayIntegratedAnalysis,
    workflowStore.displayP1Content,
    workflowStore.displayP2Content,
    workflowStore.displayP3Content,
    workflowStore.displayExperimentWorkorder,
    workflowStore.showExperimentInput
  ],
  () => {
    scrollToBottom()
  },
  { deep: true }
)
</script>

<style scoped>
.right-panel {
  min-width: 350px;
  max-width: 1100px;
  background: var(--bg-secondary);
  padding: 20px;
  overflow-y: auto;
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 滚动条样式 */
.right-panel::-webkit-scrollbar {
  width: 8px;
}

.right-panel::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.right-panel::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
  transition: background 0.2s;
}

.right-panel::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>
