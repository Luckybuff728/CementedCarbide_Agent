<template>
  <div class="right-panel">
    <div class="panel-header">
      <h3>
        <el-icon><DataAnalysis /></el-icon>
        分析结果
      </h3>
      <el-dropdown @command="handleCommand">
        <el-button size="small" circle>
          <el-icon><MoreFilled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="export">导出结果</el-dropdown-item>
            <el-dropdown-item command="print">打印报告</el-dropdown-item>
            <el-dropdown-item command="share">分享</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="panel-content">
      <!-- 空状态 -->
      <div v-if="!hasResults" class="empty-state">
        <el-icon :size="60" color="#c0c4cc"><DataAnalysis /></el-icon>
        <p>等待分析结果</p>
        <p class="subtitle">结果将在分析完成后展示</p>
      </div>

      <!-- 结果内容 -->
      <div v-else class="results-content">
        <!-- 步骤完成结果 -->
        <div v-if="completedStepResults.length > 0" class="step-results">
          <el-card 
            v-for="result in completedStepResults" 
            :key="result.step"
            class="step-result-card" 
            shadow="never"
          >
            <template #header>
              <div class="card-header">
                <span>
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                  {{ result.title }}
                </span>
                <el-tag type="success" size="small">已完成</el-tag>
              </div>
            </template>
            <div class="step-result-content">
              <div v-html="formatStepResult(result.content)"></div>
            </div>
          </el-card>
        </div>

        <!-- 实验工单（新增：从analysisResults中获取） -->
        <el-card v-if="analysisResults?.experimentWorkorder" class="result-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Tickets /></el-icon>
                实验工单
              </span>
              <el-tag type="warning" size="small">待执行</el-tag>
            </div>
          </template>
          
          <div class="workorder-content">
            <!-- 工单内容（Markdown格式） -->
            <div class="workorder-text" v-html="formatMarkdown(analysisResults.experimentWorkorder)"></div>
            
            <div class="workorder-actions">
              <el-button type="primary" size="small" @click="downloadWorkorder">
                <el-icon><Download /></el-icon>
                下载工单
              </el-button>
              <el-button size="small" @click="printWorkorder">
                <el-icon><DocumentCopy /></el-icon>
                打印
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 优化方案选择（当优化完成后显示） -->
        <OptimizationSelection
          v-if="showOptimizationSelection"
          :comprehensive-recommendation="comprehensiveRecommendation"
          :p1-content="p1Content"
          :p2-content="p2Content"
          :p3-content="p3Content"
          @select="handleOptimizationSelect"
        />

        <!-- 综合分析报告 -->
        <el-card v-if="integratedAnalysis" class="result-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><TrendCharts /></el-icon>
                综合分析报告
              </span>
              <el-button size="small" @click="exportReport">
                <el-icon><Share /></el-icon>
                导出
              </el-button>
            </div>
          </template>
          
          <div class="analysis-content">
            <!-- 根因分析 -->
            <div v-if="integratedAnalysis.root_cause_analysis" class="root-cause-section">
              <el-divider content-position="left">🔍 根因分析</el-divider>
              <div class="root-cause-text" v-html="formatMarkdown(integratedAnalysis.root_cause_analysis)"></div>
            </div>
            
            <!-- 性能摘要 -->
            <div v-if="integratedAnalysis.performance_summary" class="performance-summary">
              <el-descriptions title="性能摘要" :column="2" border>
                <el-descriptions-item label="预测硬度">
                  <el-tag type="success" size="large">
                    {{ integratedAnalysis.performance_summary?.predicted_hardness || 'N/A' }} GPa
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="预测置信度">
                  <el-progress 
                    :percentage="integratedAnalysis.performance_summary?.confidence ? (integratedAnalysis.performance_summary.confidence * 100).toFixed(0) : 0" 
                    :color="getConfidenceColor(integratedAnalysis.performance_summary?.confidence || 0)"
                  />
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 关键发现 -->
            <div v-if="integratedAnalysis.performance_summary?.key_findings" class="analysis-summary">
              <el-divider content-position="left">🔍 关键发现</el-divider>
              <ul class="findings-list">
                <li v-for="(finding, index) in integratedAnalysis.performance_summary.key_findings" :key="index">
                  <el-icon color="#409EFF"><Check /></el-icon>
                  {{ finding }}
                </li>
              </ul>
            </div>
            
            <!-- 优化建议 -->
            <div v-if="integratedAnalysis.recommendation" class="analysis-recommendations">
              <el-divider content-position="left">💡 建议</el-divider>
              <el-alert
                :title="integratedAnalysis.recommendation"
                type="info"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>

        <!-- 实验结果（如果有） -->
        <el-card v-if="experimentResults" class="result-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><DataLine /></el-icon>
                实验结果
              </span>
              <el-tag type="success" size="small">已完成</el-tag>
            </div>
          </template>
          
          <div class="experiment-results">
            <div class="results-grid">
              <div class="result-item">
                <label>硬度</label>
                <span>{{ experimentResults.hardness }} ± {{ experimentResults.hardness_std }} GPa</span>
              </div>
              <div class="result-item">
                <label>结合力</label>
                <span>{{ experimentResults.adhesion_level }}</span>
              </div>
              <div class="result-item">
                <label>磨损率</label>
                <span>{{ experimentResults.wear_rate }} mm³/Nm</span>
              </div>
              <div class="result-item">
                <label>涂层厚度</label>
                <span>{{ experimentResults.coating_thickness }} μm</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  DataAnalysis, 
  MoreFilled, 
  Loading, 
  MagicStick, 
  Tickets, 
  TrendCharts,
  Share,
  Download,
  DocumentCopy,
  DataLine,
  Check,
  CircleCheck
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import OptimizationSelection from './OptimizationSelection.vue'

