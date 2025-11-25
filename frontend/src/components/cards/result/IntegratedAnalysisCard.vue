<template>
  <SummaryCard 

    :icon-component="BulbOutline"
    title="根因分析"
    :clickable="true"
    :show-header="showHeader"
    @click="emit('jump-to-node', 'integrated_analysis')"
  >
    <div class="analysis-summary">
      <!-- 综合评价 -->
      <div v-if="summary" class="analysis-section">
        <div class="section-header">
          <el-icon><CheckmarkCircleOutline /></el-icon>
          <span class="section-title">综合评价</span>
        </div>
        <div class="summary-text">{{ summary }}</div>
      </div>

      <!-- 关键发现 -->
      <div v-if="keyFindings.length > 0" class="analysis-section">
        <div class="section-header">
          <el-icon><AlertCircleOutline /></el-icon>
          <span class="section-title">关键发现</span>
        </div>
        <div class="findings-list">
          <div 
            v-for="(finding, index) in keyFindings" 
            :key="index"
            class="finding-item"
          >
            <el-icon class="bullet"><ChevronForwardOutline /></el-icon>
            <span class="finding-text" v-html="renderInlineMarkdown(finding)"></span>
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div v-if="!hasContent" class="no-content">
        <el-icon><DocumentTextOutline /></el-icon>
        <span>等待分析结果...</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { ElIcon } from 'element-plus'
import {
  BulbOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  ChevronForwardOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../common/SummaryCard.vue'
import MarkdownRenderer from '../../common/MarkdownRenderer.vue'

// 定义props和emits
const props = defineProps({
  analysis: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  },
  showHeader: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['jump-to-node'])



// 判断是否有内容（简化：只检查对象类型）
const hasContent = computed(() => {
  return props.analysis && typeof props.analysis === 'object'
})

// 访问数据字段并做轻量清洗，去掉不成对的 Markdown 星号
const summary = computed(() => {
  if (!hasContent.value) return ''
  return props.analysis.summary || ''
})

const keyFindings = computed(() => {
  if (!hasContent.value) return []
  const list = props.analysis.key_findings || []
  return list.map(item => item || '')
})

const recommendations = computed(() => {
  if (!hasContent.value) return []
  return props.analysis.recommendations || []
})

const rootCauseAnalysis = computed(() => {
  if (!hasContent.value) return ''
  return props.analysis.root_cause_analysis || ''
})

// 轻量级内联Markdown渲染（处理粗体、斜体）
const renderInlineMarkdown = (text) => {
  if (!text) return ''
  return text
    // 粗体: **text** 或 __text__
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    // 斜体: *text* 或 _text_
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/_([^_]+)_/g, '<em>$1</em>')
    // 行内代码: `code`
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}
</script>

<style scoped>
/* 根因分析摘要卡片 - 简洁样式 */
.analysis-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.section-header .el-icon {
  font-size: 14px;
  color: #10b981;
}

.section-title {
  color: #374151;
}

.summary-text {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.6;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #10b981;
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.finding-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.finding-text {
  flex: 1;
}

/* 内联Markdown样式 */
.finding-text :deep(strong) {
  font-weight: 600;
  color: #1f2937;
}

.finding-text :deep(em) {
  font-style: italic;
  color: #4b5563;
}

.finding-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  padding: 1px 4px;
  background: #e5e7eb;
  border-radius: 3px;
  color: #6366f1;
}

.finding-item .bullet {
  font-size: 12px;
  color: #6366f1;
  flex-shrink: 0;
  margin-top: 2px;
}

.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  color: #9ca3af;
  font-size: 14px;
}

.no-content .el-icon {
  font-size: 20px;
}
</style>
