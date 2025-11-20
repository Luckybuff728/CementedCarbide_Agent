<template>
  <SummaryCard 

    :icon-component="FlaskOutline"
    title="TopPhi相场模拟"
    :badge="topphiBadge"
    :clickable="true"
    @click="emit('jump-to-node', 'topphi_simulation')"
  >
    <div class="topphi-content">
      <div v-if="topphiView" class="metrics-container">
        <!-- 主要指标：晶粒尺寸 -->
        <div class="metric-primary">
          <div class="label">预测晶粒尺寸</div>
          <div class="value">{{ topphiView.grainSizeText }}</div>
        </div>

        <!-- 次要指标网格 -->
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="label">择优取向</span>
            <span class="value">{{ topphiView.orientationText }}</span>
          </div>
          <div class="metric-item">
            <span class="label">残余应力</span>
            <span class="value">{{ topphiView.stressText }}</span>
          </div>
          <div class="metric-item">
            <span class="label">形成能</span>
            <span class="value">{{ topphiView.formationEnergyText }}</span>
          </div>
          <div v-if="topphiView.confidencePercent !== null" class="metric-item">
            <span class="label">置信度</span>
            <span class="value">{{ topphiView.confidencePercent }}%</span>
          </div>
        </div>

        <!-- 底部元信息 -->
        <div class="meta-info">
          <span v-if="topphiView.simulationTimeText">耗时 {{ topphiView.simulationTimeText }}</span>
          <span v-if="topphiView.dimensionsText" class="divider">|</span>
          <span v-if="topphiView.dimensionsText">网格 {{ topphiView.dimensionsText }}</span>
          <span v-if="topphiView.pointCountText" class="divider">|</span>
          <span v-if="topphiView.pointCountText">{{ topphiView.pointCountText }} 点</span>
        </div>
      </div>

      <!-- VTK可视化 -->
      <div v-if="vtkData" class="vtk-visualization">
        <!-- 时间序列播放器 -->
        <VtkTimeSeriesViewer
          v-if="isTimeSeries && timeSeriesFiles.length > 0"
          :timeSeriesFiles="timeSeriesFiles"
          :baseUrl="apiBaseUrl"
          height="380px"
        />
        
        <!-- 单帧查看器 -->
        <VtkViewer
          v-else-if="!isTimeSeries"
          :vtkData="vtkData"
          :baseUrl="apiBaseUrl"
          height="380px"
          renderMode="volume"
        />
        
        <!-- 加载时间序列中 -->
        <div v-else-if="isTimeSeries && loadingTimeSeries" class="loading-timeseries">
          <el-icon class="is-loading" size="32"><ReloadOutline /></el-icon>
          <span>加载数据...</span>
        </div>
      </div>

      <div v-else class="no-vtk">
        <span>暂无可视化数据</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElIcon } from 'element-plus'
import { FlaskOutline, ReloadOutline } from '@vicons/ionicons5'
import { API_BASE_URL } from '../../config'
import SummaryCard from '../common/SummaryCard.vue'
import VtkTimeSeriesViewer from '../viz/VtkTimeSeriesViewer.vue'
import VtkViewer from '../viz/VtkViewer.vue'

// 定义props
const props = defineProps({
  topphiResult: {
    type: [Object, String],  // 支持Object和String类型
    default: null
  }
})

const emit = defineEmits(['jump-to-node'])

// API基础URL
const apiBaseUrl = ref(API_BASE_URL)

// TopPhi显示数据
const topphiView = computed(() => {
  const result = props.topphiResult
  if (!result || typeof result !== 'object') {
    return null
  }

  const vtk = result.vtk_data || {}
  const rawDimensions = vtk.dimensions || (vtk.metadata && vtk.metadata.dimensions) || null
  const hasDims = Array.isArray(rawDimensions) && rawDimensions.length === 3

  return {
    grainSizeText: result.grain_size_nm != null ? `${result.grain_size_nm} nm` : 'N/A',
    orientationText: result.preferred_orientation || 'N/A',
    stressText: result.residual_stress_gpa != null ? `${result.residual_stress_gpa} GPa` : 'N/A',
    formationEnergyText: result.formation_energy != null ? `${result.formation_energy} eV` : 'N/A',
    confidencePercent: typeof result.confidence === 'number' ? Math.round(result.confidence * 100) : null,
    simulationTimeText: result.simulation_time != null ? `${result.simulation_time}s` : null,
    dimensionsText: hasDims ? `${rawDimensions[0]}×${rawDimensions[1]}×${rawDimensions[2]}` : null,
    pointCountText: vtk.point_count != null ? String(vtk.point_count) : null,
    fileSizeText: vtk.file_size_mb != null ? `${vtk.file_size_mb} MB` : null,
    isTimeSeries: vtk.type === 'timeseries'
  }
})

// 卡片徽章
const topphiBadge = computed(() => {
  if (!topphiView.value) return null
  return topphiView.value.isTimeSeries
    ? { text: '时间序列', type: 'info' }
    : { text: '单帧', type: 'success' }
})

// 时间序列文件列表
const timeSeriesFiles = ref([])
const loadingTimeSeries = ref(false)

// 获取VTK数据
const vtkData = computed(() => {
  if (!props.topphiResult || !props.topphiResult.vtk_data) return null
  return props.topphiResult.vtk_data
})

// 判断是否为时间序列
const isTimeSeries = computed(() => {
  return vtkData.value?.type === 'timeseries'
})

// 监听时间序列数据变化，自动获取文件列表
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
        const response = await fetch(`${apiBaseUrl.value}/api/vtk/timeseries/${folder}`)
        if (response.ok) {
          const data = await response.json()
          timeSeriesFiles.value = data.files
        }
      } catch (err) {
        console.error('[TopPhiResultCard] 获取时间序列列表出错:', err)
      } finally {
        loadingTimeSeries.value = false
      }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.topphi-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metrics-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-primary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.metric-primary .label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-primary .value {
  font-size: var(--font-3xl);
  font-weight: 700;
  color: var(--primary);
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-item .label {
  font-size: var(--font-sm);
  color: var(--text-tertiary);
  font-weight: 500;
}

.metric-item .value {
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.meta-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  font-size: var(--font-sm);
  color: var(--text-tertiary);
  font-weight: 500;
}

.meta-info .divider {
  color: var(--border-color);
  font-weight: 400;
}

.vtk-visualization {
  width: 100%;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-light);
  background: #000; /* VTK背景通常较深 */
}

.no-vtk {
  padding: 24px;
  text-align: center;
  font-size: var(--font-sm);
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.loading-timeseries {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px;
  color: rgba(255, 255, 255, 0.9);
}

.loading-timeseries .el-icon {
  animation: spin 1s linear infinite;
  font-size: 36px;
}

.loading-timeseries span {
  font-size: 15px;
  font-weight: 500;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
