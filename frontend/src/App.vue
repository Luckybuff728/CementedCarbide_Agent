<template>
  <div class="app-container">
    <!-- 会话侧边栏 -->
    <SessionSidebar
      :sessions="sessions"
      :currentSessionId="currentSessionId"
      @create="handleCreateSession"
      @select="handleSelectSession"
      @rename="handleRenameSession"
      @delete="handleDeleteSession"
    />

    <!-- 主工作区 -->
    <div class="main-workspace">
      <!-- 顶部导航栏 -->
      <header class="header">
        <div class="header-content">
          <div class="logo">
            <el-icon :size="28" color="#67C23A"><ChatDotRound /></el-icon>
            <h1>TopMat Agent</h1>
          </div>
          <div class="header-info">
            <span class="header-desc">硬质合金涂层智能优化系统</span>
            <el-tag :type="connectionStatus ? 'success' : 'danger'" size="small">
              {{ connectionStatus ? '已连接' : '未连接' }}
            </el-tag>
          </div>
        </div>
      </header>

      <!-- 主内容区 - 表单布局 -->
      <main class="main-content">
        <!-- 参数输入表单 -->
        <div class="form-section">
          <CoatingInputForm
            :loading="isProcessing"
            @submit="handleFormSubmit"
          />
        </div>

        <!-- 结果展示区 - 按节点分步骤展示 -->
        <div v-if="messages.length > 0 || isProcessing" class="result-section">

          <!-- 滚动到底部按钮 -->
          <transition name="fade">
            <el-button 
              v-if="showScrollToBottom" 
              class="scroll-to-bottom-btn"
              type="primary" 
              circle 
              size="large"
              @click="resumeAutoScroll"
              title="返回底部"
            >
              <el-icon><ArrowDown /></el-icon>
            </el-button>
          </transition>

          <!-- 各节点结果展示 -->
          <div ref="resultsContainer" class="workflow-results">
            <!-- 1. 输入验证节点 -->
            <el-card v-if="getNodeMessage('input_validation')" class="node-card" shadow="hover">
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon"><CircleCheck /></el-icon>
                    <span>输入验证</span>
                  </div>
                  <el-tag type="success" size="small">已完成</el-tag>
                </div>
              </template>
              <div class="node-content" v-html="formatContent(getNodeMessage('input_validation').content)"></div>
            </el-card>

            <!-- 2. TopPhi模拟节点 -->
            <el-card 
              v-if="getNodeMessage('topphi_simulation') || (currentNode === 'topphi_simulation' && (isThinking || isStreaming))"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'topphi_simulation' && (isThinking || isStreaming) }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'topphi_simulation' && (isThinking || isStreaming) }">
                      <Cpu />
                    </el-icon>
                    <span>TopPhi第一性原理模拟</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'topphi_simulation' && (isThinking || isStreaming) ? 'warning' : 'success'" 
                    size="default"
                    effect="dark"
                  >
                    <el-icon v-if="currentNode === 'topphi_simulation' && (isThinking || isStreaming)" class="is-loading" style="margin-right: 4px;"><Loading /></el-icon>
                    {{ currentNode === 'topphi_simulation' && (isThinking || isStreaming) ? '正在计算...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              <div v-if="currentNode === 'topphi_simulation' && isThinking && !isStreaming" class="processing-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>{{ thinkingText }}</span>
              </div>
              <div v-else class="node-content" :class="{ 'streaming': currentNode === 'topphi_simulation' && isStreaming }" v-html="formatContent(getNodeMessage('topphi_simulation')?.content)"></div>
            </el-card>

            <!-- 3. ML模型预测节点 -->
            <el-card 
              v-if="getNodeMessage('ml_prediction') || (currentNode === 'ml_prediction' && (isThinking || isStreaming))"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'ml_prediction' && (isThinking || isStreaming) }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'ml_prediction' && (isThinking || isStreaming) }">
                      <Histogram />
                    </el-icon>
                    <span>ML模型性能预测</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'ml_prediction' && (isThinking || isStreaming) ? 'warning' : 'success'" 
                    size="default"
                    effect="dark"
                  >
                    <el-icon v-if="currentNode === 'ml_prediction' && (isThinking || isStreaming)" class="is-loading" style="margin-right: 4px;"><Loading /></el-icon>
                    {{ currentNode === 'ml_prediction' && (isThinking || isStreaming) ? '正在预测...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              <div v-if="currentNode === 'ml_prediction' && isThinking && !isStreaming" class="processing-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>{{ thinkingText }}</span>
              </div>
              <div v-else>
                <!-- 流式输出内容 -->
                <div v-if="getNodeMessage('ml_prediction')?.content" 
                     class="node-content" 
                     :class="{ 'streaming': currentNode === 'ml_prediction' && isStreaming }" 
                     v-html="formatContent(getNodeMessage('ml_prediction')?.content)">
                </div>
                <!-- 预测结果卡片 -->
                <PredictionResults
                  v-if="getNodeMessage('ml_prediction')?.data?.ml_prediction"
                  :prediction="getNodeMessage('ml_prediction').data.ml_prediction"
                  :analysis="getNodeMessage('ml_prediction').data.root_cause_analysis"
                />
              </div>
            </el-card>

            <!-- 4. 历史数据比对节点 -->
            <el-card 
              v-if="getNodeMessage('historical_comparison') || (currentNode === 'historical_comparison' && isThinking)"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'historical_comparison' && isThinking }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'historical_comparison' && isThinking }">
                      <Document />
                    </el-icon>
                    <span>历史数据比对</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'historical_comparison' && isThinking ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ currentNode === 'historical_comparison' && isThinking ? '检索中...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              <div v-if="currentNode === 'historical_comparison' && isThinking" class="processing-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>{{ thinkingText }}</span>
              </div>
              <div v-else class="node-content" v-html="formatContent(getNodeMessage('historical_comparison')?.content)"></div>
            </el-card>

            <!-- 5. 综合分析节点 -->
            <el-card 
              v-if="getNodeMessage('integrated_analysis') || (currentNode === 'integrated_analysis' && isStreaming)"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'integrated_analysis' && isStreaming }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'integrated_analysis' && isStreaming }">
                      <DataAnalysis />
                    </el-icon>
                    <span>综合分析与根因</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'integrated_analysis' && isStreaming ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ currentNode === 'integrated_analysis' && isStreaming ? 'AI分析中...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              <div class="node-content streaming" v-html="formatContent(getNodeMessage('integrated_analysis')?.content)"></div>
            </el-card>

            <!-- 6. 优化方案生成（合并P1/P2/P3） -->
            <el-card 
              v-if="getNodeMessage('p1_composition_optimization') || getNodeMessage('p2_structure_optimization') || getNodeMessage('p3_process_optimization') || ['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(currentNode)"
              class="node-card optimization-card" 
              shadow="hover"
              :class="{ 'processing': ['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(currentNode) }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': ['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(currentNode) }">
                      <MagicStick />
                    </el-icon>
                    <span>优化方案生成</span>
                  </div>
                  <el-tag 
                    :type="['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(currentNode) ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ getOptimizationStatus() }}
                  </el-tag>
                </div>
              </template>
              
              <el-tabs v-model="activeOptimizationTab" class="optimization-tabs">
                <!-- P1 成分优化 -->
                <el-tab-pane name="p1">
                  <template #label>
                    <span class="tab-label">
                      <el-icon><Orange /></el-icon>
                      <span>P1 成分优化</span>
                      <el-tag v-if="getNodeMessage('p1_composition_optimization')" type="success" size="small" class="tab-tag">✓</el-tag>
                      <el-icon v-else-if="currentNode === 'p1_composition_optimization' && isStreaming" class="is-loading" size="small"><Loading /></el-icon>
                    </span>
                  </template>
                  <div v-if="currentNode === 'p1_composition_optimization' && isThinking && !isStreaming" class="processing-indicator">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ thinkingText }}</span>
                  </div>
                  <div v-else-if="getNodeMessage('p1_composition_optimization')?.content" 
                       class="node-content" 
                       :class="{ 'streaming': currentNode === 'p1_composition_optimization' && isStreaming }" 
                       v-html="formatContent(getNodeMessage('p1_composition_optimization')?.content)">
                  </div>
                  <el-empty v-else description="等待生成..." :image-size="80" />
                </el-tab-pane>
                
                <!-- P2 结构优化 -->
                <el-tab-pane name="p2">
                  <template #label>
                    <span class="tab-label">
                      <el-icon><Grid /></el-icon>
                      <span>P2 结构优化</span>
                      <el-tag v-if="getNodeMessage('p2_structure_optimization')" type="success" size="small" class="tab-tag">✓</el-tag>
                      <el-icon v-else-if="currentNode === 'p2_structure_optimization' && isStreaming" class="is-loading" size="small"><Loading /></el-icon>
                    </span>
                  </template>
                  <div v-if="currentNode === 'p2_structure_optimization' && isThinking && !isStreaming" class="processing-indicator">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ thinkingText }}</span>
                  </div>
                  <div v-else-if="getNodeMessage('p2_structure_optimization')?.content" 
                       class="node-content" 
                       :class="{ 'streaming': currentNode === 'p2_structure_optimization' && isStreaming }" 
                       v-html="formatContent(getNodeMessage('p2_structure_optimization')?.content)">
                  </div>
                  <el-empty v-else description="等待生成..." :image-size="80" />
                </el-tab-pane>
                
                <!-- P3 工艺优化 -->
                <el-tab-pane name="p3">
                  <template #label>
                    <span class="tab-label">
                      <el-icon><Setting /></el-icon>
                      <span>P3 工艺优化</span>
                      <el-tag v-if="getNodeMessage('p3_process_optimization')" type="success" size="small" class="tab-tag">✓</el-tag>
                      <el-icon v-else-if="currentNode === 'p3_process_optimization' && isStreaming" class="is-loading" size="small"><Loading /></el-icon>
                    </span>
                  </template>
                  <div v-if="currentNode === 'p3_process_optimization' && isThinking && !isStreaming" class="processing-indicator">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ thinkingText }}</span>
                  </div>
                  <div v-else-if="getNodeMessage('p3_process_optimization')?.content" 
                       class="node-content" 
                       :class="{ 'streaming': currentNode === 'p3_process_optimization' && isStreaming }" 
                       v-html="formatContent(getNodeMessage('p3_process_optimization')?.content)">
                  </div>
                  <el-empty v-else description="等待生成..." :image-size="80" />
                </el-tab-pane>
              </el-tabs>
            </el-card>

            <!-- 7. 优化建议汇总节点 -->
            <el-card 
              v-if="getNodeMessage('optimization_summary') || (currentNode === 'optimization_summary' && isStreaming)"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'optimization_summary' && isStreaming }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'optimization_summary' && isStreaming }">
                      <MagicStick />
                    </el-icon>
                    <span>优化方案选择</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'optimization_summary' && isStreaming ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ currentNode === 'optimization_summary' && isStreaming ? '生成综合建议中...' : '请选择' }}
                  </el-tag>
                </div>
              </template>
              
              <!-- 综合建议流式生成中 -->
              <div 
                v-if="currentNode === 'optimization_summary' && isStreaming && getNodeMessage('optimization_summary')?.content"
                class="node-content streaming"
                style="margin-bottom: 20px; padding: 16px; background: #F5F9FF; border-radius: 8px; border-left: 4px solid #409EFF;"
              >
                <h3 style="margin: 0 0 12px 0; color: #409EFF; font-size: 16px;">💡 综合建议</h3>
                <div v-html="formatContent(getNodeMessage('optimization_summary')?.content)"></div>
              </div>
              
              <!-- 优化建议选择组件 -->
              <OptimizationSuggestions
                v-if="getNodeMessage('optimization_summary')?.data?.optimization_suggestions"
                :suggestions="getNodeMessage('optimization_summary').data.optimization_suggestions"
                :recommendation="getNodeMessage('optimization_summary').data.comprehensive_recommendation"
                @select="handleOptimizationSelect"
              />
            </el-card>

            <!-- 7. 实验工单节点 -->
            <el-card 
              v-if="getNodeMessage('experiment_workorder_generation') || (currentNode === 'experiment_workorder_generation' && (isThinking || isStreaming))"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'experiment_workorder_generation' && (isThinking || isStreaming) }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'experiment_workorder_generation' && (isThinking || isStreaming) }">
                      <Tickets />
                    </el-icon>
                    <span>实验工单生成</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'experiment_workorder_generation' && (isThinking || isStreaming) ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ currentNode === 'experiment_workorder_generation' && (isThinking || isStreaming) ? '生成中...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              
              <!-- 生成中提示 -->
              <div v-if="currentNode === 'experiment_workorder_generation' && isThinking" class="processing-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>{{ thinkingText }}</span>
              </div>
              
              <!-- 流式输出内容 -->
              <div 
                v-else
                class="node-content" 
                :class="{ 'streaming': currentNode === 'experiment_workorder_generation' && isStreaming }"
                v-html="formatContent(getNodeMessage('experiment_workorder_generation')?.content)"
              ></div>
            </el-card>

            <!-- 8. 等待实验结果输入节点 -->
            <el-card 
              v-if="getNodeMessage('await_experiment_results')"
              class="node-card" 
              shadow="hover"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon">
                      <DataLine />
                    </el-icon>
                    <span>等待实验结果</span>
                  </div>
                  <el-tag type="info" size="small">待输入</el-tag>
                </div>
              </template>
              <div class="node-content">
                <el-alert 
                  type="info" 
                  :closable="false"
                  title="请输入实验测试结果"
                  description="完成实验后，请输入实际测得的性能数据以进行对比分析"
                />
                <!-- TODO: 添加实验结果输入表单 -->
              </div>
            </el-card>

            <!-- 9. 实验结果分析节点 -->
            <el-card 
              v-if="getNodeMessage('experiment_result_analysis') || (currentNode === 'experiment_result_analysis' && isStreaming)"
              class="node-card" 
              shadow="hover"
              :class="{ 'processing': currentNode === 'experiment_result_analysis' && isStreaming }"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon" :class="{ 'is-loading': currentNode === 'experiment_result_analysis' && isStreaming }">
                      <TrendCharts />
                    </el-icon>
                    <span>实验结果分析</span>
                  </div>
                  <el-tag 
                    :type="currentNode === 'experiment_result_analysis' && isStreaming ? 'warning' : 'success'" 
                    size="small"
                  >
                    {{ currentNode === 'experiment_result_analysis' && isStreaming ? '分析中...' : '已完成' }}
                  </el-tag>
                </div>
              </template>
              <div 
                class="node-content" 
                :class="{ 'streaming': currentNode === 'experiment_result_analysis' && isStreaming }"
                v-html="formatContent(getNodeMessage('experiment_result_analysis')?.content)"
              ></div>
            </el-card>

            <!-- 10. 迭代决策节点 -->
            <el-card 
              v-if="getNodeMessage('decide_next_iteration')"
              class="node-card" 
              shadow="hover"
            >
              <template #header>
                <div class="node-header">
                  <div class="node-title">
                    <el-icon class="node-icon">
                      <Refresh />
                    </el-icon>
                    <span>迭代决策</span>
                  </div>
                  <el-tag type="success" size="small">已决策</el-tag>
                </div>
              </template>
              <div class="node-content">
                <div style="padding: 16px;">
                  <h3 style="margin: 0 0 12px 0;">📋 决策结果</h3>
                  <p><strong>决策：</strong>{{ getNodeMessage('decide_next_iteration')?.data?.next_action }}</p>
                  <p><strong>原因：</strong>{{ getNodeMessage('decide_next_iteration')?.data?.decision_reason }}</p>
                  <p><strong>下一步：</strong>{{ getNodeMessage('decide_next_iteration')?.data?.next_step }}</p>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ChatDotRound, Loading, CircleCheck, Cpu, Histogram, 
  Document, DataAnalysis, MagicStick, Tickets, Orange, Grid, Setting, ArrowDown,
  DataLine, TrendCharts, Refresh
} from '@element-plus/icons-vue'
import SessionSidebar from './components/SessionSidebar.vue'
import CoatingInputForm from './components/CoatingInputForm.vue'
import PredictionResults from './components/PredictionResults.vue'
import OptimizationSuggestions from './components/OptimizationSuggestions.vue'
import { useWebSocket } from './composables/useWebSocket'
import { marked } from 'marked'

