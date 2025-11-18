<template>
  <div
    v-if="hasAnyContent"
    ref="rootRef"
    :class="['process-card', optimizationCardStatusClass, { collapsed: collapsed }]"
  >
    <div class="card-header" @click="toggleCollapse">
      <div class="header-left">
        <n-icon :class="['status-icon', optimizationCardStatusClass]" :component="optimizationStatusIcon" />
        <n-icon class="title-icon" :component="BulbOutline" />
        <h4>优化建议</h4>
        <el-tag :type="optimizationStatusTag.type" size="small">
          {{ optimizationStatusTag.text }}
        </el-tag>
        <div class="optimization-availability">
          <span>可用方案：</span>
          <span class="value">{{ optimizationAvailabilityText }}</span>
        </div>
      </div>
      <div class="header-right">
        <n-icon class="toggle-icon" :component="collapsed ? ChevronDownOutline : ChevronUpOutline" />
      </div>
    </div>
    <transition name="collapse">
      <div v-show="!collapsed" class="card-content">
        <el-tabs v-model="activeOptimizationTab" class="optimization-tabs">
          <el-tab-pane
            v-if="p1Content"
            name="p1"
          >
            <template #label>
              <div class="tab-label">
                <n-icon :component="FlaskOutline" />
                <span>P1 成分优化</span>
              </div>
            </template>
            <div ref="p1TabContent" class="tab-content-wrapper">
              <MarkdownRenderer :content="p1Content" :streaming="isProcessing && currentNode === 'p1_composition_optimization'" />
            </div>
          </el-tab-pane>
          <el-tab-pane
            v-if="p2Content"
            name="p2"
          >
            <template #label>
              <div class="tab-label">
                <n-icon :component="BuildOutline" />
                <span>P2 结构优化</span>
              </div>
            </template>
            <div ref="p2TabContent" class="tab-content-wrapper">
              <MarkdownRenderer :content="p2Content" :streaming="isProcessing && currentNode === 'p2_structure_optimization'" />
            </div>
          </el-tab-pane>
          <el-tab-pane
            v-if="p3Content"
            name="p3"
          >
            <template #label>
              <div class="tab-label">
                <n-icon :component="SettingsOutline" />
                <span>P3 工艺优化</span>
              </div>
            </template>
            <div ref="p3TabContent" class="tab-content-wrapper">
              <MarkdownRenderer :content="p3Content" :streaming="isProcessing && currentNode === 'p3_process_optimization'" />
            </div>
          </el-tab-pane>
        </el-tabs>
        <div class="card-footer">
          <el-button text size="small" @click.stop="copyOptimizationContent">
            <n-icon :component="CopyOutline" />
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
import { NIcon } from 'naive-ui'
import {
  ChevronDownOutline,
  ChevronUpOutline,
  CopyOutline,
  CloseCircleOutline,
  BulbOutline,
  RadioButtonOnOutline,
  FlaskOutline,
  BuildOutline,
  SettingsOutline,
  CheckmarkCircle,
  Settings
} from '@vicons/ionicons5'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'

