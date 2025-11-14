<template>
  <div class="vtk-timeseries-viewer">
    <!-- 外部控制栏 -->
    <div v-if="!loading && !error" class="external-controls">
      <div class="control-group left">
        <div class="playback-controls">
          <el-button-group>
            <el-button @click="togglePlayback" type="primary">
              <n-icon :component="isPlaying ? PauseOutline : PlayOutline" size="18" />
            </el-button>
            <el-button @click="previousFrame" :disabled="currentFrameIndex === 0">
              <n-icon :component="ChevronBackOutline" size="16" />
            </el-button>
            <el-button @click="nextFrame" :disabled="currentFrameIndex === timeSeriesFiles.length - 1">
              <n-icon :component="ChevronForwardOutline" size="16" />
            </el-button>
          </el-button-group>
        </div>
      </div>
      
      <div class="control-group center">
        <div class="frame-info">
          <span class="current-frame">{{ currentFrameIndex + 1 }} / {{ timeSeriesFiles.length }}</span>
          <span class="physical-time">{{ formatPhysicalTime(currentFrameIndex) }}</span>
        </div>
      </div>
      
      <div class="control-group right">
        <div class="view-controls">
          <el-button @click="resetCamera">
            <n-icon :component="RefreshOutline" size="16" />
            重置
          </el-button>
          <el-button @click="downloadCurrentFrame">
            <n-icon :component="DownloadOutline" size="16" />
            下载
          </el-button>
        </div>
        <div class="file-info">
          <span class="file-size">{{ formatFileSize(currentFileSize) }}</span>
        </div>
      </div>
    </div>

    <!-- VTK渲染区域 -->
    <div class="vtk-viewer-container" ref="viewerContainerRef">
      <div ref="vtkContainerRef" class="vtk-canvas"></div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <n-icon class="is-loading" :component="ReloadOutline" size="40" />
        <p>{{ loadingText }}</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        <n-icon :component="CloseCircleOutline" size="40" />
        <p>{{ error }}</p>
      </div>
    </div>
    
    <!-- 预加载进度 -->
    <div v-if="preloading" class="preload-progress">
      <el-progress 
        :percentage="Math.round(preloadProgress / preloadTotal * 100)" 
        :format="() => `缓存中 ${preloadProgress}/${preloadTotal} 帧`"
      />
    </div>
    
    <!-- 优化的时间轴控制 -->
    <div v-if="!loading && !error && timeSeriesFiles.length > 0" class="timeline-panel">
      <div class="timeline-header">
        <div class="timeline-title">
          <div class="title-icon-wrapper">
            <n-icon :component="TimeOutline" size="20" />
          </div>
          <span class="title-text">时间演化控制</span>
        </div>
        <div class="timeline-settings">
          <div class="speed-control">
            <el-radio-group v-model="playbackSpeed" size="default">
              <el-radio-button :value="0.5">0.5×</el-radio-button>
              <el-radio-button :value="1">1×</el-radio-button>
              <el-radio-button :value="2">2×</el-radio-button>
              <el-radio-button :value="4">4×</el-radio-button>
            </el-radio-group>
          </div>
          <el-checkbox v-model="loopPlayback" class="loop-checkbox">
            <n-icon :component="RefreshOutline" size="16" />
            <span class="checkbox-text">循环</span>
          </el-checkbox>
        </div>
      </div>
      
      <div class="timeline-slider-container">
        <div class="timeline-info">
          <span class="current-step">{{ currentFrameIndex + 1 }} / {{ timeSeriesFiles.length }}</span>
          <span class="physical-time">{{ formatPhysicalTime(currentFrameIndex) }}</span>
        </div>
        <el-slider 
          v-model="currentFrameIndex" 
          :min="0" 
          :max="timeSeriesFiles.length - 1"
          :show-tooltip="true"
          :format-tooltip="formatDetailedTooltipWrapper"
          @change="onFrameChange"
          class="time-slider"
        />
        <div class="timeline-marks">
          <span class="mark start">初始</span>
          <span class="mark middle">演化</span>
          <span class="mark end">稳态</span>
        </div>
      </div>
    </div>
    
    <!-- 优化的色标面板 -->
    <div v-if="!loading && !error && currentDataRange" class="colorbar-panel">
      <div class="colorbar-header">
        <div class="colorbar-title">
          <div class="title-icon-wrapper colorbar-icon">
            <n-icon :component="ColorPaletteOutline" size="20" />
          </div>
          <span class="title-text">Al组分浓度</span>
        </div>
        <el-button text @click="showStats = !showStats" class="stats-toggle">
          <n-icon :component="showStats ? EyeOffOutline : BarChartOutline" size="16" />
          <span class="toggle-text">{{ showStats ? '隐藏' : '统计' }}</span>
        </el-button>
      </div>
      <div class="colorbar-container">
        <div class="colorbar-gradient"></div>
        <div class="colorbar-labels">
          <div class="colorbar-label">
            <div class="color-indicator blue"></div>
            <div class="value-group">
              <span class="value">{{ currentDataRange.min.toFixed(3) }}</span>
              <span class="phase-label">富Ti相</span>
            </div>
          </div>
          <div class="colorbar-label center">
            <div class="color-indicator green"></div>
            <div class="value-group">
              <span class="value">{{ currentDataRange.mid.toFixed(3) }}</span>
              <span class="phase-label">相界面</span>
            </div>
          </div>
          <div class="colorbar-label">
            <div class="color-indicator red"></div>
            <div class="value-group">
              <span class="value">{{ currentDataRange.max.toFixed(3) }}</span>
              <span class="phase-label">富Al相</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <transition name="slide-down">
        <div v-if="showStats && phaseStats" class="stats-panel">
          <div class="stats-header">
            <div class="stats-icon-wrapper">
              <n-icon :component="BarChartOutline" size="18" />
            </div>
            <span class="stats-title">相场统计信息</span>
          </div>
          <div class="stats-content">
            <div class="stat-row">
              <div class="stat-item primary">
                <div class="stat-icon">
                  <n-icon :component="TrendingUpOutline" size="20" />
                </div>
                <div class="stat-data">
                  <span class="stat-value">{{ (currentDataRange.max - currentDataRange.min).toFixed(4) }}</span>
                  <span class="stat-label">浓度范围</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">
                  <n-icon :component="TimeOutline" size="20" />
                </div>
                <div class="stat-data">
                  <span class="stat-value">{{ formatPhysicalTime(currentFrameIndex) }}</span>
                  <span class="stat-label">物理时间</span>
                </div>
              </div>
            </div>
            <div class="stat-row">
              <div class="stat-item">
                <div class="stat-icon">
                  <n-icon :component="GridOutline" size="20" />
                </div>
                <div class="stat-data">
                  <span class="stat-value">{{ formatGridSize(phaseStats.totalPoints) }}</span>
                  <span class="stat-label">网格尺寸</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">
                  <n-icon :component="LayersOutline" size="20" />
                </div>
                <div class="stat-data">
                  <span class="stat-value">{{ calculateDepth(currentFrameIndex) }}</span>
                  <span class="stat-label">沉积厚度</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { NIcon } from 'naive-ui'
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
import { API_BASE_URL } from '../config'

