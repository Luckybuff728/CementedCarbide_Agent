<template>
  <SummaryCard 
    icon=""
    :icon-component="FlaskOutline"
    title="TopPhi相场模拟"
    :clickable="false"
  >
    <div class="topphi-content">
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

// API基础URL
const apiBaseUrl = ref(API_BASE_URL)

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

.vtk-visualization {
  width: 100%;
  border-radius: var(--radius-md);
  overflow: hidden;
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
