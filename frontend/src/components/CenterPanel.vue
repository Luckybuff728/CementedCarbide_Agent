<template>
  <div class="center-panel">
    <div class="panel-header">
      <div class="header-left">
        <h3>分析过程</h3>
        <el-tag v-if="workflowStore.isProcessing" type="warning" size="small">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在处理...
        </el-tag>
      </div>
      <div class="actions">
        <el-button text size="small" @click="expandAll" icon="Expand">全部展开</el-button>
        <el-button text size="small" @click="collapseAll" icon="Fold">全部收起</el-button>
      </div>
    </div>
    
    <div class="panel-content" ref="scrollContainer" @scroll="handleScroll">
      <!-- 空状态 -->
      <div v-if="workflowStore.processSteps.length === 0" class="empty-state">
        <el-icon class="empty-icon"><DocumentAdd /></el-icon>
        <p>请在左侧输入参数并点击"开始分析"</p>
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
      
      <!-- 💡 优化建议（Tab卡片，整合P1/P2/P3） -->
      <div 
        v-if="showOptimizationCards" 
        ref="optimizationCardRef"
        :class="['process-card', 'completed', { collapsed: optimizationCollapsed }]"
      >
        <div class="card-header" @click="toggleOptimizationCollapse">
          <div class="header-left">
            <span class="status-icon">✅</span>
            <h4>💡 优化建议</h4>
            <el-tag type="success" size="small">已完成</el-tag>
          </div>
          <div class="header-right">
            <el-icon class="toggle-icon">
              <component :is="optimizationCollapsed ? 'ArrowDown' : 'ArrowUp'" />
            </el-icon>
          </div>
        </div>
        <transition name="collapse">
          <div v-show="!optimizationCollapsed" class="card-content">
            <el-tabs v-model="activeOptimizationTab" class="optimization-tabs">
              <el-tab-pane 
                v-if="workflowStore.p1Content" 
                label="🧪 P1 成分优化" 
                name="p1"
              >
                <div ref="p1TabContent" class="tab-content-wrapper" @scroll="handleTabScroll">
                  <MarkdownRenderer :content="workflowStore.p1Content" :streaming="workflowStore.isProcessing && workflowStore.currentNode === 'p1_composition_optimization'" />
                </div>
              </el-tab-pane>
              <el-tab-pane 
                v-if="workflowStore.p2Content" 
                label="🏗️ P2 结构优化" 
                name="p2"
              >
                <div ref="p2TabContent" class="tab-content-wrapper" @scroll="handleTabScroll">
                  <MarkdownRenderer :content="workflowStore.p2Content" :streaming="workflowStore.isProcessing && workflowStore.currentNode === 'p2_structure_optimization'" />
                </div>
              </el-tab-pane>
              <el-tab-pane 
                v-if="workflowStore.p3Content" 
                label="⚙️ P3 工艺优化" 
                name="p3"
              >
                <div ref="p3TabContent" class="tab-content-wrapper" @scroll="handleTabScroll">
                  <MarkdownRenderer :content="workflowStore.p3Content" :streaming="workflowStore.isProcessing && workflowStore.currentNode === 'p3_process_optimization'" />
                </div>
              </el-tab-pane>
            </el-tabs>
            
            <!-- 底部操作栏 -->
            <div class="card-footer">
              <el-button text size="small" @click="copyOptimizationContent">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
          </div>
        </transition>
      </div>
      
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
          <el-icon><ArrowDown /></el-icon>
        </el-button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Loading, ArrowDown, ArrowUp, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '../stores/workflow'
import ProcessCard from './ProcessCard.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'

const workflowStore = useWorkflowStore()
const scrollContainer = ref(null)
const cardRefs = ref({})
const optimizationCardRef = ref(null)
const p1TabContent = ref(null)
const p2TabContent = ref(null)
const p3TabContent = ref(null)

// 当前激活的优化方案Tab
const activeOptimizationTab = ref('p1')

// 优化建议卡片折叠状态
const optimizationCollapsed = ref(false)

// 自动滚动控制
const autoScrollEnabled = ref(true)  // 是否启用自动滚动
const showScrollToBottom = ref(false)  // 是否显示"回到底部"按钮
const userIsScrolling = ref(false)  // 用户是否正在滚动
const tabAutoScrollEnabled = ref(true)  // Tab内容自动滚动

// 是否显示优化方案卡片
const showOptimizationCards = computed(() => {
  return workflowStore.p1Content || workflowStore.p2Content || workflowStore.p3Content
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
  return workflowStore.processSteps.filter(step => beforeNodes.includes(step.nodeId))
})

