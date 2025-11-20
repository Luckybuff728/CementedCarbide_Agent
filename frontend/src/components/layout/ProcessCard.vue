<template>
  <div :class="['process-card', step.status, { collapsed, current: isCurrent }]">
    <div class="card-header" @click="$emit('toggle')">
      <div class="header-left">
        <el-icon :class="['status-icon', step.status]"><component :is="getStatusIcon(step.status)" /></el-icon>
        <h4>{{ getNodeTitle(step.nodeId) }}</h4>
        <el-tag :type="getStatusType(step.status)" size="small" class="status-tag">
          {{ getStatusText(step.status) }}
        </el-tag>
      </div>
      <div class="header-right">
        <span v-if="step.timestamp" class="timestamp">{{ formatTime(step.timestamp) }}</span>
        <el-icon class="toggle-icon"><component :is="collapsed ? ChevronDownOutline : ChevronUpOutline" /></el-icon>
      </div>
    </div>
    <transition name="collapse">
      <div v-show="!collapsed" class="card-content" ref="cardContentRef">
        <MarkdownRenderer :content="step.content || ''" :streaming="step.status === 'processing'" />
        
        <!-- 底部操作栏 -->
        <div class="card-footer">
          <el-button text size="small" @click="copyContent">
            <el-icon class="el-icon--left"><CopyOutline /></el-icon>
            复制
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElButton, ElIcon } from 'element-plus'
import {
  ChevronDownOutline,
  ChevronUpOutline,
  CopyOutline,
  ReloadOutline,
  HourglassOutline,
  Settings,
  CheckmarkCircle,
  CloseCircle
} from '@vicons/ionicons5'
import { getStatusType, getStatusText, formatTime } from '../../utils/markdown'
import { useWorkflowStore } from '../../stores/workflow'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'

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
// 注释：移除了卡片内部滚动，内容现在自适应高度
// const autoScrollEnabled = ref(true)

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
</script>

<style scoped>
.process-card {
  background: white;
  border-radius: var(--radius-lg);
  margin-bottom: 18px;
  border: 1px solid var(--border-color);
  border-left: 4px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
}

.process-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

.process-card.current {
  border-left-color: var(--primary);
  border-left-width: 5px;
  border-color: var(--primary-light);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
  background: linear-gradient(90deg, var(--primary-lighter) 0%, white 8%);
}

.process-card.processing {
  border-left-color: var(--warning);
  border-left-width: 5px;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
}

.process-card.completed {
  border-left-color: var(--success);
  border-left-width: 5px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.process-card.error {
  border-left-color: var(--danger);
  border-left-width: 5px;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
}

.process-card.collapsed .card-header {
  border-bottom: none;
}

.card-header {
  padding: 20px 24px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-header:hover {
  background: var(--bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
}

.header-left h4 {
  margin: 0;
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.status-icon {
  font-size: var(--icon-lg);
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
  font-size: var(--font-sm);
  color: var(--text-tertiary);
  font-weight: 500;
}

.toggle-icon {
  font-size: var(--icon-base);
  color: var(--text-secondary);
  transition: all 0.2s;
}

.card-header:hover .toggle-icon {
  color: var(--primary);
  transform: scale(1.1);
}

.card-content {
  padding: 28px;
  /* 移除固定高度，让内容自适应 */
  overflow-x: hidden;
  line-height: 1.8;
}

.card-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: 10px;
}

.card-footer :deep(.el-button) {
  font-size: 14px;
  padding: 8px 16px;
  font-weight: 500;
}

.card-footer :deep(.el-button:hover) {
  color: var(--primary);
  background: var(--primary-lighter);
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
  max-height: 5000px; /* 使用较大值以适应任意长度的内容 */
  opacity: 1;
}

/* Tag 标签美化 */
.status-tag {
  font-weight: 600;
  font-size: var(--font-sm);
  padding: 4px 12px;
  border-radius: 6px;
  border: none;
}

.status-tag.el-tag--success {
  background: var(--success-light);
  color: var(--success);
}

.status-tag.el-tag--warning {
  background: var(--warning-light);
  color: #d97706;
}

.status-tag.el-tag--info {
  background: #e5e7eb;
  color: #6b7280;
}

.status-tag.el-tag--danger {
  background: var(--danger-light);
  color: var(--danger);
}
</style>
