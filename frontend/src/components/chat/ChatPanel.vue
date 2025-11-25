<template>
  <div class="chat-panel">
    <!-- 简洁的顶部栏 -->
    <div class="chat-header">
      <div class="header-left">
        <component :is="Icon" :component="ChatboxEllipsesOutline" :size="20" class="header-icon" />
        <span class="header-title">Agent 对话</span>
      </div>
      <div class="agent-status" :class="agentStatusClass">
        <component :is="Icon" :component="getAgentIcon()" :size="14" />
        <span>{{ currentAgent }}</span>
      </div>
    </div>
    
    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
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
        <div class="message-bubble" :class="{ 'tool-bubble': msg.isToolExecution }">
          <div class="message-meta">
            <span class="message-agent">{{ msg.agent }}</span>
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
            <span v-if="msg.isStreaming" class="streaming-indicator">正在输入...</span>
          </div>
          <div class="message-content">
            <MarkdownRenderer v-if="!msg.isToolExecution" :content="msg.content" />
            <span v-else class="tool-execution-text" :class="{ 'tool-running': msg.isToolRunning }">{{ msg.content }}</span>
          </div>
        </div>
      </div>
      
      <!-- Typing动画 -->
      <div v-if="isAgentTyping" class="message agent">
        <div class="message-avatar agent">
          <img src="/1.svg" alt="Agent" class="avatar-image" />
        </div>
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="输入消息与Agent对话... (Ctrl+Enter发送)"
          :disabled="!canSendMessage"
          @keydown.ctrl.enter="sendMessage"
          class="chat-input"
        />
      </div>
      <div class="input-actions">
        <el-button
          type="primary"
          :disabled="!canSendMessage || !userInput.trim()"
          @click="sendMessage"
          class="send-button"
        >
          <component :is="Icon" :component="SendOutline" :size="18" style="margin-right: 4px;" />
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, h } from 'vue'
import { ElButton, ElInput } from 'element-plus'
import { 
  ChatboxEllipsesOutline,
  SendOutline,
  RibbonOutline,
  CheckmarkCircleOutline,
  AnalyticsOutline,
  BulbOutline,
  FlaskOutline,
  SettingsOutline
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
  canSendMessage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send-message'])

const userInput = ref('')
const messagesContainer = ref(null)

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

const sendMessage = () => {
  const message = userInput.value.trim()
  if (!message) return
  
  emit('send-message', message)
  userInput.value = ''
  
  // 添加用户消息到界面
  // 实际消息由父组件通过props更新
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
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
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 顶部栏 - 简洁现代 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  color: #2d2d2d;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #0d0d0d;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  background: #f0f0f0;
  color: #2d2d2d;
  transition: all 0.2s;
}

/* 统一的Agent状态样式 - 简洁灰色 */
.status-supervisor,
.status-validator,
.status-analyst,
.status-optimizer,
.status-experimenter,
.status-default {
  background: #f0f0f0;
  color: #2d2d2d;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #ffffff;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 消息布局 */
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: messageSlideIn 0.3s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

/* 头像 */
.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.message-avatar.agent {
  background: #ffffff;
  border: 1px solid #e5e5e5;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 消息气泡 */
.message-bubble {
  max-width: 85%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message.user .message-bubble {
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 0 4px;
}

.message.user .message-meta {
  flex-direction: row-reverse;
}

.message-agent {
  font-weight: 600;
  color: #0d0d0d;
}

.message-time {
  color: #8e8ea0;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  word-wrap: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.message.user .message-content {
  background: #f4f4f4;
  color: #0d0d0d;
  border-bottom-right-radius: 4px;
}

.message.agent .message-content {
  background: #ffffff;
  color: #0d0d0d;
  border: 1px solid #e5e5e5;
  border-bottom-left-radius: 4px;
}

/* Typing指示器 */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  width: fit-content;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  30% {
    transform: scale(1.1);
    opacity: 1;
  }
}

/* 输入区域 */
.chat-input-area {
  padding: 16px 20px;
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
}

.input-wrapper {
  margin-bottom: 10px;
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 12px;
  border: 1px solid #d1d5db;
  padding: 12px 14px;
  font-size: 14px;
  color: #0d0d0d;
  transition: all 0.2s;
  background: #ffffff;
}

.chat-input :deep(.el-textarea__inner:focus) {
  border-color: #2d2d2d;
  background: #ffffff;
  box-shadow: 0 0 0 1px #2d2d2d;
}

.chat-input :deep(.el-textarea__inner::placeholder) {
  color: #b0b0b0;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

.send-button {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
  background: #2d2d2d;
  border-color: #2d2d2d;
}

.send-button:hover:not(:disabled) {
  background: #1a1a1a;
  border-color: #1a1a1a;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
  background: #0d0d0d;
}

/* Markdown内容样式优化 */
.message-content :deep(.markdown-content) {
  font-size: 14px;
  line-height: 1.6;
}

.message-content :deep(p) {
  margin: 0 0 8px 0;
  line-height: 1.6;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  color: #0d0d0d;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.message.user .message-content :deep(code) {
  background: rgba(0, 0, 0, 0.08);
  color: #0d0d0d;
}

/* 聊天消息中的标题 - 紧凑化 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4) {
  font-size: 15px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  padding: 0;
  border: none;
  color: #1f2937;
}

.message-content :deep(h1:first-child),
.message-content :deep(h2:first-child),
.message-content :deep(h3:first-child) {
  margin-top: 0;
}

/* 聊天消息中的表格 - 确保完整显示 */
.message-content :deep(table) {
  font-size: 13px;
  margin: 10px 0;
  width: 100%;
  border-collapse: collapse;
  display: block;
  overflow-x: auto;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 8px 12px;
  border: 1px solid #e5e5e5;
  text-align: left;
  min-width: 80px;
}

.message-content :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}

/* 聊天消息中的列表 */
.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

/* 工具执行消息 */
.message.tool-message {
  opacity: 0.9;
}

.message-bubble.tool-bubble {
  max-width: 80%;
}

.tool-execution-text {
  color: #666;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 工具运行中：斜体 + 旋转图标 */
.tool-execution-text.tool-running {
  font-style: italic;
}

.tool-execution-text.tool-running::before {
  content: '';
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #2d2d2d;
  border-top-color: transparent;
  border-radius: 50%;
  animation: toolSpinner 0.8s linear infinite;
}

/* 工具完成：正常字体 + 无动画 */
.tool-execution-text:not(.tool-running) {
  font-style: normal;
  color: #2d2d2d;
}

@keyframes toolSpinner {
  to {
    transform: rotate(360deg);
  }
}

/* 流式输出消息 */
.message.streaming .message-content {
  position: relative;
}

.streaming-indicator {
  color: #2d2d2d;
  font-size: 11px;
  font-weight: 600;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>