// ============ 会话管理 ============
// 会话列表
const sessions = ref([])
// 当前会话ID
const currentSessionId = ref(null)

// LocalStorage键
const SESSIONS_KEY = 'topmat_sessions'
const CURRENT_SESSION_KEY = 'topmat_current_session'
const TASK_ID_KEY = 'topmat_current_task_id'
const MESSAGES_KEY = 'topmat_messages'

// ============ 消息和状态 ============
// 连接状态
const connectionStatus = ref(false)
// 当前任务ID
const currentTaskId = ref(null)
// 消息列表
const messages = ref([])
// 处理状态
const isProcessing = ref(false)
const isStreaming = ref(false)
const isThinking = ref(false)
const thinkingText = ref('正在分析中...')
// 当前处理的节点
const currentNode = ref('')
// 流式输出缓存
const streamBuffer = ref({})

// ============ UI状态 ============
// 结果容器ref
const resultsContainer = ref(null)
// 当前激活的优化tab
const activeOptimizationTab = ref('p1')
// 自动滚动控制
const autoScrollEnabled = ref(true)
const showScrollToBottom = ref(false)

// WebSocket连接
const { connect, send, disconnect, isConnected } = useWebSocket()

// 处理表单提交
const handleFormSubmit = (formData) => {
  console.log('表单提交:', formData)
  
  // 清空之前的消息（开始新任务）
  messages.value = []
  streamBuffer.value = {}
  
  // 设置处理状态
  isProcessing.value = true
  isThinking.value = true
  thinkingText.value = '正在验证参数...'
  
  // 发送到后端
  send({
    type: 'start_workflow',
    data: formData
  })
  
  ElMessage.success('已提交，开始分析...')
}

