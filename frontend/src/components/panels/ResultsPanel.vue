<template>
  <div class="results-panel">
    <div class="results-header">
      <div class="header-left">
        <span class="header-title">分析结果</span>
        <span class="result-count" v-if="results.length > 0">{{ results.length }}</span>
      </div>
      <el-button text circle @click="clearResults" v-if="results.length > 0">
        <el-icon :size="18"><CloseCircleOutline /></el-icon>
      </el-button>
    </div>
    
    <div class="results-content" ref="resultsContainer">
      <div v-if="results.length === 0" class="empty-state">
        <div class="empty-image">
          <el-icon :size="64"><AnalyticsOutline /></el-icon>
        </div>
        <div class="empty-text">
          <h3>暂无分析结果</h3>
          <p>提交任务后，AI 分析的详细报告、<br>性能预测及优化方案将显示在这里</p>
        </div>
      </div>
      
      <div v-else class="results-list">
        <div
          v-for="result in results"
          :key="result.id"
          class="result-card"
          :class="`result-${result.type}`"
        >
          <!-- TopPhi相场模拟结果（包含VTK可视化） -->
          <div v-if="result.type === 'topphi'" class="result-topphi">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><PlanetOutline /></el-icon>
                <h4>TopPhi相场模拟</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- 使用完整的TopPhiResultCard组件，包含VTK可视化 -->
            <TopPhiResultCard :result="result" />
          </div>
          
          <!-- 性能预测结果 -->
          <div v-if="result.type === 'performance'" class="result-performance">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><SpeedometerOutline /></el-icon>
                <h4>性能预测</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <PerformancePredictionCard :prediction="result.data" :show-header="false" />
          </div>
          
          <!-- 历史对比结果 -->
          <div v-if="result.type === 'historical'" class="result-historical">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><TimeOutline /></el-icon>
                <h4>历史案例对比</h4>
              </div>
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
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><AnalyticsOutline /></el-icon>
                <h4>根因分析</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <IntegratedAnalysisCard :analysis="result.data" :show-header="false" />
          </div>
          
          <!-- 优化方案概览（从 Agent 输出提取） -->
          <div v-if="result.type === 'optimization_plans'" class="result-optimization-plans">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><BulbOutline /></el-icon>
                <h4>优化方案概览</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <OptimizationPlansCard :data="result.data" />
          </div>
          
          <!-- 实验工单（从 Agent 输出提取） -->
          <div v-if="result.type === 'workorder'" class="result-workorder">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><ClipboardOutline /></el-icon>
                <h4>实验工单</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <WorkorderDownloadCard :data="result.data" />
          </div>
          
          <!-- 性能对比图表（从 show_performance_comparison_tool 返回） -->
          <div v-if="result.type === 'performance_comparison'" class="result-performance-comparison">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><BarChartOutline /></el-icon>
                <h4>性能对比分析</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- 达标状态提示 -->
            <div class="analysis-status" :class="result.data.is_target_met ? 'success' : 'warning'">
              <el-icon :size="20">
                <CheckmarkCircleOutline v-if="result.data.is_target_met" />
                <AlertCircleOutline v-else />
              </el-icon>
              <span v-if="result.data.is_target_met">🎉 性能指标达标！</span>
              <span v-else>⚠️ 部分指标未达标</span>
            </div>
            <!-- 简要总结 -->
            <div v-if="result.data.summary" class="comparison-summary">
              {{ result.data.summary }}
            </div>
            <!-- 对比图表 -->
            <PerformanceComparisonChart
              :experimentData="result.data.experiment"
              :predictionData="result.data.prediction"
              :historicalBest="result.data.historical"
            />
          </div>
          
          <!-- 旧的性能对比图（含分析报告） -->
          <div v-if="result.type === 'comparison'" class="result-comparison">
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><BarChartOutline /></el-icon>
                <h4>实验结果分析</h4>
              </div>
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
            </div>
            <!-- 达标状态提示 -->
            <div class="analysis-status" :class="result.data.is_target_met ? 'success' : 'warning'">
              <el-icon :size="20">
                <CheckmarkCircleOutline v-if="result.data.is_target_met" />
                <AlertCircleOutline v-else />
              </el-icon>
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
            <div class="result-header-strip">
              <div class="strip-left">
                <el-icon :size="18" color="#5f6368"><FlaskOutline /></el-icon>
                <h4>实验数据录入</h4>
              </div>
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
import { ElButton, ElIcon } from 'element-plus'
import {
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
import PerformancePredictionCard from '../cards/PerformancePredictionCard.vue'
import IntegratedAnalysisCard from '../cards/IntegratedAnalysisCard.vue'
import TopPhiResultCard from '../cards/TopPhiResultCard.vue'
import ExperimentInputCard from '../experiment/ExperimentInputCard.vue'
import PerformanceComparisonChart from '../experiment/PerformanceComparisonChart.vue'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'
import OptimizationPlansCard from '../cards/OptimizationPlansCard.vue'
import WorkorderDownloadCard from '../cards/WorkorderDownloadCard.vue'

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
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dadce0;
  overflow: hidden;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #f1f3f4;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #202124;
}

