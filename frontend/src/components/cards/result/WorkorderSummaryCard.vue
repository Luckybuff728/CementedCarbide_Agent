<template>
  <SummaryCard 
    :icon-component="DocumentTextOutline"
    :title="solutionName"
    :badge="{ text: '工单已生成', type: 'success' }"
    :clickable="true"
    :show-header="showHeader"
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
import { ElButton, ElIcon, ElMessage } from 'element-plus'
import {
  DocumentTextOutline,
  BulbOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import SummaryCard from '../../common/SummaryCard.vue'
import { generateWorkorderPDF } from '../../../utils/pdfExporter'

// 定义props和emits
const props = defineProps({
  workorder: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  },
  selectedOptimization: {
    type: String,
    default: ''
  },
  showHeader: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['jump-to-node'])

// 判断是否有内容（简化：只检查对象类型）
const hasContent = computed(() => {
  const result = props.workorder && typeof props.workorder === 'object'
  console.log('[WorkorderCard] hasContent:', result, 'workorder:', props.workorder)
  return result
})

// 直接访问数据字段（简化：不做复杂处理）
const solutionName = computed(() => {
  if (!hasContent.value) return '实验工单'
  const name = props.workorder.solution_name || '实验工单'
  console.log('[WorkorderCard] solutionName:', name)
  return name
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

// 优化方案名称
const selectedOptimization = computed(() => {
  if (!hasContent.value) return ''
  return props.workorder.selected_optimization || ''
})

// 处理下载 - 生成PDF格式
const handleDownload = async () => {
  try {
    const data = props.workorder
    const content = data.content || ''
    const workorderId = data.workorder_id || data.experiment_id || 'workorder'
    const solutionNameValue = solutionName.value || '实验工单'
    
    if (!content) {
      ElMessage.error('工单内容为空，无法下载')
      return
    }
    
    // 显示生成中提示
    ElMessage.info('正在生成PDF，请稍候...')
    
    // 使用PDF导出器生成PDF
    const fileName = await generateWorkorderPDF(
      content,
      workorderId,
      solutionNameValue
    )
    
    ElMessage.success(`工单已下载: ${fileName}`)
    console.log('[下载工单] PDF生成成功:', fileName)
  } catch (error) {
    console.error('[下载工单] PDF生成失败:', error)
    ElMessage.error('PDF生成失败，请重试')
  }
}

/**
 * 生成工单HTML内容
 */
const generateWorkorderHTML = (data, content) => {
  const workorderId = data.workorder_id || data.experiment_id || 'N/A'
  const solutionNameValue = data.solution_name || '实验工单'
  const experimentGoalValue = data.experiment_goal || ''
  const selectedOptimizationValue = data.selected_optimization || ''
  const optimizationNameValue = data.optimization_name || ''
  const keyParametersValue = data.key_parameters || []
  
  // 转换Markdown为HTML（简单处理）
  const htmlContent = content
    .replace(/\n/g, '<br>')
    .replace(/## (.*?)<br>/g, '<h2>$1</h2>')
    .replace(/### (.*?)<br>/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/- (.*?)<br>/g, '<li>$1</li>')
  
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${solutionNameValue} - ${workorderId}</title>
  <style>
    body {
      font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
      line-height: 1.8;
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 20px;
      color: #333;
      background: #fff;
    }
    .header {
      text-align: center;
      padding: 30px 0;
      border-bottom: 3px solid #2d2d2d;
      margin-bottom: 30px;
    }
    .header h1 {
      margin: 0 0 10px 0;
      font-size: 28px;
      color: #0d0d0d;
    }
    .header .workorder-id {
      font-size: 14px;
      color: #6b7280;
      font-weight: 500;
    }
    .meta-info {
      background: #f9fafb;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 30px;
    }
    .meta-info .row {
      display: flex;
      padding: 10px 0;
      border-bottom: 1px solid #e5e7eb;
    }
    .meta-info .row:last-child {
      border-bottom: none;
    }
    .meta-info .label {
      font-weight: 600;
      color: #4b5563;
      min-width: 120px;
    }
    .meta-info .value {
      color: #0d0d0d;
      flex: 1;
    }
    .content {
      padding: 20px 0;
    }
    h2 {
      font-size: 20px;
      color: #0d0d0d;
      margin: 30px 0 15px 0;
      padding-bottom: 10px;
      border-bottom: 2px solid #e5e7eb;
    }
    h3 {
      font-size: 16px;
      color: #374151;
      margin: 20px 0 10px 0;
    }
    ul, ol {
      padding-left: 25px;
    }
    li {
      margin: 8px 0;
      list-style-position: outside;
    }
    strong {
      color: #0d0d0d;
      font-weight: 600;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }
    table th, table td {
      padding: 12px;
      text-align: left;
      border: 1px solid #e5e7eb;
    }
    table th {
      background: #f9fafb;
      font-weight: 600;
      color: #374151;
    }
    .footer {
      margin-top: 50px;
      padding-top: 20px;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      color: #9ca3af;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>${solutionNameValue}</h1>
    <div class="workorder-id">工单编号: ${workorderId}</div>
  </div>
  
  <div class="meta-info">
    ${experimentGoalValue ? `
    <div class="row">
      <div class="label">实验目标:</div>
      <div class="value">${experimentGoalValue}</div>
    </div>
    ` : ''}
    ${selectedOptimizationValue ? `
    <div class="row">
      <div class="label">优化方案:</div>
      <div class="value">${selectedOptimizationValue} - ${optimizationNameValue}</div>
    </div>
    ` : ''}
    ${keyParametersValue.length > 0 ? `
    <div class="row">
      <div class="label">关键参数:</div>
      <div class="value">
        ${keyParametersValue.map(p => `${p.name}: ${p.value}`).join(' | ')}
      </div>
    </div>
    ` : ''}
  </div>
  
  <div class="content">
    ${htmlContent}
  </div>
  
  <div class="footer">
    TopMat Agent 硬质合金涂层优化专家系统<br>
    生成时间: ${new Date().toLocaleString('zh-CN')}
  </div>
</body>
</html>
  `.trim()
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
