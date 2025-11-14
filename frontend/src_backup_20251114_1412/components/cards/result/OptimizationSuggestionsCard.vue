<template>
  <SummaryCard 
    icon=""
    :icon-component="BulbOutline"
    title="优化建议"
    :badge="getOptimizationBadge()"
    :clickable="true"
    @click="emit('jump-to-node', 'optimization')"
  >
    <div class="optimization-summary">
      <!-- 可用方案列表 -->
      <div class="suggestions-list">
        <div v-if="suggestions.p1" class="suggestion-item p1">
          <div class="suggestion-header">
            <n-icon :component="FlaskOutline" />
            <span class="suggestion-tag">P1</span>
            <span class="suggestion-name">成分优化</span>
          </div>
          <div class="suggestion-preview">
            {{ getPreview(suggestions.p1, 80) }}
          </div>
        </div>

        <div v-if="suggestions.p2" class="suggestion-item p2">
          <div class="suggestion-header">
            <n-icon :component="BuildOutline" />
            <span class="suggestion-tag">P2</span>
            <span class="suggestion-name">结构优化</span>
          </div>
          <div class="suggestion-preview">
            {{ getPreview(suggestions.p2, 80) }}
          </div>
        </div>

        <div v-if="suggestions.p3" class="suggestion-item p3">
          <div class="suggestion-header">
            <n-icon :component="SettingsOutline" />
            <span class="suggestion-tag">P3</span>
            <span class="suggestion-name">工艺优化</span>
          </div>
          <div class="suggestion-preview">
            {{ getPreview(suggestions.p3, 80) }}
          </div>
        </div>
      </div>

      <!-- 无建议提示 -->
      <div v-if="!hasAnySuggestion" class="no-suggestions">
        <n-icon :component="InformationCircleOutline" />
        <span>等待优化建议...</span>
      </div>

      <!-- 点击查看提示 -->
      <div v-if="hasAnySuggestion" class="view-hint">
        <n-icon :component="ArrowForwardOutline" />
        <span>点击查看详细优化方案</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import {
  BulbOutline,
  FlaskOutline,
  BuildOutline,
  SettingsOutline,
  InformationCircleOutline,
  ArrowForwardOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  suggestions: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['jump-to-node'])

// 是否有任何建议
const hasAnySuggestion = computed(() => {
  return props.suggestions.p1 || props.suggestions.p2 || props.suggestions.p3
})

// 获取可用方案数量
const availableCount = computed(() => {
  let count = 0
  if (props.suggestions.p1) count++
  if (props.suggestions.p2) count++
  if (props.suggestions.p3) count++
  return count
})

// 获取优化徽章
const getOptimizationBadge = () => {
  const count = availableCount.value
  if (count === 3) {
    return { text: '3个方案', type: 'success' }
  } else if (count === 2) {
    return { text: '2个方案', type: 'info' }
  } else if (count === 1) {
    return { text: '1个方案', type: 'warning' }
  }
  return null
}

// 获取内容预览
const getPreview = (content, maxLength = 80) => {
  if (!content) return ''
  
  // 去除Markdown标记和多余空白
  const plainText = content
    .replace(/[#*`_]/g, '')
    .replace(/\n+/g, ' ')
    .trim()
  
  // 截取指定长度
  if (plainText.length > maxLength) {
    return plainText.substring(0, maxLength) + '...'
  }
  
  return plainText
}
</script>

<style scoped>
.optimization-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-item {
  padding: 12px;
  border-radius: var(--radius-md);
  border-left: 3px solid;
  background: var(--bg-tertiary);
  transition: all var(--transition-fast);
  cursor: default;
}

.suggestion-item.p1 {
  border-left-color: var(--success);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.02) 100%);
}

.suggestion-item.p2 {
  border-left-color: var(--primary);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(59, 130, 246, 0.02) 100%);
}

.suggestion-item.p3 {
  border-left-color: var(--warning);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(245, 158, 11, 0.02) 100%);
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.suggestion-header .n-icon {
  font-size: 16px;
  color: var(--text-secondary);
}

.suggestion-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 700;
  background: var(--primary);
  color: white;
}

.suggestion-item.p1 .suggestion-tag {
  background: var(--success);
}

.suggestion-item.p2 .suggestion-tag {
  background: var(--primary);
}

.suggestion-item.p3 .suggestion-tag {
  background: var(--warning);
}

.suggestion-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.suggestion-preview {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.no-suggestions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.no-suggestions .n-icon {
  font-size: 20px;
}

.view-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  font-size: 12px;
  color: var(--primary);
  background: var(--primary-lighter);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.view-hint .n-icon {
  font-size: 14px;
  animation: slideRight 1.5s ease-in-out infinite;
}

@keyframes slideRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(4px);
  }
}
</style>
