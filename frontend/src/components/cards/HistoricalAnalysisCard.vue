<template>
  <div class="historical-analysis-card">
    <!-- 检索概览 -->
    <div class="overview-section">
      <div class="overview-stats">
        <div class="stat-item">
          <el-icon :size="16"><DocumentTextOutline /></el-icon>
          <span>检索到 <strong>{{ data.total_docs_retrieved || 0 }}</strong> 篇文献</span>
        </div>
        <div class="stat-item" v-if="data.cn_docs_count">
          <span class="lang-tag zh">中文</span>
          <span>{{ data.cn_docs_count }} 篇</span>
        </div>
        <div class="stat-item" v-if="data.en_docs_count">
          <span class="lang-tag en">EN</span>
          <span>{{ data.en_docs_count }} 篇</span>
        </div>
        <div class="stat-item" v-if="performanceCount > 0">
          <el-icon :size="16"><StatsChartOutline /></el-icon>
          <span>提取 <strong>{{ performanceCount }}</strong> 条性能数据</span>
        </div>
      </div>
    </div>
    
    <!-- 关键指标汇总（用于实验对比） -->
    <div v-if="hasMetrics" class="metrics-summary">
      <div class="section-title">
        <el-icon :size="16"><SpeedometerOutline /></el-icon>
        <span>文献性能参考范围</span>
      </div>
      <div class="metrics-grid">
        <div v-if="data.extracted_metrics?.hardness" class="metric-card hardness">
          <div class="metric-label">硬度 (GPa)</div>
          <div class="metric-value">
            {{ data.extracted_metrics.hardness.min }} ~ {{ data.extracted_metrics.hardness.max }}
          </div>
          <div class="metric-avg">平均: {{ data.extracted_metrics.hardness.avg }}</div>
        </div>
        <div v-if="data.extracted_metrics?.elastic_modulus" class="metric-card modulus">
          <div class="metric-label">弹性模量 (GPa)</div>
          <div class="metric-value">
            {{ data.extracted_metrics.elastic_modulus.min }} ~ {{ data.extracted_metrics.elastic_modulus.max }}
          </div>
          <div class="metric-avg">平均: {{ data.extracted_metrics.elastic_modulus.avg }}</div>
        </div>
        <div v-if="data.extracted_metrics?.adhesion_strength" class="metric-card adhesion">
          <div class="metric-label">结合力 (N)</div>
          <div class="metric-value">
            {{ data.extracted_metrics.adhesion_strength.min }} ~ {{ data.extracted_metrics.adhesion_strength.max }}
          </div>
          <div class="metric-avg">平均: {{ data.extracted_metrics.adhesion_strength.avg }}</div>
        </div>
        <div v-if="data.extracted_metrics?.wear_rate" class="metric-card wear">
          <div class="metric-label">磨损率 (×10⁻⁶ mm³/Nm)</div>
          <div class="metric-value">
            {{ formatWearRate(data.extracted_metrics.wear_rate.min) }} ~ {{ formatWearRate(data.extracted_metrics.wear_rate.max) }}
          </div>
          <div class="metric-avg">平均: {{ formatWearRate(data.extracted_metrics.wear_rate.avg) }}</div>
        </div>
      </div>
      <!-- 最佳案例 -->
      <div v-if="data.extracted_metrics?.best_case" class="best-case">
        <span class="best-label">📊 最高硬度参考:</span>
        <span class="best-value">{{ data.extracted_metrics.best_case.hardness }} GPa</span>
        <span class="best-source">({{ data.extracted_metrics.best_case.composition || data.extracted_metrics.best_case.source }})</span>
        <span v-if="data.extracted_metrics.best_case.elastic_modulus" class="best-extra">
          | 模量: {{ data.extracted_metrics.best_case.elastic_modulus }} GPa
        </span>
        <span v-if="data.extracted_metrics.best_case.adhesion_strength" class="best-extra">
          | 结合力: {{ data.extracted_metrics.best_case.adhesion_strength }} N
        </span>
      </div>
    </div>
    
    <!-- 相关性总结 -->
    <div v-if="data.relevance_summary" class="relevance-summary">
      <el-icon :size="16"><InformationCircleOutline /></el-icon>
      <p>{{ data.relevance_summary }}</p>
    </div>
    
    <!-- 关键发现 -->
    <div v-if="data.key_findings?.length" class="content-section">
      <div class="section-title">
        <el-icon :size="16"><BulbOutline /></el-icon>
        <span>关键发现</span>
      </div>
      <ul class="findings-list">
        <li v-for="(finding, idx) in data.key_findings" :key="idx">
          {{ finding }}
        </li>
      </ul>
    </div>
    
    <!-- 性能数据详情 -->
    <div v-if="data.performance_data?.length" class="content-section">
      <div class="section-title">
        <el-icon :size="16"><GridOutline /></el-icon>
        <span>性能数据</span>
        <span class="section-count">({{ data.performance_data.length }})</span>
      </div>
      <div class="performance-list">
        <div 
          v-for="(item, idx) in data.performance_data.slice(0, showAllPerf ? undefined : 3)" 
          :key="idx" 
          class="perf-item"
        >
          <div class="perf-header">
            <span class="perf-source">{{ item.source || '文献' + (idx + 1) }}</span>
          </div>
          <div class="perf-body">
            <span v-if="item.composition" class="perf-tag comp">{{ item.composition }}</span>
            <span v-if="item.process" class="perf-tag process">{{ item.process }}</span>
          </div>
          <div class="perf-values">
            <span v-if="item.hardness" class="perf-value">
              <strong>硬度:</strong> {{ item.hardness }} GPa
            </span>
            <span v-if="item.elastic_modulus" class="perf-value">
              <strong>模量:</strong> {{ item.elastic_modulus }} GPa
            </span>
            <span v-if="item.adhesion_strength" class="perf-value">
              <strong>结合力:</strong> {{ item.adhesion_strength }} N
            </span>
            <span v-if="item.wear_rate" class="perf-value">
              <strong>磨损率:</strong> {{ formatWearRate(item.wear_rate) }} ×10⁻⁶
            </span>
          </div>
          <div v-if="item.notes" class="perf-other">
            {{ item.notes }}
          </div>
        </div>
        <div 
          v-if="data.performance_data.length > 3" 
          class="show-more"
          @click="showAllPerf = !showAllPerf"
        >
          {{ showAllPerf ? '收起' : `展开更多 (${data.performance_data.length - 3})` }}
        </div>
      </div>
    </div>
    
    <!-- 改进建议 -->
    <div v-if="data.recommendations?.length" class="content-section recommendations">
      <div class="section-title">
        <el-icon :size="16"><RocketOutline /></el-icon>
        <span>改进建议</span>
      </div>
      <ul class="recommendations-list">
        <li v-for="(rec, idx) in data.recommendations" :key="idx">
          {{ rec }}
        </li>
      </ul>
    </div>
    
    <!-- 文献引用 -->
    <div v-if="data.references?.length" class="content-section references">
      <el-collapse>
        <el-collapse-item>
          <template #title>
            <div class="section-title collapse-title">
              <el-icon :size="16"><BookOutline /></el-icon>
              <span>参考文献 ({{ data.references.length }})</span>
            </div>
          </template>
          <div class="references-list">
            <div 
              v-for="(ref, idx) in data.references" 
              :key="idx" 
              class="ref-item"
            >
              <span class="ref-index">[{{ idx + 1 }}]</span>
              <span class="ref-lang" :class="ref.language">
                {{ ref.language === 'en' ? 'EN' : '中' }}
              </span>
              <span class="ref-citation">
                <!-- 学术格式引用：作者. 标题. DOI: xxx -->
                {{ ref.citation || ref.title || '未知标题' }}
              </span>
              <span class="ref-score" v-if="ref.relevance_score">
                {{ (ref.relevance_score * 100).toFixed(0) }}%
              </span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
