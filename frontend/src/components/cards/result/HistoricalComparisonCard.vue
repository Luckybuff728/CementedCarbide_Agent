<template>
  <SummaryCard 
    icon=""
    :icon-component="BarChartOutline"
    title="历史对比"
    :badge="getBadge()"
    :clickable="true"
    @click="emit('jump-to-node', 'historical_comparison')"
  >
    <div class="comparison-summary">
      <!-- 统计信息 -->
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">相似案例</span>
          <span class="stat-value">{{ comparison.total_cases || 0 }} 个</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最高硬度</span>
          <span class="stat-value highlight">
            {{ comparison.highest_hardness || 'N/A' }} GPa
          </span>
        </div>
      </div>

      <!-- 相似案例预览 -->
      <div v-if="hasSimilarCases" class="cases-preview">
        <div class="preview-label">最相似案例</div>
        <div 
          v-for="(c, i) in topCases" 
          :key="i"
          class="case-item"
        >
          <div class="case-similarity">
            <n-tag size="small" :type="getSimilarityType(c.similarity)">
              {{ Math.round(c.similarity * 100) }}% 相似
            </n-tag>
          </div>
          <div class="case-metrics">
            <span class="metric">
              <n-icon :component="DiamondOutline" />
              {{ c.hardness || 'N/A' }} GPa
            </span>
            <span v-if="c.adhesion_strength" class="metric">
              <n-icon :component="LinkOutline" />
              {{ c.adhesion_strength }} N
            </span>
          </div>
        </div>
      </div>

      <!-- 无案例提示 -->
      <div v-else class="no-cases">
        <n-icon :component="InformationCircleOutline" />
        <span>暂无相似历史案例</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { NTag, NIcon } from 'naive-ui'
import {
  BarChartOutline,
  DiamondOutline,
  LinkOutline,
  InformationCircleOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../common/SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  comparison: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  }
})

const emit = defineEmits(['jump-to-node'])

// 是否有相似案例
const hasSimilarCases = computed(() => {
  return props.comparison && 
         typeof props.comparison === 'object' && 
         props.comparison.similar_cases && 
         props.comparison.similar_cases.length > 0
})

// 取前2个最相似的案例
const topCases = computed(() => {
  if (!hasSimilarCases.value) return []
  return props.comparison.similar_cases.slice(0, 2)
})

// 获取徽章
const getBadge = () => {
  const total = props.comparison?.total_cases || 0
  if (total >= 5) {
    return { text: `${total}个案例`, type: 'success' }
  } else if (total > 0) {
    return { text: `${total}个案例`, type: 'warning' }
  }
  return null
}

// 获取相似度类型
const getSimilarityType = (similarity) => {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.7) return 'info'
  return 'warning'
}
</script>

<style scoped>
.comparison-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.highlight {
  color: var(--primary);
}

.cases-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.case-item {
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--primary-light);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-similarity {
  display: flex;
  align-items: center;
}

.case-metrics {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--text-primary);
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric .n-icon {
  font-size: 14px;
  color: var(--text-secondary);
}

.no-cases {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.no-cases .n-icon {
  font-size: 18px;
}
</style>
