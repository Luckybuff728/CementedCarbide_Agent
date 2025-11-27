<template>
  <SummaryCard 
    :icon-component="CubeOutline"
    title="TopPhi相场模拟"
    :badge="getConfidenceBadge()"
    :clickable="true"
    :show-header="false"
    @click="emit('jump-to-node', 'topphi_simulation')"
  >
    <div class="topphi-content">
      <!-- 指标网格 -->
      <div class="metrics-grid">
        <div class="metric-item">
          <span class="label">晶粒尺寸</span>
          <span class="value">{{ formatNumber(result.data?.grain_size_nm) }} <small>nm</small></span>
        </div>
        <div class="metric-item">
          <span class="label">择优取向</span>
          <span class="value">{{ result.data?.preferred_orientation || '-' }}</span>
        </div>
        <div class="metric-item">
          <span class="label">残余应力</span>
          <span class="value">{{ formatNumber(result.data?.residual_stress_gpa) }} <small>GPa</small></span>
        </div>
        <div class="metric-item">
          <span class="label">形成能</span>
          <span class="value">{{ formatNumber(result.data?.formation_energy) }} <small>eV</small></span>
        </div>
      </div>

      <!-- 3D 模拟区域 -->
      <div class="simulation-section">
        <!-- 加载状态 -->
        <div v-if="loadingTimeSeries" class="loading-state">
          <el-icon class="is-loading" :size="24"><ReloadOutline /></el-icon>
          <span>正在加载模拟数据...</span>
        </div>

        <!-- 有数据时显示 -->
        <template v-else-if="vtkFiles.length > 0">
          <!-- 顶部信息栏 -->
          <div class="info-bar">
            <span class="info-badge">{{ (viewerRef?.currentFrameIndex ?? 0) + 1 }}/{{ vtkFiles.length }}</span>
            <span class="info-badge">{{ viewerRef?.formatPhysicalTime?.(viewerRef?.currentFrameIndex ?? 0) || '0 μs' }}</span>
          </div>

          <!-- VTK 3D 查看器（可调整大小） -->
          <div 
            class="viewer-container" 
            :style="{ height: viewerHeight + 'px' }"
          >
            <VtkTimeSeriesViewer
              ref="viewerRef"
              :time-series-files="vtkFiles"
              :height="viewerHeight + 'px'"
              :auto-play="true"
            />
          </div>

          <!-- 拖动调整大小手柄 -->
          <div 
            class="resize-handle"
            @mousedown="startResize"
          >
            <div class="handle-bar"></div>
          </div>

          <!-- 控制栏 -->
          <div class="controls-bar">
            <!-- 左侧：播放控制 -->
            <div class="control-group">
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.prevFrame?.()"
                :disabled="(viewerRef?.currentFrameIndex ?? 0) <= 0"
                title="上一帧"
              >
                <el-icon :size="14"><PlaySkipBackSharp /></el-icon>
              </button>
              
              <button 
                class="ctrl-btn play-btn" 
                @click="viewerRef?.togglePlayback?.()"
                :title="viewerRef?.isPlaying ? '暂停' : '播放'"
              >
                <el-icon :size="16">
                  <Pause v-if="viewerRef?.isPlaying" />
                  <Play v-else />
                </el-icon>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.nextFrame?.()"
                :disabled="(viewerRef?.currentFrameIndex ?? 0) >= vtkFiles.length - 1"
                title="下一帧"
              >
                <el-icon :size="14"><PlaySkipForwardSharp /></el-icon>
              </button>
            </div>
            
            <!-- 中间：进度条 -->
            <div class="progress-track">
              <el-slider 
                :model-value="viewerRef?.currentFrameIndex ?? 0"
                :min="0" 
                :max="vtkFiles.length - 1"
                :show-tooltip="false"
                @change="(val) => viewerRef?.onFrameChange?.(val)"
              />
            </div>
            
            <!-- 右侧：功能按钮 -->
            <div class="control-group">
              <el-dropdown trigger="click" @command="setPlaybackSpeed" placement="top">
                <button class="ctrl-btn text-btn">{{ viewerRef?.playbackSpeed ?? 1 }}x</button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="0.5">0.5x</el-dropdown-item>
                    <el-dropdown-item :command="1">1x</el-dropdown-item>
                    <el-dropdown-item :command="2">2x</el-dropdown-item>
                    <el-dropdown-item :command="4">4x</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              
              <button 
                class="ctrl-btn" 
                :class="{ active: viewerRef?.loopPlayback }" 
                @click="toggleLoop"
                title="循环播放"
              >
                <el-icon :size="14"><SyncOutline /></el-icon>
              </button>
              
              <div class="divider"></div>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.zoomOut?.()"
                title="缩小"
              >
                <el-icon :size="14"><RemoveOutline /></el-icon>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.zoomIn?.()"
                title="放大"
              >
                <el-icon :size="14"><AddOutline /></el-icon>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.resetCamera?.()"
                title="重置视角"
              >
                <el-icon :size="14"><ScanOutline /></el-icon>
              </button>
            </div>
          </div>
        </template>

        <!-- 无数据状态 -->
        <div v-else class="empty-state">
          <el-icon :size="32" color="#9ca3af"><VideocamOffOutline /></el-icon>
          <span>暂无模拟数据</span>
        </div>
      </div>
    </div>
  </SummaryCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElIcon, ElSlider, ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'
