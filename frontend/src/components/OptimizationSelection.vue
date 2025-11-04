<template>
  <el-card class="selection-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span style="display: flex; align-items: center; gap: 8px;">
          <el-icon color="#409EFF"><Select /></el-icon>
          <span style="font-size: 16px; font-weight: 600;">请选择优化方案</span>
        </span>
        <el-tag v-if="selectedOption" type="success" size="small">
          已选择: {{ selectedOption }}
        </el-tag>
      </div>
    </template>

    <!-- 综合建议 -->
    <el-alert 
      v-if="comprehensiveRecommendation" 
      type="info" 
      :closable="false"
      class="recommendation-alert"
    >
      <template #title>
        <div style="font-weight: 600; margin-bottom: 8px;">💡 AI综合建议</div>
      </template>
      <div class="recommendation-text">{{ comprehensiveRecommendation }}</div>
    </el-alert>

    <!-- 三个方案选项卡片 -->
    <div class="options-container">
      <!-- P1 成分优化 -->
      <div 
        class="option-card" 
        :class="{ selected: selectedOption === 'P1' }"
        @click="selectOption('P1')"
      >
        <div class="option-header">
          <span class="option-icon">🧪</span>
          <span class="option-title">P1 成分优化</span>
          <el-icon v-if="selectedOption === 'P1'" class="check-icon" color="#67C23A">
            <CircleCheck />
          </el-icon>
        </div>
        <div v-if="p1Content" class="option-preview">
          {{ getPreview(p1Content) }}
        </div>
        <div v-else class="option-preview empty">正在生成方案...</div>
      </div>

      <!-- P2 结构优化 -->
      <div 
        class="option-card" 
        :class="{ selected: selectedOption === 'P2' }"
        @click="selectOption('P2')"
      >
        <div class="option-header">
          <span class="option-icon">🏭️</span>
          <span class="option-title">P2 结构优化</span>
          <el-icon v-if="selectedOption === 'P2'" class="check-icon" color="#67C23A">
            <CircleCheck />
          </el-icon>
        </div>
        <div v-if="p2Content" class="option-preview">
          {{ getPreview(p2Content) }}
        </div>
        <div v-else class="option-preview empty">正在生成方案...</div>
      </div>

      <!-- P3 工艺优化 -->
      <div 
        class="option-card" 
        :class="{ selected: selectedOption === 'P3' }"
        @click="selectOption('P3')"
      >
        <div class="option-header">
          <span class="option-icon">⚙️</span>
          <span class="option-title">P3 工艺优化</span>
          <el-icon v-if="selectedOption === 'P3'" class="check-icon" color="#67C23A">
            <CircleCheck />
          </el-icon>
        </div>
        <div v-if="p3Content" class="option-preview">
          {{ getPreview(p3Content) }}
        </div>
        <div v-else class="option-preview empty">正在生成方案...</div>
      </div>
    </div>

    <!-- 确认按钮 -->
    <div class="action-area">
      <el-button 
        type="success" 
        size="large" 
        :disabled="!selectedOption"
        @click="confirmSelection"
      >
        <el-icon><Check /></el-icon>
        确认选择并生成实验工单
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Select, Check, CircleCheck } from '@element-plus/icons-vue'

const props = defineProps({
  comprehensiveRecommendation: {
    type: String,
    default: ''
  },
  p1Content: {
    type: String,
    default: ''
  },
  p2Content: {
    type: String,
    default: ''
  },
  p3Content: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

const selectedOption = ref('')

// 选择方案
const selectOption = (option) => {
  selectedOption.value = option
}

// 确认选择
const confirmSelection = () => {
  if (!selectedOption.value) {
    ElMessage.warning('请先选择一个优化方案')
    return
  }

  // 直接发送选择的P1/P2/P3
  emit('select', selectedOption.value)
  
  ElMessage.success('已确认选择，正在生成实验工单...')
}

// 获取方案名称作为预览
const getPreview = (content) => {
  if (!content) return '无内容'
  
  // 尝试提取"1. 方案名称"或"**方案名称**"后面的内容
  const lines = content.split('\n').map(line => line.trim()).filter(line => line)
  
  // 查找"方案名称"关键字所在行的下一行
  const nameIndex = lines.findIndex(line => 
    line.includes('方案名称') || line.includes('1.') && line.includes('名称')
  )
  
  if (nameIndex >= 0 && nameIndex < lines.length - 1) {
    // 返回下一行内容（去除markdown符号）
    const nameLine = lines[nameIndex + 1].replace(/[#*`\-]/g, '').trim()
    return nameLine || '优化方案'
  }
  
  // 如果找不到，返回第一行非标题内容
  for (const line of lines) {
    const cleaned = line.replace(/[#*`\-]/g, '').trim()
    if (cleaned && !cleaned.includes('---') && cleaned.length > 5) {
      return cleaned.length > 50 ? cleaned.substring(0, 50) + '...' : cleaned
    }
  }
  
  return '优化方案'
}
</script>

<style scoped>
.selection-card {
  border: 2px solid #409EFF;
  border-radius: 12px;
}

.selection-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #e8f4ff 0%, #d9ecff 100%);
  border-bottom: 2px solid #409EFF;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendation-alert {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #f5f9ff 0%, #ecf5ff 100%);
  border: 1px solid #d4e4ff;
}

.recommendation-text {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.options-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.option-card {
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.option-card:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.option-card.selected {
  border-color: #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #e7f5ff 100%);
  box-shadow: 0 4px 16px rgba(103, 194, 58, 0.3);
}

.option-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.option-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.option-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.check-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.option-preview {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  max-height: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.option-preview.empty {
  color: #909399;
  font-style: italic;
}

.action-area {
  text-align: center;
}

.action-area .el-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
}
</style>
