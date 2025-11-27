<template>
  <div class="chat-panel">
    <!-- 简洁的顶部栏 -->
    <div class="chat-header">
      <div class="header-left">
        <span class="header-title">研发助手</span>
        <div class="agent-status" :class="agentStatusClass" v-if="currentAgent !== 'System'">
          <component :is="Icon" :component="getAgentIcon()" :size="14" />
          <span>{{ currentAgent }}</span>
        </div>
      </div>
      <div class="header-right">
        <!-- 可以在这里添加更多操作，如清除对话等 -->
      </div>
    </div>
    
    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <component :is="Icon" :component="ChatboxEllipsesOutline" :size="48" />
        </div>
        <p>开始与多智能体协作系统对话...</p>
      </div>
      
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message"
        :class="[msg.type, { 'tool-message': msg.isToolExecution, 'streaming': msg.isStreaming }]"
      >
        <!-- 只为agent消息显示头像 -->
        <div v-if="msg.type === 'agent'" class="message-avatar agent">
          <img src="/1.svg" alt="Agent" class="avatar-image" />
        </div>
        <div class="message-bubble-wrapper">
          <div class="message-meta" v-if="msg.type === 'agent'">
            <span class="message-agent">{{ msg.agent }}</span>
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
          
          <div class="message-bubble" :class="{ 'tool-bubble': msg.isToolExecution }">
            <!-- 思考过程（Cascade 风格：默认收起，点击展开） -->
            <div 
              v-if="msg.thinking || msg.isThinking" 
              class="thinking-block"
              :class="{ 'expanded': expandedThinking[index], 'thinking-active': msg.isThinking }"
            >
              <div class="thinking-header" @click="toggleThinking(index)">
                <span class="thinking-dot" :class="{ 'animating': msg.isThinking }"></span>
                <span class="thinking-label">{{ msg.isThinking ? 'Thinking...' : 'Thought for a few seconds' }}</span>
                <span class="thinking-toggle">{{ expandedThinking[index] ? '▼' : '▶' }}</span>
              </div>
              <div v-show="expandedThinking[index] || msg.isThinking" class="thinking-text">{{ msg.thinking }}</div>
            </div>
            
            <!-- 工具执行状态（嵌入在消息中） -->
            <div v-if="msg.tools && msg.tools.length > 0" class="tools-list">
              <div 
                v-for="tool in msg.tools" 
                :key="tool.name" 
                class="tool-item"
                :class="{ 'tool-running': tool.isRunning }"
              >
                <component :is="Icon" :component="SettingsOutline" :size="14" class="tool-icon" :class="{ 'spinning': tool.isRunning }" />
                <span class="tool-name">{{ tool.displayName }}</span>
                <span v-if="!tool.isRunning" class="tool-done">✓</span>
                <span v-else class="tool-loading">...</span>
              </div>
            </div>
            
            <div class="message-content" v-if="msg.content">
              <MarkdownRenderer v-if="!msg.isToolExecution" :content="cleanContent(msg.content)" />
              <span v-else class="tool-execution-text" :class="{ 'tool-running': msg.isToolRunning }">
                <component :is="Icon" :component="SettingsOutline" :size="14" class="tool-icon" />
                {{ msg.content }}
              </span>
            </div>
          </div>
          
          <div class="message-meta user-meta" v-if="msg.type === 'user'">
             <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </div>
      </div>
      
      <!-- Typing动画已移除，使用消息内的 streaming 状态代替 -->
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 6 }"
          placeholder="输入消息与Agent对话..."
          @keydown.enter.prevent="handleEnterKey"
          class="chat-input"
        />
        <!-- 生成中显示停止按钮，否则显示发送按钮 -->
        <el-button
          v-if="isGenerating"
          type="danger"
          @click="stopGenerate"
          class="stop-button"
          circle
        >
          <el-icon :size="18"><StopOutline /></el-icon>
        </el-button>
        <el-button
          v-else
          type="primary"
          :disabled="!userInput.trim()"
          @click="sendMessage"
          class="send-button"
          circle
        >
          <el-icon :size="20"><ArrowUp /></el-icon>
        </el-button>
      </div>
      <div class="input-footer">
        <span>按 Enter 发送，Shift + Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, h } from 'vue'
