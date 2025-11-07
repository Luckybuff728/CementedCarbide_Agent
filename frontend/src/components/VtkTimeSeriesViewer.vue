<template>
  <div class="vtk-timeseries-viewer">
    <!-- VTK渲染区域 -->
    <div class="vtk-viewer-container">
      <div ref="vtkContainerRef" class="vtk-canvas" :style="{ height }"></div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>{{ loadingText }}</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        <el-icon :size="40"><CircleClose /></el-icon>
        <p>{{ error }}</p>
      </div>
      
      <!-- 控制栏 -->
      <div v-if="!loading && !error" class="controls">
        <div class="control-buttons">
          <el-button-group>
            <!-- 播放/暂停 -->
            <el-button @click="togglePlayback" :icon="isPlaying ? VideoPause : VideoPlay">
              {{ isPlaying ? '暂停' : '播放' }}
            </el-button>
            <!-- 上一帧 -->
            <el-button @click="previousFrame" :icon="DArrowLeft" :disabled="currentFrameIndex === 0" />
            <!-- 下一帧 -->
            <el-button @click="nextFrame" :icon="DArrowRight" :disabled="currentFrameIndex === timeSeriesFiles.length - 1" />
            <!-- 重置视角 -->
            <el-button @click="resetCamera" :icon="RefreshRight">重置</el-button>
            <!-- 下载当前帧 -->
            <el-button @click="downloadCurrentFrame" :icon="Download">下载</el-button>
          </el-button-group>
        </div>
        
        <div class="time-info">
          <span>帧 {{ currentFrameIndex + 1 }} / {{ timeSeriesFiles.length }}</span>
          <span class="file-size">{{ formatFileSize(currentFileSize) }}</span>
        </div>
      </div>
    </div>
    
    <!-- 预加载进度 -->
    <div v-if="preloading" class="preload-progress">
      <el-progress 
        :percentage="Math.round(preloadProgress / preloadTotal * 100)" 
        :format="() => `缓存中 ${preloadProgress}/${preloadTotal} 帧`"
      />
    </div>
    
    <!-- 时间轴控制 -->
    <div v-if="!loading && !error && timeSeriesFiles.length > 0" class="timeline-controls">
      <div class="timeline-slider">
        <span class="timeline-label">时间步:</span>
        <el-slider 
          v-model="currentFrameIndex" 
          :min="0" 
          :max="timeSeriesFiles.length - 1"
          :show-tooltip="true"
          :format-tooltip="formatTooltip"
          @change="onFrameChange"
        />
        <span class="timeline-value">{{ currentTimeStep }}</span>
      </div>
      
      <div class="playback-controls">
        <span class="control-label">播放速度:</span>
        <el-radio-group v-model="playbackSpeed" size="small">
          <el-radio-button :value="0.5">0.5x</el-radio-button>
          <el-radio-button :value="1">1x</el-radio-button>
          <el-radio-button :value="2">2x</el-radio-button>
          <el-radio-button :value="4">4x</el-radio-button>
        </el-radio-group>
        
        <el-checkbox v-model="loopPlayback" style="margin-left: 16px">循环播放</el-checkbox>
      </div>
    </div>
    
    <!-- Colorbar 色标 -->
    <div v-if="!loading && !error && currentDataRange" class="colorbar-panel">
      <div class="colorbar-header">
        <span class="colorbar-title">浓度 (c)</span>
        <el-button text size="small" @click="showStats = !showStats">
          {{ showStats ? '隐藏' : '显示' }}统计
        </el-button>
      </div>
      <div class="colorbar-container">
        <div class="colorbar-gradient"></div>
        <div class="colorbar-labels">
          <div class="colorbar-label">
            <span class="color-dot blue"></span>
            <span>{{ currentDataRange.min.toFixed(3) }}</span>
            <span class="phase-label">α相</span>
          </div>
          <div class="colorbar-label center">
            <span class="color-dot green"></span>
            <span>{{ currentDataRange.mid.toFixed(3) }}</span>
            <span class="phase-label">界面</span>
          </div>
          <div class="colorbar-label">
            <span class="color-dot red"></span>
            <span>{{ currentDataRange.max.toFixed(3) }}</span>
            <span class="phase-label">β相</span>
          </div>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <transition name="slide-down">
        <div v-if="showStats && phaseStats" class="stats-panel">
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">数据范围:</span>
              <span class="stat-value">{{ (currentDataRange.max - currentDataRange.min).toFixed(4) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">时间步:</span>
              <span class="stat-value">{{ currentTimeStep }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">帧索引:</span>
              <span class="stat-value">{{ currentFrameIndex + 1 }} / {{ timeSeriesFiles.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">数据点:</span>
              <span class="stat-value">{{ phaseStats.totalPoints.toLocaleString() }}</span>
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
import { 
  Loading, 
  CircleClose, 
  RefreshRight, 
  Download,
  VideoPlay,
  VideoPause,
  DArrowLeft,
  DArrowRight
} from '@element-plus/icons-vue'

// VTK.js 导入
import '@kitware/vtk.js/Rendering/Profiles/Volume'
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow'
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
  // API基础URL
  baseUrl: {
    type: String,
    default: 'http://localhost:8000'
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
const loadingText = ref('初始化...')
const error = ref(null)
const currentFrameIndex = ref(0)
const isPlaying = ref(false)
const playbackSpeed = ref(1)
const loopPlayback = ref(true)
const currentFileSize = ref(0)

// 预加载状态
const preloading = ref(false)
const preloadProgress = ref(0)
const preloadTotal = ref(0)

// Colorbar和统计信息
const currentDataRange = ref(null)
const phaseStats = ref(null)
const showStats = ref(false)

// VTK渲染器对象
let fullScreenRenderer = null
let renderer = null
let renderWindow = null
let actor = null
let mapper = null
let playbackTimer = null

// 缓存已加载的数据
const frameCache = new Map()

// 保存初始相机状态，确保所有帧视角一致
let initialCameraPosition = null
let initialCameraFocalPoint = null
let initialCameraViewUp = null
let isFirstFrame = true

/**
 * 当前时间步
 */
const currentTimeStep = computed(() => {
  if (props.timeSeriesFiles.length === 0) return 0
  return props.timeSeriesFiles[currentFrameIndex.value]?.timeStep || 0
})

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
    console.log('[VTK时间序列] 开始初始化渲染器')
    
    // 创建全屏渲染窗口
    fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
      container: vtkContainerRef.value,
      background: [0.1, 0.1, 0.1],  // 深色背景
      containerStyle: {
        height: '100%',
        width: '100%',
        position: 'absolute',
        top: '0',
        left: '0'
      }
    })
    
    renderer = fullScreenRenderer.getRenderer()
    renderWindow = fullScreenRenderer.getRenderWindow()
    
    // 强制渲染窗口大小以消除黑线
    nextTick(() => {
      // 再次检查容器是否存在（防止组件已卸载）
      if (!vtkContainerRef.value || !vtkContainerRef.value.isConnected) {
        console.warn('[VTK时间序列] 容器在nextTick时已不存在，跳过resize')
        return
      }
      
      if (renderWindow) {
        try {
          const dims = vtkContainerRef.value.getBoundingClientRect()
          renderWindow.getViews()[0]?.setSize(Math.floor(dims.width), Math.floor(dims.height))
          
          // 移除VTK内部可能产生的分隔线元素
          const allDivs = vtkContainerRef.value.querySelectorAll('div')
          allDivs.forEach(div => {
            // 移除所有边框
            div.style.border = 'none'
            div.style.outline = 'none'
            // 如果div只是用于布局且有可疑的尺寸（如1px宽），隐藏它
            const computedStyle = window.getComputedStyle(div)
            if (computedStyle.width === '1px' || computedStyle.height === '1px') {
              div.style.display = 'none'
            }
          })
          
          renderWindow.render()
        } catch (err) {
          console.error('[VTK时间序列] resize失败:', err)
        }
      }
    })
    
    console.log('[VTK时间序列] 渲染器初始化成功')
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
    const vtkUrl = `${props.baseUrl}/api/vtk/files/${fileName}`
    
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
    
    // 设置相机位置（从斜上方观察）
    const distance = Math.max(
      bounds[1] - bounds[0],
      bounds[3] - bounds[2],
      bounds[5] - bounds[4]
    ) * 2.5
    
    camera.setPosition(
      center[0] + distance * 0.7,
      center[1] + distance * 0.7,
      center[2] + distance * 0.7
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
  
  // 每帧渲染后再次清理黑线
  nextTick(() => {
    if (vtkContainerRef.value) {
      const allDivs = vtkContainerRef.value.querySelectorAll('div')
      allDivs.forEach(div => {
        div.style.border = 'none'
        div.style.outline = 'none'
        const computedStyle = window.getComputedStyle(div)
        if (computedStyle.width === '1px' || computedStyle.height === '1px') {
          div.style.display = 'none'
        }
      })
    }
  })
  
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
    const url = `${props.baseUrl}/api/vtk/files/${fileInfo.name}`
    window.open(url, '_blank')
  }
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

/**
 * 格式化工具提示
 */
const formatTooltip = (value) => {
  const fileInfo = props.timeSeriesFiles[value]
  return fileInfo ? `时间步: ${fileInfo.timeStep}` : value
}

/**
 * 清理
 */
const cleanup = () => {
  console.log('[VTK时间序列] 开始清理资源')
  
  // 停止播放
  stopPlayback()
  
  // 清空缓存
  frameCache.clear()
  
  // 安全清理VTK渲染器
  if (fullScreenRenderer) {
    try {
      // 先移除resize监听等事件
      if (fullScreenRenderer.getOpenGLRenderWindow) {
        const openGLRW = fullScreenRenderer.getOpenGLRenderWindow()
        if (openGLRW) {
          openGLRW.delete()
        }
      }
      fullScreenRenderer.delete()
      console.log('[VTK时间序列] VTK渲染器已清理')
    } catch (err) {
      console.error('[VTK时间序列] 清理VTK渲染器失败:', err)
    }
    fullScreenRenderer = null
  }
  
  // 清空引用
  renderer = null
  renderWindow = null
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
}

.vtk-viewer-container {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}

.vtk-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

/* 修复VTK.js黑线问题 - 增强版 */
.vtk-canvas :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}

.vtk-canvas :deep(.js-vtk-container) {
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
}

.vtk-canvas :deep(.js-vtk-view) {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
  outline: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 强制隐藏VTK内部的分隔线元素 */
.vtk-canvas :deep(div[style*="border"]) {
  border: none !important;
}

.vtk-canvas :deep(div[style*="position: absolute"]) {
  border: none !important;
  outline: none !important;
}

/* 隐藏可能的resize handle */
.vtk-canvas :deep(.vtk-resize-handle),
.vtk-canvas :deep([class*="resize"]) {
  display: none !important;
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
</style>
