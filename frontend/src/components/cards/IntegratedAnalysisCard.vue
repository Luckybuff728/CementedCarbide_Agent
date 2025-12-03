<template>
  <div class="integrated-analysis-card">
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
</template>

<script setup>
/**
 * 根因分析卡片
 * 
 * 展示综合评价、关键发现等分析结果
 */
import { computed } from 'vue'
import { ElIcon } from 'element-plus'
import {
  CheckmarkCircleOutline,
  AlertCircleOutline,
  ChevronForwardOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'

const props = defineProps({
  // 分析数据对象
  analysis: {
    type: [Object, String],
    default: null
  },
  // 是否显示头部（兼容旧接口）
  showHeader: {
    type: Boolean,
    default: true
  }
})



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
.integrated-analysis-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.section-header .el-icon {
  font-size: 14px;
  color: #10b981;
}

.summary-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  padding-left: 12px;
  border-left: 2px solid #10b981;
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.finding-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
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
  color: #111827;
}

.finding-text :deep(em) {
  font-style: italic;
  color: #4b5563;
}

.finding-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  padding: 1px 4px;
  background: #f3f4f6;
  border-radius: 3px;
  color: #4f46e5;
}

.finding-item .bullet {
  font-size: 14px;
  color: #10b981;
  flex-shrink: 0;
  margin-top: 1px;
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
  font-size: 24px;
}
</style>
