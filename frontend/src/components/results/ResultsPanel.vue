<template>
  <div class="results-panel">
    <div class="results-header">
      <h3>分析结果</h3>
      <el-button text @click="clearResults" v-if="results.length > 0">
        <component :is="Icon" :component="CloseCircleOutline" :size="16" />
        清空
      </el-button>
    </div>
    
    <div class="results-content" ref="resultsContainer">
      <div v-if="results.length === 0" class="empty-state">
        <component :is="Icon" :component="DocumentTextOutline" :size="48" />
        <p>等待分析结果...</p>
      </div>
      
      <div v-else class="results-list">
        <div
          v-for="result in results"
          :key="result.id"
          class="result-card"
          :class="`result-${result.type}`"
        >
          <!-- 验证结果 -->
          <div v-if="result.type === 'validation'" class="result-validation">
            <div class="result-header">
              <component :is="Icon" :component="CheckmarkCircleOutline" :size="20" />
              <h4>参数验证</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <ValidationSummaryCard :validation-result="result.data" :show-header="false" />
          </div>
          
          <!-- TopPhi相场模拟结果（包含VTK可视化） -->
          <div v-if="result.type === 'topphi'" class="result-topphi">
            <div class="result-header">
              <component :is="Icon" :component="PlanetOutline" :size="20" />
              <h4>TopPhi相场模拟</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- 使用完整的TopPhiResultCard组件，包含VTK可视化 -->
            <TopPhiResultCard :result="result" />
          </div>
          
          <!-- 性能预测结果 -->
          <div v-if="result.type === 'performance'" class="result-performance">
            <div class="result-header">
              <component :is="Icon" :component="SpeedometerOutline" :size="20" />
              <h4>性能预测</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <PerformancePredictionCard :prediction="result.data" :show-header="false" />
          </div>
          
          <!-- 历史对比结果 -->
          <div v-if="result.type === 'historical'" class="result-historical">
            <div class="result-header">
              <component :is="Icon" :component="TimeOutline" :size="20" />
              <h4>历史案例对比</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <div class="result-content-box">
              <div class="result-item">
                <span class="label">相似案例数：</span>
                <span class="value">{{ result.data.total_cases || 0 }} 个</span>
              </div>
              <div v-if="result.data.similar_cases && result.data.similar_cases.length > 0" class="historical-cases">
                <div v-for="(caseItem, idx) in result.data.similar_cases.slice(0, 3)" :key="idx" class="case-item">
                  <div class="case-header">案例 {{ idx + 1 }} (相似度: {{ (caseItem.similarity * 100).toFixed(1) }}%)</div>
                  <div class="case-detail">
                    <span>硬度: {{ caseItem.hardness || 'N/A' }} GPa</span>
                    <span>磨损率: {{ caseItem.wear_rate ? caseItem.wear_rate.toExponential(2) : 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 根因分析结果 -->
          <div v-if="result.type === 'analysis'" class="result-analysis">
            <div class="result-header">
              <component :is="Icon" :component="AnalyticsOutline" :size="20" />
              <h4>根因分析</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <IntegratedAnalysisCard :analysis="result.data" :show-header="false" />
          </div>
          
          <!-- 优化方案选择器 -->
          <div v-if="result.type === 'optimization'" class="result-optimization">
            <div class="result-header">
              <component :is="Icon" :component="BulbOutline" :size="20" />
              <h4>优化方案</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- ✅ 显示完整的选择器，而不仅仅是文本 -->
            <OptimizationSelector
              :p1-content="result.data.p1"
              :p2-content="result.data.p2"
              :p3-content="result.data.p3"
              :comprehensive="result.data.comprehensive"
              @select="$emit('select-optimization', $event)"
            />
          </div>
          
          <!-- 实验工单 -->
          <div v-if="result.type === 'workorder'" class="result-workorder">
            <div class="result-header">
              <component :is="Icon" :component="ClipboardOutline" :size="20" />
              <h4>实验工单</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <WorkorderSummaryCard 
              :workorder="result.data"
              :selected-optimization="result.data.selected_optimization || ''"
              :show-header="false"
            />
          </div>
          
          <!-- 性能对比图（含分析报告） -->
          <div v-if="result.type === 'comparison'" class="result-comparison">
            <div class="result-header">
              <component :is="Icon" :component="BarChartOutline" :size="20" />
              <h4>实验结果分析</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- 达标状态提示 -->
            <div class="analysis-status" :class="result.data.is_target_met ? 'success' : 'warning'">
              <component 
                :is="Icon" 
                :component="result.data.is_target_met ? CheckmarkCircleOutline : AlertCircleOutline" 
                :size="20" 
              />
              <span v-if="result.data.is_target_met">🎉 所有性能指标达标！</span>
              <span v-else>
                ⚠️ 部分指标未达标：{{ formatUnmetMetrics(result.data.unmet_metrics) }}
              </span>
            </div>
            <!-- 分析报告 -->
            <div v-if="result.data.analysis_report" class="analysis-report">
              <MarkdownRenderer :content="result.data.analysis_report" />
            </div>
            <!-- 对比图 -->
            <PerformanceComparisonChart
              :experimentData="result.data.experiment_data"
              :predictionData="result.data.prediction_data"
              :historicalBest="result.data.historical_best"
            />
          </div>
          
          <!-- 实验数据输入 -->
          <div v-if="result.type === 'experiment_input'" class="result-experiment">
            <div class="result-header">
              <component :is="Icon" :component="FlaskOutline" :size="20" />
              <h4>实验数据录入</h4>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <ExperimentInputCard 
              :iteration="result.data.iteration || 1"
              :historicalBest="result.data.historicalBest"
              :targetHardness="result.data.targetHardness"
              @submit="handleExperimentSubmit"
              @cancel="handleExperimentCancel"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, h } from 'vue'
import { ElButton } from 'element-plus'
import {
  DocumentTextOutline,
  CheckmarkCircleOutline,
  PlanetOutline,
  SpeedometerOutline,
  AnalyticsOutline,
  BulbOutline,
  ClipboardOutline,
  CloseCircleOutline,
  TimeOutline,
  FlaskOutline,
  BarChartOutline,
  AlertCircleOutline
} from '@vicons/ionicons5'
import ValidationSummaryCard from '../cards/ValidationSummaryCard.vue'
import PerformancePredictionCard from '../cards/PerformancePredictionCard.vue'
import IntegratedAnalysisCard from '../cards/result/IntegratedAnalysisCard.vue'
import TopPhiResultCard from '../cards/TopPhiResultCard.vue'
import WorkorderSummaryCard from '../cards/result/WorkorderSummaryCard.vue'
import ExperimentInputCard from '../experiment/ExperimentInputCard.vue'
import PerformanceComparisonChart from '../experiment/PerformanceComparisonChart.vue'
import OptimizationSelector from '../cards/OptimizationSelector.vue'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'

// Icon包装器
const Icon = (props) => {
  return h('span', { class: 'icon-wrapper' }, h(props.component, { size: props.size }))
}

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['clear', 'select-optimization', 'experiment-submit', 'experiment-cancel'])

