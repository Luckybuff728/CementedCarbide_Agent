<template>
  <div class="vtk-timeseries-viewer" :class="{ 'immersive-mode': immersive }">
    <!-- 1. 主视图区域 -->
    <div class="viewer-wrapper" ref="viewerContainerRef" :style="{ height: height }">
      <!-- VTK Canvas -->
      <div ref="vtkContainerRef" class="vtk-canvas"></div>
      
      <!-- 顶部信息栏 -->
      <div v-if="!loading && !error && timeSeriesFiles.length > 0" class="top-info">
        <span class="frame-badge">{{ currentFrameIndex + 1 }}/{{ timeSeriesFiles.length }}</span>
        <span class="time-badge">{{ formatPhysicalTime(currentFrameIndex) }}</span>
      </div>

      <!-- 底部简洁控制栏 -->
      <div v-if="!loading && !error && timeSeriesFiles.length > 0" class="controls-bar">
        <!-- 播放按钮 -->
        <button class="ctrl-btn play-btn" @click="togglePlayback">
          <el-icon :size="16"><component :is="isPlaying ? PauseOutline : PlayOutline" /></el-icon>
        </button>
        
        <!-- 进度条 -->
        <div class="progress-track">
          <el-slider 
            v-model="currentFrameIndex" 
            :min="0" 
            :max="timeSeriesFiles.length - 1"
            :show-tooltip="false"
            @change="onFrameChange"
            class="mini-slider"
          />
        </div>
        
        <!-- 速度选择 -->
        <el-dropdown trigger="click" @command="(val) => playbackSpeed = val" placement="top">
          <button class="ctrl-btn speed-btn">{{ playbackSpeed }}×</button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :command="0.5">0.5×</el-dropdown-item>
              <el-dropdown-item :command="1">1×</el-dropdown-item>
              <el-dropdown-item :command="2">2×</el-dropdown-item>
              <el-dropdown-item :command="4">4×</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 循环 -->
        <button class="ctrl-btn" :class="{ active: loopPlayback }" @click="loopPlayback = !loopPlayback">
          <el-icon :size="14"><RefreshOutline /></el-icon>
        </button>
      </div>


      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading" size="32"><ReloadOutline /></el-icon>
        <p>{{ loadingText }}</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        <el-icon size="32"><CloseCircleOutline /></el-icon>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ElIcon } from 'element-plus'
