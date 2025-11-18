<template>
  <div class="center-panel">
    <div class="panel-header">
      <div class="header-left">
        <h3>分析过程</h3>
        <el-tag v-if="workflowStore.isProcessing" type="warning" size="small">
          <n-icon class="is-loading" :component="ReloadOutline" />
          正在处理...
        </el-tag>
      </div>
      <div class="actions">
        <n-button text size="small" @click="expandAll">
          <template #icon>
            <n-icon :component="ExpandOutline" />
          </template>
          全部展开
        </n-button>
        <n-button text size="small" @click="collapseAll">
          <template #icon>
            <n-icon :component="ContractOutline" />
          </template>
          全部收起
        </n-button>
      </div>
    </div>
    
    <div class="panel-content" ref="scrollContainer" @scroll="handleScroll">
      <!-- 空状态 -->
      <div v-if="workflowStore.displayProcessSteps.length === 0" class="empty-state">
        <p class="empty-description">
          输入涂层参数后，系统将自动执行以下分析流程
        </p>
        
        <!-- 流程步骤预览 -->
        <div class="process-preview">
          <div class="preview-step">
            <div class="step-number">1</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="CheckmarkCircleOutline" />
                <span>参数验证</span>
              </div>
              <div class="step-desc">验证成分配比、工艺参数和结构设计</div>
            </div>
          </div>
          
          <div class="preview-step">
            <div class="step-number">2</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="FlaskOutline" />
                <span>TopPhi相场模拟</span>
              </div>
              <div class="step-desc">相场模拟计算晶体结构和微观组织演化</div>
            </div>
          </div>
          
          <div class="preview-step">
            <div class="step-number">3</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="RadioButtonOnOutline" />
                <span>ML性能预测</span>
              </div>
              <div class="step-desc">机器学习预测硬度、结合力等性能指标</div>
            </div>
          </div>
          
          <div class="preview-step">
            <div class="step-number">4</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="BarChartOutline" />
                <span>历史对比</span>
              </div>
              <div class="step-desc">与历史案例对比，识别相似配方</div>
            </div>
          </div>
          
          <div class="preview-step">
            <div class="step-number">5</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="BulbOutline" />
                <span>根因分析</span>
              </div>
              <div class="step-desc">综合分析性能结果，提供优化建议</div>
            </div>
          </div>
          
          <div class="preview-step">
            <div class="step-number">6</div>
            <div class="step-info">
              <div class="step-title">
                <n-icon :component="DocumentTextOutline" />
                <span>实验工单</span>
              </div>
              <div class="step-desc">生成详细实验方案和操作指导</div>
            </div>
          </div>
        </div>
        
        <div class="empty-hint">
          <n-icon :component="ArrowForwardOutline" />
          <span>在左侧面板输入参数，点击「开始分析」启动流程</span>
        </div>
      </div>
      
      <!-- 前期分析卡片（排除P1/P2/P3和优化方案汇总） -->
      <ProcessCard
        v-for="step in beforeOptimizationSteps"
        :key="step.id"
        :ref="el => setCardRef(step.nodeId, el)"
        :step="step"
        :collapsed="workflowStore.collapsedNodes[step.nodeId] || false"
        :is-current="step.nodeId === workflowStore.currentNode"
        @toggle="workflowStore.toggleNodeCollapse(step.nodeId)"
      />
      
      <!-- 优化建议（Tab卡片，整合P1/P2/P3） -->
      <OptimizationPanelCard
        v-if="showOptimizationCards"
        :ref="el => setCardRef('optimization', el)"
        :p1-content="workflowStore.displayP1Content"
        :p2-content="workflowStore.displayP2Content"
        :p3-content="workflowStore.displayP3Content"
        :process-steps="workflowStore.displayProcessSteps"
        :is-processing="workflowStore.isProcessing"
        :current-node="workflowStore.currentNode"
        :collapsed="optimizationCollapsed"
        @update:collapsed="optimizationCollapsed = $event"
      />
      
      <!-- 后续卡片（优化方案汇总等） -->
      <ProcessCard
        v-for="step in afterOptimizationSteps"
        :key="step.id"
        :ref="el => setCardRef(step.nodeId, el)"
        :step="step"
        :collapsed="workflowStore.collapsedNodes[step.nodeId] || false"
        :is-current="step.nodeId === workflowStore.currentNode"
        @toggle="workflowStore.toggleNodeCollapse(step.nodeId)"
      />
    </div>
    
    <!-- 回到底部按钮 -->
    <transition name="fade">
      <div v-if="showScrollToBottom" class="scroll-to-bottom" @click="handleScrollToBottomClick">
        <el-button type="primary" circle size="large">
          <n-icon :component="ChevronDownOutline" />
        </el-button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import {
  ReloadOutline,
  ChevronDownOutline,
  ChevronUpOutline,
  CopyOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  FlaskOutline,
  DocumentTextOutline,
  BulbOutline,
  RadioButtonOnOutline,
  BarChartOutline,
  ArrowForwardOutline,
  ExpandOutline,
  ContractOutline,
  CheckmarkCircle,
  BuildOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { useWorkflowStore } from '../../stores/workflow'
import ProcessCard from './ProcessCard.vue'
import OptimizationPanelCard from './OptimizationPanelCard.vue'

const workflowStore = useWorkflowStore()
const scrollContainer = ref(null)
const cardRefs = ref({})
const optimizationCollapsed = ref(false)

// 自动滚动控制
const autoScrollEnabled = ref(true)  // 是否启用自动滚动
const showScrollToBottom = ref(false)  // 是否显示"回到底部"按钮
const userIsScrolling = ref(false)  // 用户是否正在滚动

// 是否显示优化方案卡片
const showOptimizationCards = computed(() => {
  return workflowStore.displayP1Content || workflowStore.displayP2Content || workflowStore.displayP3Content
})

// 优化建议之前的卡片（只包含前期分析节点）
const beforeOptimizationSteps = computed(() => {
  const beforeNodes = [
    'input_validation',
    'topphi_simulation',
    'ml_prediction',
    'historical_comparison',
    'integrated_analysis'
  ]
  return workflowStore.displayProcessSteps.filter(step => beforeNodes.includes(step.nodeId))
})

// 优化建议之后的卡片（优化方案汇总、实验工单）
const afterOptimizationSteps = computed(() => {
  const afterNodes = ['optimization_summary', 'experiment_workorder']
  return workflowStore.displayProcessSteps.filter(step => afterNodes.includes(step.nodeId))
})

// 检测是否在底部附近（距离底部小于100px）
const isNearBottom = () => {
  if (!scrollContainer.value) return false
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
  return scrollHeight - scrollTop - clientHeight < 100
}

// 滚动到底部
const scrollToBottom = (smooth = true) => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollTo({
    top: scrollContainer.value.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  })
}