import { ElButton, ElInput, ElIcon } from 'element-plus'
import { 
  ChatboxEllipsesOutline,
  ArrowUp,
  RibbonOutline,
  CheckmarkCircleOutline,
  AnalyticsOutline,
  BulbOutline,
  FlaskOutline,
  SettingsOutline,
  StopOutline
} from '@vicons/ionicons5'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'

// Icon包装器组件（替代naive-ui的NIcon）
const Icon = (props) => {
  return h('span', { 
    class: 'icon-wrapper',
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: props.size ? `${props.size}px` : '16px'
    }
  }, h(props.component))
}

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  currentAgent: {
    type: String,
    default: 'System'
  },
  isAgentTyping: {
    type: Boolean,
    default: false
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
})

const emit = defineEmits(['send-message', 'stop-generate'])

// 是否显示 typing 动画：只在生成中且最后一条 agent 消息完全没有内容时显示
const showTypingIndicator = computed(() => {
  if (!props.isGenerating) return false
  // 检查最后一条 agent 消息是否已有任何内容
  const lastMsg = props.messages[props.messages.length - 1]
  if (lastMsg && lastMsg.type === 'agent') {
    // 如果消息已有内容、思考内容或工具，不显示 typing
    const hasContent = lastMsg.content || lastMsg.thinking || (lastMsg.tools && lastMsg.tools.length > 0)
    return !hasContent
  }
  // 如果最后一条不是 agent 消息，显示 typing
  return true
})

// 终止生成
const stopGenerate = () => {
  emit('stop-generate')
}

const userInput = ref('')
const messagesContainer = ref(null)

// 思考过程展开状态（默认收起）
const expandedThinking = ref({})
const toggleThinking = (index) => {
  expandedThinking.value[index] = !expandedThinking.value[index]
}

const agentStatusClass = computed(() => {
  const agent = props.currentAgent.toLowerCase()
  if (agent.includes('supervisor')) return 'status-supervisor'
  if (agent.includes('validator')) return 'status-validator'
  if (agent.includes('analyst')) return 'status-analyst'
  if (agent.includes('optimizer')) return 'status-optimizer'
  if (agent.includes('experimenter')) return 'status-experimenter'
  return 'status-default'
})

// 根据当前Agent返回对应图标
const getAgentIcon = () => {
  const agent = props.currentAgent.toLowerCase()
  if (agent.includes('supervisor')) return RibbonOutline
  if (agent.includes('validator')) return CheckmarkCircleOutline
  if (agent.includes('analyst')) return AnalyticsOutline
  if (agent.includes('optimizer')) return BulbOutline
  if (agent.includes('experimenter')) return FlaskOutline
  return SettingsOutline
}

const handleEnterKey = (e) => {
  if (e.shiftKey) return
  sendMessage()
}

const sendMessage = () => {
  const message = userInput.value.trim()
  if (!message) return
  
  emit('send-message', message)
  userInput.value = ''
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

/**
 * 清理消息内容，移除 LLM 输出的奇怪前缀
 * 例如：'validator### ✅ 涂层参数验证报告' -> '✅ 涂层参数验证报告'
 * 例如：'analyst' -> '' (过滤单独的 agent 名称)
 */
const cleanContent = (content) => {
  if (!content || typeof content !== 'string') return content
  
  let cleaned = content
  
  // 过滤掉单独的 agent 名称（整个内容只有 agent 名称）
  const agentNames = ['validator', 'analyst', 'optimizer', 'experimenter', 'assistant', 'supervisor', 'router']
  if (agentNames.includes(cleaned.trim().toLowerCase())) {
    return ''
  }
  
  // 移除开头的 agent 名称前缀（如 validator###、analyst#、optimizer##）
  cleaned = cleaned.replace(/^(validator|analyst|optimizer|experimenter|assistant|supervisor|router)[#\s]+/gi, '')
  
  // 移除开头的多余空白和换行
  cleaned = cleaned.replace(/^[\s\n]+/, '')
  
  return cleaned
}

// 自动滚动到底部
watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

watch(() => props.isAgentTyping, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dadce0;
  overflow: hidden;
  /* box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); */
}

/* 顶部栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #f1f3f4;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #202124;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #e8f0fe;
  color: #1967d2;
  transition: all 0.2s;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #ffffff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9aa0a6;
  gap: 16px;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #dadce0;
  border-radius: 3px;
}

/* 消息布局 */
.message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: messageFadeIn 0.3s ease-out;
}

@keyframes messageFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  justify-content: flex-end;
}

.message-bubble-wrapper {
  max-width: 85%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message.user .message-bubble-wrapper {
  align-items: flex-end;
}

/* 头像 */
.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4px; /* 对齐第一行文字 */
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 消息元数据 */
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 0 2px;
  margin-bottom: 2px;
}

.message-agent {
  font-weight: 600;
  color: #202124;
}

.message-time {
  color: #9aa0a6;
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  position: relative;
}

.message.agent .message-bubble {
  background: #ffffff;
  /* border: 1px solid #e0e0e0; */
  color: #202124;
  border-top-left-radius: 4px;
}

.message.user .message-bubble {
  background: #e8f0fe;
  color: #1f1f1f;
  border-top-right-radius: 4px;
}

/* 工具执行消息 */
.message.tool-message .message-bubble {
  background: #f8f9fa;
  border: 1px solid #f1f3f4;
  border-radius: 12px;
  padding: 8px 12px;
}

.tool-execution-text {
  color: #5f6368;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Roboto Mono', monospace;
}

.tool-running {
  color: #1967d2;
}

.tool-icon {
  color: inherit;
}

.tool-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 工具列表（嵌入在消息中） */
.tools-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8eaed;
}