// 渲染Markdown内容（使用marked库统一渲染）
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked(content, {
      breaks: true,  // 支持换行符转换为<br>
      gfm: true      // 支持GitHub Flavored Markdown
    })
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return content
  }
}

// 兼容旧的formatContent函数
const formatContent = renderMarkdown

// 根据节点ID获取消息
const getNodeMessage = (nodeId) => {
  return messages.value.find(msg => msg.nodeId === nodeId && msg.role === 'assistant')
}


// 获取优化进度
const getOptimizationProgress = () => {
  if (currentNode.value === 'p1_composition_optimization') return 33
  if (currentNode.value === 'p2_structure_optimization') return 66
  if (currentNode.value === 'p3_process_optimization') return 100
  return 0
}

// 获取优化状态文本
const getOptimizationStatusText = () => {
  if (currentNode.value === 'p1_composition_optimization') return '正在生成成分优化方案...'
  if (currentNode.value === 'p2_structure_optimization') return '正在生成结构优化方案...'
  if (currentNode.value === 'p3_process_optimization') return '正在生成工艺优化方案...'
  return '准备生成优化建议...'
}

// 获取优化整体状态
const getOptimizationStatus = () => {
  const p1Done = !!getNodeMessage('p1_composition_optimization')
  const p2Done = !!getNodeMessage('p2_structure_optimization')
  const p3Done = !!getNodeMessage('p3_process_optimization')
  
  if (p1Done && p2Done && p3Done) return '已完成'
  if (['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(currentNode.value)) {
    return '生成中...'
  }
  return '生成中...'
}

// 自动滚动到底部
const scrollToBottom = (force = false) => {
  if (!resultsContainer.value) return
  
  // 只在启用自动滚动或强制滚动时执行
  if (!autoScrollEnabled.value && !force) return
  
  setTimeout(() => {
    resultsContainer.value.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'end' 
    })
    showScrollToBottom.value = false
  }, 100)
}

