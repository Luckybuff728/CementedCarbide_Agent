<template>
  <div class="topphi-result-card">
    <div class="topphi-content">
      <!-- 指标网格 - 2x2 布局 -->
      <div class="metrics-grid">
        <div class="metric-item">
          <span class="label">晶粒尺寸</span>
          <span class="value">{{ formatNumber(result.data?.grain_size_nm) }} <small>nm</small></span>
        </div>
        <div class="metric-item">
          <span class="label">择优取向</span>
          <span class="value">({{ result.data?.preferred_orientation || '-' }})</span>
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

      <!-- 3D 模拟区域 - 优化设计 -->
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

          <!-- 控制栏 - 专业设计 -->
          <div class="controls-bar">
            <!-- 左侧：播放控制 -->
            <div class="control-group playback-controls">
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.prevFrame?.()"
                :disabled="(viewerRef?.currentFrameIndex ?? 0) <= 0"
                title="上一帧 (Previous Frame)"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
                </svg>
              </button>
              
              <button 
                class="ctrl-btn play-btn" 
                @click="viewerRef?.togglePlayback?.()"
                :title="viewerRef?.isPlaying ? '暂停 (Pause)' : '播放 (Play)'"
              >
                <svg v-if="viewerRef?.isPlaying" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                  <path d="M6 4h4v16H6zm8 0h4v16h-4z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.nextFrame?.()"
                :disabled="(viewerRef?.currentFrameIndex ?? 0) >= vtkFiles.length - 1"
                title="下一帧 (Next Frame)"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                </svg>
              </button>
            </div>
            
            <!-- 中间：进度条 -->
            <div class="progress-section">
              <div class="progress-track">
                <el-slider 
                  :model-value="viewerRef?.currentFrameIndex ?? 0"
                  :min="0" 
                  :max="vtkFiles.length - 1"
                  :show-tooltip="false"
                  @change="(val) => viewerRef?.onFrameChange?.(val)"
                />
              </div>
            </div>
            
            <!-- 右侧：功能按钮 -->
            <div class="control-group tool-controls">
              <el-dropdown trigger="click" @command="setPlaybackSpeed" placement="top">
                <button class="ctrl-btn speed-btn" title="播放速度">
                  <span class="speed-value">{{ viewerRef?.playbackSpeed ?? 1 }}x</span>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="speed-dropdown">
                    <el-dropdown-item :command="0.5" :class="{ active: viewerRef?.playbackSpeed === 0.5 }">
                      <span>慢速</span><span class="speed-label">0.5x</span>
                    </el-dropdown-item>
                    <el-dropdown-item :command="1" :class="{ active: viewerRef?.playbackSpeed === 1 }">
                      <span>正常</span><span class="speed-label">1x</span>
                    </el-dropdown-item>
                    <el-dropdown-item :command="2" :class="{ active: viewerRef?.playbackSpeed === 2 }">
                      <span>快速</span><span class="speed-label">2x</span>
                    </el-dropdown-item>
                    <el-dropdown-item :command="4" :class="{ active: viewerRef?.playbackSpeed === 4 }">
                      <span>极快</span><span class="speed-label">4x</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              
              <button 
                class="ctrl-btn" 
                :class="{ active: viewerRef?.loopPlayback }" 
                @click="toggleLoop"
                title="循环播放 (Loop)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M17 2l4 4-4 4"/>
                  <path d="M3 11V9a4 4 0 014-4h14"/>
                  <path d="M7 22l-4-4 4-4"/>
                  <path d="M21 13v2a4 4 0 01-4 4H3"/>
                </svg>
              </button>
              
              <div class="divider"></div>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.zoomOut?.()"
                title="缩小 (Zoom Out)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35M8 11h6"/>
                </svg>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.zoomIn?.()"
                title="放大 (Zoom In)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35M11 8v6M8 11h6"/>
                </svg>
              </button>
              
              <button 
                class="ctrl-btn" 
                @click="viewerRef?.resetCamera?.()"
                title="重置视角 (Reset View)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                </svg>
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
  </div>