const props = defineProps({
  analysisResults: Object,     // 分析结果数据对象
  isProcessing: Boolean,       // 是否正在处理
  currentNode: String,         // 当前节点ID
  currentNodeTitle: String,    // 当前节点标题
  processSteps: Array,         // 已完成的步骤列表
  p1Content: String,           // P1优化方案内容
  p2Content: String,           // P2优化方案内容
  p3Content: String,           // P3优化方案内容
  showOptimizationSelection: Boolean  // 是否显示优化方案选择界面
})

const emit = defineEmits(['optimization-select'])

// 检查是否有结果
const hasResults = computed(() => {
  if (!props.analysisResults) return false
  return Object.values(props.analysisResults).some(v => v !== null && v !== '') ||
         completedStepResults.value.length > 0
})

// 已完成步骤结果
const completedStepResults = computed(() => {
  if (!props.processSteps) return []
  
  const stepTitleMap = {
    'input_validation': '参数验证',
    'topphi_simulation': '理论计算',
    'ml_prediction': '性能预测',
    'historical_comparison': '历史对比',
    'integrated_analysis': '根因分析',
    'optimization': '优化建议',
    'experiment': '实验验证'
  }
  
  return props.processSteps
    .filter(step => 
      step.status === 'completed' && 
      step.content && 
      step.content.trim() !== '' &&
      !isGenericMessage(step.content)
    )
    .map(step => ({
      step: step.node_id || step.id,
      title: stepTitleMap[step.node_id] || step.title || '分析步骤',
      content: step.content,
      timestamp: step.timestamp
    }))
})

// 检查是否为通用信息
const isGenericMessage = (content) => {
  if (!content || typeof content !== 'string') return false
  
  const genericMessages = [
    '节点执行完成',
    '处理完成',
    '执行成功',
    '任务完成',
    'success',
    'completed',
    'done'
  ]
  
  const trimmedContent = content.trim().toLowerCase()
  return genericMessages.some(msg => 
    trimmedContent === msg || 
    trimmedContent === msg.toLowerCase()
  )
}

// 格式化步骤结果内容
const formatStepResult = (content) => {
  if (!content) return ''
  try {
    marked.setOptions({
      breaks: true,
      gfm: true
    })
    return marked.parse(content)
  } catch (error) {
    return content
  }
}

// 格式化Markdown文本（用于根因分析等）
const formatMarkdown = (content) => {
  if (!content) return ''
  try {
    marked.setOptions({
      breaks: true,
      gfm: true
    })
    return marked.parse(content)
  } catch (error) {
    return content
  }
}