import { 
  ReloadOutline,
  PlayOutline,
  PauseOutline,
  RefreshOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import { API_BASE_URL } from '../../config'

// 导入composables
import { useResizeObserver } from '../../composables/useResizeObserver'
import { formatPhysicalTime } from '../../composables/useVtkTimeSeriesHelpers'

// VTK.js 导入
import '@kitware/vtk.js/Rendering/Profiles/Volume'
import vtkRenderWindow from '@kitware/vtk.js/Rendering/Core/RenderWindow'
import vtkRenderer from '@kitware/vtk.js/Rendering/Core/Renderer'
import vtkRenderWindowInteractor from '@kitware/vtk.js/Rendering/Core/RenderWindowInteractor'
import vtkInteractorStyleTrackballCamera from '@kitware/vtk.js/Interaction/Style/InteractorStyleTrackballCamera'
import vtkOpenGLRenderWindow from '@kitware/vtk.js/Rendering/OpenGL/RenderWindow'
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume'
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper'
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction'
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction'
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData'
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray'

const props = defineProps({
  timeSeriesFiles: {
    type: Array,
    default: () => []
  },
  baseUrl: {
    type: String,
    default: API_BASE_URL
  },
  height: {
    type: String,
    default: '500px'
  },
  autoPlay: {
    type: Boolean,
    default: false
  },
  immersive: {
    type: Boolean,
    default: false
  }
})

const vtkContainerRef = ref(null)
const loading = ref(false)
const error = ref('')
const loadingText = ref('初始化中...')
const preloading = ref(false)
const preloadProgress = ref(0)
const preloadTotal = ref(0)

// 播放控制
const isPlaying = ref(false)
const currentFrameIndex = ref(0)
const playbackSpeed = ref(1)
const loopPlayback = ref(false)

// 数据状态
const currentDataRange = ref(null)
const phaseStats = ref(null)
const currentFileSize = computed(() => {
  if (props.timeSeriesFiles.length > 0 && currentFrameIndex.value < props.timeSeriesFiles.length) {
    return props.timeSeriesFiles[currentFrameIndex.value]?.size || 0
  }
  return 0
})

// 使用composables
const { setupResizeObserver, cleanup: cleanupResizeObserver } = useResizeObserver()

// VTK相关变量
let openGLRenderWindow = null
let renderer = null
let renderWindow = null
let renderWindowInteractor = null
let actor = null
let mapper = null

// 播放控制相关
let playbackTimer = null

// 缓存管理
const frameCache = new Map()

// 相机状态保存
let initialCameraPosition = null
let initialCameraFocalPoint = null  
let initialCameraViewUp = null
let isFirstFrame = true

/**
 * 初始化VTK渲染器
 */
const initRenderer = () => {
  if (!vtkContainerRef.value || !vtkContainerRef.value.isConnected) return
  
  try {
    openGLRenderWindow = vtkOpenGLRenderWindow.newInstance()
    openGLRenderWindow.setContainer(vtkContainerRef.value)
    
    const rect = vtkContainerRef.value.getBoundingClientRect()
    openGLRenderWindow.setSize(Math.floor(rect.width), Math.floor(rect.height))
    
    renderWindow = vtkRenderWindow.newInstance()
    renderWindow.addView(openGLRenderWindow)
    
    renderer = vtkRenderer.newInstance()
    renderer.setBackground(0.1, 0.1, 0.1)  // 深色背景
    renderWindow.addRenderer(renderer)
    
    renderWindowInteractor = vtkRenderWindowInteractor.newInstance()
    renderWindowInteractor.setView(openGLRenderWindow)
    renderWindowInteractor.initialize()
    
    const interactorStyle = vtkInteractorStyleTrackballCamera.newInstance()
    renderWindowInteractor.setInteractorStyle(interactorStyle)
    renderWindowInteractor.bindEvents(vtkContainerRef.value)
    
    nextTick(() => {
      if (vtkContainerRef.value && renderWindow) {
        setupResizeObserver(vtkContainerRef.value, renderWindow)
        renderWindow.render()
      }
    })
  } catch (err) {
    console.error('[VTK时间序列] 初始化失败:', err)
    error.value = '初始化渲染器失败'
  }
}

/**
 * 预加载所有帧到缓存
 */
const preloadAllFrames = async () => {
  if (preloading.value || props.timeSeriesFiles.length === 0) return
  
  preloading.value = true
  preloadProgress.value = 0
  preloadTotal.value = props.timeSeriesFiles.length
  
  for (let i = 0; i < props.timeSeriesFiles.length; i++) {
    const fileInfo = props.timeSeriesFiles[i]
    const fileName = fileInfo.name
    
    if (frameCache.has(fileName)) {
      preloadProgress.value++
      continue
    }
    
    try {
      const vtkUrl = `${props.baseUrl}/api/vtk/files/${fileName}`
      const response = await fetch(vtkUrl)
      
      if (response.ok) {
        const vtkText = await response.text()
        const source = parseLegacyVTK(vtkText)
        frameCache.set(fileName, source)
        preloadProgress.value++
      }
    } catch (err) {
      console.error(`[VTK时间序列] 预加载帧 ${i} 失败:`, err)
      preloadProgress.value++
    }
  }
  
  preloading.value = false
}

/**
 * 加载指定帧的VTK文件
 */
const loadFrame = async (frameIndex, showLoading = true) => {
  if (frameIndex < 0 || frameIndex >= props.timeSeriesFiles.length) return
  
  const fileInfo = props.timeSeriesFiles[frameIndex]
  const fileName = fileInfo.name
  
  if (frameCache.has(fileName)) {
    renderFrame(frameCache.get(fileName))
    currentFrameIndex.value = frameIndex
    return
  }
  
  if (showLoading) {
    loading.value = true
    loadingText.value = `加载帧 ${frameIndex + 1}/${props.timeSeriesFiles.length}...`
  }
  error.value = null
  
  try {
    const vtkUrl = `${API_BASE_URL}/api/vtk/files/${fileName}`
    const response = await fetch(vtkUrl)
    if (!response.ok) throw new Error(`HTTP错误: ${response.status}`)
    
    const vtkText = await response.text()
    const source = parseLegacyVTK(vtkText)
    
    frameCache.set(fileName, source)
    renderFrame(source)
    currentFrameIndex.value = frameIndex
    
    if (showLoading) loading.value = false
    
  } catch (err) {
    console.error('[VTK时间序列] 加载失败:', err)
    error.value = `加载失败: ${err.message}`
    if (showLoading) loading.value = false
  }
}

/**
 * 解析Legacy VTK格式文件
 */
const parseLegacyVTK = (vtkText) => {
  const lines = vtkText.split('\n')
  
  let dimensions = [64, 64, 64]
  let origin = [0, 0, 0]
  let spacing = [1, 1, 1]
  let pointDataIndex = -1
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    if (line.startsWith('DIMENSIONS')) {
      const parts = line.split(/\s+/)
      dimensions = [parseInt(parts[1]), parseInt(parts[2]), parseInt(parts[3])]
    } else if (line.startsWith('ORIGIN')) {
      const parts = line.split(/\s+/)
      origin = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]
    } else if (line.startsWith('SPACING')) {
      const parts = line.split(/\s+/)
      spacing = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]
    } else if (line.startsWith('ASPECT_RATIO')) {
      const parts = line.split(/\s+/)
      const ratio = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]
      spacing = [
        ratio[0] * 64 / dimensions[0],
        ratio[1] * 64 / dimensions[1],
        ratio[2] * 64 / dimensions[2]
      ]
    } else if (line.startsWith('POINT_DATA')) {
      pointDataIndex = i
    } else if (line.startsWith('SCALARS') && pointDataIndex > 0) {
      pointDataIndex = i + 2
      break
    }
  }
  
  const scalarData = []
  for (let i = pointDataIndex; i < lines.length; i++) {
    const line = lines[i].trim()
    if (line && !line.startsWith('#')) {
      const values = line.split(/\s+/)
      for (let j = 0; j < values.length; j++) {
        const val = parseFloat(values[j])
        if (!isNaN(val)) scalarData.push(val)
      }
    }
  }
  
  if (scalarData.length === 0) throw new Error('VTK文件中没有找到数据')
  
  const imageData = vtkImageData.newInstance()
  imageData.setDimensions(dimensions)
  imageData.setOrigin(origin)
  imageData.setSpacing(spacing)
  
  const dataArray = vtkDataArray.newInstance({
    name: 'scalars',
    numberOfComponents: 1,
    values: Float32Array.from(scalarData)
  })
  
  imageData.getPointData().setScalars(dataArray)
  
  return imageData
}

