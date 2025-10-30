<template>
  <div class="chat-container">
    <!-- 消息列表 -->
    <div ref="messagesRef" class="messages-list">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-screen">
        <el-icon :size="64" color="#67C23A">
          <ChatDotRound />
        </el-icon>
        <h2>欢迎使用 TopMat Agent</h2>
        <p>硬质合金涂层智能优化系统</p>
        <div class="example-prompts">
          <el-card 
            v-for="(example, index) in examplePrompts" 
            :key="index"
            shadow="hover"
            class="example-card"
            @click="$emit('example-click', example)"
          >
            <div class="example-icon">{{ example.icon }}</div>
            <div class="example-text">{{ example.text }}</div>
          </el-card>
        </div>
      </div>
      
      <!-- 消息列表 -->
      <div v-else class="messages-content">
        <ChatMessage
          v-for="(msg, index) in messages"
          :key="index"
          :message="msg"
          :isStreaming="index === messages.length - 1 && isStreaming"
          @select-optimization="$emit('select-optimization', $event)"
        />
        
        <!-- 加载指示器 - 类ChatGPT样式 -->
        <div v-if="isThinking" class="thinking-indicator">
          <el-avatar :size="36" style="background-color: #67C23A">
            <el-icon class="thinking-icon">
              <ChatDotRound />
            </el-icon>
          </el-avatar>
          <div class="thinking-content">
            <div class="thinking-message">
              <div class="thinking-header">
                <span class="thinking-label">TopMat Agent</span>
                <div class="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              <span class="thinking-text">🧠 {{ thinkingText }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 滚动到底部按钮 -->
    <transition name="fade">
      <el-button
        v-if="showScrollButton"
        circle
        class="scroll-to-bottom"
        @click="scrollToBottom"
      >
        <el-icon><ArrowDown /></el-icon>
      </el-button>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { ChatDotRound, ArrowDown } from '@element-plus/icons-vue'
import ChatMessage from './ChatMessage.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  isThinking: {
    type: Boolean,
    default: false
  },
  thinkingText: {
    type: String,
    default: '正在思考中...'
  }
})

const emit = defineEmits(['example-click', 'select-optimization'])

// 消息列表引用
const messagesRef = ref(null)

// 滚动到底部按钮显示状态
const showScrollButton = ref(false)

// 示例提示
const examplePrompts = [
  {
    icon: '⚡',
    text: '高速切削刀具涂层，需要硬度>32GPa'
  },
  {
    icon: '🔥',
    text: '耐高温涂层，抗氧化温度>900℃'
  },
  {
    icon: '💎',
    text: '低摩擦系数涂层，用于精密模具'
  },
  {
    icon: '🛡️',
    text: '高结合力涂层，要求HF1级别'
  }
]

// 滚动到底部
const scrollToBottom = (smooth = true) => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTo({
        top: messagesRef.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
      // 滚动后更新用户位置状态
      setTimeout(() => {
        isUserNearBottom.value = true
      }, 100)
    }
  })
}

// 用户是否在底部附近
const isUserNearBottom = ref(true)

// 检查滚动位置
const checkScrollPosition = () => {
  if (!messagesRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesRef.value
  const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
  
  // 更新用户位置状态
  isUserNearBottom.value = isNearBottom
  
  // 显示/隐藏滚动按钮
  showScrollButton.value = !isNearBottom && props.messages.length > 0
}

// 监听消息变化，只有在底部时才自动滚动
watch(() => props.messages.length, () => {
  if (isUserNearBottom.value) {
    scrollToBottom()
  }
}, { immediate: true })

// 监听流式输出，只有在底部时才保持滚动
watch(() => props.isStreaming, (isStreaming) => {
  if (isStreaming) {
    const interval = setInterval(() => {
      if (!props.isStreaming) {
        clearInterval(interval)
        return
      }
      // 只有用户在底部时才自动滚动
      if (isUserNearBottom.value) {
        scrollToBottom(false)
      }
    }, 100)
  }
})

// 挂载时添加滚动监听
onMounted(() => {
  if (messagesRef.value) {
    messagesRef.value.addEventListener('scroll', checkScrollPosition)
  }
})
</script>

<style scoped>
.chat-container {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* 滚动条样式 */
.messages-list::-webkit-scrollbar {
  width: 6px;
}

.messages-list::-webkit-scrollbar-track {
  background: transparent;
}

.messages-list::-webkit-scrollbar-thumb {
  background: #DCDFE6;
  border-radius: 3px;
}

.messages-list::-webkit-scrollbar-thumb:hover {
  background: #C0C4CC;
}

/* 欢迎屏幕 */
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 40px 20px;
}

.welcome-screen h2 {
  margin: 20px 0 10px 0;
  color: #303133;
  font-size: 28px;
}

.welcome-screen p {
  margin: 0 0 40px 0;
  color: #909399;
  font-size: 16px;
}

.example-prompts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  width: 100%;
  max-width: 800px;
}

.example-card {
  cursor: pointer;
  transition: all 0.3s;
}

.example-card:hover {
  transform: translateY(-4px);
  border-color: #409EFF;
}

.example-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.example-text {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

/* 消息内容 */
.messages-content {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

/* 思考指示器 - 类ChatGPT样式 */
.thinking-indicator {
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

.thinking-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.thinking-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.thinking-message {
  background: linear-gradient(135deg, #F4F4F5 0%, #FAFAFA 100%);
  padding: 16px;
  border-radius: 12px;
  border-top-left-radius: 4px;
  border-left: 3px solid #67C23A;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.thinking-label {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.thinking-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #67C23A;
  animation: bounce 1.4s infinite ease-in-out;
}

.thinking-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.thinking-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.4;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.thinking-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  font-style: italic;
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