.result-count {
  background: #f1f3f4;
  color: #5f6368;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.results-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f8f9fa; /* 稍微深一点的背景，突出卡片 */
}

.results-content::-webkit-scrollbar {
  width: 6px;
}

.results-content::-webkit-scrollbar-track {
  background: transparent;
}

.results-content::-webkit-scrollbar-thumb {
  background: #dadce0;
  border-radius: 3px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 24px;
  padding: 0 40px;
  text-align: center;
}

.empty-image {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #f1f3f4;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dadce0;
}

.empty-text h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #3c4043;
}

.empty-text p {
  margin: 0;
  font-size: 14px;
  color: #9aa0a6;
  line-height: 1.5;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  overflow: hidden;
  transition: all 0.3s ease;
  animation: cardSlideIn 0.4s ease-out;
}

.result-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: #d2d2d2;
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #ffffff;
  border-bottom: 1px solid #f1f3f4;
}

.strip-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1f1f1f;
}

.strip-left h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.result-time {
  font-size: 12px;
  color: #9aa0a6;
}

.result-content-box {
  padding: 16px;
}

.result-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f1f3f4;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item .label {
  font-size: 13px;
  color: #5f6368;
  min-width: 100px;
}

.result-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #202124;
}

/* 历史对比特定样式 */
.historical-cases {
  margin-top: 12px;
}

.case-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #1967d2;
}

.case-item:last-child {
  margin-bottom: 0;
}

.case-header {
  font-size: 13px;
  font-weight: 600;
  color: #202124;
  margin-bottom: 6px;
}

.case-detail {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #5f6368;
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
  background: #e6f4ea;
  color: #137333;
  border-left: 3px solid #137333;
}

.analysis-status.warning {
  background: #fef7e0;
  color: #b06000;
  border-left: 3px solid #f9ab00;
}

/* 分析报告 */
.analysis-report {
  padding: 16px;
  border-bottom: 1px solid #f1f3f4;
  max-height: 300px;
  overflow-y: auto;
}

.analysis-report :deep(h2) {
  font-size: 15px;
  margin: 12px 0 8px 0;
  color: #202124;
}

.analysis-report :deep(h3) {
  font-size: 14px;
  margin: 10px 0 6px 0;
  color: #202124;
}

.analysis-report :deep(table) {
  font-size: 12px;
  margin: 8px 0;
}

.analysis-report :deep(th),
.analysis-report :deep(td) {
  padding: 6px 10px;
  border-color: #e0e0e0;
}

/* 卡片内容区域的通用padding */
:deep(.card-content) {
  padding: 16px;
}

/* 性能对比分析 - 简要总结 */
.comparison-summary {
  padding: 12px 16px;
  font-size: 13px;
  color: #5f6368;
  background: #f8f9fa;
  border-bottom: 1px solid #f1f3f4;
  line-height: 1.5;
}
</style>