/**
 * 渲染帧数据
 */
const renderFrame = (source) => {
  if (!renderer || !renderWindow) return
  
  if (actor) renderer.removeVolume(actor)
  
  mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(source)
  mapper.setSampleDistance(0.4)
  
  actor = vtkVolume.newInstance()
  actor.setMapper(mapper)
  
  const dataArray = source.getPointData().getScalars()
  const dataRange = dataArray.getRange()
  const [minVal, maxVal] = dataRange
  const range = maxVal - minVal
  
  currentDataRange.value = { min: minVal, max: maxVal }
  phaseStats.value = { totalPoints: dataArray.getNumberOfTuples(), dataRange: range }
  
  const ctfun = vtkColorTransferFunction.newInstance()
  ctfun.addRGBPoint(minVal, 0.0, 0.0, 1.0)
  ctfun.addRGBPoint(minVal + range * 0.5, 0.0, 1.0, 0.0)
  ctfun.addRGBPoint(maxVal, 1.0, 0.0, 0.0)
  
  const ofun = vtkPiecewiseFunction.newInstance()
  const isEarlyStage = range < 0.025
  
  if (isEarlyStage) {
    ofun.addPoint(minVal, 0.35)
    ofun.addPoint(minVal + range * 0.25, 0.65)         
    ofun.addPoint(minVal + range * 0.5, 0.9)
    ofun.addPoint(minVal + range * 0.75, 0.65)         
    ofun.addPoint(maxVal, 0.35)
  } else {
    ofun.addPoint(minVal, 0.8)
    ofun.addPoint(minVal + range * 0.47, 0.75)
    ofun.addPoint(minVal + range * 0.5, 0.25)
    ofun.addPoint(minVal + range * 0.53, 0.75)
    ofun.addPoint(maxVal, 0.8)
  }
  
  actor.getProperty().setRGBTransferFunction(0, ctfun)
  actor.getProperty().setScalarOpacity(0, ofun)
  actor.getProperty().setInterpolationTypeToLinear()
  actor.getProperty().setShade(true)
  actor.getProperty().setAmbient(0.3)
  actor.getProperty().setDiffuse(0.7)
  actor.getProperty().setSpecular(0.2)
  actor.getProperty().setSpecularPower(8)
  
  renderer.addVolume(actor)
  
  const camera = renderer.getActiveCamera()
  
  if (isFirstFrame) {
    renderer.resetCamera()
    const bounds = source.getBounds()
    const center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2]
    
    camera.setFocalPoint(center[0], center[1], center[2])
    // 增加相机距离，确保立方体完整显示不被裁切
    const distance = Math.max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 4.5
    
    camera.setPosition(center[0] + distance * 0.7, center[1] + distance * 0.7, center[2] + distance * 0.7)
    camera.setViewUp(0, 0, 1)
    
    initialCameraPosition = camera.getPosition()
    initialCameraFocalPoint = camera.getFocalPoint()
    initialCameraViewUp = camera.getViewUp()
    
    isFirstFrame = false
  } else if (initialCameraPosition) {
    camera.setPosition(...initialCameraPosition)
    camera.setFocalPoint(...initialCameraFocalPoint)
    camera.setViewUp(...initialCameraViewUp)
  }
  
  renderWindow.render()
}