import { 
  ReloadOutline, 
  CubeOutline,
  VideocamOffOutline,
  Play,
  Pause,
  PlaySkipBackSharp,
  PlaySkipForwardSharp,
  SyncOutline,
  ScanOutline,
  AddOutline,
  RemoveOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import SummaryCard from '../common/SummaryCard.vue'
import VtkTimeSeriesViewer from '../common/VtkTimeSeriesViewer.vue'
import { API_BASE_URL } from '../../config'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['jump-to-node'])

// VTK 查看器引用
const viewerRef = ref(null)

// 查看器高度（可拖动调整）
const viewerHeight = ref(320)
const minHeight = 200
const maxHeight = 600

// 时间序列文件列表状态
const timeSeriesFiles = ref([])
const loadingTimeSeries = ref(false)

// 拖动调整大小
let isResizing = false
let startY = 0
let startHeight = 0

const startResize = (e) => {
  isResizing = true
  startY = e.clientY
  startHeight = viewerHeight.value
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
}

const onResize = (e) => {
  if (!isResizing) return
  const deltaY = e.clientY - startY
  const newHeight = Math.min(maxHeight, Math.max(minHeight, startHeight + deltaY))
  viewerHeight.value = newHeight
}

const stopResize = () => {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// 播放控制
const setPlaybackSpeed = (speed) => {
  if (viewerRef.value) {
    viewerRef.value.playbackSpeed = speed
  }
}

const toggleLoop = () => {
  if (viewerRef.value) {
    viewerRef.value.loopPlayback = !viewerRef.value.loopPlayback
  }
}

// 格式化数字
const formatNumber = (num) => {
  if (num === undefined || num === null) return '-'
  return Number(num).toFixed(2)
}

// 获取置信度徽章
const getConfidenceBadge = () => {
  const confidence = props.result?.data?.confidence
  if (confidence === undefined || confidence === null) return null
  
  const percent = Math.round(confidence * 100)
  if (percent >= 80) {
    return { text: `${percent}% 置信`, type: 'success' }
  } else if (percent >= 60) {
    return { text: `${percent}% 置信`, type: 'warning' }
  }
  return { text: `${percent}% 置信`, type: 'info' }
}

// 获取 VTK 数据
const vtkData = computed(() => props.result?.data?.vtk_data)
const isTimeSeries = computed(() => vtkData.value?.type === 'timeseries')

// 监听时间序列数据变化
watch(
  () => [isTimeSeries.value, vtkData.value?.folder],
  async ([isTS, folder]) => {
    if (!isTS) {
      timeSeriesFiles.value = []
      return
    }
    if (isTS && folder) {
      loadingTimeSeries.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/vtk/timeseries/${folder}`)
        if (response.ok) {
          const data = await response.json()
          timeSeriesFiles.value = data.files || []
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

// VTK文件列表
const vtkFiles = computed(() => {
  if (isTimeSeries.value) {
    return timeSeriesFiles.value
  }
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
.topphi-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 指标网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.metric-item {
  background: #f9fafb;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item .label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
}

.metric-item .value {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.metric-item .value small {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
}

/* 模拟区域 */
.simulation-section {
  background: #f3f4f6;
  border-radius: 12px;
  overflow: hidden;
}

/* 顶部信息栏 */
.info-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.info-badge {
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  color: #374151;
  font-weight: 500;
}

/* 3D 视图容器 */
.viewer-container {
  background: #111827;
  overflow: hidden;
}

/* 拖动调整大小手柄 */
.resize-handle {
  height: 12px;
  background: #e5e7eb;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.resize-handle:hover {
  background: #d1d5db;
}

.handle-bar {
  width: 40px;
  height: 4px;
  background: #9ca3af;
  border-radius: 2px;
}

/* 控制栏 */
.controls-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.divider {
  width: 1px;
  height: 20px;
  background: #e5e7eb;
  margin: 0 2px;
}

/* 控制按钮 */
.ctrl-btn {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 6px;
  background: #f3f4f6;
  color: #374151;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.ctrl-btn:hover:not(:disabled) {
  background: #e5e7eb;
  color: #111827;
}

.ctrl-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ctrl-btn.active {
  background: #dbeafe;
  color: #2563eb;
}

.ctrl-btn.play-btn {
  width: 34px;
  height: 34px;
  background: #3b82f6;
  color: #ffffff;
  border-radius: 50%;
}

.ctrl-btn.play-btn:hover {
  background: #2563eb;
}

.ctrl-btn.text-btn {
  width: auto;
  min-width: 36px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 600;
}

/* 进度条 */
.progress-track {
  flex: 1;
  min-width: 100px;
}

.progress-track :deep(.el-slider__runway) {
  height: 4px;
  background: #e5e7eb;
  margin: 14px 0;
  border-radius: 2px;
}

.progress-track :deep(.el-slider__bar) {
  height: 4px;
  background: #3b82f6;
  border-radius: 2px;
}

.progress-track :deep(.el-slider__button-wrapper) {
  top: -14px;
}

.progress-track :deep(.el-slider__button) {
  width: 12px;
  height: 12px;
  border: 2px solid #3b82f6;
  background: #ffffff;
}

/* 加载和空状态 */
.loading-state {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #6b7280;
  font-size: 13px;
  background: #ffffff;
}

.loading-state .is-loading {
  animation: spin 1s linear infinite;
}

.empty-state {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #6b7280;
  font-size: 13px;
  background: #ffffff;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
