<template>
  <div class="center-stream">
    <div class="stream-header">
      <div class="header-left">
        <h3>
          <el-icon><ChatDotSquare /></el-icon>
          AI分析过程
        </h3>
        <el-tag v-if="isProcessing" type="warning" effect="dark">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在分析...
        </el-tag>
      </div>
      
      <div class="header-right">
        <el-button-group size="small">
          <el-button @click="scrollToTop">
            <el-icon><Top /></el-icon>
          </el-button>
          <el-button @click="scrollToBottom">
            <el-icon><Bottom /></el-icon>
          </el-button>
        </el-button-group>
        <el-button size="small" @click="clearMessages">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div class="stream-content" ref="streamContainer">
      <!-- 空状态 -->
      <div v-if="!hasSteps && !isProcessing" class="empty-state">
        <el-icon :size="80" color="#c0c4cc"><ChatDotSquare /></el-icon>
        <p>请在左侧配置涂层参数，然后点击“开始分析”</p>
        <p class="subtitle">AI将实时展示分析过程和思路</p>
      </div>

      <!-- 工作流过程显示 -->
      <div v-else class="process-flow">
        <!-- 第一部分：优化前的步骤（参数验证、TopPhi、ML预测、历史对比、根因分析） -->
        <div 
          v-for="(step, index) in stepsBeforeOptimization" 
          :key="step.id || index"
          class="process-step"
          :class="`step-${step.status}`"
        >
          <!-- 步骤头部 -->
          <div class="step-header">
            <div class="step-icon">
              <el-icon v-if="step.status === 'completed'" color="#67C23A">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="step.status === 'error'" color="#F56C6C">
                <CircleClose />
              </el-icon>
              <el-icon v-else class="is-loading" color="#409EFF">
                <Loading />
              </el-icon>
            </div>
            
            <div class="step-info">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-time">{{ formatTime(step.timestamp) }}</div>
            </div>

            <el-tag :type="getStepTagType(step.status)" size="small">
              {{ getStepStatusText(step.status) }}
            </el-tag>
          </div>

          <!-- 步骤内容 - 过滤通用信息 -->
          <div v-if="step.content && !isGenericMessage(step.content)" class="step-content">
            <div v-html="formatContent(step.content)"></div>
          </div>
        </div>

        <!-- 第二部分：优化建议方案卡片（P1/P2/P3 tab） -->
        <div v-if="shouldShowOptimizationCard" class="optimization-card-wrapper">
          <el-card class="optimization-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span style="display: flex; align-items: center; gap: 8px;">
                  <el-icon color="#409EFF"><MagicStick /></el-icon>
                  <span style="font-size: 16px; font-weight: 600;">优化建议方案</span>
                </span>
              </div>
            </template>

            <!-- Tab切换 -->
            <el-tabs v-model="activeTab" type="border-card" class="optimization-tabs">
              <!-- P1 成分优化 -->
              <el-tab-pane label="P1 成分优化" name="P1">
                <!-- P1节点生成内容 -->
                <div v-if="p1Content" class="tab-content">
                  <div class="pure-streaming-output" v-html="formatContent(p1Content)"></div>
                </div>
                
                <el-empty v-else description="等待生成..." :image-size="60" />
              </el-tab-pane>

              <!-- P2 结构优化 -->
              <el-tab-pane label="P2 结构优化" name="P2">
                <!-- P2节点生成内容 -->
                <div v-if="p2Content" class="tab-content">
                  <div class="pure-streaming-output" v-html="formatContent(p2Content)"></div>
                </div>
                
                <el-empty v-else description="等待生成..." :image-size="60" />
              </el-tab-pane>

              <!-- P3 工艺优化 -->
              <el-tab-pane label="P3 工艺优化" name="P3">
                <!-- P3节点生成内容 -->
                <div v-if="p3Content" class="tab-content">
                  <div class="pure-streaming-output" v-html="formatContent(p3Content)"></div>
                </div>
                
                <el-empty v-else description="等待生成..." :image-size="60" />
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>

        <!-- 第三部分：综合建议卡片（独立显示） -->
        <div v-if="comprehensiveRecommendation" class="comprehensive-card-wrapper">
          <el-card class="comprehensive-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span style="display: flex; align-items: center; gap: 8px;">
                  <el-icon color="#67C23A"><ChatDotRound /></el-icon>
                  <span style="font-size: 16px; font-weight: 600;">💡 AI综合建议</span>
                </span>
              </div>
            </template>
            <div class="comprehensive-content" v-html="formatContent(comprehensiveRecommendation)"></div>
          </el-card>
        </div>

        <!-- 第四部分：优化后的已完成步骤（用户选择、实验工单等） -->
        <div 
          v-for="(step, index) in stepsAfterOptimization" 
          :key="step.id || index"
          class="process-step"
          :class="`step-${step.status}`"
        >
          <!-- 步骤头部 -->
          <div class="step-header">
            <div class="step-icon">
              <el-icon v-if="step.status === 'completed'" color="#67C23A">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="step.status === 'error'" color="#F56C6C">
                <CircleClose />
              </el-icon>
              <el-icon v-else class="is-loading" color="#409EFF">
                <Loading />
              </el-icon>
            </div>
            
            <div class="step-info">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-time">{{ formatTime(step.timestamp) }}</div>
            </div>

            <el-tag :type="getStepTagType(step.status)" size="small">
              {{ getStepStatusText(step.status) }}
            </el-tag>
          </div>

          <!-- 步骤内容 - 过滤通用信息 -->
          <div v-if="step.content && !isGenericMessage(step.content)" class="step-content">
            <div v-html="formatContent(step.content)"></div>
          </div>
        </div>

        <!-- 第五部分：当前正在执行的节点（排除P1/P2/P3优化子节点） -->
        <div v-if="isProcessing && currentNodeTitle && !isOptimizationSubNode(currentNode)" class="process-step step-active">
          <!-- 步骤头部 -->
          <div class="step-header">
            <div class="step-icon">
              <el-icon class="is-loading" color="#409EFF">
                <Loading />
              </el-icon>
            </div>
            
            <div class="step-info">
              <div class="step-title">{{ currentNodeTitle }}</div>
              <div class="step-time">正在执行...</div>
            </div>

            <el-tag type="warning" size="small" effect="dark">
              处理中
            </el-tag>
          </div>

          <!-- 流式输出内容 -->
          <div v-if="getCurrentNodeStreamingContent" class="step-content streaming">
            <div v-html="formatContent(getCurrentNodeStreamingContent)"></div>
            <span class="stream-cursor">|</span>
          </div>
          <div v-else class="thinking-indicator">
            <div class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="thinking-text">正在分析...</span>
          </div>
        </div>
      </div>

      <!-- 自动滚动提示 -->
      <transition name="fade">
        <div v-if="showScrollHint" class="scroll-hint">
          <el-button type="primary" size="small" @click="resumeAutoScroll">
            <el-icon><ArrowDown /></el-icon>
            回到底部
          </el-button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
