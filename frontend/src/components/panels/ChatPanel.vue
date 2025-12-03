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
    <div class="chat-messages" ref="messagesContainer" @scroll="handleScroll">
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
          <img src="/favicon.ico" alt="Agent" class="avatar-image" />
        </div>
        <div class="message-bubble-wrapper">
          <!-- 简化：只显示时间 -->
          <div class="message-meta" v-if="msg.type === 'agent'">
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
              <div 
                v-show="expandedThinking[index] || msg.isThinking" 
                class="thinking-text"
                :ref="el => { if (el && msg.isThinking) thinkingRefs[index] = el }"
                @scroll="handleThinkingScroll(index, $event)"
              >{{ msg.thinking }}</div>
            </div>
            
            <!-- 工具执行状态（简洁专业设计） -->
            <div v-if="msg.tools && msg.tools.length > 0" class="tools-container">
              <div 
                v-for="tool in msg.tools" 
                :key="tool.name" 
                class="tool-item"
                :class="{ 'running': tool.isRunning, 'completed': !tool.isRunning }"
              >
                <span class="tool-status-icon">
                  <svg v-if="tool.isRunning" class="spinner" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="28" stroke-dashoffset="8"/>
                  </svg>
                  <svg v-else viewBox="0 0 16 16" fill="none">
                    <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
                <span class="tool-name">{{ tool.displayName }}</span>
              </div>
            </div>
            
            <!-- 加载指示器：agent消息无内容时显示 -->
            <div v-if="msg.type === 'agent' && !msg.content && !msg.thinking && (!msg.tools || msg.tools.length === 0) && props.isGenerating" class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            
            <div class="message-content" v-if="msg.content">
              <MarkdownRenderer v-if="!msg.isToolExecution" :content="cleanContent(msg.content)" />
              <div v-else class="tool-execution-block">
                <span class="tool-status-icon">
                  <svg v-if="msg.isToolRunning" class="spinner" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="28" stroke-dashoffset="8"/>
                  </svg>
                  <svg v-else viewBox="0 0 16 16" fill="none">
                    <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
                <span class="tool-exec-text">{{ msg.content }}</span>
              </div>
            </div>
          </div>
          
          <div class="message-meta user-meta" v-if="msg.type === 'user'">
             <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </div>
      </div>
      
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
import { ref, computed, watch, nextTick, h, onUnmounted } from 'vue'
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

// 思考区域的 refs（用于滚动到底部）
const thinkingRefs = ref({})

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
 * 例如：'researcher### 正文' -> '正文'
 * 例如：'analyst' -> '' (过滤单独的 agent 名称)
 */