// 检测用户是否在底部
const checkIfAtBottom = () => {
  const container = document.querySelector('.main-content')
  if (!container) return true
  
  const scrollTop = container.scrollTop
  const scrollHeight = container.scrollHeight
  const clientHeight = container.clientHeight
  
  // 如果距离底部小于100px，认为在底部
  return (scrollHeight - scrollTop - clientHeight) < 100
}

// 监听用户滚动
let scrollTimeout = null
const handleUserScroll = () => {
  // 清除之前的延迟
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
  
  // 检测用户是否在底部
  const isAtBottom = checkIfAtBottom()
  
  if (!isAtBottom) {
    // 用户向上滚动，立即暂停自动滚动
    autoScrollEnabled.value = false
    showScrollToBottom.value = true
  }
  
  // 延迟检测恢复，避免频繁触发
  scrollTimeout = setTimeout(() => {
    const isAtBottom = checkIfAtBottom()
    
    console.log('[滚动检测]', { 
      isAtBottom, 
      autoScrollEnabled: autoScrollEnabled.value, 
      showButton: showScrollToBottom.value 
    })
    
    if (isAtBottom) {
      // 用户滚动到底部，恢复自动滚动
      autoScrollEnabled.value = true
      showScrollToBottom.value = false
    }
  }, 50)  // 50ms 防抖，提高响应速度
}

// 监听消息变化，自动滚动（仅在启用自动滚动时）
watch(messages, () => {
  // 只有在自动滚动启用时才滚动，避免打断用户浏览
  if (autoScrollEnabled.value) {
    scrollToBottom()
  }
}, { deep: true })

// 监听流式输出，自动滚动（仅在启用自动滚动时）
watch(isStreaming, (newVal) => {
  if (newVal && autoScrollEnabled.value) {
    scrollToBottom()
  }
})

// 手动恢复自动滚动
const resumeAutoScroll = () => {
  console.log('[点击按钮] 恢复自动滚动')
  autoScrollEnabled.value = true
  showScrollToBottom.value = false
  scrollToBottom(true)  // 强制滚动到底部
}

// 监听按钮显示状态变化（调试用）
watch(showScrollToBottom, (newVal) => {
  console.log('[按钮状态]', newVal ? '显示' : '隐藏')
})

// 监听当前节点变化，自动切换tab
watch(currentNode, (newNode) => {
  if (newNode === 'p1_composition_optimization') {
    activeOptimizationTab.value = 'p1'
    scrollToBottom()
  } else if (newNode === 'p2_structure_optimization') {
    activeOptimizationTab.value = 'p2'
    scrollToBottom()
  } else if (newNode === 'p3_process_optimization') {
    activeOptimizationTab.value = 'p3'
    scrollToBottom()
  }
})

// 处理优化方案选择
const handleOptimizationSelect = (selection) => {
  // 添加用户选择消息
  messages.value.push({
    role: 'user',
    content: `已选择 ${selection.type} 优化方案`,
    timestamp: new Date().toISOString()
  })

  // 设置处理状态
  isProcessing.value = true
  isThinking.value = true
  thinkingText.value = '正在处理您的选择...'

  // 发送选择到后端
  send({
    type: 'select_optimization',
    data: selection
  })

  ElMessage.success(`已确认选择 ${selection.type}，继续执行工作流...`)
}

// 创建AI消息
const createAIMessage = (content = '', data = null, nodeId = null) => {
  return {
    role: 'assistant',
    content: content,
    data: data,
    nodeId: nodeId,
    timestamp: new Date().toISOString()
  }
}

// 为节点创建新消息
const createNodeMessage = (node) => {
  const nodeTitle = getNodeTitle(node)
  messages.value.push(createAIMessage(`**${nodeTitle}**\n\n`, null, node))
}

// 更新指定节点的消息
const updateNodeMessage = (node, content, data = null) => {
  // 查找该节点的消息
  const nodeMessage = messages.value.find(msg => msg.nodeId === node && msg.role === 'assistant')
  if (nodeMessage) {
    const nodeTitle = getNodeTitle(node)
    nodeMessage.content = `**${nodeTitle}**\n\n${content}`
    if (data) {
      nodeMessage.data = { ...nodeMessage.data, ...data }
    }
  }
}

// 获取节点标题
const getNodeTitle = (node) => {
  const titles = {
    'requirement_extraction': '📋 需求分析',
    'input_validation': '✅ 输入验证',
    // 性能预测拆分为4个子节点
    'topphi_simulation': '🔬 TopPhi第一性原理模拟',
    'ml_prediction': '🤖 ML模型性能预测',
    'historical_comparison': '📚 历史数据比对',
    'integrated_analysis': '📊 综合分析与根因',
    'performance_prediction': '📊 性能预测与根因分析',  // 保留兼容
    // 优化建议拆分为P1/P2/P3
    'p1_composition_optimization': '💡 P1: 成分优化',
    'p2_structure_optimization': '🔧 P2: 结构优化',
    'p3_process_optimization': '⚙️ P3: 工艺优化',
    'optimization_summary': 'Ὂ1 优化建议汇总',
    'optimization_suggestion': 'Ὂ1 优化建议',  // 兼容
    'experiment_workorder_generation': '🎫 实验工单生成',
    'await_experiment_results': '📊 等待实验结果',
    'experiment_result_analysis': '📈 实验结果分析',
    'decide_next_iteration': '🔄 迭代决策'
  }
  return titles[node] || node
}

// ============ 会话管理函数 ============
// 生成会话ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 生成会话标题（从第一条用户消息提取）
const generateSessionTitle = (msgs) => {
  if (!msgs || msgs.length === 0) return '新对话'
  const firstUserMsg = msgs.find(m => m.role === 'user')
  if (firstUserMsg && firstUserMsg.content) {
    // 截取前30个字符作为标题
    return firstUserMsg.content.substring(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '')
  }
  return '新对话'
}

// 创建新会话
const handleCreateSession = () => {
  // 保存当前会话
  if (currentSessionId.value) {
    saveCurrentSession()
  }

  // 创建新会话
  const newSession = {
    id: generateSessionId(),
    title: '新对话',
    messages: [],
    taskId: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messageCount: 0
  }

  sessions.value.push(newSession)
  currentSessionId.value = newSession.id

  // 清空当前消息和状态
  messages.value = []
  currentTaskId.value = null
  streamBuffer.value = {}
  isProcessing.value = false
  isStreaming.value = false
  isThinking.value = false

  // 保存到localStorage
  saveSessions()
  
  ElMessage.success('已创建新对话')
}