// Vue 3组合式API核心导入
import { ref, computed, watch, nextTick } from 'vue'
// Element Plus消息提示组件
import { ElMessage } from 'element-plus'
// Element Plus图标组件导入
import { 
  ChatDotSquare,   // 聊天图标
  ChatDotRound,    // 圆形聊天图标
  Loading,         // 加载图标
  Top,            // 向上箭头图标
  Bottom,         // 向下箭头图标
  Delete,         // 删除图标
  CircleCheck,    // 圆形勾选图标（已完成）
  CircleClose,    // 圆形关闭图标（错误）
  ArrowDown,      // 向下箭头图标
  MagicStick,     // 优化建议图标
  Check,          // 确认图标
  Document        // 文档图标
} from '@element-plus/icons-vue'
// Markdown渲染库
import { marked } from 'marked'

// ============ 组件属性定义 ============
const props = defineProps({
  processSteps: Array,       // 工作流执行步骤列表
  currentNode: String,       // 当前执行的节点ID
  currentNodeTitle: String,  // 当前节点的中文标题
  isProcessing: Boolean,     // 是否正在处理工作流
  streamingContent: String,  // 当前节点的流式输出内容
  p1Content: String,         // P1成分优化的流式内容
  p2Content: String,         // P2结构优化的流式内容
  p3Content: String,         // P3工艺优化的流式内容
  comprehensiveRecommendation: String  // 综合建议
})

