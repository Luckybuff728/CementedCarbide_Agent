<template>
  <SummaryCard 

    :icon-component="DocumentTextOutline"
    :title="solutionName"
    :badge="{ text: '工单已生成', type: 'success' }"
    :clickable="true"
    @click="emit('jump-to-node', 'experiment_workorder')"
  >
    <div class="workorder-summary">
      <!-- 工单基本信息 -->
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">工单编号</span>
          <span class="info-value">{{ workorderNumber }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">实验目标</span>
          <span class="info-value">{{ experimentGoal }}</span>
        </div>
      </div>

      <!-- 优化方案 -->
      <div v-if="selectedOptimization" class="optimization-info">
        <div class="opt-label">
          <el-icon><BulbOutline /></el-icon>
          <span>优化方案</span>
        </div>
        <div :class="['opt-badge', optBadgeClass]">
          <span class="opt-tag">{{ selectedOptimization }}</span>
          <span class="opt-name">{{ optimizationName }}</span>
        </div>
      </div>

      <!-- 关键参数预览 -->
      <div v-if="keyParameters.length > 0" class="parameters-preview">
        <div class="preview-label">关键参数</div>
        <div class="parameters-list">
          <div 
            v-for="(param, index) in keyParameters" 
            :key="index"
            class="param-item"
          >
            <span class="param-name">{{ param.name }}</span>
            <span class="param-value">{{ param.value }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="workorder-actions">
        <el-button 
          type="primary" 
          size="default" 
          @click.stop="handleDownload"
          style="width: 100%"
        >
          <el-icon class="el-icon--left"><DownloadOutline /></el-icon>
          下载完整工单
        </el-button>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { computed } from 'vue'
import { ElButton, ElIcon } from 'element-plus'
import {
  DocumentTextOutline,
  BulbOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../common/SummaryCard.vue'

// 定义props和emits
const props = defineProps({
  workorder: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  },
  selectedOptimization: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['jump-to-node', 'download'])

// 判断是否有内容（简化：只检查对象类型）
const hasContent = computed(() => {
  return props.workorder && typeof props.workorder === 'object'
})

// 直接访问数据字段（简化：不做复杂处理）
const solutionName = computed(() => {
  if (!hasContent.value) return '实验工单'
  return props.workorder.solution_name || '实验工单'
})

const workorderNumber = computed(() => {
  if (!hasContent.value) return 'N/A'
  const id = props.workorder.workorder_id || props.workorder.experiment_id || ''
  return id ? id.toUpperCase() : 'N/A'
})

const experimentGoal = computed(() => {
  if (!hasContent.value) return 'N/A'
  return props.workorder.experiment_goal || 'N/A'
})

const keyParameters = computed(() => {
  if (!hasContent.value) return []
  return props.workorder.key_parameters || []
})

// 优化方案显示（简化）
const optimizationName = computed(() => {
  const map = {
    'P1': '成分优化',
    'P2': '结构优化',
    'P3': '工艺优化'
  }
  return map[props.selectedOptimization] || ''
})

const optBadgeClass = computed(() => {
  const map = {
    'P1': 'opt-p1',
    'P2': 'opt-p2',
    'P3': 'opt-p3'
  }
  return map[props.selectedOptimization] || 'opt-p1'
})

// 处理下载
const handleDownload = () => {
  emit('download')
}
</script>

<style scoped>
.workorder-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.info-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.optimization-info {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.opt-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.opt-label .el-icon {
  font-size: 14px;
}

.opt-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
}

.opt-badge.opt-p1 {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid var(--success);
}

.opt-badge.opt-p2 {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1px solid var(--primary);
}

.opt-badge.opt-p3 {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
  border: 1px solid var(--warning);
}

.opt-tag {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 700;
  color: white;
  background: var(--success);
}

.opt-badge.opt-p2 .opt-tag {
  background: var(--primary);
}

.opt-badge.opt-p3 .opt-tag {
  background: var(--warning);
}

.opt-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.parameters-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.parameters-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: 12px;
}

.param-name {
  color: var(--text-secondary);
}

.param-value {
  color: var(--text-primary);
  font-weight: 600;
}

.workorder-actions {
  margin-top: 4px;
}
</style>
