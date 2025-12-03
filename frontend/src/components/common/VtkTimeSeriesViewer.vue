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
import '@kitware/vtk.js/Rendering/Profiles/Geometry'
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

// 增强功能导入
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor'
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper'
import vtkOutlineFilter from '@kitware/vtk.js/Filters/General/OutlineFilter'
import vtkOrientationMarkerWidget from '@kitware/vtk.js/Interaction/Widgets/OrientationMarkerWidget'
import vtkAxesActor from '@kitware/vtk.js/Rendering/Core/AxesActor'
import vtkScalarBarActor from '@kitware/vtk.js/Rendering/Core/ScalarBarActor'

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
  },
  // 背景颜色
  backgroundColor: {
    type: Array,
    default: () => [0.1, 0.1, 0.1]
  },
  // 显示选项
  showScalarBar: {
    type: Boolean,
    default: true
  },
  showOrientationWidget: {
    type: Boolean,
    default: true
  },
  showOutline: {
    type: Boolean,
    default: true
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

// 辅助组件变量
let outlineActor = null
let outlineMapper = null
let orientationWidget = null
let axesActor = null
let scalarBarActor = null

// 播放控制相关
let playbackTimer = null
let isLoadingFrame = false  // 帧加载锁，防止竞态条件
let abortController = null  // 用于取消进行中的请求

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
    renderer.setBackground(...props.backgroundColor)
    renderWindow.addRenderer(renderer)
    
    renderWindowInteractor = vtkRenderWindowInteractor.newInstance()
    renderWindowInteractor.setView(openGLRenderWindow)
    renderWindowInteractor.initialize()
    
    const interactorStyle = vtkInteractorStyleTrackballCamera.newInstance()
    renderWindowInteractor.setInteractorStyle(interactorStyle)
    renderWindowInteractor.bindEvents(vtkContainerRef.value)
    
    // 初始化 Orientation Widget
    if (props.showOrientationWidget) {
      axesActor = vtkAxesActor.newInstance()
      orientationWidget = vtkOrientationMarkerWidget.newInstance({
        actor: axesActor,
        interactor: renderWindowInteractor
      })
      orientationWidget.setEnabled(true)
      orientationWidget.setViewportCorner(vtkOrientationMarkerWidget.Corners.BOTTOM_LEFT)
      orientationWidget.setViewportSize(0.15)
      orientationWidget.setMinPixelSize(100, 100)
    }

    // 初始化 Scalar Bar (配置科研规范样式)
    if (props.showScalarBar) {
      scalarBarActor = vtkScalarBarActor.newInstance()
      scalarBarActor.setVisibility(false)
      // 不添加到renderer，等有数据时再添加
    }

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
 * 支持取消机制，避免组件卸载后继续执行
 */
let isPreloading = false
let preloadAbortController = null

const preloadAllFrames = async () => {
  if (isPreloading || props.timeSeriesFiles.length === 0) return
  
  isPreloading = true
  preloadAbortController = new AbortController()
  
  for (let i = 0; i < props.timeSeriesFiles.length; i++) {
    // 检查是否已取消
    if (preloadAbortController.signal.aborted) break
    
    const fileInfo = props.timeSeriesFiles[i]
    const fileName = fileInfo.name
    
    if (frameCache.has(fileName)) continue
    
    try {
      // 统一使用 props.baseUrl
      const vtkUrl = `${props.baseUrl}/api/vtk/files/${fileName}`
      const response = await fetch(vtkUrl, { 
        signal: preloadAbortController.signal 
      })
      
      if (response.ok) {
        const vtkText = await response.text()
        const source = parseLegacyVTK(vtkText)
        frameCache.set(fileName, source)
      }
    } catch (err) {
      // 忽略取消错误
      if (err.name === 'AbortError') break
      console.error(`[VTK时间序列] 预加载帧 ${i} 失败:`, err)
    }
  }
  
  isPreloading = false
  preloadAbortController = null
}

/**
 * 加载指定帧的VTK文件
 * 支持取消机制和加载锁，防止竞态条件
 */
const loadFrame = async (frameIndex, showLoading = true) => {
  if (frameIndex < 0 || frameIndex >= props.timeSeriesFiles.length) return
  
  const fileInfo = props.timeSeriesFiles[frameIndex]
  const fileName = fileInfo.name
  
  // 从缓存加载
  if (frameCache.has(fileName)) {
    renderFrame(frameCache.get(fileName))
    currentFrameIndex.value = frameIndex
    return
  }
  
  // 如果正在加载其他帧，取消之前的请求
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()
  
  // 设置加载锁
  isLoadingFrame = true
  
  if (showLoading) {
    loading.value = true
    loadingText.value = `加载帧 ${frameIndex + 1}/${props.timeSeriesFiles.length}...`
  }
  error.value = null
  
  try {
    // 统一使用 props.baseUrl
    const vtkUrl = `${props.baseUrl}/api/vtk/files/${fileName}`
    const response = await fetch(vtkUrl, { signal: abortController.signal })
    if (!response.ok) throw new Error(`HTTP错误: ${response.status}`)
    
    const vtkText = await response.text()
    const source = parseLegacyVTK(vtkText)
    
    frameCache.set(fileName, source)
    renderFrame(source)
    currentFrameIndex.value = frameIndex
    
    if (showLoading) loading.value = false
    
  } catch (err) {
    // 忽略取消错误
    if (err.name === 'AbortError') return
    
    console.error('[VTK时间序列] 加载失败:', err)
    error.value = `加载失败: ${err.message}`
    if (showLoading) loading.value = false
  } finally {
    isLoadingFrame = false
  }
}

/**
 * 解析Legacy VTK格式文件
 * 增强的解析器，支持更多VTK格式变体
 */
const parseLegacyVTK = (vtkText) => {
  const lines = vtkText.split('\n')
  
  let dimensions = [64, 64, 64]
  let origin = [0, 0, 0]
  let spacing = [1, 1, 1]
  let dataStartIndex = -1
  let expectedPoints = 0
  
  // 第一遍扫描：提取元数据
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    if (line.startsWith('DIMENSIONS')) {
      const parts = line.split(/\s+/)
      dimensions = [parseInt(parts[1]), parseInt(parts[2]), parseInt(parts[3])]
      expectedPoints = dimensions[0] * dimensions[1] * dimensions[2]
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
      // 记录POINT_DATA位置，继续查找SCALARS
      continue
    } else if (line.startsWith('SCALARS')) {
      // 找到SCALARS后，跳过LOOKUP_TABLE行
      for (let j = i + 1; j < lines.length; j++) {
        const nextLine = lines[j].trim()
        if (nextLine.startsWith('LOOKUP_TABLE') || nextLine === '') {
          continue
        }
        // 找到第一行数据
        dataStartIndex = j
        break
      }
      break
    }
  }
  
  if (dataStartIndex < 0) {
    throw new Error('VTK文件格式错误：未找到标量数据')
  }
  
  // 第二遍扫描：提取数值数据
  const scalarData = []
  for (let i = dataStartIndex; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line || line.startsWith('#')) continue
    
    const values = line.split(/\s+/)
    for (const val of values) {
      const num = parseFloat(val)
      if (!isNaN(num)) scalarData.push(num)
    }
    
    // 已收集足够数据时提前退出
    if (expectedPoints > 0 && scalarData.length >= expectedPoints) break
  }
  
  if (scalarData.length === 0) {
    throw new Error('VTK文件中没有找到数据')
  }
  
  // 验证数据完整性
  if (expectedPoints > 0 && scalarData.length !== expectedPoints) {
    console.warn(`[VTK解析] 数据点数量不匹配: 期望 ${expectedPoints}, 实际 ${scalarData.length}`)
  }
  
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