</template>

<script setup>
/**
 * TopPhi 相场模拟结果卡片
 * 
 * 展示相场模拟的微观结构参数和 VTK 3D 可视化
 */
import { ref, computed, watch } from 'vue'
import { ElIcon, ElSlider, ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'
import { 
  ReloadOutline, 
  VideocamOffOutline
} from '@vicons/ionicons5'
import VtkTimeSeriesViewer from '../common/VtkTimeSeriesViewer.vue'
import { API_BASE_URL } from '../../config'

const props = defineProps({
  // 模拟结果对象
  result: {
    type: Object,
    required: true
  }
})

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
.topphi-result-card {
  padding: 16px;
}

.topphi-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 指标网格 - 2x2 紧凑布局 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--bg-secondary, #f9fafb);
  border-radius: 8px;
}

.metric-item .label {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.metric-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.metric-item .value small {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  font-weight: 500;
  margin-left: 2px;
}

/* ========================================
   3D 模拟区域
   ======================================== */
.simulation-section {
  background: #1a1f2e;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #374151;
}

/* 顶部信息栏 */
.info-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #1f2937;
  border-bottom: 1px solid #374151;
}

.info-badge {
  background: rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  color: #d1d5db;
  font-weight: 500;
}

/* 3D 视图容器 */
.viewer-container {
  background: #0f1219;
  overflow: hidden;
}

/* 拖动调整大小手柄 */
.resize-handle {
  height: 10px;
  background: #1f2937;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.resize-handle:hover {
  background: #374151;
}

.handle-bar {
  width: 48px;
  height: 3px;
  background: #4b5563;
  border-radius: 2px;
}

/* ========================================
   控制栏 - 专业播放器设计
   ======================================== */
.controls-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
  border-top: 1px solid #374151;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.playback-controls {
  flex-shrink: 0;
}

.progress-section {
  flex: 1;
  min-width: 100px;
}

.tool-controls {
  flex-shrink: 0;
}

.divider {
  width: 1px;
  height: 20px;
  background: #374151;
  margin: 0 4px;
}

/* 控制按钮 */
.ctrl-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  color: #d1d5db;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.ctrl-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: #f9fafb;
}

.ctrl-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.ctrl-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

/* 播放按钮 */
.ctrl-btn.play-btn {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

.ctrl-btn.play-btn:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: scale(1.05);
}

/* 速度按钮 */
.ctrl-btn.speed-btn {
  width: auto;
  min-width: 40px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.speed-value {
  color: #93c5fd;
}

/* 进度条 */
.progress-track {
  flex: 1;
}

.progress-track :deep(.el-slider__runway) {
  height: 4px;
  background: #374151;
  margin: 14px 0;
  border-radius: 2px;
}

.progress-track :deep(.el-slider__bar) {
  height: 4px;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  border-radius: 2px;
}

.progress-track :deep(.el-slider__button-wrapper) {
  top: -14px;
}

.progress-track :deep(.el-slider__button) {
  width: 14px;
  height: 14px;
  border: 2px solid #3b82f6;
  background: #1f2937;
  transition: all 0.15s ease;
}

.progress-track :deep(.el-slider__button:hover) {
  transform: scale(1.2);
}

/* 速度下拉菜单 */
.speed-dropdown :deep(.el-dropdown-menu__item) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
}

.speed-dropdown :deep(.el-dropdown-menu__item.active) {
  background: #eff6ff;
  color: #2563eb;
}

.speed-label {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  color: #9ca3af;
  margin-left: 12px;
}

/* 加载和空状态 */
.loading-state {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #9ca3af;
  font-size: 13px;
  background: #111827;
}

.loading-state .is-loading {
  animation: spin 1s linear infinite;
  color: #60a5fa;
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
  background: #111827;
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
  
  
  .controls-bar {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .progress-section {
    order: 3;
    width: 100%;
  }
}
</style>