// 当前节点显示标题（直接使用props）
const displayNodeTitle = computed(() => {
  return props.currentNodeTitle || '处理中'
})

// 进度百分比
const progressPercentage = computed(() => {
  const nodeProgress = {
    'input_validation': 10,
    'topphi_simulation': 25,
    'ml_prediction': 45,
    'historical_comparison': 55,
    'integrated_analysis': 65,
    'p1_composition_optimization': 75,
    'p2_structure_optimization': 85,
    'p3_process_optimization': 90,
    'optimization_summary': 95,
    'experiment_workorder': 98,
    'experiment_result_analysis': 100
  }
  return nodeProgress[props.currentNode] || 0
})

// 直接从 analysisResults 中获取数据
const integratedAnalysis = computed(() => {
  return props.analysisResults?.integratedAnalysis
})

const comprehensiveRecommendation = computed(() => {
  return props.analysisResults?.comprehensiveRecommendation
})

const experimentWorkorder = computed(() => {
  return props.analysisResults?.experimentWorkorder
})

const experimentResults = computed(() => {
  return props.analysisResults?.experimentResults
})

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67C23A'  // 绿色 - 高置信度
  if (confidence >= 0.6) return '#E6A23C'  // 橙色 - 中等置信度
  return '#F56C6C'  // 红色 - 低置信度
}

// 处理命令
const handleCommand = (command) => {
  switch (command) {
    case 'export':
      exportResults()
      break
    case 'print':
      printResults()
      break
    case 'share':
      shareResults()
      break
  }
}

// 处理优化方案选择
const handleOptimizationSelect = (option) => {
  emit('optimization-select', option)
}

// 导出结果
const exportResults = () => {
  ElMessage.success('结果导出功能开发中...')
}

// 打印结果
const printResults = () => {
  window.print()
}

// 分享结果
const shareResults = () => {
  ElMessage.success('分享功能开发中...')
}

// 下载工单
const downloadWorkorder = () => {
  if (experimentWorkorder.value) {
    const content = JSON.stringify(experimentWorkorder.value, null, 2)
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workorder_${experimentWorkorder.value.workorder_id}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('工单下载完成')
  }
}

// 打印工单
const printWorkorder = () => {
  ElMessage.success('打印功能开发中...')
}

// 导出报告
const exportReport = () => {
  ElMessage.success('报告导出功能开发中...')
}

// 获取优先级类型
const getPriorityType = (priority) => {
  const types = {
    '高优先级': 'danger',
    '中优先级': 'warning',
    '低优先级': 'info'
  }
  return types[priority] || 'info'
}
</script>

<style scoped>
/* ============ 右侧面板主体布局 ============ */
.right-panel {
  width: 650px;                          /* 固定宽度：520像素 */
  height: calc(100vh - 70px);            /* 高度：全屏减去状态栏高度(70px) */
  background: #fafbfc;                   /* 浅灰色背景 */
  border-left: 1px solid #e4e7ed;       /* 左侧分隔线 */
  display: flex;                         /* 弹性盒子布局 */
  flex-direction: column;                /* 垂直方向排列 */
  overflow: hidden;                      /* 隐藏超出内容，防止布局破坏 */
}

/* ============ 面板头部区域样式 ============ */
.panel-header {
  padding: 20px;                        /* 内边距：上下左右20px */
  border-bottom: 1px solid #e4e7ed;     /* 底部分隔线 */
  background: white;                    /* 白色背景，区别于面板主体 */
  display: flex;                        /* 弹性布局 */
  align-items: center;                  /* 垂直居中对齐 */
  justify-content: space-between;       /* 两端对齐(标题和操作按钮) */
}

/* 面板标题样式 */
.panel-header h3 {
  margin: 0;                           /* 清除默认外边距 */
  font-size: 16px;                     /* 标题字体大小 */
  font-weight: 600;                    /* 字体粗细：半粗体 */
  color: #303133;                      /* 深色文字 */
  display: flex;                       /* 弹性布局用于图标和文字对齐 */
  align-items: center;                 /* 图标和文字垂直居中 */
  gap: 8px;                           /* 图标和文字间距 */
}

