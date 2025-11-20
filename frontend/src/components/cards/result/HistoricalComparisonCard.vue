<template>
  <SummaryCard 

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
            <el-tag size="small" :type="getSimilarityType(c.similarity)">
              {{ Math.round(c.similarity * 100) }}% 相似
            </el-tag>
          </div>
          <div class="case-metrics">
            <span class="metric">
              <el-icon><DiamondOutline /></el-icon>
              {{ c.hardness || 'N/A' }} GPa
            </span>
            <span v-if="c.adhesion_strength" class="metric">
              <el-icon><LinkOutline /></el-icon>
              {{ c.adhesion_strength }} N
            </span>
          </div>
        </div>
      </div>

      <!-- 无案例提示 -->
      <div v-else class="no-cases">
        <el-icon><InformationCircleOutline /></el-icon>
        <span>暂无相似历史案例</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { ElTag, ElIcon } from 'element-plus'
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
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: var(--font-lg);
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
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-weight: 600;
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
  font-size: var(--font-sm);
  color: var(--text-primary);
  font-weight: 500;
}

.metric {
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric .el-icon {
  font-size: var(--icon-sm);
  color: var(--text-secondary);
}

.no-cases {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  color: var(--text-secondary);
  font-size: var(--font-base);
  font-weight: 500;
}

.no-cases .el-icon {
  font-size: var(--icon-base);
}
</style>