// 处理用户滚动事件（立即响应，无延迟）
const handleScroll = () => {
  if (!scrollContainer.value) return
  
  const nearBottom = isNearBottom()
  
  // 如果用户离开底部，立即暂停自动滚动并显示按钮
  if (!nearBottom) {
    autoScrollEnabled.value = false
    showScrollToBottom.value = true
    userIsScrolling.value = true
  }
  
  // 如果用户滚动到底部附近，恢复自动滚动并隐藏按钮
  if (nearBottom) {
    autoScrollEnabled.value = true
    showScrollToBottom.value = false
    userIsScrolling.value = false
  }
}

// 点击"回到底部"按钮
const handleScrollToBottomClick = () => {
  autoScrollEnabled.value = true
  showScrollToBottom.value = false
  scrollToBottom(true)
}

// 智能自动滚动：仅在启用时且有内容更新时滚动
const smartAutoScroll = () => {
  if (!autoScrollEnabled.value) return
  if (!workflowStore.isProcessing) return
  
  nextTick(() => {
    scrollToBottom(true)
  })
}

// 保存卡片引用
const setCardRef = (nodeId, el) => {
  if (el) {
    cardRefs.value[nodeId] = el
  }
}

// 滚动到指定节点
const scrollToNode = (nodeId) => {
  nextTick(() => {
    const card = cardRefs.value[nodeId]
    if (card && card.$el) {
      card.$el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 展开该节点
      workflowStore.collapsedNodes[nodeId] = false
    }
  })
}

// 展开所有
const expandAll = () => workflowStore.expandAll()

// 收起所有
const collapseAll = () => workflowStore.collapseAll()

// 监听当前节点变化，自动滚动
watch(() => workflowStore.currentNode, (newNode) => {
  if (newNode) {
    nextTick(() => {
      scrollToNode(newNode)
    })
  }
})

