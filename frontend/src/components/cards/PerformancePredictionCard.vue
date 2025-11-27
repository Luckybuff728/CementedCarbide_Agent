<template>
  <SummaryCard 

    :icon-component="RadioButtonOnOutline"
    title="性能预测"
    :badge="confidenceBadge"
    :clickable="true"
    :show-header="showHeader"
    @click="emit('jump-to-node', 'ml_prediction')"
  >
    <div class="prediction-summary">
      <div class="key-metric">
        <span class="metric-label">预测硬度</span>
        <span class="metric-value highlight">
          {{ predictionData.hardness }} GPa
        </span>
      </div>
      <div class="metrics-grid">
        <div class="metric-item">
          <span>弹性模量</span>
          <span>{{ predictionData.elastic_modulus }} GPa</span>
        </div>
        <div class="metric-item">
          <span>磨损率</span>
          <span>{{ predictionData.wear_rate }} mm³/Nm</span>
        </div>
        <div class="metric-item">
          <span>结合力</span>
          <span>{{ predictionData.adhesion_strength }} N</span>
        </div>
      </div>
      <div class="metric-item" style="margin-top: 8px;">
        <span>模型置信度</span>
        <el-progress 
          :percentage="predictionData.confidence"
          :color="getConfidenceColor(predictionData.confidence / 100)"
          :stroke-width="8"
        />
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
// import { NIcon } from 'naive-ui' // Removed unused import
import { RadioButtonOnOutline } from '@vicons/ionicons5'
import { getConfidenceColor } from '../../utils/markdown'
import SummaryCard from '../common/SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  prediction: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  },
  showHeader: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['jump-to-node'])

// 获取预测数据
const predictionData = computed(() => {
  const pred = props.prediction
  // 检查是否为对象类型
  if (!pred || typeof pred !== 'object') {
    return {
      hardness: 'N/A',
      elastic_modulus: 'N/A',
      wear_rate: 'N/A',
      adhesion_strength: 'N/A',
      confidence: 0
    }
  }
  
  return {
    hardness: pred.hardness ?? 'N/A',
    elastic_modulus: pred.elastic_modulus ?? 'N/A',
    wear_rate: pred.wear_rate ?? 'N/A',
    adhesion_strength: pred.adhesion_strength ?? 'N/A',
    confidence: Math.round((pred.model_confidence || 0) * 100)
  }
})

// 获取置信度徽章
const confidenceBadge = computed(() => {
  const confidence = predictionData.value.confidence
  if (confidence >= 80) {
    return { text: '高置信度', type: 'success' }
  } else if (confidence >= 60) {
    return { text: '中等置信度', type: 'warning' }
  } else {
    return { text: '低置信度', type: 'danger' }
  }
})
</script>

<style scoped>
.prediction-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.key-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.metric-value.highlight {
  color: #1967d2;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}

.metric-item span:first-child {
  font-weight: 500;
  color: #6b7280;
}

.metric-item span:last-child {
  font-weight: 600;
  color: #111827;
}
</style>