// 通用的获取节点内容函数（用于其他节点）
const getNodeStreamingContent = (nodeId) => {
  const step = props.processSteps?.find(s => s.nodeId === nodeId)
  return step?.content || ''
}

// 检查节点是否正在执行（通用函数）
const isNodeProcessing = (nodeId) => {
  const step = props.processSteps?.find(s => s.nodeId === nodeId)
  return step?.status === 'processing'
}

// ============ 事件发射器定义 ============
const emit = defineEmits(['clear', 'optimization-select'])  // 清空消息事件和优化方案选择事件

// ============ 响应式状态管理 ============
const streamContainer = ref(null)      // 流式内容容器DOM引用
const showScrollHint = ref(false)      // 是否显示滚动提示
const autoScrollEnabled = ref(true)    // 是否启用自动滚动到底部
const activeTab = ref('P1')            // 当前激活的优化建议tab

// ============ 计算属性 ============
// 检查是否有执行步骤
const hasSteps = computed(() => {
  return props.processSteps && props.processSteps.length > 0
})

// 检查是否有流式内容
const hasStreamingContent = computed(() => {
  return props.streamingContent && props.streamingContent.length > 0
})

// 检查是否有优化建议数据
const hasOptimizationSuggestions = computed(() => {
  return props.optimizationSuggestions && Object.keys(props.optimizationSuggestions).length > 0
})

// 检查是否正在执行优化节点或已完成优化
const isOptimizationNode = computed(() => {
  const optimizationNodes = ['p1_composition_optimization', 'p2_structure_optimization', 
                             'p3_process_optimization', 'optimization_summary', 'await_user_selection']
  return optimizationNodes.includes(props.currentNode) || hasOptimizationSuggestions.value
})

// 检查是否显示优化建议卡片（只要有任何一个优化节点在执行或已完成，就显示）
const shouldShowOptimizationCard = computed(() => {
  // 如果是等待用户选择节点，不显示卡片（让用户关注右侧选择面板）
  if (props.currentNode === 'await_user_selection') {
    return false
  }
  
  // 检查是否有任何优化节点在执行或已完成
  const optimizationNodes = ['p1_composition_optimization', 'p2_structure_optimization', 
                             'p3_process_optimization', 'optimization_summary', 'optimization_suggestions']
  
  const hasOptimizationNode = props.processSteps?.some(step => 
    optimizationNodes.includes(step.nodeId) && 
    (step.status === 'processing' || step.status === 'completed')
  )
  
  // 如果currentNode是优化相关节点，或者有P1/P2/P3内容，就显示卡片
  return hasOptimizationNode || optimizationNodes.includes(props.currentNode) || 
         props.p1Content || props.p2Content || props.p3Content
})

// 判断节点是否是优化相关子节点（这些节点不单独显示，只在优化建议卡片中展示）
const isOptimizationSubNode = (nodeId) => {
  const subNodes = [
    'p1_composition_optimization', 
    'p2_structure_optimization', 
    'p3_process_optimization',
    'optimization_summary',  // 综合建议也不在主流程中显示
    'optimization_suggestions'  // 优化建议生成状态也不单独显示
  ]
  return subNodes.includes(nodeId)
}