// 优化建议之后的卡片（优化方案汇总、实验工单）
const afterOptimizationSteps = computed(() => {
  const afterNodes = ['optimization_summary', 'experiment_workorder']
  return workflowStore.processSteps.filter(step => afterNodes.includes(step.nodeId))
})

// 切换优化建议折叠状态
const toggleOptimizationCollapse = () => {
  optimizationCollapsed.value = !optimizationCollapsed.value
}

// 复制优化建议内容
const copyOptimizationContent = async () => {
  const currentContent = activeOptimizationTab.value === 'p1' 
    ? workflowStore.p1Content 
    : activeOptimizationTab.value === 'p2' 
      ? workflowStore.p2Content 
      : workflowStore.p3Content
  
  if (currentContent) {
    try {
      await navigator.clipboard.writeText(currentContent)
      ElMessage.success('已复制到剪贴板')
    } catch (err) {
      ElMessage.error('复制失败')
    }
  }
}

// ========== 智能自动滚动相关函数 ==========

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

// 检测Tab内容是否在底部附近
const isTabNearBottom = (tabContentEl) => {
  if (!tabContentEl) return false
  const { scrollTop, scrollHeight, clientHeight } = tabContentEl
  return scrollHeight - scrollTop - clientHeight < 50
}

// 处理Tab内容滚动事件（支持用户打断）
const handleTabScroll = (event) => {
  const tabContentEl = event.target
  const nearBottom = isTabNearBottom(tabContentEl)
  
  // 用户离开底部，暂停Tab自动滚动
  if (!nearBottom) {
    tabAutoScrollEnabled.value = false
  } else {
    // 用户滚动到底部附近，恢复Tab自动滚动
    tabAutoScrollEnabled.value = true
  }
}

// Tab内容自动滚动到底部
const scrollTabContentToBottom = () => {
  if (!tabAutoScrollEnabled.value) return
  if (!workflowStore.isProcessing) return
  
  nextTick(() => {
    let tabContentEl = null
    if (activeOptimizationTab.value === 'p1') {
      tabContentEl = p1TabContent.value
    } else if (activeOptimizationTab.value === 'p2') {
      tabContentEl = p2TabContent.value
    } else if (activeOptimizationTab.value === 'p3') {
      tabContentEl = p3TabContent.value
    }
    
    if (tabContentEl) {
      tabContentEl.scrollTop = tabContentEl.scrollHeight
    }
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
    // 特殊处理优化建议卡片
    if (nodeId === 'optimization') {
      if (optimizationCardRef.value) {
        optimizationCardRef.value.scrollIntoView({ behavior: 'smooth', block: 'center' })
        // 展开优化建议
        optimizationCollapsed.value = false
      }
      return
    }
    
    // 处理普通卡片
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
    workflowStore.processSteps.length,
    workflowStore.p1Content,
    workflowStore.p2Content,
    workflowStore.p3Content,
    // 监听最后一个step的content长度
    workflowStore.processSteps[workflowStore.processSteps.length - 1]?.content
  ],
  () => {
    smartAutoScroll()
    scrollTabContentToBottom()  // 同时滚动Tab内容
  },
  { deep: true }
)

// 监听activeTab切换，恢复自动滚动并显示最新内容
watch(activeOptimizationTab, () => {
  tabAutoScrollEnabled.value = true  // 切换Tab时恢复Tab自动滚动
  scrollTabContentToBottom()
})

// 监听处理状态，重置滚动控制
watch(() => workflowStore.isProcessing, (isProcessing) => {
  if (isProcessing) {
    // 开始处理时，启用自动滚动
    autoScrollEnabled.value = true
    tabAutoScrollEnabled.value = true
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
  padding: 16px 20px;
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

.header-left h3 {
  margin: 0;
  font-size: 16px;
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
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.empty-state p {
  font-size: 14px;
}

/* ProcessCard样式（与ProcessCard.vue保持一致） */
.process-card {
  background: white;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  border-left: 4px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.process-card:hover {
  box-shadow: var(--shadow-md);
}

.process-card.completed {
  border-left-color: var(--success);
}

.process-card.collapsed .card-header {
  border-bottom: none;
}

.card-header {
  padding: 16px 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.2s;
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
  font-size: 18px;
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
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
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
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-sm);
}

.optimization-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  height: 40px;
  line-height: 40px;
  padding: 0 20px;
}

.optimization-tabs :deep(.el-tabs__item.is-active) {
  background: white;
  border-radius: var(--radius-sm);
}

.optimization-tabs :deep(.el-tabs__content) {
  max-height: 400px;
  overflow-y: auto;
}

.tab-content-wrapper {
  max-height: 400px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
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
