<template>
  <div :class="['chat-message', `chat-message-${message.role}`]">
    <div class="message-avatar">
      <el-avatar :size="36" :style="avatarStyle">
        {{ avatarText }}
      </el-avatar>
    </div>
    
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">{{ roleLabel }}</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>
      
      <div class="message-body">
        <!-- 用户消息 -->
        <div v-if="message.role === 'user'" class="user-message">
          <div v-if="message.params" class="params-summary">
            <el-tag size="small" type="primary">成分参数</el-tag>
            <el-tag size="small" type="success">工艺参数</el-tag>
            <el-tag size="small" type="warning">结构设计</el-tag>
            <el-tag size="small" type="info">性能要求</el-tag>
          </div>
          <p>{{ message.content }}</p>
        </div>
        
        <!-- AI消息 - 支持流式输出 -->
        <div v-else class="ai-message">
          <!-- Markdown渲染 -->
          <div v-html="renderedContent" class="markdown-content"></div>
          
          <!-- 流式输出光标 -->
          <span v-if="isStreaming" class="streaming-cursor">▋</span>
          
          <!-- 数据可视化 -->
          <div v-if="message.data" class="message-data">
            <!-- 性能预测结果 -->
            <el-card v-if="message.data.performance_prediction" class="data-card">
              <template #header>
                <span>📊 性能预测结果</span>
              </template>
              <div class="prediction-grid">
                <div class="prediction-item">
                  <span class="label">硬度:</span>
                  <span class="value">{{ message.data.performance_prediction.hardness }} GPa</span>
                </div>
                <div class="prediction-item">
                  <span class="label">结合力:</span>
                  <span class="value">{{ message.data.performance_prediction.adhesion }}</span>
                </div>
                <div class="prediction-item">
                  <span class="label">摩擦系数:</span>
                  <span class="value">{{ message.data.performance_prediction.friction_coefficient }}</span>
                </div>
                <div class="prediction-item">
                  <span class="label">抗氧化温度:</span>
                  <span class="value">{{ message.data.performance_prediction.oxidation_resistance_temp }}℃</span>
                </div>
              </div>
            </el-card>
            
            <!-- 优化建议 -->
            <OptimizationSuggestions
              v-if="message.data.optimization_suggestions"
              :suggestions="message.data.optimization_suggestions"
              :comprehensive-recommendation="message.data.comprehensive_recommendation || ''"
              @select="handleOptimizationSelect"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { marked } from 'marked'
import OptimizationSuggestions from './OptimizationSuggestions.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isStreaming: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select-optimization'])

// 处理优化方案选择
const handleOptimizationSelect = (selection) => {
  emit('select-optimization', selection)
}

// 角色标签
const roleLabel = computed(() => {
  return props.message.role === 'user' ? '您' : 'TopMat Agent'
})

// 头像文本
const avatarText = computed(() => {
  return props.message.role === 'user' ? '您' : 'AI'
})

// 头像样式
const avatarStyle = computed(() => {
  return props.message.role === 'user' 
    ? { backgroundColor: '#409EFF' }
    : { backgroundColor: '#67C23A' }
})

// 格式化时间
const formattedTime = computed(() => {
  if (!props.message.timestamp) return ''
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

// 渲染Markdown内容
const renderedContent = computed(() => {
  if (!props.message.content) return ''
  try {
    return marked(props.message.content, {
      breaks: true,
      gfm: true
    })
  } catch (error) {
    return props.message.content
  }
})

// 获取建议标题
const getSuggestionTitle = (key) => {
  const titles = {
    'P1': '💡 P1: 成分优化方案',
    'P2': '🔧 P2: 结构优化方案',
    'P3': '⚙️ P3: 工艺优化方案'
  }
  return titles[key] || key
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 60px);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #909399;
}

.chat-message-user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: 600;
  color: #303133;
}

.message-body {
  line-height: 1.6;
}

.user-message {
  background: #ECF5FF;
  padding: 12px 16px;
  border-radius: 12px;
  border-top-right-radius: 4px;
}

.user-message p {
  margin: 0;
  color: #303133;
}

.params-summary {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.ai-message {
  background: #F4F4F5;
  padding: 12px 16px;
  border-radius: 12px;
  border-top-left-radius: 4px;
}

.markdown-content {
  color: #303133;
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(strong) {
  color: #409EFF;
  font-weight: 600;
}

.markdown-content :deep(code) {
  background: #E6E6E6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.streaming-cursor {
  display: inline-block;
  color: #67C23A;
  animation: blink 1s step-end infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.message-data {
  margin-top: 12px;
}

.data-card {
  margin-top: 12px;
  box-shadow: none;
  border: 1px solid #E4E7ED;
}

.prediction-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.prediction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #F5F7FA;
  border-radius: 6px;
}

.prediction-item .label {
  color: #606266;
  font-size: 14px;
}

.prediction-item .value {
  color: #409EFF;
  font-weight: 600;
  font-size: 15px;
}

</style>
