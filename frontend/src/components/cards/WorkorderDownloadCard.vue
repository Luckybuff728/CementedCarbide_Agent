<template>
  <div class="workorder-download-card">
    <!-- 工单基本信息 -->
    <div class="workorder-info">
      <div class="info-row">
        <span class="label">工单编号：</span>
        <span class="value workorder-id">{{ workorderId }}</span>
      </div>
      <div class="info-row">
        <span class="label">生成时间：</span>
        <span class="value">{{ generatedTime }}</span>
      </div>
      <div class="info-row" v-if="optimizationType">
        <span class="label">优化方案：</span>
        <el-tag size="small" :type="getOptTypeColor(optimizationType)">
          {{ optimizationType }}
        </el-tag>
      </div>
    </div>
    
    <!-- 方案名称（突出显示） -->
    <div class="plan-name-box" v-if="planName">
      <div class="plan-name-label">方案名称</div>
      <div class="plan-name-text">{{ planName }}</div>
    </div>
    
    <!-- 实验目的 -->
    <div class="purpose-box" v-if="purpose">
      <div class="purpose-label">实验目的</div>
      <div class="purpose-text">{{ purpose }}</div>
    </div>
    
    <!-- 关键参数预览 -->
    <div class="params-preview" v-if="hasParams">
      <div class="preview-title">关键参数预览</div>
      <div class="params-grid">
        <!-- 成分 -->
        <div class="param-group" v-if="composition">
          <div class="group-title">成分配比</div>
          <div class="param-item" v-for="(val, key) in composition" :key="key">
            <span class="param-key">{{ key }}：</span>
            <span class="param-val">{{ val }}%</span>
          </div>
        </div>
        <!-- 工艺 -->
        <div class="param-group" v-if="processParams">
          <div class="group-title">工艺参数</div>
          <div class="param-item" v-if="processParams.temperature">
            <span class="param-key">温度：</span>
            <span class="param-val">{{ processParams.temperature }}°C</span>
          </div>
          <div class="param-item" v-if="processParams.bias_voltage">
            <span class="param-key">偏压：</span>
            <span class="param-val">-{{ processParams.bias_voltage }}V</span>
          </div>
        </div>
        <!-- 预期 -->
        <div class="param-group" v-if="expectedResults">
          <div class="group-title">预期结果</div>
          <div class="param-item" v-if="expectedResults.hardness">
            <span class="param-key">硬度：</span>
            <span class="param-val">{{ expectedResults.hardness }} GPa</span>
          </div>
          <div class="param-item" v-if="expectedResults.adhesion">
            <span class="param-key">结合力：</span>
            <span class="param-val">{{ expectedResults.adhesion }} N</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 下载按钮 -->
    <div class="download-section">
      <el-button type="primary" @click="downloadPDF" :loading="isExporting">
        <el-icon><DownloadOutline /></el-icon>
        下载工单 (PDF)
      </el-button>
      <el-button @click="copyToClipboard">
        <el-icon><CopyOutline /></el-icon>
        复制内容
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElButton, ElTag, ElMessage, ElIcon } from 'element-plus'
import { DownloadOutline, CopyOutline } from '@vicons/ionicons5'
import { generateWorkorderPDF } from '@/utils/pdfExporter'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

// 状态
const isExporting = ref(false)

// 计算属性
const workorderId = computed(() => props.data?.workorder_id || 'WO-未知')
const generatedTime = computed(() => props.data?.generated_time || '')
const optimizationType = computed(() => props.data?.optimization_type || '')
const planName = computed(() => props.data?.plan_name || '')
const purpose = computed(() => props.data?.purpose || '')
const composition = computed(() => props.data?.composition || null)
const processParams = computed(() => props.data?.process_params || null)
const expectedResults = computed(() => props.data?.expected_results || null)
const fullContent = computed(() => props.data?.full_content || '')

const hasParams = computed(() => {
  return composition.value || processParams.value || expectedResults.value
})

// 获取优化类型颜色
const getOptTypeColor = (type) => {
  const colors = {
    'P1': 'primary',
    'P2': 'success',
    'P3': 'warning'
  }
  return colors[type] || 'info'
}

// 下载 PDF
const downloadPDF = async () => {
  if (!fullContent.value) {
    ElMessage.warning('工单内容为空')
    return
  }
  
  isExporting.value = true
  
  try {
    // 使用 generateWorkorderPDF 生成 PDF
    // 函数签名: generateWorkorderPDF(markdownContent, workorderNumber, solutionName)
    await generateWorkorderPDF(
      fullContent.value,
      workorderId.value,
      planName.value || `${optimizationType.value} 优化方案`
    )
    
    ElMessage.success('PDF 工单已下载')
  } catch (err) {
    console.error('PDF 导出失败:', err)
    ElMessage.error('PDF 导出失败: ' + err.message)
  } finally {
    isExporting.value = false
  }
}

// 复制到剪贴板
const copyToClipboard = async () => {
  if (!fullContent.value) {
    ElMessage.warning('工单内容为空')
    return
  }
  
  try {
    await navigator.clipboard.writeText(fullContent.value)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.workorder-download-card {
  padding: 12px;
}

.workorder-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  font-size: 13px;
}

.info-row .label {
  color: #5f6368;
  min-width: 80px;
}

.info-row .value {
  color: #202124;
  font-weight: 500;
}

.info-row .value.workorder-id {
  font-family: 'Consolas', monospace;
  color: #1a73e8;
}

/* 方案名称框 */
.plan-name-box {
  background: linear-gradient(135deg, #e8f0fe 0%, #f1f8ff 100%);
  border: 1px solid #c2d7f2;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.plan-name-label {
  font-size: 11px;
  color: #5f6368;
  margin-bottom: 4px;
}

.plan-name-text {
  font-size: 14px;
  font-weight: 600;
  color: #1a73e8;
  line-height: 1.4;
}

/* 实验目的框 */
.purpose-box {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.purpose-label {
  font-size: 11px;
  color: #80868b;
  margin-bottom: 4px;
}

.purpose-text {
  font-size: 13px;
  color: #202124;
  line-height: 1.5;
}

.params-preview {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #5f6368;
  margin-bottom: 10px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.param-group {
  background: white;
  border-radius: 6px;
  padding: 10px;
  border: 1px solid #e0e0e0;
}

.group-title {
  font-size: 11px;
  color: #80868b;
  margin-bottom: 6px;
}

.param-item {
  font-size: 12px;
  margin-bottom: 4px;
}

.param-key {
  color: #5f6368;
}

.param-val {
  color: #202124;
  font-weight: 500;
}

.download-section {
  display: flex;
  gap: 10px;
}

/* 响应式 */
@media (max-width: 500px) {
  .params-grid {
    grid-template-columns: 1fr;
  }
  
  .download-section {
    flex-direction: column;
  }
}
</style>
