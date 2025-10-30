<template>
  <el-card class="prediction-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>🔮 性能预测结果</span>
      </div>
    </template>

    <div v-if="prediction">
      <!-- 核心指标卡片 -->
      <el-row :gutter="20" class="metrics-row">
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon hardness">💎</div>
            <div class="metric-value">{{ prediction.hardness || 'N/A' }} GPa</div>
            <div class="metric-label">硬度</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon adhesion">🔗</div>
            <div class="metric-value">{{ prediction.adhesion_level || 'N/A' }}</div>
            <div class="metric-label">结合力等级</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon temperature">🔥</div>
            <div class="metric-value">{{ prediction.oxidation_temperature || 'N/A' }}℃</div>
            <div class="metric-label">抗氧化温度</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon confidence">📊</div>
            <div class="metric-value">{{ (prediction.confidence_score * 100).toFixed(1) }}%</div>
            <div class="metric-label">预测置信度</div>
          </div>
        </el-col>
      </el-row>

      <!-- 沉积结构预测 -->
      <el-divider content-position="left">微观结构预测</el-divider>
      <div v-if="prediction.deposition_structure" class="structure-info">
        <el-descriptions :column="3" border>
          <el-descriptions-item
            v-for="(value, key) in prediction.deposition_structure"
            :key="key"
            :label="formatLabel(key)"
          >
            {{ value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 根因分析 -->
      <el-divider content-position="left">🔍 根因分析</el-divider>
      <el-alert
        v-if="analysis"
        :title="analysis"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="analysis-content" v-html="formatAnalysis(analysis)"></div>
        </template>
      </el-alert>

      <!-- LLM分析详情 -->
      <el-collapse v-if="prediction.analysis" class="analysis-collapse">
        <el-collapse-item title="🤖 AI详细分析" name="1">
          <div class="llm-analysis">{{ prediction.analysis }}</div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-empty v-else description="等待预测结果..." />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  prediction: {
    type: Object,
    default: null
  },
  analysis: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// 格式化标签
const formatLabel = (key) => {
  const labelMap = {
    grain_size: '晶粒尺寸',
    preferred_orientation: '择优取向',
    residual_stress: '残余应力',
    phase_composition: '相组成'
  }
  return labelMap[key] || key
}

// 格式化分析文本
const formatAnalysis = (text) => {
  if (!text) return ''
  
  // 将换行转换为<br>
  return text
    .split('\n')
    .map(line => {
      // 如果是数字开头的行，加粗
      if (/^\d+\./.test(line.trim())) {
        return `<strong>${line}</strong>`
      }
      return line
    })
    .join('<br>')
}
</script>

<style scoped>
.prediction-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.metrics-row {
  margin-bottom: 30px;
}

.metric-card {
  text-align: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  transition: all 0.3s;
  cursor: pointer;
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #4CAF50;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 14px;
  color: #666;
}

.structure-info {
  margin: 20px 0;
}

.analysis-content {
  line-height: 1.8;
  font-size: 14px;
}

.analysis-collapse {
  margin-top: 20px;
}

.llm-analysis {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}
</style>