const cleanContent = (content) => {
  if (!content || typeof content !== 'string') return content
  
  let cleaned = content
  
  // Agent 名称列表（包括 researcher）
  const agentNames = ['validator', 'analyst', 'optimizer', 'experimenter', 'assistant', 'supervisor', 'router', 'researcher']
  
  // 过滤掉单独的 agent 名称（整个内容只有 agent 名称）
  if (agentNames.includes(cleaned.trim().toLowerCase())) {
    return ''
  }
  
  // 移除开头的 agent 名称前缀（如 validator###、researcher###、researcherTiAlN）
  // 支持：researcher### 、researcher TiAlN、researcherTiAlN（粘连情况）
  cleaned = cleaned.replace(/^(validator|analyst|optimizer|experimenter|assistant|supervisor|router|researcher)[#\s]*/gi, '')
  
  // 移除开头的格式标签（如 "正文"、"### 正文"）
  cleaned = cleaned.replace(/^(#{1,3}\s*)?(正文|内容|回答)\s*/gi, '')
  
  // 移除开头的多余空白和换行
  cleaned = cleaned.replace(/^[\s\n]+/, '')
  
  return cleaned
}

// 用户是否在底部附近（允许 150px 的误差）
const isNearBottom = ref(true)
const SCROLL_THRESHOLD = 150

// 检测用户滚动位置
const handleScroll = () => {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  // 距离底部的距离
  const distanceToBottom = scrollHeight - scrollTop - clientHeight
  isNearBottom.value = distanceToBottom < SCROLL_THRESHOLD
}

// 滚动到底部（仅在用户在底部附近时）
const scrollToBottom = (force = false) => {
  if (!messagesContainer.value) return
  // 如果用户向上滚动查看历史，不强制滚动（除非 force=true）
  if (!force && !isNearBottom.value) return
  messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

// 强制滚动到底部（用于用户发送消息时）
const forceScrollToBottom = () => {
  isNearBottom.value = true
  nextTick(() => scrollToBottom(true))
}

// 流式滚动定时器
let streamScrollTimer = null

// 自动滚动到底部 - 消息数量变化
watch(() => props.messages.length, (newLen, oldLen) => {
  // 用户发送新消息时，强制滚动
  const lastMsg = props.messages[props.messages.length - 1]
  if (lastMsg && lastMsg.type === 'user') {
    forceScrollToBottom()
  } else {
    nextTick(() => scrollToBottom())
  }
})

// 自动滚动到底部 - 打字状态变化
watch(() => props.isAgentTyping, () => {
  nextTick(() => scrollToBottom())
})

// 记录每个 thinking 区域用户是否在底部
const thinkingNearBottom = ref({})

// 检测 thinking 区域滚动位置
const handleThinkingScroll = (index, event) => {
  const el = event.target
  const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  thinkingNearBottom.value[index] = distanceToBottom < 50
}

// 滚动所有正在输出的 thinking 区域到底部（只在用户在底部时）
const scrollThinkingToBottom = () => {
  Object.entries(thinkingRefs.value).forEach(([index, el]) => {
    if (el) {
      // 默认认为在底部，除非用户滚动过
      const nearBottom = thinkingNearBottom.value[index] !== false
      if (nearBottom) {
        el.scrollTop = el.scrollHeight
      }
    }
  })
}

// 流式生成期间持续滚动 - 解决内容更新但消息数量不变的问题
watch(() => props.isGenerating, (isGenerating) => {
  if (isGenerating) {
    // 开始生成时，启动定时滚动（每 100ms 滚动一次）
    streamScrollTimer = setInterval(() => {
      scrollToBottom()  // 只在用户在底部时滚动
      scrollThinkingToBottom()  // 滚动 thinking 区域
    }, 100)
  } else {
    // 停止生成时，清除定时器和 thinking refs
    if (streamScrollTimer) {
      clearInterval(streamScrollTimer)
      streamScrollTimer = null
    }
    thinkingRefs.value = {}  // 清理 refs
    nextTick(() => scrollToBottom())
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (streamScrollTimer) {
    clearInterval(streamScrollTimer)
    streamScrollTimer = null
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  /* box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); */
}

/* 顶部栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--bg-tertiary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: var(--primary-lighter);
  color: var(--primary);
}

.agent-status.active {
  background: var(--success-light);
  color: var(--success-hover);
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: typingPulse 1.2s ease-in-out infinite;
}

@keyframes typingPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  gap: 16px;
}

/* 滚动条样式已在全局 style.css 定义，此处只需保留必要的覆盖 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
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
  color: var(--text-primary);
}

.message-time {
  color: var(--text-tertiary);
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  position: relative;
}

.message.agent .message-bubble {
  background: var(--bg-primary);
  /* border: 1px solid #e0e0e0; */
  color: var(--text-primary);
  border-top-left-radius: 4px;
}

.message.user .message-bubble {
  background: var(--primary-lighter);
  color: var(--text-primary);
  border-top-right-radius: 4px;
}

/* 工具执行消息 */
.message.tool-message .message-bubble {
  background: var(--bg-secondary);
  border: 1px solid var(--bg-tertiary);
  border-radius: 12px;
  padding: 8px 12px;
}


/* 工具容器 - 简洁专业设计 */
.tools-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.tool-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 16px;
  color: var(--text-tertiary);
  background: rgba(0, 0, 0, 0.03);
  border-radius: 22px;
  width: fit-content;
}

.tool-item.running {
  color: var(--text-secondary);
}

.tool-item.completed {
  color: var(--text-tertiary);
}

.tool-status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.tool-status-icon svg {
  width: 14px;
  height: 14px;
}

.tool-item.running .tool-status-icon {
  color: var(--text-secondary);
}

.tool-item.completed .tool-status-icon {
  color: #22c55e;
}

.tool-status-icon .spinner {
  animation: spin 1s linear infinite;
}

.tool-name {
  font-weight: 400;
}

/* 工具执行块样式 */
.tool-execution-block {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.tool-exec-text {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: inherit;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 加载气泡 */
.loading-bubble {
  padding: 12px 16px !important;
  min-width: 60px;
}

.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 20px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: dotPulse 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) { animation-delay: 0s; }
.typing-dots span:nth-child(2) { animation-delay: 0.16s; }
.typing-dots span:nth-child(3) { animation-delay: 0.32s; }

@keyframes dotPulse {
  0%, 80%, 100% { 
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% { 
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入区域 */
.chat-input-area {
  padding: 20px 24px;
  background: var(--bg-primary);
  /* border-top: 1px solid #f1f3f4; */
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--bg-tertiary);
  border-radius: 24px;
  padding: 8px 16px;
  transition: background 0.2s;
}

.input-wrapper:focus-within {
  background: var(--bg-primary);
  box-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15);
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  border: none;
  padding: 8px 0;
  font-size: 15px;
  color: var(--text-primary);
  background: transparent;
  box-shadow: none;
  min-height: 24px !important;
  line-height: 24px;
}

.chat-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-button {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.send-button:disabled {
  background: var(--border-color);
  border-color: var(--border-color);
  color: var(--bg-primary);
}

/* 停止生成按钮 */
.stop-button {
  background: var(--bg-primary);
  border: 2px solid var(--danger);
  color: var(--danger);
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.stop-button:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: var(--bg-primary);
}

.input-footer {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
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
  font-size: 13px;
  color: #888;
  flex: 1;
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
  padding: 8px 0 10px 12px;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  border-left: 2px solid #ddd;
  margin-left: 2px;
}

/* 思考中时自动展开 */
.thinking-block.thinking-active .thinking-text {
  display: block;
}
</style>