const resultsContainer = ref(null)

// 自动滚动到底部
watch(() => props.results.length, () => {
  nextTick(() => {
    if (resultsContainer.value) {
      resultsContainer.value.scrollTop = resultsContainer.value.scrollHeight
    }
  })
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const clearResults = () => {
  emit('clear')
}

const handleExperimentSubmit = (data) => {
  emit('experiment-submit', data)
}

const handleExperimentCancel = () => {
  emit('experiment-cancel')
}

// 格式化未达标指标
const formatUnmetMetrics = (metrics) => {
  if (!metrics || metrics.length === 0) return ''
  const nameMap = {
    'hardness': '硬度',
    'elastic_modulus': '弹性模量',
    'wear_rate': '磨损率',
    'adhesion_strength': '结合力'
  }
  return metrics.map(m => nameMap[m] || m).join('、')
}
</script>

<style scoped>
.results-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fafafa;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.results-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #0d0d0d;
}

.results-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.results-content::-webkit-scrollbar {
  width: 6px;
}

.results-content::-webkit-scrollbar-track {
  background: transparent;
}

.results-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #9ca3af;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.result-header h4 {
  flex: 1;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #0d0d0d;
}

.result-time {
  font-size: 12px;
  color: #9ca3af;
}

.result-content-box {
  padding: 16px;
}

.result-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item .label {
  font-size: 13px;
  color: #6b7280;
  min-width: 100px;
}

.result-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #0d0d0d;
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  color: #2d2d2d;
}

/* 历史对比特定样式 */
.historical-cases {
  margin-top: 12px;
}

.case-item {
  padding: 10px;
  margin-bottom: 8px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #2d2d2d;
}

.case-item:last-child {
  margin-bottom: 0;
}

.case-header {
  font-size: 13px;
  font-weight: 600;
  color: #0d0d0d;
  margin-bottom: 6px;
}

.case-detail {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
}

.case-detail span {
  display: inline-block;
}

/* 实验分析状态 */
.analysis-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.analysis-status.success {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  color: #059669;
  border-left: 3px solid #10b981;
}

.analysis-status.warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
  color: #d97706;
  border-left: 3px solid #f59e0b;
}

/* 分析报告 */
.analysis-report {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  max-height: 300px;
  overflow-y: auto;
}

.analysis-report :deep(h2) {
  font-size: 15px;
  margin: 12px 0 8px 0;
}

.analysis-report :deep(h3) {
  font-size: 14px;
  margin: 10px 0 6px 0;
}

.analysis-report :deep(table) {
  font-size: 12px;
  margin: 8px 0;
}

.analysis-report :deep(th),
.analysis-report :deep(td) {
  padding: 6px 10px;
}
</style>



