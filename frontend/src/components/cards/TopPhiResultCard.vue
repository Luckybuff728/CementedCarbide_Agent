<template>
  <SummaryCard 
    icon=""
    :icon-component="FlaskOutline"
    title="TopPhi相场模拟"
    :badge="topphiBadge"
    :clickable="true"
    @click="emit('jump-to-node', 'topphi_simulation')"
  >
    <div class="topphi-content">
      <div v-if="topphiView" class="topphi-summary">
        <div class="summary-main">
          <div class="metric-label">预测晶粒尺寸</div>
          <div class="metric-value highlight">{{ topphiView.grainSizeText }}</div>
          <div v-if="topphiView.simulationTimeText" class="metric-sub">计算时长约 {{ topphiView.simulationTimeText }}</div>
        </div>
        <div class="summary-metrics">
          <div class="metric-item">
            <span>择优取向</span>
            <span>{{ topphiView.orientationText }}</span>
          </div>
          <div class="metric-item">
            <span>残余应力</span>
            <span>{{ topphiView.stressText }}</span>
          </div>
          <div class="metric-item">
            <span>形成能</span>
            <span>{{ topphiView.formationEnergyText }}</span>
          </div>
          <div v-if="topphiView.confidencePercent !== null" class="metric-item">
            <span>模型置信度</span>
            <span>{{ topphiView.confidencePercent }}%</span>
          </div>
        </div>
        <div v-if="topphiView.dimensionsText || topphiView.pointCountText || topphiView.fileSizeText" class="summary-meta">
          <span v-if="topphiView.dimensionsText" class="meta-item">网格：{{ topphiView.dimensionsText }}</span>
          <span v-if="topphiView.pointCountText" class="meta-item">点数：{{ topphiView.pointCountText }}</span>
          <span v-if="topphiView.fileSizeText" class="meta-item">文件大小：{{ topphiView.fileSizeText }}</span>
        </div>
      </div>

      <!-- VTK可视化 -->
      <div v-if="vtkData" class="vtk-visualization">
        <!-- 时间序列播放器 -->
        <VtkTimeSeriesViewer
          v-if="isTimeSeries && timeSeriesFiles.length > 0"
          :timeSeriesFiles="timeSeriesFiles"
          :baseUrl="apiBaseUrl"
          height="450px"
        />
        
        <!-- 单帧查看器 -->
        <VtkViewer
          v-else-if="!isTimeSeries"
          :vtkData="vtkData"
          :baseUrl="apiBaseUrl"
          height="450px"
          renderMode="volume"
        />
        
        <!-- 加载时间序列中 -->
        <div v-else-if="isTimeSeries && loadingTimeSeries" class="loading-timeseries">
          <n-icon class="is-loading" :component="ReloadOutline" size="40" />
          <span>加载时间序列数据...</span>
        </div>
      </div>

      <div v-else class="no-vtk">
        <span>暂无可视化数据，请先完成 TopPhi 模拟。</span>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { NIcon } from 'naive-ui'
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
    simulationTimeText: result.simulation_time != null ? `${result.simulation_time} s` : null,
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
    : { text: '单帧结果', type: 'success' }
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
  gap: 12px;
}

.topphi-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
}

.summary-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-main .metric-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-main .metric-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary);
}

.summary-main .metric-sub {
  font-size: 12px;
  color: var(--text-tertiary);
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.summary-metrics .metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.summary-metrics .metric-item span:first-child {
  color: var(--text-secondary);
}

.summary-metrics .metric-item span:last-child {
  font-weight: 600;
}

.summary-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.summary-meta .meta-item {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
}

.vtk-visualization {
  width: 100%;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.no-vtk {
  padding: 32px 16px;
  text-align: center;
  font-size: 13px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.loading-timeseries {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
}

.loading-timeseries .n-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