const togglePlayback = () => {
  isPlaying.value = !isPlaying.value
  isPlaying.value ? startPlayback() : stopPlayback()
}

const startPlayback = () => {
  if (playbackTimer) return
  const interval = 1000 / playbackSpeed.value
  
  playbackTimer = setInterval(() => {
    if (currentFrameIndex.value < props.timeSeriesFiles.length - 1) {
      currentFrameIndex.value++
      loadFrame(currentFrameIndex.value, false)
    } else {
      if (loopPlayback.value) {
        currentFrameIndex.value = 0
        loadFrame(0, false)
      } else {
        stopPlayback()
        isPlaying.value = false
      }
    }
  }, interval)
}

const stopPlayback = () => {
  if (playbackTimer) {
    clearInterval(playbackTimer)
    playbackTimer = null
  }
}

const onFrameChange = (value) => {
  stopPlayback()
  isPlaying.value = false
  loadFrame(value)
}

const resetCamera = () => {
  if (renderer && renderWindow) {
    const camera = renderer.getActiveCamera()
    renderer.resetCamera()
    initialCameraPosition = camera.getPosition()
    initialCameraFocalPoint = camera.getFocalPoint()
    initialCameraViewUp = camera.getViewUp()
    renderWindow.render()
  }
}

const downloadCurrentFrame = () => {
  const fileInfo = props.timeSeriesFiles[currentFrameIndex.value]
  if (fileInfo) {
    const url = `${API_BASE_URL}/api/vtk/files/${fileInfo.name}`
    window.open(url, '_blank')
  }
}

const formatDetailedTooltipWrapper = (value) => formatDetailedTooltip(value, props.timeSeriesFiles)

const cleanup = () => {
  stopPlayback()
  frameCache.clear()
  cleanupResizeObserver()
  
  if (actor && renderer) {
    renderer.removeVolume(actor)
    actor.delete()
  }
  if (mapper) mapper.delete()
  if (renderWindowInteractor) {
    renderWindowInteractor.unbindEvents()
    renderWindowInteractor.delete()
  }
  if (renderer) renderer.delete()
  if (renderWindow) renderWindow.delete()
  if (openGLRenderWindow) openGLRenderWindow.delete()
  
  openGLRenderWindow = null
  renderer = null
  renderWindow = null
  renderWindowInteractor = null
  actor = null
  mapper = null
}

watch(playbackSpeed, () => {
  if (isPlaying.value) {
    stopPlayback()
    startPlayback()
  }
})

onMounted(() => {
  initRenderer()
  if (props.timeSeriesFiles.length > 0) {
    setTimeout(() => {
      loadFrame(0).then(() => {
        setTimeout(() => preloadAllFrames(), 500)
      })
      if (props.autoPlay) setTimeout(() => togglePlayback(), 2000)
    }, 100)
  }
})

onBeforeUnmount(() => cleanup())
</script>

<style scoped>
.vtk-timeseries-viewer {
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #121212;
  position: relative;
  overflow: hidden;
}

.vtk-timeseries-viewer.immersive-mode {
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.viewer-wrapper {
  position: relative;
  width: 100%;
  background: #121212;
  overflow: hidden;
}

.vtk-canvas {
  width: 100%;
  height: 100%;
}

.vtk-canvas :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

/* 顶部信息栏 */
.top-info {
  position: absolute;
  top: 10px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
}

.frame-badge,
.time-badge {
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', monospace;
  color: rgba(255, 255, 255, 0.85);
}

/* 底部简洁控制栏 */
.controls-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 44px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, transparent 100%);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 8px;
  z-index: 20;
}

.ctrl-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.ctrl-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.ctrl-btn.play-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #1a1a1a;
}

.ctrl-btn.play-btn:hover {
  background: #fff;
}

.ctrl-btn.speed-btn {
  width: auto;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', monospace;
}

/* 进度条 - 自适应宽度 */
.progress-track {
  flex: 1;
  min-width: 80px;
  padding: 0 4px;
}

.mini-slider :deep(.el-slider__runway) {
  height: 3px;
  background: rgba(255, 255, 255, 0.2);
  margin: 14px 0;
}

.mini-slider :deep(.el-slider__bar) {
  height: 3px;
  background: rgba(255, 255, 255, 0.8);
}

.mini-slider :deep(.el-slider__button-wrapper) {
  top: -15px;
}

.mini-slider :deep(.el-slider__button) {
  width: 10px;
  height: 10px;
  border: 2px solid #fff;
  background: #1a1a1a;
}

/* 加载与错误 */
.loading-overlay, .error-message {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  color: #fff;
  z-index: 30;
}

.error-message {
  color: #f56c6c;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