/* ============ 面板内容区域布局 ============ */
.panel-content {
  flex: 1;                            /* 占用剩余全部空间 */
  overflow-y: auto;                   /* 垂直滚动，处理内容溢出 */
  padding: 16px;                      /* 内边距：16px */
}

/* ============ 结果内容区域布局 ============ */
.results-content {
  display: flex;                      /* 弹性布局 */
  flex-direction: column;             /* 垂直排列各个结果卡片 */
  gap: 12px;                         /* 卡片之间间距：12px */
}

.step-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ============ 步骤结果卡片样式 ============ */
.step-result-card {
  border: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border-left: 3px solid #67C23A;
}

.step-result-content {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

/* 步骤结果内容样式 */
:deep(.step-result-content) h3 {
  margin: 8px 0 6px;
  color: #409EFF;
  font-size: 14px;
  font-weight: 600;
}

:deep(.step-result-content) h4 {
  margin: 6px 0 4px;
  color: #606266;
  font-size: 13px;
  font-weight: 600;
}

:deep(.step-result-content) p {
  margin: 6px 0;
}

:deep(.step-result-content) ul {
  padding-left: 20px;
  margin: 6px 0;
}

:deep(.step-result-content) li {
  margin: 4px 0;
}

/* ============ 通用结果卡片样式 ============ */
.result-card {
  border: none;                      /* 移除默认边框 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 添加阴影效果 */
}

/* 卡片头部布局 */
.card-header {
  display: flex;                     /* 弹性布局 */
  align-items: center;               /* 垂直居中对齐 */
  justify-content: space-between;    /* 两端对齐(标题和操作区) */
  font-weight: 600;                  /* 字体粗细：半粗体 */
  color: #303133;                    /* 深色文字 */
}

/* 卡片头部图标和文字容器 */
.card-header span {
  display: flex;                     /* 弹性布局用于图标文字对齐 */
  align-items: center;               /* 垂直居中对齐 */
  gap: 8px;                         /* 图标和文字间距：8px */
}

/* ============ 工单内容区域样式 ============ */
.workorder-content {
  padding: 8px 0;                    /* 上下内边距：8px */
}

/* 工单条目布局 */
.workorder-item {
  display: flex;                     /* 弹性布局 */
  align-items: flex-start;           /* 顶部对齐，适应多行文本 */
  margin-bottom: 12px;              /* 底部外边距：12px */
  padding: 8px 0;                   /* 上下内边距：8px */
}

/* 工单字段标签 */
.workorder-item label {
  width: 80px;                      /* 固定宽度：80px，保持对齐 */
  font-weight: 600;                 /* 字体粗细：半粗体 */
  color: #606266;                   /* 中性灰色 */
  font-size: 13px;                  /* 字体大小 */
}

/* 工单字段值 */
.workorder-item span {
  flex: 1;                          /* 占用剩余空间 */
  font-size: 13px;                  /* 字体大小 */
}

/* ============ 改进建议标签布局 ============ */
.improvements {
  display: flex;                     /* 弹性布局 */
  flex-wrap: wrap;                   /* 允许换行 */
  gap: 4px;                         /* 标签间距：4px */
}

/* 改进建议标签样式 */
.improvement-tag {
  font-size: 13px;                  /* 字体大小：增大到13px */
}

/* ============ 工单内容区域 ============ */
.workorder-text {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
  font-size: 14px;
  margin-bottom: 16px;
  max-height: 500px;
  overflow-y: auto;
}

:deep(.workorder-text) h1,
:deep(.workorder-text) h2,
:deep(.workorder-text) h3 {
  color: #303133;
  margin: 16px 0 8px 0;
}

:deep(.workorder-text) h1 { font-size: 18px; }
:deep(.workorder-text) h2 { font-size: 16px; }
:deep(.workorder-text) h3 { font-size: 15px; }

:deep(.workorder-text) p {
  margin: 8px 0;
}

:deep(.workorder-text) ul,
:deep(.workorder-text) ol {
  padding-left: 20px;
  margin: 10px 0;
}

:deep(.workorder-text) strong {
  color: #409EFF;
  font-weight: 600;
}

/* ============ 工单操作按钮区域 ============ */
.workorder-actions {
  display: flex;                    /* 弹性布局 */
  gap: 8px;                        /* 按钮间距：8px */
  justify-content: center;
}

/* ============ 分析内容区域样式 ============ */
.analysis-content {
  padding: 8px 0;                   /* 上下内边距：8px */
}

/* 分析内容标题 */
.analysis-content h4 {
  margin: 16px 0 8px 0;             /* 外边距：上16px 下8px 左右0 */
  font-size: 14px;                  /* 字体大小 */
  color: #303133;                   /* 深色文字 */
}

/* 分析总结列表样式 */
.analysis-summary ul {
  padding-left: 16px;               /* 左内边距：16px，用于缩进 */
  margin: 0;                        /* 清除默认外边距 */
}

/* 分析总结列表项 */
.analysis-summary li {
  font-size: 13px;                  /* 字体大小 */
  line-height: 1.5;                 /* 行高：1.5倍字体大小 */
  margin-bottom: 4px;               /* 底部外边距：4px */
  color: #606266;                   /* 中性灰色文字 */
}

/* ============ 推荐建议列表布局 ============ */
.recommendations-list {
  display: flex;                    /* 弹性布局 */
  flex-direction: column;           /* 垂直排列 */
  gap: 8px;                        /* 建议项之间间距：8px */
}

.recommendation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.experiment-results {
  padding: 8px 0;
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.result-item {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  text-align: center;
}

.result-item label {
  display: block;
  font-size: 13px;                  /* 增大标签字体到13px */
  color: #909399;
  margin-bottom: 4px;
}

.result-item span {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

/* 美化滚动条 */
.panel-content::-webkit-scrollbar,
.comparison-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track,
.comparison-content::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.panel-content::-webkit-scrollbar-thumb,
.comparison-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover,
.comparison-content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

:deep(.status-card .el-card__body) {
  background: transparent;
  color: white;
}

:deep(.status-card .el-progress-bar__outer) {
  background: rgba(255, 255, 255, 0.2);
}

:deep(.status-card .el-progress-bar__inner) {
  background: white;
}

/* 响应式设计 */
@media (max-width: 1600px) {
  .right-panel {
    width: 450px;
  }
}

@media (max-width: 1400px) {
  .right-panel {
    width: 380px;
  }
}

@media (max-width: 1200px) {
  .right-panel {
    width: 320px;
  }
}

/* 性能摘要样式 */
.performance-summary {
  margin-bottom: 20px;
}

/* 关键发现列表样式 */
.findings-list {
  list-style: none;
  padding: 0;
  margin: 10px 0;
}

.findings-list li {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 10px;
  background: #f0f9ff;
  border-left: 3px solid #409EFF;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.findings-list li .el-icon {
  margin-right: 10px;
  flex-shrink: 0;
}

/* 综合分析报告内容样式 */
.analysis-content {
  padding: 10px 0;
}

/* 根因分析样式 */
.root-cause-section {
  margin-bottom: 20px;
}

.root-cause-text {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #f0f9ff 100%);
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  line-height: 1.8;
  font-size: 14px;
  color: #333;
}

:deep(.root-cause-text) h1,
:deep(.root-cause-text) h2,
:deep(.root-cause-text) h3,
:deep(.root-cause-text) h4 {
  color: #409EFF;
  font-weight: 600;
  margin: 16px 0 8px 0;
}

:deep(.root-cause-text) h1 { font-size: 18px; }
:deep(.root-cause-text) h2 { font-size: 16px; }
:deep(.root-cause-text) h3 { font-size: 15px; }
:deep(.root-cause-text) h4 { font-size: 14px; }

:deep(.root-cause-text) p {
  margin: 8px 0;
  line-height: 1.8;
}

:deep(.root-cause-text) ul,
:deep(.root-cause-text) ol {
  padding-left: 20px;
  margin: 10px 0;
}

:deep(.root-cause-text) li {
  margin: 6px 0;
  line-height: 1.6;
}

:deep(.root-cause-text) strong {
  color: #409EFF;
  font-weight: 600;
}

:deep(.root-cause-text) code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #e74c3c;
}

.analysis-summary {
  margin-bottom: 20px;
}

.analysis-recommendations {
  margin-top: 20px;
}
</style>