// 选择会话
const handleSelectSession = (sessionId) => {
  // 保存当前会话
  if (currentSessionId.value) {
    saveCurrentSession()
  }

  // 加载选中的会话
  const session = sessions.value.find(s => s.id === sessionId)
  if (session) {
    currentSessionId.value = session.id
    messages.value = session.messages || []
    currentTaskId.value = session.taskId || null
    streamBuffer.value = {}
    
    // 如果有任务ID，尝试重连
    if (session.taskId) {
      tryRestoreTask(session.taskId)
    }
    
    console.log(`已切换到会话: ${session.title}`)
  }
}

// 重命名会话
const handleRenameSession = ({ sessionId, newTitle }) => {
  const session = sessions.value.find(s => s.id === sessionId)
  if (session) {
    session.title = newTitle
    session.updatedAt = new Date().toISOString()
    saveSessions()
  }
}

// 删除会话
const handleDeleteSession = (sessionId) => {
  const index = sessions.value.findIndex(s => s.id === sessionId)
  if (index !== -1) {
    sessions.value.splice(index, 1)
    
    // 如果删除的是当前会话，切换到第一个会话或创建新会话
    if (sessionId === currentSessionId.value) {
      if (sessions.value.length > 0) {
        handleSelectSession(sessions.value[0].id)
      } else {
        handleCreateSession()
      }
    }
    
    saveSessions()
  }
}

// 保存当前会话
const saveCurrentSession = () => {
  if (!currentSessionId.value) return
  
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.messages = [...messages.value]
    session.taskId = currentTaskId.value
    session.updatedAt = new Date().toISOString()
    session.messageCount = messages.value.length
    
    // 自动更新标题（如果还是默认标题）
    if (session.title === '新对话' && messages.value.length > 0) {
      session.title = generateSessionTitle(messages.value)
    }
  }
}

// 保存所有会话到localStorage
const saveSessions = () => {
  try {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.value))
    localStorage.setItem(CURRENT_SESSION_KEY, currentSessionId.value || '')
  } catch (error) {
    console.error('保存会话失败:', error)
  }
}

// 从localStorage加载会话
const loadSessions = () => {
  try {
    const savedSessions = localStorage.getItem(SESSIONS_KEY)
    const savedCurrentId = localStorage.getItem(CURRENT_SESSION_KEY)
    
    if (savedSessions) {
      sessions.value = JSON.parse(savedSessions)
      console.log(`已加载 ${sessions.value.length} 个会话`)
    }
    
    // 恢复当前会话
    if (savedCurrentId && sessions.value.find(s => s.id === savedCurrentId)) {
      currentSessionId.value = savedCurrentId
      const currentSession = sessions.value.find(s => s.id === savedCurrentId)
      if (currentSession) {
        messages.value = currentSession.messages || []
        currentTaskId.value = currentSession.taskId || null
      }
    } else if (sessions.value.length > 0) {
      // 如果没有保存的当前会话ID，使用第一个
      currentSessionId.value = sessions.value[0].id
      messages.value = sessions.value[0].messages || []
      currentTaskId.value = sessions.value[0].taskId || null
    } else {
      // 如果没有任何会话，创建一个新的
      handleCreateSession()
    }
  } catch (error) {
    console.error('加载会话失败:', error)
    // 创建默认会话
    handleCreateSession()
  }
}

// ============ 消息管理函数 ============
// 保存消息到localStorage（已废弃，使用saveCurrentSession）
const saveMessagesToStorage = () => {
  saveCurrentSession()
  saveSessions()
}

// 从 localStorage 恢复消息（已废弃，使用loadSessions）
const restoreMessagesFromStorage = () => {
  // 这个函数现在被loadSessions替代
  console.log('使用loadSessions替代restoreMessagesFromStorage')
}

// 清除localStorage中的任务数据
const clearTaskStorage = () => {
  // 只清除当前任务ID，保留会话数据
  if (currentSessionId.value) {
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      session.taskId = null
      currentTaskId.value = null
      saveSessions()
    }
  }
}

// 尝试恢复任务
const tryRestoreTask = (taskId) => {
  const taskIdToRestore = taskId || currentTaskId.value
  if (taskIdToRestore) {
    console.log(`尝试恢复任务: ${taskIdToRestore}`)
    ElMessage.info('正在恢复之前的任务...')
    
    send({
      type: 'reconnect',
      task_id: taskIdToRestore
    })
    
    // 设置超时，如果5秒内没有恢复成功，清除任务ID
    setTimeout(() => {
      if (currentTaskId.value === null || currentTaskId.value !== taskIdToRestore) {
        console.log('任务恢复超时，清除本地存储')
        clearTaskStorage()
        ElMessage.warning('无法恢复之前的任务，请重新开始')
      }
    }, 5000)
  }
}