// 导入composables
import { useResizeObserver } from '../composables/useResizeObserver'
import { 
  formatTooltip, 
  formatDetailedTooltip, 
  formatPhysicalTime, 
  formatGridSize, 
  calculateDepth, 
  formatFileSize 
} from '../composables/useVtkTimeSeriesHelpers'

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
    console.log('[VTK时间序列] 开始初始化渲染器（使用低级API）')
    
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
        console.log('[VTK时间序列] 渲染窗口初始化完成:', width, 'x', height)
      }
    })
    
    console.log('[VTK时间序列] 低级API渲染器初始化成功，无额外UI元素')
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
  
  console.log('[VTK时间序列] 开始预加载', preloadTotal.value, '帧')
  
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
        console.log(`[VTK时间序列] 预加载进度: ${preloadProgress.value}/${preloadTotal.value}`)
      }
    } catch (err) {
      console.error(`[VTK时间序列] 预加载帧 ${i} 失败:`, err)
      preloadProgress.value++
    }
  }
  
  preloading.value = false
  console.log('[VTK时间序列] 预加载完成')
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
    console.log('[VTK时间序列] 使用缓存:', fileName)
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
    currentFileSize.value = vtkText.length
    
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
  
  console.log('[VTK解析] 维度:', dimensions, '数据点数:', scalarData.length, '预期:', dimensions[0] * dimensions[1] * dimensions[2])
  
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
  
  console.log('[VTK解析] ImageData创建成功')
  
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
  
  console.log('[VTK时间序列] 数据范围:', dataRange, '点数:', dataArray.getNumberOfTuples())
  
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
    console.log('[VTK时间序列] 初始状态 - 强化扰动对比度')
    ofun.addPoint(minVal, 0.35)                         // 低值区域
    ofun.addPoint(minVal + range * 0.25, 0.65)         
    ofun.addPoint(minVal + range * 0.5, 0.9)           // 平均值峰值提升
    ofun.addPoint(minVal + range * 0.75, 0.65)         
    ofun.addPoint(maxVal, 0.35)                         // 高值区域
  } else {
    // 相分离状态：两相高不透明，界面窄且半透明
    console.log('[VTK时间序列] 相分离状态 - 突出两相体积')
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
    console.log('[VTK时间序列] 初始相机设置:', {
      center: center,
      position: initialCameraPosition,
      focalPoint: initialCameraFocalPoint
    })
  } else {
    // 后续帧：使用保存的相机状态
    if (initialCameraPosition && initialCameraFocalPoint && initialCameraViewUp) {
      camera.setPosition(...initialCameraPosition)
      camera.setFocalPoint(...initialCameraFocalPoint)
      camera.setViewUp(...initialCameraViewUp)
    }
  }
  
  renderWindow.render()
  
  
  console.log('[VTK时间序列] 渲染完成，帧索引:', currentFrameIndex.value)
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
    
    console.log('[VTK时间序列] 相机已重置并保存新状态')
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
  console.log('[VTK时间序列] 开始清理资源')
  
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
    
    console.log('[VTK时间序列] VTK资源已清理')
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
  
  console.log('[VTK时间序列] 资源清理完成')
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
  gap: 16px;
}