// 计算属性：将步骤分为优化前和优化后
const stepsBeforeOptimization = computed(() => {
  if (!props.processSteps) return []
  // 优化前的步骤：参数验证、TopPhi、ML预测、历史对比、根因分析
  const beforeNodes = ['input_validation', 'topphi_simulation', 'ml_prediction', 
                       'historical_comparison', 'integrated_analysis']
  return props.processSteps.filter(step => 
    beforeNodes.includes(step.nodeId) && 
    step.nodeId !== props.currentNode &&
    !isOptimizationSubNode(step.nodeId)
  )
})

const stepsAfterOptimization = computed(() => {
  if (!props.processSteps) return []
  // 优化后的步骤：用户选择、实验工单生成等
  const afterNodes = ['user_selection', 'experiment_workorder']
  return props.processSteps.filter(step => 
    afterNodes.includes(step.nodeId) && 
    step.nodeId !== props.currentNode &&
    !isOptimizationSubNode(step.nodeId)
  )
})

// 获取当前节点的流式内容（优先从processSteps获取，否则使用streamingContent）
const getCurrentNodeStreamingContent = computed(() => {
  // 对于正在执行的节点，尝试从processSteps中查找
  if (props.currentNode && props.processSteps) {
    const currentStep = props.processSteps.find(s => s.nodeId === props.currentNode)
    if (currentStep && currentStep.content) {
      return currentStep.content
    }
  }
  // 如果processSteps中没有，使用传入的streamingContent
  return props.streamingContent || ''
})

// ============ 滚动控制函数 ============
// 滚动到内容顶部
const scrollToTop = () => {
  if (streamContainer.value) {
    streamContainer.value.scrollTop = 0     // 设置滚动位置为0
    autoScrollEnabled.value = false         // 禁用自动滚动
  }
}

// 滚动到内容底部
const scrollToBottom = () => {
  nextTick(() => {  // 等待DOM更新完成
    if (streamContainer.value) {
      streamContainer.value.scrollTop = streamContainer.value.scrollHeight  // 滚动到最底部
      autoScrollEnabled.value = true        // 启用自动滚动
      showScrollHint.value = false          // 隐藏滚动提示
    }
  })
}

// 恢复自动滚动功能（响应用户点击回到底部按钮）
const resumeAutoScroll = () => {
  scrollToBottom()
}

// ============ 消息管理函数 ============
// 清空所有消息内容
const clearMessages = () => {
  emit('clear')                    // 发射清空事件到父组件
  ElMessage.success('对话已清空')   // 显示成功提示
}

// ============ 内容格式化函数 ============
// 格式化时间戳为可读时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString()  // 返回本地时间格式
}

// 格式化Markdown内容为HTML
const formatContent = (content) => {
  if (!content) return ''
  try {
    // 配置marked选项
    marked.setOptions({
      breaks: true,    // 支持换行符转换
      gfm: true       // 启用GitHub风格Markdown
    })
    // 使用marked.parse渲染Markdown
    return marked.parse(content)
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return content   // 渲染失败时返回原始内容
  }
}

// ============ 步骤状态处理函数 ============
// 获取步骤标签类型
const getStepTagType = (status) => {
  const typeMap = {
    'completed': 'success',
    'processing': 'warning',
    'error': 'danger',
    'pending': 'info'
  }
  return typeMap[status] || 'info'
}

// 获取步骤状态文本
const getStepStatusText = (status) => {
  const textMap = {
    'completed': '已完成',
    'processing': '执行中',
    'error': '错误',
    'pending': '等待中'
  }
  return textMap[status] || '未知'
}

// 检查是否为通用信息，过滤掉不有意义的内容
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

// ============ 响应式监听器 ============
// 监听步骤数组长度变化，实现自动滚动
watch(() => props.processSteps?.length, () => {
  if (autoScrollEnabled.value) {
    scrollToBottom()
  } else {
    showScrollHint.value = true
  }
})

// 监听流式内容变化，实现自动滚动
watch(() => props.streamingContent, () => {
  if (autoScrollEnabled.value) {
    scrollToBottom()
  }
})

