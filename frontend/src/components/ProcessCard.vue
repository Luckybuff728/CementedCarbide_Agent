<template>
  <div :class="['process-card', step.status, { collapsed, current: isCurrent }]">
    <div class="card-header" @click="$emit('toggle')">
      <div class="header-left">
        <n-icon :class="['status-icon', step.status]" :component="getStatusIcon(step.status)" />
        <h4>{{ getNodeTitle(step.nodeId) }}</h4>
        <el-tag :type="getStatusType(step.status)" size="small">
          {{ getStatusText(step.status) }}
        </el-tag>
      </div>
      <div class="header-right">
        <span v-if="step.timestamp" class="timestamp">{{ formatTime(step.timestamp) }}</span>
        <el-icon class="toggle-icon">
          <component :is="collapsed ? 'ArrowDown' : 'ArrowUp'" />
        </el-icon>
      </div>
    </div>
    <transition name="collapse">
      <div v-show="!collapsed" class="card-content" ref="cardContentRef" @scroll="handleCardScroll">
        <MarkdownRenderer :content="step.content || ''" :streaming="step.status === 'processing'" />
        
        <!-- 底部操作栏 -->
        <div class="card-footer">
          <el-button text size="small" @click="copyContent">
            <el-icon><DocumentCopy /></el-icon>
            复制
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, ArrowUp, DocumentCopy, Loading } from '@element-plus/icons-vue'
import { NIcon } from 'naive-ui'
import {
  HourglassOutline,
  Settings,
  CheckmarkCircle,
  CloseCircle
} from '@vicons/ionicons5'
import { getStatusType, getStatusText, formatTime } from '../utils/markdown'
import { useWorkflowStore } from '../stores/workflow'
import MarkdownRenderer from './MarkdownRenderer.vue'

// 使用workflow store
const workflowStore = useWorkflowStore()

const props = defineProps({
  step: {
    type: Object,
    required: true
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  isCurrent: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const cardContentRef = ref(null)
const autoScrollEnabled = ref(true)  // 卡片内部自动滚动控制

// 节点名称映射
const nodeNameMap = {
  'input_validation': '参数验证',
  'topphi_simulation': 'TopPhi相场模拟',
  'ml_prediction': 'ML模型性能预测',
  'historical_comparison': '历史数据比对',
  'integrated_analysis': '根因分析',
  'p1_composition_optimization': 'P1成分优化',
  'p2_structure_optimization': 'P2结构优化',
  'p3_process_optimization': 'P3工艺优化',
  'optimization_summary': '优化方案汇总',
  'experiment_workorder': '实验工单生成'
}

// 获取节点标题
const getNodeTitle = (nodeId) => nodeNameMap[nodeId] || nodeId

// 获取状态图标组件
const getStatusIcon = (status) => {
  const iconMap = {
    'pending': HourglassOutline,
    'processing': Settings,
    'completed': CheckmarkCircle,
    'error': CloseCircle
  }
  return iconMap[status] || HourglassOutline
}

// 复制内容
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.step.content || '')
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

// 检测卡片内容是否在底部附近
const isCardNearBottom = () => {
  if (!cardContentRef.value) return false
  const { scrollTop, scrollHeight, clientHeight } = cardContentRef.value
  return scrollHeight - scrollTop - clientHeight < 50  // 距离底部小于50px
}

// 处理卡片内部滚动事件（立即响应用户操作）
const handleCardScroll = () => {
  if (!cardContentRef.value) return
  
  const nearBottom = isCardNearBottom()
  
  // 用户离开底部，立即暂停自动滚动
  if (!nearBottom) {
    autoScrollEnabled.value = false
  } else {
    // 用户滚动到底部附近，恢复自动滚动
    autoScrollEnabled.value = true
  }
}

// 监听内容变化，智能自动滚动（仅在启用时且处理中时）
watch(
  () => props.step.content,
  () => {
    if (props.step.status === 'processing' && !props.collapsed && autoScrollEnabled.value && cardContentRef.value) {
      nextTick(() => {
        // 滚动卡片内部的内容区域到底部
        if (cardContentRef.value) {
          cardContentRef.value.scrollTop = cardContentRef.value.scrollHeight
        }
      })
    }
  }
)

// 监听展开状态，展开时恢复自动滚动并滚动到底部
watch(
  () => props.collapsed,
  (newVal) => {
    if (!newVal && props.step.status === 'processing') {
      autoScrollEnabled.value = true  // 重新展开时恢复自动滚动
      if (cardContentRef.value) {
        nextTick(() => {
          cardContentRef.value.scrollTop = cardContentRef.value.scrollHeight
        })
      }
    }
  }
)

// 监听状态变化，开始处理时启用自动滚动
watch(
  () => props.step.status,
  (newStatus) => {
    if (newStatus === 'processing') {
      autoScrollEnabled.value = true
    }
  }
)
</script>

<style scoped>
.process-card {
  background: white;
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--border-color);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.process-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

.process-card.current {
  border-left-color: var(--primary);
  border-left-width: 4px;
  border-color: var(--primary-light);
  box-shadow: var(--shadow-lg);
  background: linear-gradient(90deg, var(--primary-lighter) 0%, white 10%);
}

.process-card.processing {
  border-left-color: var(--warning);
  border-left-width: 4px;
}

.process-card.completed {
  border-left-color: var(--success);
  border-left-width: 4px;
}

.process-card.error {
  border-left-color: var(--danger);
  border-left-width: 4px;
}

.process-card.collapsed .card-header {
  border-bottom: none;
}

.card-header {
  padding: 18px 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.card-header:hover {
  background: var(--bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.header-left h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-icon {
  font-size: 20px;
  transition: all var(--transition-base);
}

.status-icon.pending {
  color: var(--text-tertiary);
}

.status-icon.processing {
  color: var(--warning);
  animation: rotate 2s linear infinite;
}

.status-icon.completed {
  color: var(--success);
}

.status-icon.error {
  color: var(--danger);
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timestamp {
  font-size: 12px;
  color: var(--text-tertiary);
}

.toggle-icon {
  font-size: 16px;
  color: var(--text-secondary);
}

.card-content {
  padding: 24px;
  max-height: 600px;
  overflow-y: auto;
  overflow-x: hidden;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: 8px;
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all var(--transition-base);
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding: 0 20px;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 600px;
  opacity: 1;
}
</style>
