<template>
  <SummaryCard 

    :icon-component="BulbOutline"
    title="根因分析"
    :clickable="true"
    @click="emit('jump-to-node', 'integrated_analysis')"
  >
    <div class="analysis-summary">
      <!-- 综合评价 -->
      <div v-if="summary" class="analysis-section">
        <div class="section-header">
          <el-icon><CheckmarkCircleOutline /></el-icon>
          <span class="section-title">综合评价</span>
        </div>
        <div class="summary-text">
          <MarkdownRenderer :content="summary" />
        </div>
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
            <div class="finding-text">
              <MarkdownRenderer :content="finding" />
            </div>
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
  }
})

const emit = defineEmits(['jump-to-node'])

// 清洗分析文本中的 Markdown 星号，避免不成对的 ** 裸露显示
const sanitizeAnalysisText = (text) => {
  if (!text) return ''
  return String(text)
    // 去掉可能出现在行首的列表符号，如 "- ", "* ", "• "
    .replace(/^\s*[-*•]\s+/gm, '')
    // 去掉剩余的星号/圆点（包含全角变体），避免残留
    .replace(/[\*•＊﹡]/g, '')
}

// 判断是否有内容（简化：只检查对象类型）
const hasContent = computed(() => {
  return props.analysis && typeof props.analysis === 'object'
})

// 访问数据字段并做轻量清洗，去掉不成对的 Markdown 星号
const summary = computed(() => {
  if (!hasContent.value) return ''
  return sanitizeAnalysisText(props.analysis.summary || '')
})

const keyFindings = computed(() => {
  if (!hasContent.value) return []
  const list = props.analysis.key_findings || []
  return list.map(item => sanitizeAnalysisText(item || ''))
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
  gap: 8px;
  color: var(--primary);
  font-size: var(--font-base);
  font-weight: 600;
}

.section-header .el-icon {
  font-size: var(--icon-base);
}

.section-title {
  color: var(--text-primary);
}

.summary-text {
  font-size: var(--font-base);
  color: var(--text-primary);
  line-height: 1.7;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--success);
}

.summary-text :deep(.markdown-content) {
  font-size: var(--font-base);
  line-height: 1.7;
  margin: 0;
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.finding-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  color: var(--text-primary);
  line-height: 1.6;
}

.finding-text {
  flex: 1;
}

.finding-item :deep(.markdown-content) {
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.finding-item .bullet {
  font-size: var(--icon-sm);
  color: var(--primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.recommendation {
  border-top: 1px solid var(--border-light);
  padding-top: 12px;
}

.recommendation-text {
  font-size: var(--font-base);
  color: var(--text-primary);
  line-height: 1.7;
  padding: 12px;
  background: linear-gradient(135deg, var(--warning-lighter) 0%, var(--warning-light) 100%);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--warning);
}

.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px 20px;
  color: var(--text-secondary);
  font-size: var(--font-base);
  font-weight: 500;
}

.no-content .el-icon {
  font-size: var(--icon-md);
}
</style>
