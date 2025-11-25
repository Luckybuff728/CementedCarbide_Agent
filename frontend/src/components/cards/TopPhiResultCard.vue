<template>
  <div class="topphi-result-card">
    <!-- 核心指标网格 -->
    <div class="metrics-grid">
      <!-- 主指标：晶粒尺寸 -->
      <div class="metric-card primary">
        <span class="metric-label">晶粒尺寸</span>
        <div class="metric-main">
          <span class="metric-value">{{ formatNumber(result.data?.grain_size_nm) }}</span>
          <span class="metric-unit">nm</span>
        </div>
      </div>
      <!-- 次要指标 -->
      <div class="metric-card">
        <span class="metric-label">择优取向</span>
        <span class="metric-value small">{{ result.data?.preferred_orientation || '-' }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">残余应力</span>
        <div class="metric-main">
          <span class="metric-value small">{{ formatNumber(result.data?.residual_stress_gpa) }}</span>
          <span class="metric-unit">GPa</span>
        </div>
      </div>
      <div class="metric-card">
        <span class="metric-label">形成能</span>
        <div class="metric-main">
          <span class="metric-value small">{{ formatNumber(result.data?.formation_energy) }}</span>
          <span class="metric-unit">eV</span>
        </div>
      </div>
      <div class="metric-card">
        <span class="metric-label">置信度</span>
        <span class="metric-value small success">{{ formatConfidence(result.data?.confidence) }}%</span>
      </div>
    </div>

    <!-- 3D 视图区域 -->
    <div class="viewer-section">
      <!-- 加载状态 -->
      <div v-if="loadingTimeSeries" class="loading-state">
        <el-icon class="is-loading" :size="28"><Loading /></el-icon>
        <span>正在加载模拟数据...</span>
      </div>
      <!-- VTK 时间序列播放器 -->
      <VtkTimeSeriesViewer
        v-else-if="vtkFiles.length > 0"
        :time-series-files="vtkFiles"
        height="380px"
        :auto-play="true"
        :immersive="true"
      />
      <!-- 无数据状态 -->
      <div v-else class="empty-state">
        <el-empty description="暂无模拟数据" :image-size="80" />
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElIcon, ElEmpty } from 'element-plus'
import { ReloadOutline as Loading } from '@vicons/ionicons5'
import VtkTimeSeriesViewer from '../viz/VtkTimeSeriesViewer.vue'
import { API_BASE_URL } from '../../config'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

// 时间序列文件列表状态
const timeSeriesFiles = ref([])
const loadingTimeSeries = ref(false)

// 格式化数字
const formatNumber = (num) => {
  if (num === undefined || num === null) return '-'
  return Number(num).toFixed(2)
}

// 格式化置信度（处理 undefined 情况）
const formatConfidence = (confidence) => {
  if (confidence === undefined || confidence === null) return '-'
  return (confidence * 100).toFixed(0)
}

// 获取 VTK 数据
const vtkData = computed(() => props.result?.data?.vtk_data)

// 是否为时间序列类型
const isTimeSeries = computed(() => vtkData.value?.type === 'timeseries')

// 监听时间序列数据变化，自动从后端获取文件列表
watch(
  () => [isTimeSeries.value, vtkData.value?.folder],
  async ([isTS, folder]) => {
    // 如果不是时间序列，清空数据
    if (!isTS) {
      timeSeriesFiles.value = []
      return
    }
    // 如果是时间序列且有文件夹，加载文件列表
    if (isTS && folder) {
      loadingTimeSeries.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/vtk/timeseries/${folder}`)
        if (response.ok) {
          const data = await response.json()
          timeSeriesFiles.value = data.files || []
          console.log('[TopPhiResultCard] 加载时间序列文件:', timeSeriesFiles.value.length, '个')
        }
      } catch (err) {
        console.error('[TopPhiResultCard] 获取时间序列列表出错:', err)
        timeSeriesFiles.value = []
      } finally {
        loadingTimeSeries.value = false
      }
    }
  },
  { immediate: true }
)

// VTK文件列表（用于非时间序列类型）
const vtkFiles = computed(() => {
  // 时间序列类型使用 timeSeriesFiles ref
  if (isTimeSeries.value) {
    return timeSeriesFiles.value
  }
  // 如果有直接的 vtk_files 列表
  if (props.result?.data?.vtk_files) {
    return props.result.data.vtk_files.map((file, index) => ({
      name: file,
      timeStep: index,
      size: props.result.data?.file_sizes?.[index] || 0
    }))
  }
  return []
})
</script>

<style scoped>
/* ===============================
   TopPhi相场模拟卡片 - 现代简洁风格
   =============================== */
.topphi-result-card {
  background: #ffffff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 指标网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #f0f0f0;
  padding: 1px;
}

.metric-card {
  background: #fff;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-card.primary {
  grid-column: span 2;
  background: #fafafa;
  padding: 14px;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.metric-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.1;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.metric-value.small {
  font-size: 16px;
  font-weight: 600;
}

.metric-value.success {
  color: #1f2937;
}

.metric-unit {
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
}

.metric-card.primary .metric-value {
  font-size: 28px;
  color: #1f2937;
}

.metric-card.primary .metric-unit {
  font-size: 14px;
  color: #6b7280;
}

/* 3D 视图区域 */
.viewer-section {
  background: #0a0a0a;
  position: relative;
  min-height: 320px;
  /* 确保内容不被裁切 */
  overflow: visible;
}

.empty-state {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.loading-state {
  height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #0a0a0a;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.loading-state .is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

</style>
