<template>
  <el-card class="iteration-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>🔄 迭代优化进度</span>
        <el-tag type="success" v-if="iterations.length > 0">
          当前: 第 {{ iterations.length }} 次迭代
        </el-tag>
      </div>
    </template>

    <div v-if="iterations.length > 0">
      <!-- 迭代进度条 -->
      <div class="progress-section">
        <el-progress
          :percentage="(iterations.length / maxIterations) * 100"
          :stroke-width="24"
          :color="progressColor"
        >
          <span class="progress-text">{{ iterations.length }} / {{ maxIterations }}</span>
        </el-progress>
      </div>

      <!-- 迭代历史时间线 -->
      <el-timeline class="iteration-timeline">
        <el-timeline-item
          v-for="(iteration, index) in iterations"
          :key="index"
          :timestamp="formatTimestamp(iteration.timestamp)"
          :type="getIterationType(iteration)"
          size="large"
        >
          <el-card>
            <div class="iteration-header">
              <h4>第 {{ index + 1 }} 次迭代</h4>
              <el-tag :type="iteration.status === 'completed' ? 'success' : 'info'" size="small">
                {{ iteration.status === 'completed' ? '已完成' : '进行中' }}
              </el-tag>
            </div>

            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="优化类型">
                <el-tag size="small">{{ iteration.optimization_type }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="改进措施">
                {{ iteration.action || '工艺参数调整' }}
              </el-descriptions-item>
              <el-descriptions-item label="预期提升">
                <span class="improvement">+{{ iteration.expected_improvement || 0 }}%</span>
              </el-descriptions-item>
              <el-descriptions-item label="实际效果" v-if="iteration.actual_improvement">
                <span class="improvement actual">+{{ iteration.actual_improvement }}%</span>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 实验结果 -->
            <div v-if="iteration.experimental_results" class="experimental-results">
              <el-divider content-position="left">实验验证结果</el-divider>
              <el-row :gutter="16">
                <el-col :span="8">
                  <div class="result-item">
                    <span class="label">硬度:</span>
                    <span class="value">{{ iteration.experimental_results.hardness }} GPa</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="result-item">
                    <span class="label">结合力:</span>
                    <span class="value">{{ iteration.experimental_results.adhesion }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="result-item">
                    <span class="label">SEM质量:</span>
                    <span class="value">{{ iteration.experimental_results.sem_quality }}</span>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <!-- 收敛判断 -->
      <el-alert
        v-if="isConverged"
        title="🎉 优化已收敛！"
        type="success"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>经过 {{ iterations.length }} 次迭代，涂层性能已达到目标要求</p>
          <p><strong>最终性能提升: +{{ totalImprovement.toFixed(1) }}%</strong></p>
        </template>
      </el-alert>

      <el-alert
        v-else-if="iterations.length >= maxIterations"
        title="⚠️ 已达到最大迭代次数"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>已完成 {{ maxIterations }} 次迭代，建议评估当前结果</p>
        </template>
      </el-alert>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button
          v-if="!isConverged && iterations.length < maxIterations"
          type="primary"
          size="large"
          @click="continueIteration"
        >
          <el-icon><RefreshRight /></el-icon>
          继续下一轮迭代
        </el-button>
        <el-button size="large" @click="generateReport">
          <el-icon><Document /></el-icon>
          生成优化报告
        </el-button>
        <el-button size="large" type="success" @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </div>
    </div>

    <el-empty v-else description="等待迭代开始..." />
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight, Document, Download } from '@element-plus/icons-vue'

const props = defineProps({
  iterations: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  maxIterations: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits(['continue', 'report', 'export'])

// 判断是否收敛
const isConverged = computed(() => {
  if (props.iterations.length < 2) return false
  
  const recent = props.iterations.slice(-2)
  return recent.every(iter => 
    iter.actual_improvement && iter.actual_improvement < 0.5
  )
})

// 计算总提升
const totalImprovement = computed(() => {
  return props.iterations.reduce((sum, iter) => {
    return sum + (iter.actual_improvement || 0)
  }, 0)
})

// 进度条颜色
const progressColor = computed(() => {
  const percentage = (props.iterations.length / props.maxIterations) * 100
  if (percentage < 40) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
})

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  if (!timestamp) return new Date().toLocaleString()
  return new Date(timestamp).toLocaleString()
}

// 获取迭代类型
const getIterationType = (iteration) => {
  if (iteration.status === 'completed') return 'success'
  if (iteration.status === 'failed') return 'danger'
  return 'primary'
}

// 继续迭代
const continueIteration = () => {
  emit('continue')
  ElMessage.info('准备下一轮迭代...')
}

// 生成报告
const generateReport = () => {
  emit('report', {
    iterations: props.iterations,
    total_improvement: totalImprovement.value,
    is_converged: isConverged.value
  })
  ElMessage.success('报告生成中...')
}

// 导出数据
const exportData = () => {
  const data = {
    iterations: props.iterations,
    summary: {
      total_iterations: props.iterations.length,
      total_improvement: totalImprovement.value,
      converged: isConverged.value
    }
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `iteration_data_${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('数据已导出')
}
</script>

<style scoped>
.iteration-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.progress-section {
  margin: 30px 0;
  padding: 0 20px;
}

.progress-text {
  font-size: 14px;
  font-weight: bold;
}

.iteration-timeline {
  margin: 30px 0;
}

.iteration-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.iteration-header h4 {
  margin: 0;
  font-size: 16px;
}

.improvement {
  color: #4CAF50;
  font-weight: bold;
}

.improvement.actual {
  color: #2e7d32;
}

.experimental-results {
  margin-top: 15px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.result-item .label {
  color: #666;
  font-size: 14px;
}

.result-item .value {
  color: #333;
  font-weight: bold;
  font-size: 14px;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}
</style>