// 监听processSteps变化，在首次出现优化节点时设置初始tab
watch(() => props.processSteps, (newSteps) => {
  if (!newSteps) return
  
  // 查找第一个正在执行的优化节点
  const firstOptNode = newSteps.find(step => 
    ['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization'].includes(step.nodeId) &&
    step.status === 'processing'
  )
  
  // 如果找到且当前tab不匹配，则切换（仅首次）
  if (firstOptNode) {
    if (firstOptNode.nodeId === 'p1_composition_optimization' && activeTab.value !== 'P1') {
      activeTab.value = 'P1'
    } else if (firstOptNode.nodeId === 'p2_structure_optimization' && activeTab.value !== 'P2') {
      activeTab.value = 'P2'
    } else if (firstOptNode.nodeId === 'p3_process_optimization' && activeTab.value !== 'P3') {
      activeTab.value = 'P3'
    }
  }
}, { deep: true })

// 处理用户手动滚动事件
const handleScroll = () => {
  if (!streamContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = streamContainer.value
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10
  
  if (isAtBottom) {
    autoScrollEnabled.value = true
    showScrollHint.value = false
  } else {
    autoScrollEnabled.value = false
    showScrollHint.value = true
  }
}

// ============ 优化建议相关函数 ============
// 获取指定类型的优化建议
const getSuggestionsByType = (type) => {
  if (!props.optimizationSuggestions) return []
  
  // 尝试多种可能的key格式
  const possibleKeys = [
    type,
    `${type}_成分优化`,
    `${type}_结构优化`,
    `${type}_工艺优化`
  ]
  
  for (const key of possibleKeys) {
    if (props.optimizationSuggestions[key] && Array.isArray(props.optimizationSuggestions[key])) {
      return props.optimizationSuggestions[key]
    }
  }
  
  return []
}

</script>

<style scoped>
/* ============ 中间流式面板主体布局 ============ */
.center-stream {
  flex: 1;                         /* 占用剩余全部空间 */
  height: 100vh;                   /* 高度：全屏高度 */
  background: white;               /* 白色背景 */
  display: flex;                   /* 弹性布局 */
  flex-direction: column;          /* 垂直方向排列 */
  overflow: hidden;                /* 隐藏超出内容，防止布局破坏 */
}

/* ============ 流式面板头部区域 ============ */
.stream-header {
  padding: 20px;                   /* 内边距：20px */
  border-bottom: 1px solid #e4e7ed; /* 底部分隔线 */
  display: flex;                   /* 弹性布局 */
  align-items: center;             /* 垂直居中对齐 */
  justify-content: space-between;  /* 两端对齐(标题和操作区) */
  background: #fafbfc;             /* 浅灰色背景，区别于内容区 */
}

/* 头部左侧区域(标题和状态) */
.header-left {
  display: flex;                   /* 弹性布局 */
  align-items: center;             /* 垂直居中对齐 */
  gap: 16px;                      /* 元素间距：16px */
}

/* 头部标题样式 */
.header-left h3 {
  margin: 0;                       /* 清除默认外边距 */
  font-size: 16px;                 /* 字体大小 */
  font-weight: 600;                /* 字体粗细：半粗体 */
  color: #303133;                  /* 深色文字 */
  display: flex;                   /* 弹性布局用于图标文字对齐 */
  align-items: center;             /* 垂直居中对齐 */
  gap: 8px;                       /* 图标和文字间距：8px */
}

/* 头部右侧操作区域 */
.header-right {
  display: flex;                   /* 弹性布局 */
  align-items: center;             /* 垂直居中对齐 */
  gap: 8px;                       /* 按钮间距：8px */
}

/* ============ 流式内容显示区域 ============ */
.stream-content {
  flex: 1;                        /* 占用剩余全部空间 */
  overflow-y: auto;               /* 垂直滚动，处理内容溢出 */
  padding: 20px;                  /* 内边距：20px */
  position: relative;             /* 相对定位，用于浮动元素 */
}

/* ============ 空状态显示样式 ============ */
.empty-state {
  text-align: center;              /* 文字居中对齐 */
  padding: 80px 20px;             /* 内边距：上下80px 左右20px */
  color: #909399;                 /* 中性灰色文字 */
}

.empty-state p {
  margin: 16px 0 0;               /* 外边距：顶部16px */
  font-size: 16px;                /* 主要提示文字大小 */
}

.empty-state .subtitle {
  font-size: 14px;                /* 副标题文字大小 */
  margin-top: 8px;                /* 顶部外边距：8px */
}

/* ============ 工作流过程容器布局 ============ */
.process-flow {
  max-width: 800px;
  margin: 0 auto;
  padding: 0;
}

/* ============ 过程步骤通用样式 ============ */
/* 过程步骤通用样式 - 紧凑设计 */
.process-step {
  margin-bottom: 12px;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.process-step:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 已完成的步骤 */
.step-completed {
  border-left: 4px solid #67C23A;
}

/* 正在执行的步骤 */
.step-active {
  border-left: 4px solid #409EFF;
  background: linear-gradient(to right, #f0f7ff 0%, #ffffff 100%);
}

/* 错误状态的步骤 */
.step-error {
  border-left: 4px solid #F56C6C;
  background: #fef0f0;
}

/* 步骤头部布局 - 紧凑 */
.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.step-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  margin-bottom: 2px;
}

.step-time {
  font-size: 12px;
  color: #909399;
}

.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f0f7ff;
  border-radius: 6px;
  border: 1px dashed #409EFF;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: thinking 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

.thinking-text {
  font-style: italic;
  opacity: 0.8;
}

/* 步骤内容区域 - 紧凑 */
.step-content {
  padding: 8px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  line-height: 1.5;
  color: #606266;
  font-size: 13px;
}

.step-content.streaming {
  position: relative;
  animation: fadeInUp 0.3s ease;
}

.stream-cursor {
  animation: blink 1s infinite;
  font-weight: bold;
  color: #409EFF;
  margin-left: 2px;
}

.scroll-hint {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
}

/* 美化滚动条 */
.stream-content::-webkit-scrollbar {
  width: 6px;
}

.stream-content::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.stream-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.stream-content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 动画效果 */
@keyframes thinking {
  0%, 80%, 100% { 
    transform: scale(0);
  } 40% { 
    transform: scale(1);
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Markdown样式 */
:deep(.step-content) {
  line-height: 1.6;
}

:deep(.step-content h3) {
  margin: 12px 0 8px;
  color: #409EFF;
  font-size: 15px;
  font-weight: 600;
}

:deep(.step-content h4) {
  margin: 10px 0 6px;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
}

:deep(.step-content p) {
  margin: 8px 0;
}

:deep(.step-content ul) {
  padding-left: 24px;
  margin: 8px 0;
}

:deep(.step-content li) {
  margin: 6px 0;
}

:deep(.step-content strong) {
  color: #303133;
  font-weight: 600;
}

:deep(.step-content code) {
  background: rgba(64, 158, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #409EFF;
}

:deep(.step-content pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  border: 1px solid #e4e7ed;
}

:deep(.step-content pre code) {
  background: transparent;
  padding: 0;
  color: #303133;
}

/* ============ 优化建议卡片样式 ============ */
.optimization-card-wrapper {
  margin-bottom: 20px;
}

/* ============ 综合建议卡片样式 ============ */
.comprehensive-card-wrapper {
  margin-bottom: 20px;
}

.comprehensive-card {
  border: 2px solid #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
}

.comprehensive-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-bottom: 2px solid #67C23A;
}

.comprehensive-content {
  padding: 12px 0;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}

.comprehensive-content :deep(p) {
  margin: 10px 0;
  line-height: 1.8;
}

.comprehensive-content :deep(strong) {
  font-weight: 600;
  color: #67C23A;
}

.optimization-card {
  border: 2px solid #409EFF;
  border-radius: 12px;
}

.optimization-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #e8f4ff 0%, #d9ecff 100%);
  border-bottom: 2px solid #409EFF;
}

.optimization-tabs {
  margin-bottom: 20px;
}

.optimization-tabs :deep(.el-tabs__content) {
  padding: 20px;
  min-height: 300px;
}

.tab-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 16px;
}

.suggestion-item {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.3s;
}

.suggestion-item:hover {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.suggestion-item.selected {
  border-color: #409EFF;
  background: linear-gradient(135deg, #ecf5ff 0%, #e6f3ff 100%);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.25);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.item-desc-wrapper {
  margin: 10px 0;
}

.item-desc {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.item-desc :deep(p) {
  display: inline;
  margin: 0;
}

.item-desc :deep(strong) {
  color: #303133;
  font-weight: 600;
}

.full-content-toggle {
  margin-top: 8px;
}

.full-content {
  margin-top: 12px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.full-content :deep(h1),
.full-content :deep(h2),
.full-content :deep(h3) {
  color: #303133;
  margin: 16px 0 8px;
  font-weight: 600;
}

.full-content :deep(h2) {
  font-size: 16px;
  color: #409EFF;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.full-content :deep(p) {
  margin: 12px 0;
  color: #606266;
  line-height: 1.8;
}

.full-content :deep(ul),
.full-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.full-content :deep(li) {
  margin: 6px 0;
  color: #606266;
}

.full-content :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}

.comprehensive-recommendation {
  margin-top: 20px;
  background: linear-gradient(135deg, #f5f9ff 0%, #ecf5ff 100%);
  border: 1px solid #d4e4ff;
}

.comprehensive-recommendation :deep(.el-card__header) {
  background: linear-gradient(135deg, #e8f4ff 0%, #d9ecff 100%);
  border-bottom: 2px solid #409EFF;
}

.recommendation-content {
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.recommendation-content :deep(h2) {
  font-size: 16px;
  color: #409EFF;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
  margin: 16px 0 12px;
}

.recommendation-content :deep(h3) {
  font-size: 15px;
  margin: 12px 0 8px;
}

.recommendation-content :deep(p) {
  margin: 12px 0;
}

.recommendation-content :deep(ul),
.recommendation-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.recommendation-content :deep(li) {
  margin: 8px 0;
  line-height: 1.8;
}

.recommendation-content :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}

.action-buttons {
  margin-top: 24px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}

/* Tab内容容器 */
.tab-content {
  padding: 4px 0;
}

/* 纯流式输出 - 简洁样式 */
.pure-streaming-output {
  padding: 0;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
  min-height: 100px;
}

.pure-streaming-output :deep(h1),
.pure-streaming-output :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
  margin: 20px 0 12px;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.pure-streaming-output :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 10px;
}

.pure-streaming-output :deep(p) {
  margin: 12px 0;
  line-height: 1.8;
}

.pure-streaming-output :deep(ul),
.pure-streaming-output :deep(ol) {
  margin: 12px 0;
  padding-left: 28px;
}

.pure-streaming-output :deep(li) {
  margin: 8px 0;
  line-height: 1.7;
}

.pure-streaming-output :deep(strong) {
  font-weight: 600;
  color: #409EFF;
}

.pure-streaming-output :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.pure-streaming-output :deep(blockquote) {
  border-left: 3px solid #dcdfe6;
  padding-left: 16px;
  margin: 12px 0;
  color: #606266;
}

/* 保留旧的样式以兼容其他地方 */
.tab-streaming-content {
  margin-bottom: 20px;
}

.streaming-output {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  line-height: 1.6;
  color: #606266;
  font-size: 14px;
  min-height: 100px;
}

.streaming-output :deep(h2) {
  font-size: 16px;
  color: #409EFF;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
  margin: 16px 0 12px;
}

.streaming-output :deep(h3) {
  font-size: 15px;
  margin: 12px 0 8px;
}

.streaming-output :deep(p) {
  margin: 12px 0;
}

.streaming-output :deep(ul),
.streaming-output :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.streaming-output :deep(li) {
  margin: 6px 0;
}

.streaming-output :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}
</style>
