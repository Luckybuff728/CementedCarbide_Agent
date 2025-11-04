<template>
  <div class="status-bar">
    <div class="status-content">
      <div class="left-section">
        <div class="title-section">
          <h2 class="app-title">TopMat Agent</h2>
          <p class="app-subtitle">涂层材料智能分析系统</p>
        </div>
        <el-divider direction="vertical" />
        <div class="progress-nodes">
          <div 
            v-for="(node, index) in nodes" 
            :key="node.id" 
            :class="['node-step', node.status]" 
            @click="handleNodeClick(node)"
          >
            <div class="step-content">
              <n-icon class="step-icon" :component="getStatusIcon(node.status)" />
              <span class="step-name">{{ node.name }}</span>
            </div>
            <div v-if="index < nodes.length - 1" class="step-connector"></div>
          </div>
        </div>
      </div>
      
      <div class="actions">
        <n-button 
          size="small" 
          @click="handleExport" 
          :disabled="!canExport"
          secondary
        >
          <template #icon>
            <n-icon><Download /></n-icon>
          </template>
          导出
        </n-button>
        <n-button 
          size="small" 
          @click="handleClear" 
          :disabled="!canClear"
          secondary
        >
          <template #icon>
            <n-icon><Trash /></n-icon>
          </template>
          清空
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { NButton, NIcon } from 'naive-ui'
import { 
  CheckmarkCircle, 
  HourglassOutline, 
  EllipseOutline,
  Settings,
  Download,
  Trash
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../stores/workflow'

const workflowStore = useWorkflowStore()
const emit = defineEmits(['jump-to-node', 'export', 'clear'])

const nodes = computed(() => {
  const nodeList = [
    { id: 'input_validation', name: '参数验证', status: getNodeStatus('input_validation') },
    { id: 'topphi_simulation', name: 'TopPhi模拟', status: getNodeStatus('topphi_simulation') },
    { id: 'ml_prediction', name: 'ML预测', status: getNodeStatus('ml_prediction') },
    { id: 'historical_comparison', name: '历史对比', status: getNodeStatus('historical_comparison') },
    { id: 'integrated_analysis', name: '根因分析', status: getNodeStatus('integrated_analysis') },
    { id: 'optimization', name: '优化方案', status: getOptimizationStatus() },
    { id: 'experiment_workorder', name: '实验工单', status: getNodeStatus('experiment_workorder') }
  ]
  
  // 调试日志：显示当前状态
  console.log('[📊 StatusBar状态]', {
    currentNode: workflowStore.currentNode,
    completedNodes: workflowStore.completedNodes,
    statuses: nodeList.map(n => `${n.name}:${n.status}`)
  })
  
  return nodeList
})

// 能否导出
const canExport = computed(() => {
  return workflowStore.processSteps.length > 0 || workflowStore.experimentWorkorder
})

// 能否清空
const canClear = computed(() => {
  return workflowStore.processSteps.length > 0
})

function getNodeStatus(nodeId) {
  // ⚠️ 关键修复：优先检查completed状态，避免已完成节点仍显示processing
  if (workflowStore.completedNodes.includes(nodeId)) return 'completed'
  if (workflowStore.currentNode === nodeId) return 'processing'
  return 'pending'
}

function getOptimizationStatus() {
  if (workflowStore.p1Content || workflowStore.p2Content || workflowStore.p3Content) {
    return 'completed'
  }
  return 'pending'
}

// 获取状态图标组件
function getStatusIcon(status) {
  const iconMap = {
    'pending': EllipseOutline,
    'processing': Settings,
    'completed': CheckmarkCircle
  }
  return iconMap[status] || EllipseOutline
}

function handleNodeClick(node) {
  if (node.status === 'completed' || node.status === 'processing') {
    emit('jump-to-node', node.id)
  }
}

function handleExport() {
  emit('export')
}

function handleClear() {
  ElMessageBox.confirm(
    '确定要清空当前所有数据吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    workflowStore.reset()
    ElMessage.success('已清空')
    emit('clear')
  }).catch(() => {})
}
</script>

<style scoped>
.status-bar {
  height: 60px;
  background: white;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
  position: relative;
  z-index: 10;
}

.status-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  overflow-x: auto;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary);
  line-height: 1.5;
}

.app-subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.progress-nodes {
  display: flex;
  align-items: center;
  gap: 0;
}

.node-step {
  display: flex;
  align-items: center;
  position: relative;
}

.step-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.node-step.pending .step-content {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.node-step.processing .step-content {
  background: #fef3c7;
  color: var(--warning);
  font-weight: 500;
}

.node-step.completed .step-content {
  background: #d1fae5;
  color: var(--success);
}

.node-step.completed .step-content:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.step-icon {
  font-size: 16px;
  transition: all 0.3s ease;
}

/* processing状态图标旋转动画 */
.node-step.processing .step-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.step-name {
  font-size: 13px;
}

.step-connector {
  width: 20px;
  height: 2px;
  background: var(--border-color);
  margin: 0 4px;
}

.node-step.completed .step-connector {
  background: var(--success);
}

.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Naive UI按钮自定义样式 */
.actions :deep(.n-button) {
  border-radius: 6px;
}
</style>
