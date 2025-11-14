<template>
  <SummaryCard 
    icon=""
    :icon-component="BulbOutline"
    title="根因分析"
    :clickable="true"
    @click="emit('jump-to-node', 'integrated_analysis')"
  >
    <div class="analysis-summary">
      <!-- 综合评价 -->
      <div v-if="summary" class="analysis-section">
        <div class="section-header">
          <n-icon :component="CheckmarkCircleOutline" />
          <span class="section-title">综合评价</span>
        </div>
        <div class="summary-text">
          {{ summary }}
        </div>
      </div>

      <!-- 关键发现 -->
      <div v-if="keyFindings.length > 0" class="analysis-section">
        <div class="section-header">
          <n-icon :component="AlertCircleOutline" />
          <span class="section-title">关键发现</span>
        </div>
        <div class="findings-list">
          <div 
            v-for="(finding, index) in keyFindings" 
            :key="index"
            class="finding-item"
          >
            <n-icon :component="ChevronForwardOutline" class="bullet" />
            <span>{{ finding }}</span>
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div v-if="!hasContent" class="no-content">
        <n-icon :component="DocumentTextOutline" />
        <span>等待分析结果...</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import {
  BulbOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  ChevronForwardOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../common/SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  analysis: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  }
})

const emit = defineEmits(['jump-to-node'])

// 判断是否有内容（简化：只检查对象类型）
const hasContent = computed(() => {
  return props.analysis && typeof props.analysis === 'object'
})

// 直接访问数据字段（简化：不做复杂处理）
const summary = computed(() => {
  if (!hasContent.value) return ''
  return props.analysis.summary || ''
})

const keyFindings = computed(() => {
  if (!hasContent.value) return []
  return props.analysis.key_findings || []
})

const recommendations = computed(() => {
  if (!hasContent.value) return []
  return props.analysis.recommendations || []
})

const rootCauseAnalysis = computed(() => {
  if (!hasContent.value) return ''
  return props.analysis.root_cause_analysis || ''
})
</script>

<style scoped>
.analysis-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.analysis-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
}

.section-header .n-icon {
  font-size: 16px;
}

.section-title {
  color: var(--text-primary);
}

.summary-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--success);
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.finding-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.5;
}

.finding-item .bullet {
  font-size: 14px;
  color: var(--primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.recommendation {
  border-top: 1px solid var(--border-light);
  padding-top: 12px;
}

.recommendation-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  padding: 10px;
  background: linear-gradient(135deg, var(--warning-lighter) 0%, var(--warning-light) 100%);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--warning);
}

.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.no-content .n-icon {
  font-size: 20px;
}
</style>