/**
 * 历史数据智能分析卡片
 * 
 * 展示基于 RAG+LLM 的文献检索和分析结果
 * 
 * 数据结构:
 * - performance_data: 性能数据列表
 * - key_findings: 关键发现
 * - recommendations: 改进建议
 * - relevance_summary: 相关性总结
 * - extracted_metrics: 关键指标汇总（用于实验对比）
 * - references: 文献引用列表
 */
import { ref, computed } from 'vue'
import { ElIcon, ElCollapse, ElCollapseItem } from 'element-plus'
import {
  DocumentTextOutline,
  StatsChartOutline,
  SpeedometerOutline,
  InformationCircleOutline,
  BulbOutline,
  GridOutline,
  RocketOutline,
  BookOutline
} from '@vicons/ionicons5'

const props = defineProps({
  // 历史分析数据
  data: {
    type: Object,
    required: true
  },
  // 是否显示头部
  showHeader: {
    type: Boolean,
    default: true
  }
})

// 是否展开所有性能数据
const showAllPerf = ref(false)

// 计算属性
const performanceCount = computed(() => {
  return props.data.performance_data?.length || 0
})

const hasMetrics = computed(() => {
  const metrics = props.data.extracted_metrics
  return metrics && (metrics.hardness || metrics.elastic_modulus || metrics.adhesion_strength || metrics.wear_rate)
})

