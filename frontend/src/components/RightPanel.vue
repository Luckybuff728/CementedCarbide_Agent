<template>
  <div class="right-panel" ref="rightPanelRef" @scroll="handlePanelScroll">
    <!-- 空状态展示 -->
    <div v-if="!hasAnyContent" class="empty-state">
      <div class="empty-icon">
        <n-icon :component="RocketOutline" />
      </div>
      <h3 class="empty-title">准备开始分析</h3>
      <p class="empty-description">
        在左侧面板输入涂层参数，点击「开始分析」按钮<br />
        系统将为您提供全面的性能预测和优化建议
      </p>
      <div class="empty-features">
        <div class="feature-item">
          <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
          <span>参数验证与可行性分析</span>
        </div>
        <div class="feature-item">
          <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
          <span>相场模拟</span>
        </div>
        <div class="feature-item">
          <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
          <span>AI性能预测与历史对比</span>
        </div>
        <div class="feature-item">
          <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
          <span>智能优化建议与实验工单</span>
        </div>
      </div>
    </div>

    <!-- 参数验证摘要 -->
    <SummaryCard 
      v-if="hasValidationResult" 
      icon=""
      :icon-component="getValidationIcon"
      title="参数验证"
      :clickable="true"
      @click="jumpToNode('input_validation')"
    >
      <div class="validation-summary">
        <template v-if="isValidationSuccess">
          <div class="validation-item success">
            <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
            <span>成分配比验证通过</span>
          </div>
          <div class="validation-item success">
            <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
            <span>工艺参数合理</span>
          </div>
          <div class="validation-item success">
            <n-icon :component="CheckmarkCircleOutline" color="#10b981" />
            <span>结构设计可行</span>
          </div>
        </template>
        <template v-else>
          <div class="validation-item error">
            <n-icon :component="CloseCircleOutline" color="#ef4444" />
            <span>参数验证失败</span>
          </div>
          <div class="validation-errors">
            <div 
              v-for="(error, index) in getValidationErrors()" 
              :key="index"
              class="error-message"
            >
              {{ error }}
            </div>
          </div>
          <div class="validation-hint error-hint">
            点击查看详细分析
          </div>
        </template>
      </div>
    </SummaryCard>

    <!-- 相场模拟摘要 -->
    <SummaryCard 
      v-if="hasTopPhiResult" 
      icon=""
      :icon-component="FlaskOutline"
      title="TopPhi相场模拟"
      :clickable="false"
    >
      <div class="topphi-content">
        <!-- 文本摘要 -->

        
        <!-- VTK可视化 -->
        <div v-if="topPhiVtkData" class="vtk-visualization">
          <!-- 时间序列播放器 -->
          <VtkTimeSeriesViewer
            v-if="isTimeSeries && timeSeriesFiles.length > 0"
            :time-series-files="timeSeriesFiles"
            :base-url="apiBaseUrl"
            height="450px"
            :auto-play="false"
          />
          
          <!-- 单帧查看器 -->
          <VtkViewer
            v-else-if="!isTimeSeries"
            :vtk-data="topPhiVtkData"
            :base-url="apiBaseUrl"
            height="450px"
            render-mode="volume"
          />
          
          <!-- 加载时间序列中 -->
          <div v-else-if="isTimeSeries && loadingTimeSeries" class="loading-timeseries">
            <n-icon class="is-loading" :component="ReloadOutline" size="40" />
            <span>加载时间序列数据...</span>
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 性能预测摘要 -->
    <SummaryCard 
      v-if="hasMlPrediction" 
      icon=""
      :icon-component="RadioButtonOnOutline"
      title="性能预测"
      :badge="getMlConfidenceBadge()"
      :clickable="true"
      @click="jumpToNode('ml_prediction')"
    >
      <div class="prediction-summary">
        <div class="key-metric">
          <span class="metric-label">预测硬度</span>
          <span class="metric-value highlight">
            {{ getMlPredictionData().hardness }} GPa
          </span>
        </div>
        <div class="metrics-grid">
          <div class="metric-item">
            <span>结合力</span>
            <span>{{ getMlPredictionData().adhesion }}</span>
          </div>
          <div class="metric-item">
            <span>氧化温度</span>
            <span>{{ getMlPredictionData().oxidation }}°C</span>
          </div>
        </div>
        <div class="metric-item" style="margin-top: 8px;">
          <span>模型置信度</span>
          <el-progress 
            :percentage="getMlPredictionData().confidence"
            :color="getConfidenceColor(getMlPredictionData().confidence / 100)"
            :stroke-width="8"
          />
        </div>
      </div>
    </SummaryCard>

    <!-- 历史对比摘要 -->
    <SummaryCard 
      v-if="workflowStore.displayHistoricalComparison" 
      icon=""
      :icon-component="BarChartOutline"
      title="历史对比"
      :clickable="true"
      @click="jumpToNode('historical_comparison')"
    >
      <div class="comparison-summary">
        <div class="stat-row">
          <span>相似案例</span>
          <span class="stat-value">{{ workflowStore.displayHistoricalComparison.total_cases || 0 }} 个</span>
        </div>
        <div class="stat-row">
          <span>最高硬度</span>
          <span class="stat-value highlight">{{ workflowStore.displayHistoricalComparison.highest_hardness || 0 }} GPa</span>
        </div>
        <div v-if="workflowStore.displayHistoricalComparison.similar_cases" class="cases-preview">
          <div 
            v-for="(c, i) in workflowStore.displayHistoricalComparison.similar_cases.slice(0, 2)"
            :key="i"
            class="case-item"
          >
            <n-tag size="small" type="info">{{ Math.round(c.similarity * 100) }}% 相似</n-tag>
            <span>{{ c.hardness }} GPa</span>
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 根因分析摘要 -->
    <SummaryCard 
      v-if="workflowStore.displayIntegratedAnalysis" 
      icon=""
      :icon-component="BulbOutline"
      title="根因分析"
      :clickable="true"
      @click="jumpToNode('integrated_analysis')"
    >
      <div class="analysis-summary">
        <div class="analysis-section">
          <div class="section-title">综合评价</div>
          <div class="summary-text">
            {{ getRootCauseAnalysisSummary() }}
          </div>
        </div>
        <div v-if="getRecommendation()" class="analysis-section">
          <div class="section-title">优化建议</div>
          <div class="recommendation-text">
            {{ getRecommendation() }}
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 优化建议摘要 -->
    <SummaryCard 
      v-if="hasOptimizationSuggestions" 
      icon=""
      :icon-component="BulbOutline"
      title="优化建议"
      :badge="getOptimizationBadge()"
      :clickable="true"
      @click="jumpToNode('optimization')"
    >
      <div class="optimization-summary">
        <div class="suggestion-list">
          <div v-if="workflowStore.displayP1Content" class="suggestion-item">
            <span class="suggestion-tag">P1</span>
            <span>成分优化方案可用</span>
          </div>
          <div v-if="workflowStore.displayP2Content" class="suggestion-item">
            <span class="suggestion-tag">P2</span>
            <span>结构优化方案可用</span>
          </div>
          <div v-if="workflowStore.displayP3Content" class="suggestion-item">
            <span class="suggestion-tag">P3</span>
            <span>工艺优化方案可用</span>
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 优化方案选择 -->
    <div v-if="workflowStore.showOptimizationSelection" class="optimization-section">
      <div class="section-header">
        <n-icon :component="BulbOutline" />
        <h4>选择优化方案</h4>
      </div>
      
      <div class="opt-cards">
        <div 
          v-for="opt in optimizationOptions"
          :key="opt.id"
          :class="['opt-card', { selected: selectedOpt === opt.id }]"
          @click="selectedOpt = opt.id"
        >
          <div class="opt-header">
            <n-icon class="opt-icon" :component="opt.iconComponent" />
            <h5>{{ opt.title }}</h5>
          </div>
          <p class="opt-desc">{{ opt.description }}</p>
          <div v-if="opt.summary" class="opt-summary">
            {{ opt.summary }}
          </div>
        </div>
      </div>

      <!-- 综合建议 -->
      <div v-if="workflowStore.displayComprehensiveRecommendation" class="recommendation-box">
        <h5>📌 综合建议</h5>
        <p>{{ workflowStore.displayComprehensiveRecommendation }}</p>
      </div>

      <n-button 
        type="primary"
        size="large"
        :disabled="!selectedOpt"
        @click="handleOptimizationSelect"
        block
      >
        确认选择并生成工单
      </n-button>
    </div>

    <!-- 实验工单摘要 -->
    <SummaryCard 
      v-if="workflowStore.displayExperimentWorkorder" 
      icon=""
      :icon-component="DocumentTextOutline"
      title="实验工单"
      :clickable="true"
      @click="jumpToNode('experiment_workorder')"
    >
      <div class="workorder-summary">
        <div class="summary-row">
          <span class="label">工单编号</span>
          <span class="value">{{ getWorkorderNumber() }}</span>
        </div>
        <div class="summary-row">
          <span class="label">实验目标</span>
          <span class="value">AlTiN涂层性能优化</span>
        </div>
        <div class="summary-row">
          <span class="label">优化方案</span>
          <span class="value">{{ getSelectedPlan() }}</span>
        </div>
        <div class="workorder-actions">
          <n-button type="primary" size="small" @click.stop="downloadWorkorder">
            <template #icon>
              <n-icon :component="DownloadOutline" />
            </template>
            下载完整工单
          </n-button>
        </div>
      </div>
    </SummaryCard>
    
    <!-- 实验数据输入 -->
    <ExperimentInputCard
      v-if="workflowStore.showExperimentInput"
      :iteration="workflowStore.currentIteration"
      :historicalBest="getHistoricalBest()"
      :targetHardness="30"
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
import { useMessage } from 'naive-ui'
import { ElMessage } from 'element-plus'
import { NButton, NIcon } from 'naive-ui'
import {
  DownloadOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  FlaskOutline,
  RadioButtonOnOutline,
  BarChartOutline,
  BulbOutline,
  DocumentTextOutline,
  BuildOutline,
  LayersOutline,
  SettingsOutline,
  RocketOutline,
  ReloadOutline
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../stores/workflow'
import { getConfidenceColor, getConfidenceBadge } from '../utils/markdown'
import { API_BASE_URL } from '../config'
import SummaryCard from './SummaryCard.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import ExperimentInputCard from './ExperimentInputCard.vue'
import IterationHistoryPanel from './IterationHistoryPanel.vue'
import VtkTimeSeriesViewer from './VtkTimeSeriesViewer.vue'
import VtkViewer from './VtkViewer.vue'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['optimization-select', 'jump-to-node', 'experiment-submit'])

