<template>
  <div class="iteration-history-panel">
    <div class="panel-header">
      <div class="header-left">
        <el-icon size="24" color="#6366f1"><TimeOutline /></el-icon>
        <h3>迭代历史</h3>
      </div>
      <el-tag :type="getStatusType()" size="large">
        {{ getStatusText() }}
      </el-tag>
    </div>
    
    <!-- 性能对比图表 -->
    <PerformanceComparisonChart
      v-if="selectedRecord"
      :experiment-data="selectedRecord.experiment_results"
      :prediction-data="selectedRecord.snapshot?.performancePrediction"
      :historical-best="getHistoricalBest(selectedRecord)"
    />
    
    <el-timeline class="iteration-timeline">
      <el-timeline-item
        v-for="(record, index) in history"
        :key="index"
        :timestamp="formatTime(record.timestamp)"
        placement="top"
        :type="getTimelineType(index)"
        :hollow="index !== history.length - 1"
      >
        <el-card 
          shadow="hover" 
          :class="['iteration-card', { 'is-latest': index === history.length - 1, 'is-viewing': isViewing(record.iteration) }]"
          @click="handleViewIteration(record.iteration)"
        >
          <div class="iteration-header">
            <div class="iteration-title">
              <el-tag type="primary" size="large">第 {{ record.iteration }} 轮</el-tag>
              <h4>{{ record.selected_optimization_name || record.selected_optimization }}</h4>
            </div>
            <div class="header-right">
              <el-tag v-if="isViewing(record.iteration)" type="success" size="small">
                <el-icon><EyeOutline /></el-icon>
                查看中
              </el-tag>
              <el-tag :type="getIterationStatus(record)" size="small">
                {{ getIterationStatusText(record) }}
              </el-tag>
            </div>
          </div>
          
          <div class="metrics-grid">
            <div class="metric-item">
              <span class="metric-label">
                <el-icon><DiamondOutline /></el-icon>
                硬度
              </span>
              <span class="metric-value highlight">
                {{ record.experiment_results.hardness }} GPa
              </span>
              <span v-if="index > 0" :class="['metric-change', getChangeClass(record.experiment_results.hardness, history[index-1].experiment_results.hardness)]">
                {{ getChangeText(record.experiment_results.hardness, history[index-1].experiment_results.hardness) }}
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">
                <el-icon><FlameOutline /></el-icon>
                弹性模量
              </span>
              <span class="metric-value">
                {{ record.experiment_results.elastic_modulus }} GPa
              </span>
            </div>
            <div v-if="record.experiment_results.wear_rate" class="metric-item">
              <span class="metric-label">
                <el-icon><EllipseOutline /></el-icon>
                磨损率
              </span>
              <span class="metric-value">
                {{ record.experiment_results.wear_rate }} mm³/Nm
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">
                <el-icon><LinkOutline /></el-icon>
                结合力
              </span>
              <span class="metric-value">
                {{ record.experiment_results.adhesion_strength }} N
              </span>
            </div>
          </div>
          
          <div v-if="record.experiment_results.notes" class="iteration-notes">
            <el-icon><DocumentTextOutline /></el-icon>
            <span>{{ record.experiment_results.notes }}</span>
          </div>
          
          <!-- 查看详细对比按钮 -->
          <div class="card-actions">
            <el-button 
              text 
              size="small" 
              type="primary"
              @click.stop="toggleRecordSelection(record)"
            >
              <el-icon><component :is="selectedRecord?.iteration === record.iteration ? EyeOffOutline : BarChartOutline" /></el-icon>
              {{ selectedRecord?.iteration === record.iteration ? '隐藏对比图' : '查看对比图' }}
            </el-button>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElIcon, ElTag, ElTimeline, ElTimelineItem, ElCard } from 'element-plus'
import { 
  TimeOutline,
  DiamondOutline,
  LinkOutline,
  FlameOutline,
  EllipseOutline,
  DocumentTextOutline,
  EyeOutline,
  BarChartOutline,
  EyeOffOutline
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../../stores/workflow'
import PerformanceComparisonChart from './PerformanceComparisonChart.vue'

const workflowStore = useWorkflowStore()

// 选中的记录（用于显示对比图）
const selectedRecord = ref(null)

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  },
  convergence: {
    type: Object,
    default: null
  }
})

// 判断是否正在查看该轮次
const isViewing = (iteration) => {
  return workflowStore.viewMode === 'history' && workflowStore.viewingIteration === iteration
}

// 点击查看历史轮次
const handleViewIteration = (iteration) => {
  console.log('[历史面板] 点击查看第', iteration, '轮')
  workflowStore.viewHistoryIteration(iteration)
}

const getStatusType = () => {
  if (props.convergence?.converged) {
    return 'success'
  }
  return 'primary'
}

const getStatusText = () => {
  if (props.convergence?.converged) {
    return '✓ 优化完成'
  }
  return `进行中 - 已完成 ${props.history.length} 轮`
}

const getTimelineType = (index) => {
  if (index === props.history.length - 1) {
    return 'primary'
  }
  return 'info'
}

const getIterationStatus = (record) => {
  // 可以根据实际情况判断状态
  return 'success'
}

const getIterationStatusText = (record) => {
  return '已完成'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getChangeClass = (current, previous) => {
  const change = current - previous
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

const getChangeText = (current, previous) => {
  const change = current - previous
  const percent = ((change / previous) * 100).toFixed(1)
  if (change > 0) return `↑ +${percent}%`
  if (change < 0) return `↓ ${percent}%`
  return '→ 0%'
}

// 切换记录选择（显示/隐藏对比图）
const toggleRecordSelection = (record) => {
  if (selectedRecord.value?.iteration === record.iteration) {
    selectedRecord.value = null
  } else {
    selectedRecord.value = record
  }
}

// 获取历史最优数据
const getHistoricalBest = (record) => {
  const historicalComparison = record.snapshot?.historicalComparison
  if (!historicalComparison?.similar_cases || historicalComparison.similar_cases.length === 0) {
    return null
  }
  
  // 返回第一个最相似的案例（相似度最高）
  const sortedCases = [...historicalComparison.similar_cases].sort((a, b) => b.similarity - a.similarity)
  return sortedCases[0]
}
</script>

<style scoped>
.iteration-history-panel {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.iteration-timeline {
  margin-top: 16px;
}

.iteration-timeline :deep(.el-timeline-item__timestamp) {
  font-size: 13px;
  color: #6b7280;
}

.iteration-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.iteration-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.iteration-card.is-viewing {
  border-left-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
}

.iteration-card.is-latest {
  border-left-color: #6366f1;
}

.iteration-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.iteration-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.iteration-title h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.metric-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.metric-value.highlight {
  font-size: 20px;
  color: #3b82f6;
}

.metric-change {
  font-size: 12px;
  font-weight: 600;
}

.metric-change.positive {
  color: #10b981;
}

.metric-change.negative {
  color: #ef4444;
}

.metric-change.neutral {
  color: #6b7280;
}

.iteration-notes {
  margin-top: 12px;
  padding: 12px;
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  font-size: 14px;
  color: #78350f;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.card-actions {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
}

.card-actions :deep(.el-button) {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
