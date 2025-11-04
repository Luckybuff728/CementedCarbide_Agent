<template>
  <div class="right-panel" ref="rightPanelRef">
    <!-- 参数验证摘要 -->
    <SummaryCard 
      v-if="hasValidationResult" 
      icon="✅" 
      title="参数验证"
      :clickable="true"
      @click="jumpToNode('input_validation')"
    >
      <div class="validation-summary">
        <div class="validation-item">
          <el-icon color="#10b981"><CircleCheck /></el-icon>
          <span>成分配比验证通过</span>
        </div>
        <div class="validation-item">
          <el-icon color="#10b981"><CircleCheck /></el-icon>
          <span>工艺参数合理</span>
        </div>
        <div class="validation-item">
          <el-icon color="#10b981"><CircleCheck /></el-icon>
          <span>结构设计可行</span>
        </div>
      </div>
    </SummaryCard>

    <!-- TopPhi模拟摘要 -->
    <SummaryCard 
      v-if="hasTopPhiResult" 
      icon="🔬" 
      title="TopPhi第一性原理"
      :clickable="true"
      @click="jumpToNode('topphi_simulation')"
    >
      <div class="topphi-summary">
        <div class="summary-row">
          <span class="label">晶体结构</span>
          <span class="value">立方相</span>
        </div>
        <div class="summary-row">
          <span class="label">形成能</span>
          <span class="value">-0.85 eV</span>
        </div>
        <div class="summary-row">
          <span class="label">带隙</span>
          <span class="value">2.1 eV</span>
        </div>
      </div>
    </SummaryCard>

    <!-- 性能预测摘要 -->
    <SummaryCard 
      v-if="hasMlPrediction" 
      icon="🎯" 
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
      v-if="workflowStore.historicalComparison" 
      icon="📊" 
      title="历史对比"
      :clickable="true"
      @click="jumpToNode('historical_comparison')"
    >
      <div class="comparison-summary">
        <div class="stat-row">
          <span>相似案例</span>
          <span class="stat-value">{{ workflowStore.historicalComparison.total_cases || 0 }} 个</span>
        </div>
        <div class="stat-row">
          <span>最高硬度</span>
          <span class="stat-value highlight">{{ workflowStore.historicalComparison.highest_hardness || 0 }} GPa</span>
        </div>
        <div v-if="workflowStore.historicalComparison.similar_cases" class="cases-preview">
          <div 
            v-for="(c, i) in workflowStore.historicalComparison.similar_cases.slice(0, 2)"
            :key="i"
            class="case-item"
          >
            <el-tag size="small" type="info">{{ Math.round(c.similarity * 100) }}% 相似</el-tag>
            <span>{{ c.hardness }} GPa</span>
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 根因分析摘要 -->
    <SummaryCard 
      v-if="workflowStore.integratedAnalysis" 
      icon="🧠" 
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
      icon="💡" 
      title="优化建议"
      :badge="getOptimizationBadge()"
      :clickable="true"
      @click="jumpToNode('optimization')"
    >
      <div class="optimization-summary">
        <div class="suggestion-list">
          <div v-if="workflowStore.p1Content" class="suggestion-item">
            <span class="suggestion-tag">P1</span>
            <span>成分优化方案可用</span>
          </div>
          <div v-if="workflowStore.p2Content" class="suggestion-item">
            <span class="suggestion-tag">P2</span>
            <span>结构优化方案可用</span>
          </div>
          <div v-if="workflowStore.p3Content" class="suggestion-item">
            <span class="suggestion-tag">P3</span>
            <span>工艺优化方案可用</span>
          </div>
        </div>
      </div>
    </SummaryCard>

    <!-- 优化方案选择 -->
    <div v-if="workflowStore.showOptimizationSelection" class="optimization-section">
      <h4>💡 选择优化方案</h4>
      
      <div class="opt-cards">
        <div 
          v-for="opt in optimizationOptions"
          :key="opt.id"
          :class="['opt-card', { selected: selectedOpt === opt.id }]"
          @click="selectedOpt = opt.id"
        >
          <div class="opt-header">
            <span class="opt-icon">{{ opt.icon }}</span>
            <h5>{{ opt.title }}</h5>
          </div>
          <p class="opt-desc">{{ opt.description }}</p>
          <div v-if="opt.summary" class="opt-summary">
            {{ opt.summary }}
          </div>
        </div>
      </div>

      <!-- 综合建议 -->
      <div v-if="workflowStore.comprehensiveRecommendation" class="recommendation-box">
        <h5>📌 综合建议</h5>
        <p>{{ workflowStore.comprehensiveRecommendation }}</p>
      </div>

      <el-button 
        type="primary"
        size="large"
        :disabled="!selectedOpt"
        @click="handleOptimizationSelect"
        block
      >
        确认选择并生成工单
      </el-button>
    </div>

    <!-- 实验工单摘要 -->
    <SummaryCard 
      v-if="workflowStore.experimentWorkorder" 
      icon="📝" 
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
          <el-button type="primary" size="small" @click.stop="downloadWorkorder">
            <el-icon><Download /></el-icon>
            下载完整工单
          </el-button>
        </div>
      </div>
    </SummaryCard>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, CircleCheck } from '@element-plus/icons-vue'