.tool-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f8f9fa;
  border-radius: 16px;
  font-size: 12px;
  color: #5f6368;
  font-family: 'Roboto Mono', monospace;
}

.tool-item.tool-running {
  background: #e8f0fe;
  color: #1967d2;
}

.tool-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-done {
  color: #34a853;
  font-weight: 500;
}

.tool-loading {
  color: #1967d2;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Typing指示器 */
.typing-bubble {
  background: #f1f3f4;
  padding: 12px 16px;
  border-radius: 16px;
  border-top-left-radius: 4px;
  width: fit-content;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9aa0a6;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.chat-input-area {
  padding: 20px 24px;
  background: #ffffff;
  /* border-top: 1px solid #f1f3f4; */
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f1f3f4;
  border-radius: 24px;
  padding: 8px 16px;
  transition: background 0.2s;
}

.input-wrapper:focus-within {
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15);
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  border: none;
  padding: 8px 0;
  font-size: 15px;
  color: #202124;
  background: transparent;
  box-shadow: none;
  min-height: 24px !important;
  line-height: 24px;
}

.chat-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-button {
  background: #1967d2;
  border-color: #1967d2;
  color: white;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.send-button:disabled {
  background: #dadce0;
  border-color: #dadce0;
  color: #ffffff;
}

/* 停止生成按钮 */
.stop-button {
  background: #ffffff;
  border: 2px solid #dc3545;
  color: #dc3545;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.stop-button:hover {
  background: #dc3545;
  border-color: #dc3545;
  color: #ffffff;
}

.input-footer {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #9aa0a6;
}

/* Markdown内容样式优化 */
.message-content :deep(.markdown-content) {
  font-size: 15px;
  line-height: 1.6;
}

.message-content :deep(p) {
  margin: 0 0 8px 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Roboto Mono', monospace;
  font-size: 13px;
}

.message-content :deep(pre) {
  background: #f1f3f4;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: #202124;
}
  
/* 思考过程样式（简洁融入式设计） */
.thinking-block {
  margin-bottom: 8px;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  cursor: pointer;
  user-select: none;
}

.thinking-header:hover .thinking-label {
  color: #444;
}

.thinking-label {
  font-size: 12px;
  color: #999;
  flex: 1;
  font-style: italic;
}

.thinking-toggle {
  font-size: 9px;
  color: #bbb;
  transition: transform 0.2s;
}

.thinking-block.expanded .thinking-toggle {
  transform: rotate(0deg);
}

.thinking-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #ccc;
  flex-shrink: 0;
}

.thinking-dot.animating {
  background: #999;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.thinking-text {
  padding: 6px 0 8px 11px;
  font-size: 12px;
  color: #888;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 180px;
  overflow-y: auto;
  border-left: 2px solid #e5e5e5;
  margin-left: 2px;
}

/* 思考中时自动展开 */
.thinking-block.thinking-active .thinking-text {
  display: block;
}
</style>