// 监听流式内容变化，触发智能自动滚动
watch(
  () => [
    workflowStore.displayProcessSteps.length,
    workflowStore.displayP1Content,
    workflowStore.displayP2Content,
    workflowStore.displayP3Content,
    // 监听最后一个step的content长度
    workflowStore.displayProcessSteps[workflowStore.displayProcessSteps.length - 1]?.content
  ],
  () => {
    smartAutoScroll()
  },
  { deep: true }
)

// 监听处理状态，重置滚动控制
watch(() => workflowStore.isProcessing, (isProcessing) => {
  if (isProcessing) {
    // 开始处理时，启用自动滚动
    autoScrollEnabled.value = true
    showScrollToBottom.value = false
  }
})

// 暴露方法给父组件
defineExpose({
  scrollToNode
})
</script>

<style scoped>
.center-panel {
  flex: 1;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
/* 正在处理图标 */
.header-left .is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-left h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.optimization-availability {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.optimization-availability .value {
  font-weight: 500;
  color: var(--primary);
}

.actions {
  display: flex;
  gap: 8px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  max-width: 800px;
  margin: 0 auto;
}

.empty-icon-wrapper {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  box-shadow: 0 12px 32px rgba(37, 99, 235, 0.25);
  animation: pulse 2s ease-in-out infinite;
}

.empty-icon {
  font-size: 48px;
  color: white;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 12px 32px rgba(37, 99, 235, 0.25);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 16px 40px rgba(37, 99, 235, 0.35);
  }
}

.empty-title {
  margin: 0 0 12px 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.empty-description {
  margin: 0 0 36px 0;
  font-size: 15px;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
}

/* 流程预览 */
.process-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 32px;
}

.preview-step {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-light);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.preview-step:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
  transform: translateX(4px);
  background: var(--primary-lighter);
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-lighter) 100%);
  color: var(--primary);
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.step-info {
  flex: 1;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.step-title .n-icon {
  font-size: 18px;
  color: var(--primary);
}

.step-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 空状态提示 */
.empty-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: linear-gradient(135deg, var(--primary-lighter) 0%, var(--primary-light) 100%);
  border-radius: var(--radius-lg);
  border: 2px solid var(--primary-light);
  color: var(--primary);
  font-size: 15px;
  font-weight: 600;
  box-shadow: var(--shadow-xs);
}

.empty-hint .n-icon {
  font-size: 20px;
  animation: slideRight 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes slideRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(4px);
  }
}

/* ProcessCard样式（与ProcessCard.vue保持一致） */
.process-card {
  background: white;
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--border-color);
  overflow: hidden;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.process-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
}

.process-card.completed {
  border-left-color: var(--success);
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
}

.status-icon {
  font-size: 20px;
}

.status-icon.completed {
  color: var(--success);
}

.status-icon.processing {
  color: var(--warning);
  animation: rotate 2s linear infinite;
}

.status-icon.error {
  color: var(--danger);
}

.status-icon.pending {
  color: var(--text-tertiary);
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.title-icon {
  font-size: 20px;
  color: var(--warning);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-icon {
  font-size: 16px;
  color: var(--text-secondary);
}

.card-content {
  padding: 24px;
  /* 移除固定高度，让内容自适应 */
  overflow-x: hidden;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: 8px;
}

/* 优化建议Tab样式 */
.optimization-tabs {
  margin-top: -8px;
  margin-bottom: 4px;
}

.optimization-tabs :deep(.el-tabs__header) {
  margin: 0 0 16px 0;
  background: var(--bg-tertiary);
  padding: 6px;
  border-radius: var(--radius-lg);
}

.optimization-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  height: 40px;
  line-height: 40px;
  padding: 0 20px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-label .n-icon {
  font-size: 16px;
}

.optimization-tabs :deep(.el-tabs__item.is-active) {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
}

/* 移除了el-tabs__content的固定高度限制，让内容自适应 */

.tab-content-wrapper {
  /* 移除固定高度，让内容自适应 */
  overflow-x: hidden;
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
  padding: 20px;
}

/* 回到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  cursor: pointer;
  animation: bounce 2s infinite;
}

.scroll-to-bottom :deep(.el-button) {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.scroll-to-bottom :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 弹跳提示动画 */
@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}
</style>