// 用于追踪需要清理的VTK对象
let currentCtfun = null
let currentOfun = null
let currentOutlineFilter = null

/**
 * 清理渲染相关的VTK对象，防止内存泄漏
 */
const cleanupRenderObjects = () => {
  // 清理 Volume Actor 和 Mapper
  if (actor) {
    renderer?.removeVolume(actor)
    actor.delete()
    actor = null
  }
  if (mapper) {
    mapper.delete()
    mapper = null
  }
  
  // 清理 Outline
  if (outlineActor) {
    renderer?.removeActor(outlineActor)
    outlineActor.delete()
    outlineActor = null
  }
  if (outlineMapper) {
    outlineMapper.delete()
    outlineMapper = null
  }
  if (currentOutlineFilter) {
    currentOutlineFilter.delete()
    currentOutlineFilter = null
  }
  
  // 清理传输函数
  if (currentCtfun) {
    currentCtfun.delete()
    currentCtfun = null
  }
  if (currentOfun) {
    currentOfun.delete()
    currentOfun = null
  }
}

/**
 * 渲染帧数据
 * 包含完整的内存管理和材料学标准颜色映射
 */
const renderFrame = (source) => {
  if (!renderer || !renderWindow) return
  
  // 清理旧的渲染对象，防止内存泄漏
  cleanupRenderObjects()
  
  // 1. 设置 Volume Rendering
  mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(source)
  
  // 根据数据维度自适应采样距离
  const dims = source.getDimensions()
  const avgDim = (dims[0] + dims[1] + dims[2]) / 3
  const sampleDistance = Math.max(0.2, Math.min(1.0, 64 / avgDim))
  mapper.setSampleDistance(sampleDistance)
  
  actor = vtkVolume.newInstance()
  actor.setMapper(mapper)
  
  const dataArray = source.getPointData().getScalars()
  const dataRange = dataArray.getRange()
  const [minVal, maxVal] = dataRange
  const range = maxVal - minVal
  
  // ========================================
  // 材料学科研规范颜色映射 (Diverging Colormap)
  // 适用于相场模拟、浓度场、成分分布等
  // 蓝色(低值) -> 白色(中间) -> 红色(高值)
  // 参考: Moreland, K. "Diverging Color Maps for Scientific Visualization"
  // ========================================
  currentCtfun = vtkColorTransferFunction.newInstance()
  
  // 使用科研标准的 Coolwarm 发散色标
  // 低值区域: 深蓝 -> 蓝
  currentCtfun.addRGBPoint(minVal, 0.230, 0.299, 0.754)                    // #3B4CC0 深蓝
  currentCtfun.addRGBPoint(minVal + range * 0.25, 0.553, 0.691, 0.996)     // #8DB0FE 浅蓝
  // 中间区域: 接近白色/浅灰
  currentCtfun.addRGBPoint(minVal + range * 0.5, 0.865, 0.865, 0.865)      // #DDDDDD 浅灰白
  // 高值区域: 橙 -> 深红
  currentCtfun.addRGBPoint(minVal + range * 0.75, 0.956, 0.647, 0.510)     // #F4A582 浅橙
  currentCtfun.addRGBPoint(maxVal, 0.706, 0.016, 0.150)                    // #B40426 深红
  
  currentOfun = vtkPiecewiseFunction.newInstance()
  
  // 自适应不透明度策略
  const isLowContrast = range < 0.025  // 早期相场，数据范围小
  const isMidRange = range >= 0.025 && range < 0.5  // 中期演化
  
  if (isLowContrast) {
    // 早期阶段：增强微小差异的可视化
    currentOfun.addPoint(minVal, 0.0)
    currentOfun.addPoint(minVal + range * 0.1, 0.0)
    currentOfun.addPoint(minVal + range * 0.3, 0.5)
    currentOfun.addPoint(minVal + range * 0.5, 0.9)
    currentOfun.addPoint(minVal + range * 0.7, 0.5)
    currentOfun.addPoint(minVal + range * 0.9, 0.0)
    currentOfun.addPoint(maxVal, 0.0)
  } else if (isMidRange) {
    // 中期阶段：平衡显示
    currentOfun.addPoint(minVal, 0.0)
    currentOfun.addPoint(minVal + range * 0.15, 0.1)
    currentOfun.addPoint(minVal + range * 0.4, 0.4)
    currentOfun.addPoint(minVal + range * 0.5, 0.5)
    currentOfun.addPoint(minVal + range * 0.6, 0.4)
    currentOfun.addPoint(minVal + range * 0.85, 0.1)
    currentOfun.addPoint(maxVal, 0.0)
  } else {
    // 后期阶段：双相清晰分离
    currentOfun.addPoint(minVal, 0.6)
    currentOfun.addPoint(minVal + range * 0.1, 0.3)
    currentOfun.addPoint(minVal + range * 0.4, 0.0)
    currentOfun.addPoint(minVal + range * 0.5, 0.0)  // 中间透明
    currentOfun.addPoint(minVal + range * 0.6, 0.0)
    currentOfun.addPoint(minVal + range * 0.9, 0.3)
    currentOfun.addPoint(maxVal, 0.6)
  }
  
  actor.getProperty().setRGBTransferFunction(0, currentCtfun)
  actor.getProperty().setScalarOpacity(0, currentOfun)
  actor.getProperty().setInterpolationTypeToLinear()
  actor.getProperty().setShade(true)
  actor.getProperty().setAmbient(0.2)
  actor.getProperty().setDiffuse(0.7)
  actor.getProperty().setSpecular(0.3)
  actor.getProperty().setSpecularPower(8.0)
  
  renderer.addVolume(actor)
  
  // 2. 设置 Outline (Bounding Box)
  if (props.showOutline) {
    currentOutlineFilter = vtkOutlineFilter.newInstance()
    currentOutlineFilter.setInputData(source)
    
    outlineMapper = vtkMapper.newInstance()
    outlineMapper.setInputConnection(currentOutlineFilter.getOutputPort())
    
    outlineActor = vtkActor.newInstance()
    outlineActor.setMapper(outlineMapper)
    outlineActor.getProperty().setColor(1, 1, 1)  // 白色线框
    outlineActor.getProperty().setOpacity(0.3)
    
    renderer.addActor(outlineActor)
  }

  // 3. 更新 Scalar Bar
  if (props.showScalarBar && scalarBarActor) {
    scalarBarActor.setScalarsToColors(currentCtfun)
    scalarBarActor.setVisibility(true)
    // 确保 Scalar Bar 在最上层
    renderer.removeActor(scalarBarActor)
    renderer.addActor(scalarBarActor)
  }
  
  const camera = renderer.getActiveCamera()
  
  if (isFirstFrame) {
    renderer.resetCamera()
    const bounds = source.getBounds()
    const center = [
      (bounds[0] + bounds[1]) / 2, 
      (bounds[2] + bounds[3]) / 2, 
      (bounds[4] + bounds[5]) / 2
    ]
    
    camera.setFocalPoint(center[0], center[1], center[2])
    // 设置相机距离，让立方体充满视图
    const distance = Math.max(
      bounds[1] - bounds[0], 
      bounds[3] - bounds[2], 
      bounds[5] - bounds[4]
    ) * 2.8
    
    camera.setPosition(
      center[0] + distance * 0.7, 
      center[1] + distance * 0.7, 
      center[2] + distance * 0.7
    )
    camera.setViewUp(0, 0, 1)
    
    initialCameraPosition = camera.getPosition()
    initialCameraFocalPoint = camera.getFocalPoint()
    initialCameraViewUp = camera.getViewUp()
    
    isFirstFrame = false
  }
  // 后续帧保持用户当前相机位置，不做任何重置
  
  renderWindow.render()
}

