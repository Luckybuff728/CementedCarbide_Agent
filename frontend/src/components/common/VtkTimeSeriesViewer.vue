<template>
  <div class="vtk-viewer">
    <!-- VTK Canvas 渲染区域 -->
    <div class="viewer-wrapper" ref="viewerContainerRef" :style="{ height: height }">
      <div ref="vtkContainerRef" class="vtk-canvas"></div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="overlay">
        <el-icon class="is-loading" :size="28"><ReloadOutline /></el-icon>
        <p>{{ loadingText }}</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="overlay error">
        <el-icon :size="28"><AlertCircleOutline /></el-icon>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElIcon } from 'element-plus'
import { ReloadOutline, AlertCircleOutline } from '@vicons/ionicons5'
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
  // 时间序列文件列表
  timeSeriesFiles: {
    type: Array,
    default: () => []
  },
  // API基础URL
  baseUrl: {
    type: String,
    default: API_BASE_URL
  },
  // 容器高度
  height: {
    type: String,
    default: '400px'
  },
  // 是否自动播放
  autoPlay: {
    type: Boolean,
    default: false
  }
})

const vtkContainerRef = ref(null)
const loading = ref(false)
const error = ref('')
const loadingText = ref('初始化中...')

// 播放控制
const isPlaying = ref(false)
const currentFrameIndex = ref(0)
const playbackSpeed = ref(1)
const loopPlayback = ref(false)

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
 * 预加载所有帧到缓存（后台静默执行）
 */
let isPreloading = false
const preloadAllFrames = async () => {
  if (isPreloading || props.timeSeriesFiles.length === 0) return
  
  isPreloading = true
  
  for (let i = 0; i < props.timeSeriesFiles.length; i++) {
    const fileInfo = props.timeSeriesFiles[i]
    const fileName = fileInfo.name
    
    if (frameCache.has(fileName)) continue
    
    try {
      const vtkUrl = `${props.baseUrl}/api/vtk/files/${fileName}`
      const response = await fetch(vtkUrl)
      
      if (response.ok) {
        const vtkText = await response.text()
        const source = parseLegacyVTK(vtkText)
        frameCache.set(fileName, source)
      }
    } catch (err) {
      console.error(`[VTK时间序列] 预加载帧 ${i} 失败:`, err)
    }
  }
  
  isPreloading = false
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
    // 设置相机距离，让立方体充满视图
    const distance = Math.max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 2.8
    
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

// 相机控制方法
const resetCamera = () => {
  if (renderer && renderWindow) {
    renderer.resetCamera()
    renderWindow.render()
  }
}

const zoomIn = () => {
  if (renderer && renderWindow) {
    const camera = renderer.getActiveCamera()
    camera.dolly(1.2)
    renderer.resetCameraClippingRange()
    renderWindow.render()
  }
}

const zoomOut = () => {
  if (renderer && renderWindow) {
    const camera = renderer.getActiveCamera()
    camera.dolly(0.8)
    renderer.resetCameraClippingRange()
    renderWindow.render()
  }
}

// 帧控制
const prevFrame = () => {
  if (currentFrameIndex.value > 0) {
    stopPlayback()
    isPlaying.value = false
    loadFrame(currentFrameIndex.value - 1)
  }
}

const nextFrame = () => {
  if (currentFrameIndex.value < props.timeSeriesFiles.length - 1) {
    stopPlayback()
    isPlaying.value = false
    loadFrame(currentFrameIndex.value + 1)
  }
}

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

// 暴露给父组件的状态和方法
defineExpose({
  // 状态
  isPlaying,
  currentFrameIndex,
  playbackSpeed,
  loopPlayback,
  loading,
  error,
  // 播放控制
  togglePlayback,
  startPlayback,
  stopPlayback,
  loadFrame,
  onFrameChange,
  // 帧控制
  prevFrame,
  nextFrame,
  // 相机控制
  resetCamera,
  zoomIn,
  zoomOut,
  // 工具函数
  formatPhysicalTime
})
</script>

<style scoped>
/* VTK 3D 渲染器 - 纯净容器 */
.vtk-viewer {
  width: 100%;
  position: relative;
  background: #111827;
  border-radius: 8px;
  overflow: hidden;
}

.viewer-wrapper {
  position: relative;
  width: 100%;
  background: #111827;
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

/* 覆盖层（加载/错误）*/
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(4px);
  color: rgba(255, 255, 255, 0.8);
  z-index: 30;
}

.overlay p {
  margin: 0;
  font-size: 13px;
}

.overlay.error {
  color: #f87171;
}

.overlay .is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