const selectedOpt = ref(null)
const rightPanelRef = ref(null)

// API基础URL - 从配置文件读取
const apiBaseUrl = ref(API_BASE_URL)

// 时间序列文件列表
const timeSeriesFiles = ref([])
const loadingTimeSeries = ref(false)

// 获取相场模拟节点的VTK数据
const topPhiVtkData = computed(() => {
  // 从store中获取相场模拟结果
  const topPhiResult = workflowStore.displayTopphiResult
  if (!topPhiResult || !topPhiResult.vtk_data) return null
  return topPhiResult.vtk_data
})

// 判断是否为时间序列
const isTimeSeries = computed(() => {
  return topPhiVtkData.value?.type === 'timeseries'
})

// 监听时间序列数据变化，自动获取文件列表
watch(
  () => [isTimeSeries.value, topPhiVtkData.value?.folder, workflowStore.viewMode],
  async ([isTS, folder, viewMode]) => {
    console.log('[RightPanel] 监听触发 - isTimeSeries:', isTS, 'folder:', folder, 'viewMode:', viewMode)
    
    // 如果不是时间序列，清空数据
    if (!isTS) {
      timeSeriesFiles.value = []
      return
    }
    
    // 如果是时间序列且有文件夹，加载文件列表
    if (isTS && folder) {
      loadingTimeSeries.value = true
      try {
        const response = await fetch(`${apiBaseUrl.value}/api/vtk/timeseries/${folder}`)
        if (response.ok) {
          const data = await response.json()
          timeSeriesFiles.value = data.files
          console.log('[RightPanel] 时间序列文件加载成功:', data.files.length, '帧')
        } else {
          console.error('[RightPanel] 获取时间序列列表失败:', response.statusText)
        }
      } catch (err) {
        console.error('[RightPanel] 获取时间序列列表出错:', err)
      } finally {
        loadingTimeSeries.value = false
      }
    }
  },
  { immediate: true }
)