// WebSocket消息处理
const handleWebSocketMessage = (data) => {
  switch (data.type) {
    case 'connected':
      connectionStatus.value = true
      // 连接成功后尝试恢复任务
      setTimeout(() => {
        tryRestoreTask()
      }, 100)
      break
    
    case 'task_restored':
      // 任务状态恢复成功
      currentTaskId.value = data.task_id
      console.log(`任务 ${data.task_id} 已恢复`, data.state)
      
      // 恢复消息历史
      restoreMessagesFromStorage()
      
      // 根据状态恢复界面
      if (data.state.workflow_status === 'awaiting_optimization_selection') {
        // 正在等待用户选择 - 重新显示优化建议
        if (data.state.optimization_suggestions) {
          // 查找或创建优化建议消息
          const existingMsg = messages.value.find(msg => 
            msg.nodeId === 'optimization_summary' && msg.role === 'assistant'
          )
          
          if (existingMsg) {
            // 更新现有消息的数据
            existingMsg.data = {
              ...existingMsg.data,
              optimization_suggestions: data.state.optimization_suggestions
            }
          } else {
            // 创建新的优化建议消息（如果消息历史中没有）
            messages.value.push(createAIMessage(
              '已生成优化建议',
              { optimization_suggestions: data.state.optimization_suggestions },
              'optimization_summary'
            ))
          }
        }
        
        isProcessing.value = false
        isThinking.value = false
        ElMessage.success('任务已恢复，请选择优化方案')
      } else if (data.state.workflow_status === 'completed') {
        isProcessing.value = false
        isThinking.value = false
        ElMessage.info('任务已完成')
      }
      break

    case 'status':
      // 保存任务ID（如果有）
      if (data.task_id && !currentTaskId.value) {
        currentTaskId.value = data.task_id
        localStorage.setItem(TASK_ID_KEY, data.task_id)
      }
      
      // 更新思考文本
      currentNode.value = data.node
      thinkingText.value = `${getNodeName(data.node)}: ${data.message}`
      
      // 只为LLM节点创建消息占位，非LLM节点由node_result创建
      const llmNodes = [
        'topphi_simulation',
        'ml_prediction',
        'integrated_analysis',
        'p1_composition_optimization',
        'p2_structure_optimization',
        'p3_process_optimization',
        'optimization_summary',  // 综合建议生成
        'experiment_workorder_generation',  // 实验工单生成
        'experiment_result_analysis'  // 实验结果分析
      ]
      
      if (llmNodes.includes(data.node) && !streamBuffer.value[data.node]) {
        // 为LLM节点创建消息占位，准备接收流式输出
        createNodeMessage(data.node)
        streamBuffer.value[data.node] = 'processing' // 标记为处理中
        isThinking.value = false
        isStreaming.value = false
        console.log(`[Status] 为LLM节点 ${data.node} 创建占位`)
      } else if (!isStreaming.value) {
        // 非LLM节点显示思考指示器
        isThinking.value = true
      }
      break

    case 'llm_stream':
      // 处理LLM流式输出
      handleLLMStream(data.node, data.content)
      break

    case 'node_result':
      // 处理节点完整结果
      handleNodeResult(data.node, data.result)
      // 收到节点结果后，清除thinking状态
      isThinking.value = false
      // 保存消息
      saveMessagesToStorage()
      break

    case 'await_user_selection':
      // 等待用户选择优化方案
      if (data.task_id && !currentTaskId.value) {
        currentTaskId.value = data.task_id
        localStorage.setItem(TASK_ID_KEY, data.task_id)
      }
      
      // 确保优化建议数据正确显示
      if (data.suggestions) {
        console.log('[前端] 收到优化建议:', data.suggestions)
        // 查找或创建优化建议消息
        const existingMsg = messages.value.find(msg => 
          msg.nodeId === 'optimization_summary' && msg.role === 'assistant'
        )
        
        if (existingMsg) {
          // 更新现有消息的数据
          console.log('[前端] 更新现有优化建议消息')
          existingMsg.data = {
            ...existingMsg.data,
            optimization_suggestions: data.suggestions,
            comprehensive_recommendation: data.comprehensive_recommendation || ''
          }
        } else {
          // 创建新的优化建议消息（如果消息历史中没有）
          console.log('[前端] 创建新的优化建议消息')
          messages.value.push(createAIMessage(
            '已生成优化建议，请选择方案',
            { 
              optimization_suggestions: data.suggestions,
              comprehensive_recommendation: data.comprehensive_recommendation || ''
            },
            'optimization_summary'
          ))
        }
      }
      
      isProcessing.value = false
      isStreaming.value = false
      isThinking.value = false
      thinkingText.value = data.message || '请选择优化方案'
      // 保存消息历史，以便重连恢复
      saveMessagesToStorage()
      break

    case 'complete':
      // 工作流完成
      isProcessing.value = false
      isStreaming.value = false
      isThinking.value = false
      streamBuffer.value = {}
      // 清除任务状态
      clearTaskStorage()
      currentTaskId.value = null
      ElMessage.success('优化分析完成')
      break

    case 'error':
      isProcessing.value = false
      isStreaming.value = false
      isThinking.value = false
      
      // 如果是任务不存在的错误，清除本地存储
      if (data.message && (data.message.includes('不存在') || data.message.includes('已过期'))) {
        console.log('任务已失效，清除本地存储')
        clearTaskStorage()
        currentTaskId.value = null
        ElMessage.error('任务已失效，请重新提交')
      } else {
        ElMessage.error(data.message)
      }
      
      messages.value.push(createAIMessage(`抱歉，处理过程中出现错误：${data.message}`))
      break
  }
}

// 获取节点名称 - 增强版，类似ChatGPT的思考描述
const getNodeName = (node) => {
  const names = {
    input_validation: '验证输入参数，检查数据合理性',
    topphi_simulation: '运行第一性原理计算，预测微观结构',
    ml_prediction: '启动机器学习模型，预测性能指标',
    historical_comparison: '检索历史数据库，查找相似案例',
    integrated_analysis: '深度分析多源数据，生成根因报告',
    performance_prediction: '整合所有预测结果，评估性能表现',
    p1_composition_optimization: '生成成分优化方案，调整元素配比',
    p2_structure_optimization: '设计结构优化方案，改进层结构',
    p3_process_optimization: '规划工艺优化方案，调优工艺参数',
    optimization_summary: '汇总优化建议，准备方案选择',
    optimization_suggestion: '整理优化建议，待用户确认',
    experiment_workorder_generation: '生成实验工单，规划具体实验步骤',
    iteration_optimization: '生成实验工单，规划具体定验步骤',  // 兼容
    await_experiment_results: '等待用户输入实验测试结果',
    experiment_result_analysis: '分析实验结果，生成根因报告',
    decide_next_iteration: '决策下一步迭代方向',
    iteration_planning: '制定迭代计划，准备下一轮优化',
    result_summary: '生成最终报告，总结优化结果'
  }
  return names[node] || node
}

// 处理LLM流式输出
const handleLLMStream = (node, content) => {
  isThinking.value = false
  isStreaming.value = true

  // 初始化缓冲区
  if (!streamBuffer.value[node]) {
    streamBuffer.value[node] = ''
    // 为新节点创建新消息
    createNodeMessage(node)
    console.log(`[LLM流式] 为节点 ${node} 创建新消息`)
  } else if (streamBuffer.value[node] === 'processing') {
    // 如果是processing状态，重置为空字符串开始累积
    streamBuffer.value[node] = ''
  }

  // 累积内容
  if (typeof streamBuffer.value[node] === 'string') {
    streamBuffer.value[node] += content
  } else {
    streamBuffer.value[node] = content
  }

  // 更新当前节点的消息（不影响之前的消息）
  updateNodeMessage(node, streamBuffer.value[node])
  
  // 调试日志
  if (streamBuffer.value[node].length % 100 === 0) {
    console.log(`[LLM流式] 节点 ${node} 累积内容长度: ${streamBuffer.value[node].length}`)
  }
}

