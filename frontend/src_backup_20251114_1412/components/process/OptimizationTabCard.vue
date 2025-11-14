<template>
  <div :class="['optimization-tab-card', 'process-card', 'completed', { collapsed }]" ref="cardRef">
    <!-- 卡片头部 -->
    <div class="card-header" @click="toggleCollapse">
      <div class="header-left">
        <n-icon class="status-icon completed" :component="CheckmarkCircle" />
        <n-icon class="title-icon" :component="BulbOutline" />
        <h4>优化建议</h4>
        <el-tag type="success" size="small">已完成</el-tag>
        <el-tag v-if="availableCount > 0" size="small" type="info">
          {{ availableCount }}个方案
        </el-tag>
      </div>
      <div class="header-right">
        <n-icon 
          class="toggle-icon" 
          :component="collapsed ? ChevronDownOutline : ChevronUpOutline" 
        />
      </div>
    </div>
    
    <!-- 卡片内容 -->
    <transition name="collapse">
      <div v-show="!collapsed" class="card-content">
        <el-tabs v-model="activeTab" class="optimization-tabs">
          <!-- P1成分优化 -->
          <el-tab-pane v-if="p1Content" name="p1">
            <template #label>
              <div class="tab-label">
                <n-icon :component="FlaskOutline" />
                <span>P1 成分优化</span>
              </div>
            </template>
            <div class="tab-content-wrapper">
              <MarkdownRenderer :content="p1Content" />
            </div>
          </el-tab-pane>
          
          <!-- P2结构优化 -->
          <el-tab-pane v-if="p2Content" name="p2">
            <template #label>
              <div class="tab-label">
                <n-icon :component="BuildOutline" />
                <span>P2 结构优化</span>
              </div>
            </template>
            <div class="tab-content-wrapper">
              <MarkdownRenderer :content="p2Content" />
            </div>
          </el-tab-pane>
          
          <!-- P3工艺优化 -->
          <el-tab-pane v-if="p3Content" name="p3">
            <template #label>
              <div class="tab-label">
                <n-icon :component="SettingsOutline" />
                <span>P3 工艺优化</span>
              </div>
            </template>
            <div class="tab-content-wrapper">
              <MarkdownRenderer :content="p3Content" />
            </div>
          </el-tab-pane>
        </el-tabs>
        
        <!-- 卡片底部操作 -->
        <div class="card-footer">
          <el-button text size="small" @click="handleCopy">
            <template #icon>
              <n-icon :component="CopyOutline" />
            </template>
            复制当前内容
          </el-button>
          
          <el-button text size="small" @click="handleExpandAll">
            <template #icon>
              <n-icon :component="ExpandOutline" />
            </template>
            展开所有
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NIcon } from 'naive-ui'
import { ElMessage } from 'element-plus'
import {
  CheckmarkCircle,
  BulbOutline,
  FlaskOutline,
  BuildOutline,
  SettingsOutline,
  ChevronDownOutline,
  ChevronUpOutline,
  CopyOutline,
  ExpandOutline
} from '@vicons/ionicons5'
import MarkdownRenderer from '../MarkdownRenderer.vue'

// 定义props
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
  defaultCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['copy', 'expand-all'])

// 状态
const collapsed = ref(props.defaultCollapsed)
const activeTab = ref('p1')
const cardRef = ref(null)

// 可用方案数量
const availableCount = computed(() => {
  let count = 0
  if (props.p1Content) count++
  if (props.p2Content) count++
  if (props.p3Content) count++
  return count
})

// 当前Tab的内容
const currentContent = computed(() => {
  switch (activeTab.value) {
    case 'p1':
      return props.p1Content
    case 'p2':
      return props.p2Content
    case 'p3':
      return props.p3Content
    default:
      return ''
  }
})

// ==================== 方法 ====================

// 切换折叠状态
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

// 复制当前内容
const handleCopy = () => {
  const content = currentContent.value
  if (!content) {
    ElMessage.warning('当前Tab没有内容')
    return
  }
  
  navigator.clipboard.writeText(content).then(() => {
    ElMessage.success('内容已复制到剪贴板')
    emit('copy', { tab: activeTab.value, content })
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 展开所有
const handleExpandAll = () => {
  emit('expand-all')
}

// 暴露方法
defineExpose({
  collapse: () => { collapsed.value = true },
  expand: () => { collapsed.value = false },
  switchTab: (tab) => { activeTab.value = tab }
})
</script>

<style scoped>
.optimization-tab-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-color);
  transition: all var(--transition-fast);
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}

.optimization-tab-card.collapsed {
  border-color: var(--border-light);
}

.card-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
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

.status-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.status-icon.completed {
  color: var(--success);
}

.title-icon {
  font-size: 20px;
  color: var(--warning);
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-icon {
  font-size: 20px;
  color: var(--text-secondary);
  transition: transform var(--transition-fast);
}

.card-content {
  border-top: 1px solid var(--border-light);
  padding: 20px;
}

.optimization-tabs {
  margin-bottom: 16px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.tab-label .n-icon {
  font-size: 16px;
}

.tab-content-wrapper {
  padding: 16px 0;
}

.card-footer {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* Tabs样式覆盖 */
.optimization-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.optimization-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--border-light);
}

.optimization-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.optimization-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary);
  font-weight: 600;
}

.optimization-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--primary);
}

/* Markdown渲染器容器样式 */
.tab-content-wrapper :deep(.markdown-body) {
  background: transparent;
  padding: 0;
}
</style>