const togglePlayback = () => {
  isPlaying.value = !isPlaying.value
  isPlaying.value ? startPlayback() : stopPlayback()
}

/**
 * 基于 requestAnimationFrame 的播放控制
 * 避免 setInterval 导致的帧率不稳定和竞态条件
 */
let lastFrameTime = 0

const startPlayback = () => {
  if (playbackTimer) return
  lastFrameTime = performance.now()
  
  const animate = async (currentTime) => {
    if (!isPlaying.value) return
    
    const interval = 1000 / playbackSpeed.value
    const elapsed = currentTime - lastFrameTime
    
    if (elapsed >= interval) {
      // 等待当前帧加载完成再切换下一帧
      if (!isLoadingFrame) {
        if (currentFrameIndex.value < props.timeSeriesFiles.length - 1) {
          currentFrameIndex.value++
          await loadFrame(currentFrameIndex.value, false)
        } else if (loopPlayback.value) {
          currentFrameIndex.value = 0
          await loadFrame(0, false)
        } else {
          stopPlayback()
          isPlaying.value = false
          return
        }
      }
      lastFrameTime = currentTime
    }
    
    playbackTimer = requestAnimationFrame(animate)
  }
  
  playbackTimer = requestAnimationFrame(animate)
}

const stopPlayback = () => {
  if (playbackTimer) {
    cancelAnimationFrame(playbackTimer)
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

/**
 * 完整清理所有VTK资源，防止内存泄漏
 */
const cleanup = () => {
  // 停止播放和取消进行中的请求
  stopPlayback()
  
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  if (preloadAbortController) {
    preloadAbortController.abort()
    preloadAbortController = null
  }
  
  // 清理缓存中的VTK ImageData对象
  frameCache.forEach((imageData) => {
    try {
      imageData.delete()
    } catch (e) {
      // 忽略已删除对象的错误
    }
  })
  frameCache.clear()
  
  cleanupResizeObserver()
  
  // 清理渲染对象
  cleanupRenderObjects()
  
  // 清理 Scalar Bar
  if (scalarBarActor && renderer) {
    renderer.removeActor(scalarBarActor)
    scalarBarActor.delete()
    scalarBarActor = null
  }
  
  // 清理 Orientation Widget
  if (orientationWidget) {
    orientationWidget.setEnabled(false)
    orientationWidget.delete()
    orientationWidget = null
  }
  if (axesActor) {
    axesActor.delete()
    axesActor = null
  }
  
  // 清理交互器
  if (renderWindowInteractor) {
    renderWindowInteractor.unbindEvents()
    renderWindowInteractor.delete()
    renderWindowInteractor = null
  }
  
  // 清理渲染器和窗口
  if (renderer) {
    renderer.delete()
    renderer = null
  }
  if (renderWindow) {
    renderWindow.delete()
    renderWindow = null
  }
  if (openGLRenderWindow) {
    openGLRenderWindow.delete()
    openGLRenderWindow = null
  }
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