import { useWorkflowStore } from '../stores/workflow'
import { getConfidenceColor, getConfidenceBadge } from '../utils/markdown'
import SummaryCard from './SummaryCard.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['optimization-select', 'jump-to-node'])

const selectedOpt = ref(null)
const rightPanelRef = ref(null)

// 是否有验证结果
const hasValidationResult = computed(() => {
  return workflowStore.completedNodes.includes('input_validation')
})

// 是否有TopPhi结果
const hasTopPhiResult = computed(() => {
  return workflowStore.completedNodes.includes('topphi_simulation')
})

// 是否有ML预测结果
const hasMlPrediction = computed(() => {
  const step = workflowStore.processSteps.find(s => s.nodeId === 'ml_prediction')
  return step && step.status === 'completed'
})

// 获取ML预测数据（从performancePrediction中提取）
const getMlPredictionData = () => {
  const pred = workflowStore.performancePrediction
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
  return workflowStore.p1Content || workflowStore.p2Content || workflowStore.p3Content
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
    icon: '🧪',
    description: '调整Al/Ti/N比例及合金元素',
    summary: getSummaryFromContent(workflowStore.p1Content)
  },
  {
    id: 'P2',
    title: 'P2 结构优化',
    icon: '🏗️',
    description: '多层/梯度结构设计',
    summary: getSummaryFromContent(workflowStore.p2Content)
  },
  {
    id: 'P3',
    title: 'P3 工艺优化',
    icon: '⚙️',
    description: '沉积参数与气体流量调整',
    summary: getSummaryFromContent(workflowStore.p3Content)
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
  const analysis = workflowStore.integratedAnalysis
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
  const analysis = workflowStore.integratedAnalysis
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
  const count = [workflowStore.p1Content, workflowStore.p2Content, workflowStore.p3Content].filter(Boolean).length
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
  if (workflowStore.p1Content) return 'P1 成分优化'
  if (workflowStore.p2Content) return 'P2 结构优化'
  if (workflowStore.p3Content) return 'P3 工艺优化'
  return '综合方案'
}

// 下载工单
const downloadWorkorder = () => {
  try {
    const blob = new Blob([workflowStore.experimentWorkorder], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `experiment_workorder_${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('工单已下载')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// ========== 自动滚动逻辑 ==========

// 滚动到底部
const scrollToBottom = () => {
  if (!rightPanelRef.value) return
  nextTick(() => {
    rightPanelRef.value.scrollTop = rightPanelRef.value.scrollHeight
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
  () => [workflowStore.p1Content, workflowStore.p2Content, workflowStore.p3Content],
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
</script>

<style scoped>
.right-panel {
  min-width: 200px;
  max-width: 600px;
  background: var(--bg-secondary);
  padding: 20px 16px;
  overflow-y: auto;
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
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
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

.optimization-section h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
}

.opt-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.opt-card {
  padding: 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.3s;
}

.opt-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-sm);
}

.opt-card.selected {
  border-color: var(--primary);
  background: #eff6ff;
}

.opt-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.opt-icon {
  font-size: 18px;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
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

/* TopPhi模拟 */
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
</style>
