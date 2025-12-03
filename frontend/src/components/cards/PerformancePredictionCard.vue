<template>
  <div class="performance-prediction-card">
    <!-- 主要指标 -->
    <div class="main-metric">
      <div class="metric-highlight">
        <span class="metric-value">{{ predictionData.hardness }}</span>
        <span class="metric-unit">GPa</span>
      </div>
      <span class="metric-label">预测硬度</span>
    </div>
    
    <!-- 其他指标 - 横向排列 -->
    <div class="metrics-row">
      <div class="metric-item">
        <span class="label">弹性模量</span>
        <span class="value">{{ predictionData.elastic_modulus }} <small>GPa</small></span>
      </div>
      <div class="metric-item">
        <span class="label">结合力</span>
        <span class="value">{{ predictionData.adhesion_strength }} <small>N</small></span>
      </div>
      <div class="metric-item">
        <span class="label">磨损率</span>
        <span class="value">{{ predictionData.wear_rate }} <small>mm³/Nm</small></span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 性能预测卡片
 * 
 * 展示 ML 模型的性能预测结果，包含硬度、弹性模量、磨损率、结合力等指标
 */
import { computed } from 'vue'

const props = defineProps({
  // 预测数据对象
  prediction: {
    type: [Object, String],
    default: null
  },
  // 是否显示头部（兼容旧接口，现由 ResultsPanel 控制）
  showHeader: {
    type: Boolean,
    default: true
  }
})

// 获取预测数据
const predictionData = computed(() => {
  const pred = props.prediction
  // 检查是否为对象类型
  if (!pred || typeof pred !== 'object') {
    return {
      hardness: 'N/A',
      elastic_modulus: 'N/A',
      wear_rate: 'N/A',
      adhesion_strength: 'N/A'
    }
  }
  
  return {
    hardness: pred.hardness ?? 'N/A',
    elastic_modulus: pred.elastic_modulus ?? 'N/A',
    wear_rate: pred.wear_rate ?? 'N/A',
    adhesion_strength: pred.adhesion_strength ?? 'N/A'
  }
})

</script>

<style scoped>
.performance-prediction-card {
  padding: 16px;
}

/* 主要指标 - 突出显示 */
.main-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(37, 99, 235, 0.04) 100%);
  border-radius: 12px;
  border: 1px solid rgba(59, 130, 246, 0.15);
}

.metric-highlight {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-highlight .metric-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary, #2563eb);
}

.metric-highlight .metric-unit {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
}

.main-metric .metric-label {
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
  margin-top: 4px;
}

/* 指标横向排列 */
.metrics-row {
  display: flex;
  gap: 8px;
}

.metric-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  background: var(--bg-secondary, #f9fafb);
  border-radius: 8px;
  text-align: center;
}

.metric-item .label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-tertiary, #9ca3af);
}

.metric-item .value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.metric-item .value small {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-tertiary, #9ca3af);
  margin-left: 2px;
}
</style>