// 格式化磨损率（转换为 ×10⁻⁶ 显示）
const formatWearRate = (value) => {
  if (!value) return 'N/A'
  // 如果值很小（如 0.0002），乘以 10^6 显示
  if (value < 0.01) {
    return (value * 1e6).toFixed(2)
  }
  return value.toFixed(4)
}
</script>

<style scoped>
.historical-analysis-card {
  background: var(--bg-primary);
}

/* 概览区域 */
.overview-section {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--bg-tertiary);
}

.overview-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-item strong {
  color: var(--primary);
  font-weight: 600;
}

.lang-tag {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.lang-tag.zh {
  background: #fef3c7;
  color: #92400e;
}

.lang-tag.en {
  background: #dbeafe;
  color: #1e40af;
}

/* 关键指标汇总 */
.metrics-summary {
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(147, 51, 234, 0.05) 100%);
  border-bottom: 1px solid var(--bg-tertiary);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.metric-card {
  padding: 10px 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.metric-card.hardness {
  border-left-color: #3b82f6;
}

.metric-card.adhesion {
  border-left-color: #10b981;
}

.metric-card.modulus {
  border-left-color: #8b5cf6;
}

.metric-card.wear {
  border-left-color: #f59e0b;
}

.best-extra {
  color: var(--text-secondary);
  font-size: 11px;
}

.metric-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-avg {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.best-case {
  margin-top: 10px;
  padding: 8px 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.best-label {
  color: var(--text-secondary);
}

.best-value {
  font-weight: 600;
  color: var(--primary);
}

.best-source {
  color: var(--text-tertiary);
  font-size: 11px;
}

/* 相关性总结 */
.relevance-summary {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-left: 3px solid #667eea;
}

.relevance-summary p {
  margin: 0;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

/* 内容区块 */
.content-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--bg-tertiary);
}

.content-section:last-child {
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.section-count {
  font-weight: 400;
  color: var(--text-tertiary);
}

/* 发现列表 */
.findings-list,
.recommendations-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.findings-list li,
.recommendations-list li {
  margin-bottom: 6px;
}

.findings-list li:last-child,
.recommendations-list li:last-child {
  margin-bottom: 0;
}

/* 建议区块 */
.recommendations .recommendations-list {
  background: var(--bg-secondary);
  padding: 12px 12px 12px 32px;
  border-radius: 8px;
}

.recommendations-list li {
  color: var(--text-primary);
}

/* 性能数据列表 */
.performance-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.perf-item {
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.perf-header {
  margin-bottom: 6px;
}

.perf-source {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.perf-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.perf-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.perf-tag.comp {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.perf-tag.process {
  background: #dbeafe;
  color: #1e40af;
}

.perf-values {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
}

.perf-value {
  color: var(--text-secondary);
}

.perf-value strong {
  color: var(--text-primary);
}

.perf-other {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.show-more {
  text-align: center;
  padding: 8px;
  font-size: 12px;
  color: var(--primary);
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
}

.show-more:hover {
  background: var(--bg-secondary);
}

/* 文献引用 */
.references :deep(.el-collapse) {
  border: none;
}

.references :deep(.el-collapse-item__header) {
  background: transparent;
  border: none;
  padding: 0;
  height: auto;
  line-height: 1.5;
}

.references :deep(.el-collapse-item__wrap) {
  background: transparent;
  border: none;
}

.references :deep(.el-collapse-item__content) {
  padding: 8px 0 0 0;
}

.collapse-title {
  margin-bottom: 0;
}

.references-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ref-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.ref-index {
  color: var(--primary);
  font-weight: 600;
  flex-shrink: 0;
}

.ref-lang {
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 500;
  flex-shrink: 0;
}

.ref-lang.zh {
  background: #fef3c7;
  color: #92400e;
}

.ref-lang.en {
  background: #dbeafe;
  color: #1e40af;
}

.ref-citation {
  flex: 1;
  color: var(--text-secondary);
  line-height: 1.4;
  font-style: normal;
}

/* DOI 样式 */
.ref-citation :deep(a) {
  color: var(--primary);
  text-decoration: none;
}

.ref-citation :deep(a):hover {
  text-decoration: underline;
}

.ref-score {
  flex-shrink: 0;
  padding: 1px 6px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  color: var(--text-tertiary);
  font-size: 11px;
}
</style>