// 是否有任何内容
const hasAnyContent = computed(() => {
  return workflowStore.displayPerformancePrediction ||
         workflowStore.displayHistoricalComparison ||
         workflowStore.displayIntegratedAnalysis ||
         hasOptimizationSuggestions.value ||
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

// 判断验证是否成功（计算属性，自动缓存结果）
const isValidationSuccess = computed(() => {
  // 使用displayValidationResult支持历史查看
  const validationResult = workflowStore.displayValidationResult
  if (validationResult) {
    const isSuccess = validationResult.input_validated === true
    // 只在开发模式下输出调试日志
    if (import.meta.env.DEV) {
      console.log('[🔍 验证状态] input_validated=', validationResult.input_validated, '→', isSuccess)
    }
    return isSuccess
  }
  
  // 降级方案：如果没有validationResult，假设通过
  return true
})

// 获取验证图标（改为计算属性）
const getValidationIcon = computed(() => {
  return isValidationSuccess.value ? CheckmarkCircleOutline : CloseCircleOutline
})

// 获取验证错误信息
const getValidationErrors = () => {
  // 使用displayValidationResult支持历史查看
  const validationResult = workflowStore.displayValidationResult
  if (!validationResult) return []
  const errors = validationResult.validation_errors || []
  
  // 提取错误文本，去除Markdown标记
  return errors.map(err => {
    // 移除 **❌ 发现问题**： 前缀
    let text = err.replace(/\*\*❌\s*发现问题\*\*[：:]\s*/g, '')
    // 移除其他Markdown标记
    text = text.replace(/[*_`#]/g, '')
    return text.trim()
  }).filter(Boolean)
}

// 是否有TopPhi结果（支持历史查看）
const hasTopPhiResult = computed(() => {
  // 使用displayTopphiResult，它会自动根据查看模式切换数据源
  return workflowStore.displayTopphiResult !== null
})

// 是否有ML预测结果
const hasMlPrediction = computed(() => {
  const step = workflowStore.displayProcessSteps.find(s => s.nodeId === 'ml_prediction')
  return step && step.status === 'completed'
})

// 获取ML预测数据（从performancePrediction中提取）
const getMlPredictionData = () => {
  const pred = workflowStore.displayPerformancePrediction
  if (!pred) return { hardness: 'N/A', adhesion: 'N/A', oxidation: 'N/A', confidence: 0 }
  
  return {
    hardness: pred.hardness || pred.hardness_gpa || 'N/A',
    adhesion: pred.adhesion_level || 'N/A',
    oxidation: pred.oxidation_temperature || pred.oxidation_temp_c || 'N/A',
    confidence: Math.round((pred.confidence_score || pred.model_confidence || 0) * 100)
  }
}

// 获取ML置信度徽章
const getMlConfidenceBadge = () => {
  const confidence = getMlPredictionData().confidence
  if (confidence >= 80) {
    return { text: '高置信度', type: 'success' }
  } else if (confidence >= 60) {
    return { text: '中等置信度', type: 'warning' }
  } else {
    return { text: '低置信度', type: 'danger' }
  }
}

// 是否有优化建议
const hasOptimizationSuggestions = computed(() => {
  return workflowStore.displayP1Content || workflowStore.displayP2Content || workflowStore.displayP3Content
})

// 总节点数
const totalNodes = computed(() => {
  return 7 // 验证、TopPhi、ML、历史、分析、优化、工单
})

// 优化方案配置
const optimizationOptions = computed(() => [
  {
    id: 'P1',
    title: 'P1 成分优化',
    iconComponent: FlaskOutline,
    description: '调整Al/Ti/N比例及合金元素',
    summary: getSummaryFromContent(workflowStore.displayP1Content)
  },
  {
    id: 'P2',
    title: 'P2 结构优化',
    iconComponent: BuildOutline,
    description: '多层/梯度结构设计',
    summary: getSummaryFromContent(workflowStore.displayP2Content)
  },
  {
    id: 'P3',
    title: 'P3 工艺优化',
    iconComponent: LayersOutline,
    description: '沉积温度/偏压/气氛优化',
    summary: getSummaryFromContent(workflowStore.displayP3Content)
  }
])

// 获取当前状态
const getCurrentStatus = () => {
  if (workflowStore.isProcessing) return '处理中'
  if (workflowStore.showOptimizationSelection) return '等待选择'
  if (workflowStore.experimentWorkorder) return '已完成'
  return '就绪'
}

// 获取状态标签类型
const getStatusTagType = () => {
  if (workflowStore.isProcessing) return 'warning'
  if (workflowStore.experimentWorkorder) return 'success'
  return 'info'
}

// 从内容中提取摘要（取前100字符）
const getSummaryFromContent = (content) => {
  if (!content) return ''
  const text = content.replace(/[#*`\n]/g, '').trim()
  return text.length > 80 ? text.substring(0, 80) + '...' : text
}

// 获取根因分析摘要（从root_cause_analysis提取前200字符）
const getRootCauseAnalysisSummary = () => {
  const analysis = workflowStore.displayIntegratedAnalysis
  if (!analysis) return '暂无分析结果'
  
  // 优先从root_cause_analysis提取
  let content = analysis.root_cause_analysis || ''
  
  // 如果没有，尝试从performance_summary提取
  if (!content && analysis.performance_summary) {
    const summary = analysis.performance_summary
    content = `预测硬度${summary.predicted_hardness}GPa，置信度${(summary.confidence * 100).toFixed(0)}%。`
  }
  
  // 提取前200字符作为摘要
  if (content.length > 200) {
    // 移除Markdown标记
    content = content.replace(/[#*`\n]/g, ' ').trim()
    return content.substring(0, 200) + '...'
  }
  
  return content || '分析完成，数据已就绪'
}

// 获取优化建议（从recommendation提取）
const getRecommendation = () => {
  const analysis = workflowStore.displayIntegratedAnalysis
  if (!analysis) return ''
  
  const rec = analysis.recommendation
  if (!rec) return ''
  
  // 提取前150字符
  if (rec.length > 150) {
    return rec.replace(/[#*`\n]/g, ' ').trim().substring(0, 150) + '...'
  }
  
  return rec
}

// 获取优化建议徽章
const getOptimizationBadge = () => {
  const count = [workflowStore.displayP1Content, workflowStore.displayP2Content, workflowStore.displayP3Content].filter(Boolean).length
  if (count === 0) return null
  return {
    text: `${count}个方案`,
    type: 'success'
  }
}

// 跳转到节点
const jumpToNode = (nodeId) => {
  emit('jump-to-node', nodeId)
}

// 处理优化方案选择
const handleOptimizationSelect = () => {
  if (!selectedOpt.value) return
  emit('optimization-select', selectedOpt.value)
}

// 获取工单编号
const getWorkorderNumber = () => {
  const date = new Date().toISOString().split('T')[0].replace(/-/g, '')
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
  return `WO-${date}-${random}`
}

// 获取选择的方案
const getSelectedPlan = () => {
  if (selectedOpt.value) {
    return selectedOpt.value
  }
  // 从内容中推断
  if (workflowStore.displayP1Content) return 'P1 成分优化'
  if (workflowStore.displayP2Content) return 'P2 结构优化'
  if (workflowStore.displayP3Content) return 'P3 工艺优化'
  return '综合方案'
}

// 下载工单
const downloadWorkorder = () => {
  const content = workflowStore.displayExperimentWorkorder
  if (!content) {
    ElMessage.warning('没有工单内容')
    return
  }
  
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `experiment_workorder_${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
  
  message.success('工单已下载')
}

// 获取历史最优数据
const getHistoricalBest = () => {
  // 第2轮及以后：使用上一轮的实验数据作为参考
  if (workflowStore.currentIteration > 1 && workflowStore.iterationHistory.length > 0) {
    const lastIteration = workflowStore.iterationHistory[workflowStore.iterationHistory.length - 1]
    if (lastIteration && lastIteration.experiment_results) {
      return {
        hardness: lastIteration.experiment_results.hardness,
        adhesion_strength: lastIteration.experiment_results.adhesion_strength,
        oxidation_temperature: lastIteration.experiment_results.oxidation_temperature
      }
    }
  }
  
  // 第1轮：使用历史数据库中的案例作为参考
  if (!workflowStore.displayHistoricalComparison?.similar_cases) return null
  const cases = workflowStore.displayHistoricalComparison.similar_cases
  if (cases.length === 0) return null
  return cases[0] // 返回硬度最高的案例
}

// 处理实验数据提交
const handleExperimentSubmit = (data) => {
  emit('experiment-submit', data)
}

// 处理取消
const handleExperimentCancel = () => {
  workflowStore.showExperimentInput = false
}

// ========== 自动滚动逻辑 ==========

// 自动滚动控制标志
const autoScrollEnabled = ref(true)

// 检测面板是否在底部附近
const isPanelNearBottom = () => {
  if (!rightPanelRef.value) return false
  const { scrollTop, scrollHeight, clientHeight } = rightPanelRef.value
  return scrollHeight - scrollTop - clientHeight < 100  // 距离底部小于100px
}

// 处理面板滚动事件（用户手动滚动时触发）
const handlePanelScroll = () => {
  if (!rightPanelRef.value) return
  
  const nearBottom = isPanelNearBottom()
  
  // 用户离开底部，立即暂停自动滚动
  if (!nearBottom) {
    autoScrollEnabled.value = false
  } else {
    // 用户滚动到底部附近，恢复自动滚动
    autoScrollEnabled.value = true
  }
}

// 滚动到底部（只在启用自动滚动时执行）
const scrollToBottom = () => {
  if (!rightPanelRef.value || !autoScrollEnabled.value) return
  nextTick(() => {
    if (rightPanelRef.value) {
      rightPanelRef.value.scrollTop = rightPanelRef.value.scrollHeight
    }
  })
}

// 监听已完成节点变化，自动滚动到底部
watch(
  () => workflowStore.completedNodes.length,
  () => {
    scrollToBottom()
  }
)

// 监听优化内容变化，自动滚动
watch(
  () => [workflowStore.displayP1Content, workflowStore.displayP2Content, workflowStore.displayP3Content],
  () => {
    scrollToBottom()
  }
)

// 监听实验工单生成，自动滚动
watch(
  () => workflowStore.experimentWorkorder,
  (newVal) => {
    if (newVal) {
      scrollToBottom()
    }
  }
)

// 监听优化方案选择显示状态，自动滚动到底部
watch(
  () => workflowStore.showOptimizationSelection,
  (newVal) => {
    if (newVal) {
      // 新内容出现时，恢复自动滚动并滚动到底部
      autoScrollEnabled.value = true
      scrollToBottom()
    }
  }
)

// 监听实验输入显示状态，自动滚动到底部
watch(
  () => workflowStore.showExperimentInput,
  (newVal) => {
    if (newVal) {
      // 新内容出现时，恢复自动滚动并滚动到底部
      autoScrollEnabled.value = true
      scrollToBottom()
    }
  }
)
</script>

<style scoped>
.right-panel {
  min-width: 600px;
  max-width: 1000px;
  background: var(--bg-secondary);
  padding: 20px;
  overflow-y: auto;
  border-left: 1px solid var(--border-color);
}

/* 任务总览 */
.overview-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 性能预测 */
.prediction-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.key-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
}

.metric-value.highlight {
  color: var(--primary);
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.metric-item span:first-child {
  color: var(--text-secondary);
}

.metric-item span:last-child {
  font-weight: 600;
}

/* 历史对比 */
.comparison-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.stat-row .stat-value.highlight {
  color: var(--primary);
  font-weight: 600;
}

.cases-preview {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.case-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

/* 根因分析 */
.analysis-summary {
  font-size: 13px;
}

.analysis-section {
  margin-bottom: 12px;
}

.analysis-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.summary-text,
.recommendation-text {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.recommendation-text {
  color: var(--primary);
  font-weight: 500;
}

/* 优化方案选择 */
.optimization-section {
  background: white;
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.section-header .n-icon {
  font-size: 20px;
  color: var(--warning);
}

.optimization-section h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.opt-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.opt-card {
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.opt-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.opt-card.selected {
  border-color: var(--primary);
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}

.opt-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.opt-icon {
  font-size: 22px;
  color: var(--primary);
}

.opt-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.opt-desc {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.opt-summary {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

/* 实验工单摘要 */
.workorder-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workorder-summary .summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
  font-size: 13px;
}

.workorder-summary .summary-row:last-of-type {
  border-bottom: none;
}

.workorder-summary .label {
  color: var(--text-secondary);
  font-weight: 500;
}

.workorder-summary .value {
  color: var(--text-primary);
  font-weight: 600;
}

.workorder-actions {
  margin-top: 8px;
}

/* 综合建议 */
.recommendation-box {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.recommendation-box h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.recommendation-box p {
  margin: 0;
  line-height: 1.6;
  font-size: 13px;
}

/* 工单内容 */
.workorder-content {
  font-size: 13px;
}

.workorder-actions {
  margin-top: 12px;
}

/* 参数验证 */
.validation-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.validation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.validation-item.success {
  color: var(--success);
}

.validation-item.error {
  color: #ef4444;
  font-weight: 500;
}

.validation-hint {
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  margin-top: 4px;
}

.validation-errors {
  margin-top: 8px;
  padding: 0;
}

.error-message {
  font-size: 12px;
  color: #ef4444;
  padding: 6px 10px;
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  margin-bottom: 6px;
  border-radius: 4px;
  line-height: 1.5;
}

.error-message:last-child {
  margin-bottom: 0;
}

.error-hint {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

/* 相场模拟 */
.topphi-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.topphi-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.summary-row .label {
  color: var(--text-secondary);
}

.summary-row .value {
  font-weight: 600;
}

/* VTK可视化 */
.vtk-visualization {
  margin-top: 12px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #1a1a1a;
}

.loading-timeseries {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
  color: #fff;
  font-size: 14px;
}

.loading-timeseries .el-icon {
  color: #67c23a;
}

/* 优化建议 */
.optimization-summary {
  font-size: 13px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.suggestion-tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--primary);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  min-height: 400px;
}

.empty-icon-wrapper {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  box-shadow: 0 12px 32px rgba(37, 99, 235, 0.25);
  animation: float 3s ease-in-out infinite;
}

.empty-icon .n-icon {
  font-size: 48px;
  color: white;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
    box-shadow: 0 12px 32px rgba(37, 99, 235, 0.25);
  }
  50% {
    transform: translateY(-10px);
    box-shadow: 0 16px 40px rgba(37, 99, 235, 0.35);
  }
}

.empty-title {
  margin: 0 0 12px 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.empty-description {
  margin: 0 0 36px 0;
  font-size: 15px;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
}

.empty-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 300px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: white;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--transition-base);
}

.feature-item:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
  background: var(--primary-lighter);
}

.feature-item .n-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.feature-item span {
  text-align: left;
  line-height: 1.5;
  font-weight: 500;
}
</style>
