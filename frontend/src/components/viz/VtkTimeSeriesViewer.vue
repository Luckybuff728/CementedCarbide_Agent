<template>
  <div class="vtk-timeseries-viewer">
    <!-- 1. 主视图区域 (包含悬浮层) -->
    <div class="viewer-wrapper" ref="viewerContainerRef">
      <!-- VTK Canvas -->
      <div ref="vtkContainerRef" class="vtk-canvas"></div>
      
      <!-- 顶部悬浮层: 文件信息与视图控制 -->
      <div v-if="!loading && !error" class="viewer-overlay-top">
        <div class="file-info-badge">
          <span class="frame-count">{{ currentFrameIndex + 1 }} / {{ timeSeriesFiles.length }}</span>
          <span class="separator">|</span>
          <span class="physical-time">{{ formatPhysicalTime(currentFrameIndex) }}</span>
          <span class="separator">|</span>
          <span class="file-size">{{ formatFileSize(currentFileSize) }}</span>
        </div>
        
        <div class="view-actions">
          <el-tooltip content="重置视角" placement="bottom" :show-after="500">
            <div class="action-btn" @click="resetCamera">
              <el-icon><RefreshOutline /></el-icon>
            </div>
          </el-tooltip>
          <el-tooltip content="下载当前帧" placement="bottom" :show-after="500">
            <div class="action-btn" @click="downloadCurrentFrame">
              <el-icon><DownloadOutline /></el-icon>
            </div>
          </el-tooltip>
        </div>
      </div>
      
      <!-- 统计信息悬浮层 (右上角) -->
      <transition name="fade">
        <div v-if="showStats && phaseStats && !loading" class="stats-overlay">
          <div class="stats-row">
            <div class="stat-item">
              <span class="label">浓度范围</span>
              <span class="value">{{ (currentDataRange?.max - currentDataRange?.min).toFixed(3) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">网格</span>
              <span class="value">{{ formatGridSize(phaseStats.totalPoints) }}</span>
            </div>
          </div>
        </div>
      </transition>

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
      
      <!-- 预加载进度条 (底部) -->
      <div v-if="preloading" class="preload-bar">
        <div class="bar-inner" :style="{ width: `${(preloadProgress / preloadTotal) * 100}%` }"></div>
      </div>
    </div>

    <!-- 2. 统一控制栏 (下方) -->
    <div v-if="!loading && !error && timeSeriesFiles.length > 0" class="unified-controls">
      <!-- 时间轴滑块 -->
      <div class="timeline-slider-section">
        <el-slider 
          v-model="currentFrameIndex" 
          :min="0" 
          :max="timeSeriesFiles.length - 1"
          :show-tooltip="true"
          :format-tooltip="formatDetailedTooltipWrapper"
          @change="onFrameChange"
          class="compact-slider"
        />
      </div>
      
      <!-- 控制行 -->
      <div class="control-row">
        <!-- 左侧: 播放控制 -->
        <div class="playback-section">
          <div class="icon-btn primary" @click="togglePlayback">
            <el-icon size="18"><component :is="isPlaying ? PauseOutline : PlayOutline" /></el-icon>
          </div>
          <div class="icon-btn" @click="previousFrame" :class="{ disabled: currentFrameIndex === 0 }">
            <el-icon size="16"><ChevronBackOutline /></el-icon>
          </div>
          <div class="icon-btn" @click="nextFrame" :class="{ disabled: currentFrameIndex === timeSeriesFiles.length - 1 }">
            <el-icon size="16"><ChevronForwardOutline /></el-icon>
          </div>
          
          <div class="divider"></div>
          
          <el-dropdown trigger="click" @command="(val) => playbackSpeed = val">
            <span class="speed-trigger">
              {{ playbackSpeed }}×
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="0.5">0.5×</el-dropdown-item>
                <el-dropdown-item :command="1">1.0×</el-dropdown-item>
                <el-dropdown-item :command="2">2.0×</el-dropdown-item>
                <el-dropdown-item :command="4">4.0×</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <div class="loop-toggle" :class="{ active: loopPlayback }" @click="loopPlayback = !loopPlayback" title="循环播放">
            <el-icon><RefreshOutline /></el-icon>
          </div>
        </div>
        
        <!-- 右侧: 色标与显示控制 -->
        <div class="legend-section" v-if="currentDataRange">
          <div class="colorbar-mini">
            <div class="gradient-bar"></div>
            <div class="labels">
              <span class="label min">{{ currentDataRange.min.toFixed(2) }}</span>
              <span class="label max">{{ currentDataRange.max.toFixed(2) }}</span>
            </div>
          </div>
          
          <div class="divider"></div>
          
          <div class="icon-btn" :class="{ active: showStats }" @click="showStats = !showStats" title="显示统计">
            <el-icon size="16"><BarChartOutline /></el-icon>
          </div>
        </div>
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
  ChevronBackOutline,
  ChevronForwardOutline,
  RefreshOutline,
  DownloadOutline,
  CloseCircleOutline,
  TimeOutline,
  ColorPaletteOutline,
  EyeOffOutline,
  BarChartOutline,
  TrendingUpOutline,
  GridOutline,
  LayersOutline
} from '@vicons/ionicons5'
import { API_BASE_URL } from '../../config'

// 导入composables
import { useResizeObserver } from '../../composables/useResizeObserver'
import { 
  formatTooltip, 
  formatDetailedTooltip, 
  formatPhysicalTime, 
  formatGridSize, 
  calculateDepth, 
  formatFileSize 
} from '../../composables/useVtkTimeSeriesHelpers'

// VTK.js 导入 - 使用低级API避免黑线
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
    // 格式: [{ name: 'conc-0.vtk', timeStep: 0 }, ...]
  },
  // API基础URL - 从配置文件读取
  baseUrl: {
    type: String,
    default: API_BASE_URL
  },
  // 容器高度
  height: {
    type: String,
    default: '500px'
  },
  // 自动播放
  autoPlay: {
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
const currentTimeStep = computed(() => {
  if (props.timeSeriesFiles.length > 0 && currentFrameIndex.value < props.timeSeriesFiles.length) {
    return props.timeSeriesFiles[currentFrameIndex.value]?.timeStep || currentFrameIndex.value + 1
  }
  return 0
})
const currentFileSize = computed(() => {
  if (props.timeSeriesFiles.length > 0 && currentFrameIndex.value < props.timeSeriesFiles.length) {
    // 直接使用后端 timeseries 接口返回的 size 字段，避免在前端写入 computed
    return props.timeSeriesFiles[currentFrameIndex.value]?.size || 0
  }
  return 0
})

// UI状态
const showStats = ref(false)

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
  if (!vtkContainerRef.value) {
    console.warn('[VTK时间序列] 容器ref不存在，跳过初始化')
    return
  }
  
  // 检查容器是否在DOM中
  if (!vtkContainerRef.value.isConnected) {
    console.warn('[VTK时间序列] 容器未连接到DOM，跳过初始化')
    return
  }
  
  try {
    // 1. 创建OpenGL渲染窗口
    openGLRenderWindow = vtkOpenGLRenderWindow.newInstance()
    openGLRenderWindow.setContainer(vtkContainerRef.value)
    
    // 获取容器尺寸
    const rect = vtkContainerRef.value.getBoundingClientRect()
    const width = Math.floor(rect.width)
    const height = Math.floor(rect.height)
    openGLRenderWindow.setSize(width, height)
    
    // 2. 创建渲染窗口
    renderWindow = vtkRenderWindow.newInstance()
    renderWindow.addView(openGLRenderWindow)
    
    // 3. 创建渲染器
    renderer = vtkRenderer.newInstance()
    renderer.setBackground(0.1, 0.1, 0.1)  // 深色背景
    renderWindow.addRenderer(renderer)
    
    // 4. 创建交互器
    renderWindowInteractor = vtkRenderWindowInteractor.newInstance()
    renderWindowInteractor.setView(openGLRenderWindow)
    renderWindowInteractor.initialize()
    
    // 5. 设置交互样式（TrackballCamera）
    const interactorStyle = vtkInteractorStyleTrackballCamera.newInstance()
    renderWindowInteractor.setInteractorStyle(interactorStyle)
    
    // 6. 绑定交互器到渲染窗口
    renderWindowInteractor.bindEvents(vtkContainerRef.value)
    
    // 7. 设置窗口大小变化监听
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
    
    // 跳过已缓存的帧
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
  ElMessage.success(`已缓存 ${frameCache.size} 帧，播放将更流畅`)
}

/**
 * 加载指定帧的VTK文件
 */
const loadFrame = async (frameIndex, showLoading = true) => {
  if (frameIndex < 0 || frameIndex >= props.timeSeriesFiles.length) {
    return
  }
  
  const fileInfo = props.timeSeriesFiles[frameIndex]
  const fileName = fileInfo.name
  
  // 检查缓存
  if (frameCache.has(fileName)) {
    renderFrame(frameCache.get(fileName))
    currentFrameIndex.value = frameIndex
    return
  }
  
  // 播放时不显示loading，避免卡顿
  if (showLoading) {
    loading.value = true
    loadingText.value = `加载帧 ${frameIndex + 1}/${props.timeSeriesFiles.length}...`
  }
  error.value = null
  
  try {
    const vtkUrl = `${API_BASE_URL}/api/vtk/files/${fileName}`
    
    // 使用fetch直接获取VTK文件内容
    const response = await fetch(vtkUrl)
    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }
    
    const vtkText = await response.text()
    
    // 解析VTK Legacy格式
    const source = parseLegacyVTK(vtkText)
    
    // 缓存数据
    frameCache.set(fileName, source)
    
    // 渲染
    renderFrame(source)
    currentFrameIndex.value = frameIndex
    
    if (showLoading) {
      loading.value = false
    }
    
  } catch (err) {
    console.error('[VTK时间序列] 加载失败:', err)
    error.value = `加载失败: ${err.message}`
    if (showLoading) {
      loading.value = false
    }
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
  
  // 解析头部
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
      // ASPECT_RATIO需要转换为合适的spacing
      // 对于64x64x64的网格，使用合理的物理尺寸
      const parts = line.split(/\s+/)
      const ratio = [parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]
      // 将ASPECT_RATIO转换为spacing（假设总长度为64单位）
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
  
  // 提取标量数据
  const scalarData = []
  for (let i = pointDataIndex; i < lines.length; i++) {
    const line = lines[i].trim()
    if (line && !line.startsWith('#')) {
      const values = line.split(/\s+/)
      for (let j = 0; j < values.length; j++) {
        const val = parseFloat(values[j])
        if (!isNaN(val)) {
          scalarData.push(val)
        }
      }
    }
  }
  
  if (scalarData.length === 0) {
    console.error('[VTK解析] 没有解析到任何数据！pointDataIndex:', pointDataIndex)
    throw new Error('VTK文件中没有找到数据')
  }
  
  // 创建vtkImageData
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
  if (!renderer || !renderWindow) {
    console.error('[VTK时间序列] 渲染器未初始化')
    return
  }
  
  // 清除之前的actor
  if (actor) {
    renderer.removeVolume(actor)
  }
  
  // 创建新的体渲染
  mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(source)
  mapper.setSampleDistance(0.4)  // 降低采样距离以提高清晰度和一致性
  
  actor = vtkVolume.newInstance()
  actor.setMapper(mapper)
  
  // 获取数据范围
  const dataArray = source.getPointData().getScalars()
  const dataRange = dataArray.getRange()
  const [minVal, maxVal] = dataRange
  const range = maxVal - minVal
  const midVal = minVal + range * 0.5
  
  // 更新当前数据范围（用于colorbar显示）
  currentDataRange.value = {
    min: minVal,
    mid: midVal,
    max: maxVal
  }
  
  // 更新统计信息
  phaseStats.value = {
    totalPoints: dataArray.getNumberOfTuples(),
    dataRange: range
  }
  
  // 颜色传输函数 - 使用固定的颜色映射确保一致性
  const ctfun = vtkColorTransferFunction.newInstance()
  ctfun.addRGBPoint(minVal, 0.0, 0.0, 1.0)                     // 蓝色（低值）
  ctfun.addRGBPoint(minVal + range * 0.5, 0.0, 1.0, 0.0)      // 绿色（中值）
  ctfun.addRGBPoint(maxVal, 1.0, 0.0, 0.0)                     // 红色（高值）
  
  // 不透明度传输函数 - 自适应：根据数据分布调整
  const ofun = vtkPiecewiseFunction.newInstance()
  
  // 判断数据分布类型（更精确的阈值）
  const isEarlyStage = range < 0.025  // 降低阈值，更准确识别初始状态
  
  if (isEarlyStage) {
    // 初始状态：强化对比度以清晰显示微小扰动
    ofun.addPoint(minVal, 0.35)                         // 低值区域
    ofun.addPoint(minVal + range * 0.25, 0.65)         
    ofun.addPoint(minVal + range * 0.5, 0.9)           // 平均值峰值提升
    ofun.addPoint(minVal + range * 0.75, 0.65)         
    ofun.addPoint(maxVal, 0.35)                         // 高值区域
  } else {
    // 相分离状态：两相高不透明，界面窄且半透明
    ofun.addPoint(minVal, 0.8)                          // α相高不透明
    ofun.addPoint(minVal + range * 0.47, 0.75)         // 接近界面
    ofun.addPoint(minVal + range * 0.5, 0.25)          // 界面更窄更透明
    ofun.addPoint(minVal + range * 0.53, 0.75)         // 离开界面
    ofun.addPoint(maxVal, 0.8)                          // β相高不透明
  }
  
  actor.getProperty().setRGBTransferFunction(0, ctfun)
  actor.getProperty().setScalarOpacity(0, ofun)
  actor.getProperty().setInterpolationTypeToLinear()
  actor.getProperty().setShade(true)
  actor.getProperty().setAmbient(0.3)
  actor.getProperty().setDiffuse(0.7)      // 增加漫反射，减少高光依赖
  actor.getProperty().setSpecular(0.2)     // 降低镜面反射强度
  actor.getProperty().setSpecularPower(8)  // 降低高光锐度
  
  renderer.addVolume(actor)
  
  // 相机管理：第一帧重置并保存，后续帧使用保存的视角
  const camera = renderer.getActiveCamera()
  
  if (isFirstFrame) {
    // 第一帧：重置相机并优化位置以居中显示
    renderer.resetCamera()
    
    // 调整相机位置，确保从合适的角度观察
    const bounds = source.getBounds()
    const center = [
      (bounds[0] + bounds[1]) / 2,
      (bounds[2] + bounds[3]) / 2,
      (bounds[4] + bounds[5]) / 2
    ]
    
    // 设置相机焦点为数据中心
    camera.setFocalPoint(center[0], center[1], center[2])
    
    // 设置相机位置（从斜上方观察，距离调大以显示完整模型）
    const distance = Math.max(
      bounds[1] - bounds[0],
      bounds[3] - bounds[2],
      bounds[5] - bounds[4]
    ) * 3.8  // 从2.5增加到3.5，相机拉远
    
    camera.setPosition(
      center[0] + distance * 0.8,  // 从0.7增加到0.8
      center[1] + distance * 0.8,  // 从0.7增加到0.8
      center[2] + distance * 0.8   // 从0.7增加到0.8
    )
    
    // 设置向上方向
    camera.setViewUp(0, 0, 1)
    
    // 保存相机参数
    initialCameraPosition = camera.getPosition()
    initialCameraFocalPoint = camera.getFocalPoint()
    initialCameraViewUp = camera.getViewUp()
    
    isFirstFrame = false
  } else {
    // 后续帧：使用保存的相机状态
    if (initialCameraPosition && initialCameraFocalPoint && initialCameraViewUp) {
      camera.setPosition(...initialCameraPosition)
      camera.setFocalPoint(...initialCameraFocalPoint)
      camera.setViewUp(...initialCameraViewUp)
    }
  }
  
  renderWindow.render()
}

/**
 * 播放/暂停
 */
const togglePlayback = () => {
  isPlaying.value = !isPlaying.value
  
  if (isPlaying.value) {
    startPlayback()
  } else {
    stopPlayback()
  }
}

/**
 * 开始播放
 */
const startPlayback = () => {
  if (playbackTimer) return
  
  const interval = 1000 / playbackSpeed.value  // 根据速度计算间隔
  
  playbackTimer = setInterval(() => {
    if (currentFrameIndex.value < props.timeSeriesFiles.length - 1) {
      currentFrameIndex.value++
      loadFrame(currentFrameIndex.value, false)  // 播放时不显示loading
    } else {
      // 到达最后一帧
      if (loopPlayback.value) {
        currentFrameIndex.value = 0
        loadFrame(0, false)  // 播放时不显示loading
      } else {
        stopPlayback()
        isPlaying.value = false
      }
    }
  }, interval)
}

/**
 * 停止播放
 */
const stopPlayback = () => {
  if (playbackTimer) {
    clearInterval(playbackTimer)
    playbackTimer = null
  }
}

/**
 * 上一帧
 */
const previousFrame = () => {
  if (currentFrameIndex.value > 0) {
    stopPlayback()
    isPlaying.value = false
    currentFrameIndex.value--
    loadFrame(currentFrameIndex.value)
  }
}

/**
 * 下一帧
 */
const nextFrame = () => {
  if (currentFrameIndex.value < props.timeSeriesFiles.length - 1) {
    stopPlayback()
    isPlaying.value = false
    currentFrameIndex.value++
    loadFrame(currentFrameIndex.value)
  }
}

/**
 * 帧变化
 */
const onFrameChange = (value) => {
  stopPlayback()
  isPlaying.value = false
  loadFrame(value)
}

/**
 * 重置相机 - 用户手动触发
 */
const resetCamera = () => {
  if (renderer && renderWindow) {
    const camera = renderer.getActiveCamera()
    renderer.resetCamera()
    
    // 重新保存相机状态
    initialCameraPosition = camera.getPosition()
    initialCameraFocalPoint = camera.getFocalPoint()
    initialCameraViewUp = camera.getViewUp()
    
    renderWindow.render()
  }
}

/**
 * 下载当前帧
 */
const downloadCurrentFrame = () => {
  const fileInfo = props.timeSeriesFiles[currentFrameIndex.value]
  if (fileInfo) {
    const url = `${API_BASE_URL}/api/vtk/files/${fileInfo.name}`
    window.open(url, '_blank')
  }
}

/**
 * 格式化文件大小
 */
// formatFileSize 已从composables导入

// 工具函数（使用composables）
const formatTooltipWrapper = (value) => formatTooltip(value, props.timeSeriesFiles)
const formatDetailedTooltipWrapper = (value) => formatDetailedTooltip(value, props.timeSeriesFiles)

/**
 * 清理
 */
const cleanup = () => {
  // 停止播放
  stopPlayback()
  
  // 清空缓存
  frameCache.clear()
  
  // 清理VTK资源
  try {
    // 清理actor
    if (actor && renderer) {
      renderer.removeVolume(actor)
      actor.delete()
    }
    
    // 清理mapper
    if (mapper) {
      mapper.delete()
    }
    
    // 清理交互器
    if (renderWindowInteractor) {
      renderWindowInteractor.unbindEvents()
      renderWindowInteractor.delete()
    }
    
    // 清理渲染器
    if (renderer) {
      renderer.delete()
    }
    
    // 清理渲染窗口
    if (renderWindow) {
      renderWindow.delete()
    }
    
    // 清理OpenGL窗口
    if (openGLRenderWindow) {
      openGLRenderWindow.delete()
    }
  } catch (err) {
    console.error('[VTK时间序列] 清理VTK资源失败:', err)
  }
  
  // 清理ResizeObserver
  cleanupResizeObserver()
  
  // 清空引用
  openGLRenderWindow = null
  renderer = null
  renderWindow = null
  renderWindowInteractor = null
  actor = null
  mapper = null
}

// 监听播放速度变化
watch(playbackSpeed, () => {
  if (isPlaying.value) {
    stopPlayback()
    startPlayback()
  }
})

// 组件挂载
onMounted(() => {
  initRenderer()
  if (props.timeSeriesFiles.length > 0) {
    setTimeout(() => {
      // 先加载并显示第一帧
      loadFrame(0).then(() => {
        // 第一帧加载完成后，开始后台预加载所有帧
        setTimeout(() => {
          preloadAllFrames()
        }, 500)
      })
      
      if (props.autoPlay) {
        // 延迟播放，等预加载几帧后再开始
        setTimeout(() => {
          togglePlayback()
        }, 2000)
      }
    }, 100)
  }
})

// 组件卸载
onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.vtk-timeseries-viewer {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  background: white;
}

/* 1. 视图区域 */
.viewer-wrapper {
  position: relative;
  width: 100%;
  height: 380px; /* 固定高度 */
  background: #1a1a1a;
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

/* 顶部悬浮层 */
.viewer-overlay-top {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  z-index: 10;
  pointer-events: none; /* 让点击穿透到canvas */
}

.file-info-badge {
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  padding: 8px 14px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.95);
  font-size: 13px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  border: 1px solid rgba(255, 255, 255, 0.15);
  pointer-events: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.file-info-badge .separator {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.file-info-badge .frame-count {
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}

.file-info-badge .physical-time {
  color: #4ade80;
  font-weight: 600;
}

.file-info-badge .file-size {
  color: rgba(255, 255, 255, 0.85);
}

.view-actions {
  display: flex;
  gap: 8px;
  pointer-events: auto;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.action-btn .el-icon {
  font-size: 18px;
}

/* 统计悬浮层 */
.stats-overlay {
  position: absolute;
  top: 56px;
  right: 12px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  z-index: 9;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.stats-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stats-overlay .stat-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 13px;
}

.stats-overlay .label {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.stats-overlay .value {
  color: #fff;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600;
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
  z-index: 20;
}

.loading-overlay p, .error-message p {
  margin-top: 16px;
  font-size: 15px;
  font-weight: 500;
}

.error-message {
  color: #f56c6c;
}

.loading-overlay .el-icon {
  font-size: 36px;
}

.error-message .el-icon {
  font-size: 36px;
}

/* 预加载条 */
.preload-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
  z-index: 10;
}

.preload-bar .bar-inner {
  height: 100%;
  background: #67c23a;
  transition: width 0.3s;
}

/* 2. 统一控制栏 */
.unified-controls {
  padding: 8px 12px;
  background: #fff;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 时间轴滑块 */
.timeline-slider-section {
  padding: 0 4px;
}

.compact-slider {
  margin-bottom: 0 !important;
}

.compact-slider :deep(.el-slider__runway) {
  margin: 8px 0;
  height: 4px;
}

.compact-slider :deep(.el-slider__button) {
  width: 12px;
  height: 12px;
}

/* 控制行 */
.control-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.playback-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 通用图标按钮 */
.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.icon-btn:hover {
  background: #f5f7fa;
  color: var(--el-color-primary);
  transform: translateY(-1px);
  border-color: var(--el-color-primary-light-7);
}

.icon-btn.primary {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  font-weight: 600;
  border-color: var(--el-color-primary-light-7);
}

.icon-btn.primary:hover {
  background: var(--el-color-primary-light-8);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.icon-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.icon-btn.disabled:hover {
  transform: none;
  background: transparent;
  border-color: transparent;
}

.icon-btn.active {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-6);
}

.divider {
  width: 1px;
  height: 16px;
  background: #dcdfe6;
  margin: 0 4px;
}

/* 速度控制 */
.speed-trigger {
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  font-weight: 600;
  border: 1px solid #e4e7ed;
  transition: all 0.2s;
  min-width: 45px;
  text-align: center;
}

.speed-trigger:hover {
  background: #f5f7fa;
  border-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
}

/* 循环按钮 */
.loop-toggle {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: #909399;
  cursor: pointer;
  transition: all 0.2s;
}

.loop-toggle:hover {
  color: #606266;
}

.loop-toggle.active {
  color: var(--el-color-primary);
}

/* 迷你色标 */
.colorbar-mini {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 140px;
}

.gradient-bar {
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, rgb(0, 0, 255), rgb(0, 255, 0), rgb(255, 0, 0));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.colorbar-mini .labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #606266;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600;
}

.colorbar-mini .labels .label {
  padding: 2px 4px;
  background: #f5f7fa;
  border-radius: 3px;
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