// 处理节点结果
const handleNodeResult = (nodeName, result) => {
  isStreaming.value = false

  // TopPhi模拟结果
  if (nodeName === 'topphi_simulation') {
    // 防止重复处理
    if (streamBuffer.value[nodeName] === 'completed') {
      console.log('[TopPhi结果] 已处理，跳过')
      return
    }
    console.log('[TopPhi结果]', result)
    
    const content = `**模拟完成**

🔬 **微观结构预测**
- 晶粒尺寸: **${result.grain_size_nm || 'N/A'} nm**
- 择优取向: **${result.preferred_orientation || 'N/A'}**
- 残余应力: **${result.residual_stress_gpa || 'N/A'} GPa**
- 晶格常数: ${result.lattice_constant || 'N/A'} Å
- 形成能: ${result.formation_energy || 'N/A'} eV
- 置信度: **${result.confidence ? (result.confidence * 100).toFixed(0) : 'N/A'}%**

✅ 模拟耗时: ${result.simulation_time || 'N/A'}秒`
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { topphi: result })
    streamBuffer.value[nodeName] = 'completed'
  }

  // ML模型预测结果
  if (nodeName === 'ml_prediction') {
    // 防止重复处理
    if (streamBuffer.value[nodeName] === 'completed') {
      console.log('[ML预测结果] 已处理，跳过')
      return
    }
    console.log('[ML预测结果]', result)
    
    const content = `**预测完成**

🤖 **性能指标预测**
- 硬度: **${result.hardness_gpa || 'N/A'} ± ${result.hardness_std || 0} GPa**
- 结合力等级: **${result.adhesion_level || 'N/A'}**
- 耐磨性: ${result.wear_rate ? result.wear_rate.toExponential(2) : 'N/A'} mm³/Nm
- 抗氧化温度: **${result.oxidation_temp_c || 'N/A'}℃**
- 摩擦系数: ${result.friction_coefficient || 'N/A'}

🎯 **关键影响因素**
${Object.entries(result.feature_importance || {}).map(([key, value]) => 
  `- ${key}: ${(value * 100).toFixed(0)}%`
).join('\n') || '未提供'}

✅ 模型置信度: **${result.model_confidence ? (result.model_confidence * 100).toFixed(0) : 'N/A'}%**`
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { ml_pred: result })
    streamBuffer.value[nodeName] = 'completed'
  }

  // 历史数据比对结果
  if (nodeName === 'historical_comparison') {
    // 防止重复处理
    if (streamBuffer.value[nodeName] === 'completed') {
      console.log('[历史比对结果] 已处理，跳过')
      return
    }
    console.log('[历史比对结果]', result)
    
    // 确保 result 是数组
    if (!Array.isArray(result)) {
      console.error('[历史比对结果] 错误的数据类型:', typeof result)
      return
    }
    
    const cases = result
    const content = `**找到 ${cases.length} 个相似案例**

📚 **历史案例分析**

${cases.map((c, i) => 
  `**${i + 1}. ${c.case_id}**
- 相似度: **${(c.similarity_score * 100).toFixed(0)}%**
- 成分: Al ${c.composition?.al_content || 'N/A'}%, Ti ${c.composition?.ti_content || 'N/A'}%, N ${c.composition?.n_content || 'N/A'}%
- 实际硬度: **${c.actual_hardness} GPa**
- 结合力: ${c.actual_adhesion}
- 与预测偏差: ${c.deviation_from_prediction}
- 应用场景: ${c.application}`
).join('\n\n')}

💡 历史数据可为本次预测提供重要参考`
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { historical: cases })
    streamBuffer.value[nodeName] = 'completed'
  }

  // 综合分析（性能预测）结果
  if (nodeName === 'performance_prediction' || nodeName === 'integrated_analysis') {
    const nodeId = 'integrated_analysis'
    
    // 防止重复处理
    if (streamBuffer.value[nodeId] === 'completed') {
      console.log(`[综合分析结果] ${nodeName} 已处理，跳过`)
      return
    }
    
    console.log(`[综合分析结果] ${nodeName}`, result)
    
    // 优先使用流式缓冲区的内容（如果有流式输出）
    let content = ''
    if (streamBuffer.value[nodeId] && typeof streamBuffer.value[nodeId] === 'string' && streamBuffer.value[nodeId].length > 0 && streamBuffer.value[nodeId] !== 'processing') {
      content = streamBuffer.value[nodeId]
      console.log(`[节点结果] ${nodeName} - 使用流式缓冲区内容，长度: ${content.length}`)
    } else if (result.root_cause_analysis) {
      content = result.root_cause_analysis
      console.log(`[节点结果] ${nodeName} - 使用结果数据，长度: ${content.length}`)
    }
    
    // 只在有内容时才更新，避免重复显示
    if (content && content !== 'processing') {
      if (!streamBuffer.value[nodeId] || streamBuffer.value[nodeId] === 'processing') {
        createNodeMessage(nodeId)
      }
      // 不再传递performance_prediction，综合分析只显示文本内容
      updateNodeMessage(nodeId, content, {})
      streamBuffer.value[nodeId] = 'completed'
    }
  }

  // P1成分优化结果
  if (nodeName === 'p1_composition_optimization') {
    const content = streamBuffer.value[nodeName] || result.content || '成分优化建议已生成'
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { p1_suggestions: result.suggestions })
    streamBuffer.value[nodeName] = 'completed'
  }

  // P2结构优化结果
  if (nodeName === 'p2_structure_optimization') {
    const content = streamBuffer.value[nodeName] || result.content || '结构优化建议已生成'
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { p2_suggestions: result.suggestions })
    streamBuffer.value[nodeName] = 'completed'
  }

  // P3工艺优化结果
  if (nodeName === 'p3_process_optimization') {
    const content = streamBuffer.value[nodeName] || result.content || '工艺优化建议已生成'
    
    if (!streamBuffer.value[nodeName] || streamBuffer.value[nodeName] === 'processing') {
      createNodeMessage(nodeName)
    }
    updateNodeMessage(nodeName, content, { p3_suggestions: result.suggestions })
    streamBuffer.value[nodeName] = 'completed'
  }

  // 优化建议汇总结果
  if (nodeName === 'optimization_suggestion' || nodeName === 'optimization_summary') {
    // 使用optimization_summary作为节点ID
    const nodeId = 'optimization_summary'
    let content = ''
    
    if (streamBuffer.value[nodeId] && typeof streamBuffer.value[nodeId] === 'string' && streamBuffer.value[nodeId].length > 0 && streamBuffer.value[nodeId] !== 'processing') {
      content = streamBuffer.value[nodeId]
    } else {
      content = '已生成优化建议'
    }
    
    if (!streamBuffer.value[nodeId] || streamBuffer.value[nodeId] === 'processing') {
      createNodeMessage(nodeId)
    }
    
    updateNodeMessage(nodeId, content, { 
      optimization_suggestions: result.optimization_suggestions,
      comprehensive_recommendation: result.comprehensive_recommendation || ''
    })
    streamBuffer.value[nodeId] = 'completed'
  }

  // 迭代结果
  if (nodeName === 'iteration_result') {
    const content = `**第 ${result.iteration} 次迭代完成**\n\n${result.analysis || ''}`
    messages.value.push(createAIMessage(content, { iteration_result: result }))
  }
}