const props = defineProps({
  p1Content: {
    type: String,
    default: ''
  },
  p2Content: {
    type: String,
    default: ''
  },
  p3Content: {
    type: String,
    default: ''
  },
  processSteps: {
    type: Array,
    default: () => []
  },
  isProcessing: {
    type: Boolean,
    default: false
  },
  currentNode: {
    type: String,
    default: ''
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:collapsed'])

const rootRef = ref(null)
const activeOptimizationTab = ref('p1')
const p1TabContent = ref(null)
const p2TabContent = ref(null)
const p3TabContent = ref(null)
const tabAutoScrollEnabled = ref(true)

const hasAnyContent = computed(() => {
  return props.p1Content || props.p2Content || props.p3Content
})

const optimizationStates = computed(() => {
  const steps = props.processSteps || []
  const getStatus = nodeId => {
    const step = steps.find(s => s.nodeId === nodeId)
    return step ? step.status : ''
  }

  let p1Status = getStatus('p1_composition_optimization')
  let p2Status = getStatus('p2_structure_optimization')
  let p3Status = getStatus('p3_process_optimization')

  const deriveStatus = (rawStatus, content) => {
    if (rawStatus === 'completed' || rawStatus === 'processing' || rawStatus === 'error') {
      return rawStatus
    }
    if (content) {
      if (props.isProcessing) {
        return 'processing'
      }
      return 'completed'
    }
    return rawStatus || ''
  }

  p1Status = deriveStatus(p1Status, props.p1Content)
  p2Status = deriveStatus(p2Status, props.p2Content)
  p3Status = deriveStatus(p3Status, props.p3Content)

  const completed = {
    p1: p1Status === 'completed' && !!props.p1Content,
    p2: p2Status === 'completed' && !!props.p2Content,
    p3: p3Status === 'completed' && !!props.p3Content
  }

  const hasCompletedAny = completed.p1 || completed.p2 || completed.p3
  const hasProcessing = p1Status === 'processing' || p2Status === 'processing' || p3Status === 'processing'
  const hasError = p1Status === 'error' || p2Status === 'error' || p3Status === 'error'

  return {
    p1Status,
    p2Status,
    p3Status,
    completed,
    hasCompletedAny,
    hasProcessing,
    hasError
  }
})

const optimizationCardStatusClass = computed(() => {
  const state = optimizationStates.value
  if (state.hasProcessing) {
    return 'processing'
  }
  if (state.hasError && !state.hasCompletedAny) {
    return 'error'
  }
  if (state.hasCompletedAny) {
    return 'completed'
  }
  return 'pending'
})

const optimizationStatusIcon = computed(() => {
  const status = optimizationCardStatusClass.value
  if (status === 'completed') {
    return CheckmarkCircle
  }
  if (status === 'processing') {
    return Settings
  }
  if (status === 'error') {
    return CloseCircleOutline
  }
  return RadioButtonOnOutline
})

const optimizationStatusTag = computed(() => {
  const state = optimizationStates.value
  if (state.hasProcessing) {
    if (state.hasCompletedAny) {
      return { type: 'warning', text: '部分生成中' }
    }
    return { type: 'warning', text: '生成中' }
  }
  if (state.hasError && state.hasCompletedAny) {
    return { type: 'danger', text: '部分失败' }
  }
  if (state.hasError && !state.hasCompletedAny) {
    return { type: 'danger', text: '生成失败' }
  }
  if (state.hasCompletedAny) {
    return { type: 'success', text: '已完成' }
  }
  return { type: 'info', text: '待生成' }
})

const optimizationAvailableList = computed(() => {
  const completed = optimizationStates.value.completed
  const list = []
  if (completed.p1) {
    list.push('P1')
  }
  if (completed.p2) {
    list.push('P2')
  }
  if (completed.p3) {
    list.push('P3')
  }
  return list
})

const optimizationAvailabilityText = computed(() => {
  const list = optimizationAvailableList.value
  if (list.length === 0) {
    return '暂无'
  }
  return list.join(' / ')
})

const toggleCollapse = () => {
  emit('update:collapsed', !props.collapsed)
}

const copyOptimizationContent = async () => {
  let currentContent = ''
  if (activeOptimizationTab.value === 'p1') {
    currentContent = props.p1Content
  } else if (activeOptimizationTab.value === 'p2') {
    currentContent = props.p2Content
  } else if (activeOptimizationTab.value === 'p3') {
    currentContent = props.p3Content
  }

  if (currentContent) {
    try {
      await navigator.clipboard.writeText(currentContent)
      ElMessage.success('已复制到剪贴板')
    } catch (err) {
      ElMessage.error('复制失败')
    }
  }
}

const scrollTabContentToBottom = () => {
  if (!tabAutoScrollEnabled.value) return
  if (!props.isProcessing) return

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

watch(
  () => [props.p1Content, props.p2Content, props.p3Content],
  () => {
    scrollTabContentToBottom()
  }
)

watch(activeOptimizationTab, () => {
  tabAutoScrollEnabled.value = true
  scrollTabContentToBottom()
})

watch(
  () => props.isProcessing,
  isProcessing => {
    if (isProcessing) {
      tabAutoScrollEnabled.value = true
    }
  }
)

const scrollIntoView = options => {
  if (rootRef.value) {
    rootRef.value.scrollIntoView(options)
  }
}

defineExpose({
  scrollIntoView
})
</script>

<style scoped>
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

.process-card.processing {
  border-left-color: var(--warning);
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
  overflow-x: hidden;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: 8px;
}

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

.tab-content-wrapper {
  overflow-x: hidden;
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
  max-height: 5000px;
  padding: 20px;
}
</style>
