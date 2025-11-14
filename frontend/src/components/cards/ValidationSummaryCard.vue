<template>
  <SummaryCard 
    icon=""
    :icon-component="validationIcon"
    title="参数验证"
    :badge="validationBadge"
    :clickable="true"
    @click="emit('jump-to-node', 'input_validation')"
  >
    <div class="validation-summary">
      <div class="validation-status">
        <n-icon :component="validationIcon" :color="statusColor" />
        <span :class="statusClass">{{ statusText }}</span>
      </div>
      
      <div v-if="hasErrors" class="validation-hint">
        <span>点击查看详细分析</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import { 
  CheckmarkCircleOutline, 
  CloseCircleOutline 
} from '@vicons/ionicons5'
import SummaryCard from '../common/SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  validationResult: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  }
})

const emit = defineEmits(['jump-to-node'])

// 判断验证是否成功
const isSuccess = computed(() => {
  if (!props.validationResult) return true
  return props.validationResult.input_validated === true
})

// 是否有错误
const hasErrors = computed(() => !isSuccess.value)

// 验证图标
const validationIcon = computed(() => {
  return isSuccess.value ? CheckmarkCircleOutline : CloseCircleOutline
})

// 状态颜色
const statusColor = computed(() => {
  return isSuccess.value ? '#10b981' : '#ef4444'
})

// 状态文本
const statusText = computed(() => {
  return isSuccess.value ? '参数验证通过' : '参数验证失败'
})

// 状态样式类
const statusClass = computed(() => {
  return isSuccess.value ? 'success' : 'error'
})

// 验证徽章
const validationBadge = computed(() => {
  return isSuccess.value 
    ? { text: '通过', type: 'success' }
    : { text: '失败', type: 'danger' }
})
</script>

<style scoped>
.validation-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.validation-status .n-icon {
  font-size: 18px;
}

.success {
  color: var(--success);
  font-weight: 500;
}

.error {
  color: var(--danger);
  font-weight: 500;
}

.validation-hint {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
}

.validation-hint span {
  color: var(--primary);
  cursor: pointer;
}
</style>