// 监听会话变化，自动保存
watch(() => messages.value.length, () => {
  if (currentSessionId.value) {
    saveCurrentSession()
    saveSessions()
  }
})

// 生命周期钩子
onMounted(() => {
  // 加载会话历史
  loadSessions()
  
  // 连接WebSocket
  connect('ws://localhost:8000/ws', handleWebSocketMessage)
  connectionStatus.value = isConnected.value
  
  // 如果有当前任务，尝试恢复
  if (currentTaskId.value) {
    setTimeout(() => {
      tryRestoreTask(currentTaskId.value)
    }, 500)
  }
  
  // 添加滚动监听
  setTimeout(() => {
    const mainContent = document.querySelector('.main-content')
    if (mainContent) {
      console.log('[滚动监听] 已添加到 .main-content')
      mainContent.addEventListener('scroll', handleUserScroll)
    } else {
      console.error('[滚动监听] 找不到 .main-content 元素')
    }
  }, 500)
})

onUnmounted(() => {
  // 保存当前会话
  if (currentSessionId.value) {
    saveCurrentSession()
    saveSessions()
  }
  
  // 移除滚动监听
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    mainContent.removeEventListener('scroll', handleUserScroll)
  }
  
  disconnect()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  background: #F5F5F5;
}

/* 主工作区 */
.main-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航栏 */
.header {
  background: white;
  border-bottom: 1px solid #E4E7ED;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-desc {
  color: #909399;
  font-size: 14px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #F5F5F5;
}

/* 表单区域 */
.form-section {
  max-width: 1200px;
  margin: 0 auto 20px;
}

/* 结果展示区 */
.result-section {
  max-width: 1200px;
  margin: 0 auto;
}


/* 工作流结果容器 */
.workflow-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 节点卡片 */
.node-card {
  background: white;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  animation: slideIn 0.4s ease-out;
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

.node-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.node-card.processing {
  border-color: #E6A23C;
  background: linear-gradient(to right, #FFF7E6 0%, white 100%);
}

/* 节点头部 */
.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.node-icon {
  font-size: 22px;
  color: #409EFF;
}

.node-icon.is-loading {
  color: #E6A23C;
}

/* 节点内容 */
.node-content {
  padding: 16px 0;
  color: #606266;
  line-height: 1.8;
  font-size: 14px;
}

.node-content strong {
  color: #409EFF;
  font-weight: 600;
}

.node-content.streaming {
  position: relative;
}

.node-content.streaming::after {
  content: '▊';
  color: #409EFF;
  animation: blink 1s infinite;
  margin-left: 4px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 处理中指示器 - 增强样式 */
.processing-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 24px;
  background: linear-gradient(135deg, #FFF7E6 0%, #FFF3E0 100%);
  border-radius: 12px;
  border: 2px solid #E6A23C;
  color: #606266;
  font-size: 15px;
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.15);
}

.processing-indicator .el-icon {
  font-size: 48px;
  color: #E6A23C;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.processing-indicator span {
  font-size: 16px;
  font-weight: 600;
  color: #E6A23C;
  text-align: center;
}

.processing-indicator .el-progress {
  width: 100%;
  max-width: 500px;
}

.processing-indicator p {
  margin: 8px 0 0 0;
  color: #909399;
}

/* Markdown渲染样式 - 统一使用marked库渲染 */
/* 标题样式 */
.node-content :deep(h1),
.node-content :deep(.markdown-h1) {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin: 20px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #DCDFE6;
}

.node-content :deep(h2),
.node-content :deep(.markdown-h2) {
  font-size: 20px;
  font-weight: 600;
  color: #409EFF;
  margin: 18px 0 12px 0;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.node-content :deep(h3),
.node-content :deep(.markdown-h3) {
  font-size: 16px;
  font-weight: 600;
  color: #606266;
  margin: 16px 0 10px 0;
}

/* 加粗和强调 */
.node-content :deep(strong),
.node-content :deep(b),
.node-content :deep(.markdown-bold) {
  color: #409EFF;
  font-weight: 600;
}

/* 行内代码 */
.node-content :deep(code),
.node-content :deep(.markdown-code) {
  background: #F5F7FA;
  color: #E6A23C;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

/* 代码块 */
.node-content :deep(pre) {
  background: #F5F7FA;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.node-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #303133;
}

/* 列表样式 */
.node-content :deep(ul),
.node-content :deep(.markdown-ul) {
  margin: 12px 0;
  padding-left: 24px;
  list-style: none;
}

.node-content :deep(ol),
.node-content :deep(.markdown-ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.node-content :deep(li),
.node-content :deep(.markdown-li),
.node-content :deep(.markdown-li-ordered) {
  padding: 6px 0;
  line-height: 1.8;
  position: relative;
}

.node-content :deep(ul > li):before {
  content: '•';
  position: absolute;
  left: -16px;
  color: #409EFF;
  font-weight: bold;
}

.node-content :deep(ol > li) {
  list-style-type: decimal;
  list-style-position: outside;
}

/* 段落 */
.node-content :deep(p) {
  margin: 12px 0;
  line-height: 1.8;
}

/* 引用 */
.node-content :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 4px solid #409EFF;
  background: #F5F9FF;
  color: #606266;
}

/* 链接 */
.node-content :deep(a) {
  color: #409EFF;
  text-decoration: none;
}

.node-content :deep(a:hover) {
  text-decoration: underline;
}

/* 优化方案卡片样式 */
.optimization-card {
  min-height: 400px;
}

.optimization-tabs {
  margin-top: -10px;
}

.optimization-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.optimization-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0 10px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.tab-label .el-icon {
  font-size: 16px;
}

.tab-tag {
  margin-left: 4px;
}

.optimization-tabs :deep(.el-tabs__item) {
  font-weight: 500;
}

.optimization-tabs :deep(.el-tabs__item.is-active) {
  color: #409EFF;
  font-weight: 600;
}

.optimization-tabs :deep(.el-tab-pane) {
  min-height: 300px;
}

.optimization-tabs .el-empty {
  padding: 60px 0;
}

/* 平滑滚动 */
.workflow-results {
  scroll-behavior: smooth;
}

/* 滚动到底部按钮 */
.scroll-to-bottom-btn {
  position: fixed;
  bottom: 40px;
  right: 40px;
  z-index: 9999 !important;
  width: 50px;
  height: 50px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
  background: #409EFF !important;
  border: none;
}

.scroll-to-bottom-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.6);
  background: #66b1ff !important;
}

.scroll-to-bottom-btn :deep(.el-icon) {
  font-size: 20px;
  color: white;
}

/* fade过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