.vtk-viewer-container {
  position: relative;
  width: 100%;
  height: 500px; /* 默认高度 */
  min-height: 400px;
  max-height: 80vh; /* 最大不超过视口的80% */
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  resize: vertical; /* 允许垂直方向调整大小 */
}

/* 调整大小手柄样式 */
.vtk-viewer-container::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  background: linear-gradient(-45deg, 
    transparent 0%, 
    transparent 30%, 
    #666 30%, 
    #666 35%, 
    transparent 35%, 
    transparent 65%,
    #666 65%,
    #666 70%,
    transparent 70%
  );
  cursor: ns-resize;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.vtk-viewer-container:hover::after {
  opacity: 1;
}

.vtk-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

/* VTK基本样式 */
.vtk-canvas :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  z-index: 10;
}

.loading-overlay p {
  margin-top: 12px;
  font-size: 14px;
}

.error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #f56c6c;
  text-align: center;
  padding: 20px;
  z-index: 10;
}

.error-message p {
  margin-top: 12px;
  font-size: 14px;
}

.controls {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
}

.time-info {
  display: flex;
  gap: 12px;
  color: #fff;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 12px;
  border-radius: 4px;
}

.file-size {
  color: #67c23a;
}

/* 预加载进度 */
.preload-progress {
  margin-top: 16px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(103, 194, 58, 0.1) 0%, rgba(103, 194, 58, 0.05) 100%);
  border-radius: 8px;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.preload-progress :deep(.el-progress__text) {
  color: #67c23a !important;
  font-weight: 600;
}

/* 时间轴控制 */
.timeline-controls {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.timeline-slider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.timeline-label,
.control-label {
  color: #fff;
  font-size: 14px;
  white-space: nowrap;
}

.timeline-value {
  color: #67c23a;
  font-size: 14px;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}

.el-slider {
  flex: 1;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Element Plus 按钮组样式调整 */
:deep(.el-button-group) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* Colorbar面板 */
.colorbar-panel {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(40, 40, 40, 0.95) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.colorbar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.colorbar-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.colorbar-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.colorbar-gradient {
  height: 20px;
  border-radius: 4px;
  background: linear-gradient(
    to right,
    rgb(0, 0, 255) 0%,
    rgb(0, 128, 255) 25%,
    rgb(0, 255, 0) 50%,
    rgb(255, 128, 0) 75%,
    rgb(255, 0, 0) 100%
  );
  box-shadow: 0 2px 8px rgba(0, 255, 0, 0.3);
}

.colorbar-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.colorbar-label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  font-size: 12px;
  color: #e0e0e0;
}

.colorbar-label.center {
  align-items: center;
}

.colorbar-label:last-child {
  align-items: flex-end;
}

.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.color-dot.blue {
  background: rgb(0, 0, 255);
}

.color-dot.green {
  background: rgb(0, 255, 0);
}

.color-dot.red {
  background: rgb(255, 0, 0);
}

.phase-label {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

/* 统计面板 */
.stats-panel {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: #999;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
}

/* 滑动动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
}

.slide-down-enter-to,
.slide-down-leave-from {
  max-height: 200px;
  opacity: 1;
}

/* 外部控制栏样式 */
.external-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--el-border-color-lighter);
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group.left {
  flex: 0 0 auto;
}

.control-group.center {
  flex: 1;
  justify-content: center;
}

.control-group.right {
  flex: 0 0 auto;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.frame-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.current-frame {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-primary);
  padding: 4px 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
  border: 1px solid var(--el-color-primary-light-7);
}

.frame-info .physical-time {
  font-size: 14px;
  color: #00d4aa;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(0, 212, 170, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(0, 212, 170, 0.3);
}

.view-controls {
  display: flex;
  gap: 8px;
}

.file-info .file-size {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.external-controls .playback-controls,
.external-controls .view-controls {
  background: white;
  border-radius: 8px;
  padding: 4px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 重置按钮组样式 */
.playback-controls :deep(.el-button-group) {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: none;
  border: none;
}

.external-controls .playback-controls :deep(.el-button),
.external-controls .view-controls :deep(.el-button) {
  min-width: 36px !important;
  height: 32px !important;
  padding: 0 8px !important;
  border: none !important;
  background: transparent !important;
  color: var(--el-text-color-primary) !important;
  border-radius: 6px !important;
  transition: all 0.2s ease !important;
  margin: 0 1px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.external-controls .playback-controls :deep(.el-button:hover),
.external-controls .view-controls :deep(.el-button:hover) {
  background: var(--el-color-primary-light-9) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.playback-controls :deep(.el-button--primary) {
  background: var(--el-color-primary) !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3) !important;
}

.playback-controls :deep(.el-button--primary:hover) {
  background: var(--el-color-primary-light-3) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4) !important;
}

.playback-controls :deep(.el-button:disabled),
.view-controls :deep(.el-button:disabled) {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
  transform: none !important;
}

.playback-controls :deep(.el-button:first-child) {
  border-top-left-radius: 6px !important;
  border-bottom-left-radius: 6px !important;
  margin-left: 0 !important;
}

.playback-controls :deep(.el-button:last-child) {
  border-top-right-radius: 6px !important;
  border-bottom-right-radius: 6px !important;
  margin-right: 0 !important;
}

/* 时间信息浮层样式已移动到外部控制栏 */

/* 时间轴面板 */
.timeline-panel {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(10px);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.timeline-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
  border-radius: 10px;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.title-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.5px;
}

.timeline-settings {
  display: flex;
  align-items: center;
  gap: 20px;
}

.speed-control :deep(.el-radio-group) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.loop-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-color-info-light-9);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.checkbox-text {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.timeline-slider-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  margin-bottom: 12px;
}

.current-step {
  font-weight: 700;
  color: var(--el-color-primary);
  font-size: 15px;
  padding: 4px 8px;
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
  border: 1px solid var(--el-color-primary-light-7);
}

.physical-time {
  color: #00d4aa;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600;
  font-size: 15px;
  padding: 4px 8px;
  background: rgba(0, 212, 170, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(0, 212, 170, 0.3);
}

.time-slider :deep(.el-slider__runway) {
  height: 6px;
  background: var(--el-color-info-light-8);
}

.time-slider :deep(.el-slider__bar) {
  background: linear-gradient(90deg, var(--el-color-primary), var(--el-color-success));
  height: 6px;
}

.timeline-marks {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

/* 优化色标面板 */
.colorbar-panel {
  background: linear-gradient(135deg, #ffffff 0%, #fff8f0 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(10px);
}

.colorbar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.colorbar-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.colorbar-icon {
  background: linear-gradient(135deg, #ff6b6b, #ffa500) !important;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3) !important;
}

.stats-toggle {
  color: var(--el-color-primary);
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  font-weight: 500;
  transition: all 0.2s ease;
}

.stats-toggle:hover {
  background: var(--el-color-primary-light-8);
  transform: translateY(-1px);
}

.toggle-text {
  margin-left: 6px;
}

.color-indicator {
  width: 16px;
  height: 16px;
  border-radius: 8px;
  border: 3px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.color-indicator.blue { 
  background: linear-gradient(135deg, rgb(0, 100, 255), rgb(0, 150, 255));
}
.color-indicator.green { 
  background: linear-gradient(135deg, rgb(0, 200, 100), rgb(50, 255, 150));
}
.color-indicator.red { 
  background: linear-gradient(135deg, rgb(255, 80, 80), rgb(255, 120, 120));
}

.value-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.value {
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.phase-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  background: linear-gradient(135deg, var(--el-color-info-light-8), var(--el-color-info-light-9));
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 500;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 统计信息面板 */
.stats-panel {
  margin-top: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.stats-icon-wrapper {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--el-color-success), var(--el-color-success-light-3));
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.3);
}

.stats-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.3px;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-row {
  display: flex;
  gap: 16px;
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.stat-item.primary {
  border-color: var(--el-color-primary);
  background: linear-gradient(135deg, var(--el-color-primary-light-9), #ffffff);
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary-light-8);
  border-radius: 10px;
  color: var(--el-color-primary);
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.2);
}

.stat-item.primary .stat-icon {
  background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

.stat-data {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .controls-overlay {
    flex-direction: column;
    gap: 8px;
  }
  
  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .stat-row {
    flex-direction: column;
  }
  
  .colorbar-labels {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
