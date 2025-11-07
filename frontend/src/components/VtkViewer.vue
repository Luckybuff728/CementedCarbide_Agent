<template>
  <div class="vtk-viewer-container">
    <!-- VTK渲染容器 -->
    <div ref="vtkContainerRef" class="vtk-canvas" :style="{ height: height }"></div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40">
        <Loading />
      </el-icon>
      <p>加载VTK数据中...</p>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <el-icon :size="24" color="#f56c6c">
        <CircleClose />
      </el-icon>
      <p>{{ error }}</p>
    </div>
    
    <!-- 控制按钮 -->
    <div v-if="!loading && !error" class="controls">
      <el-button-group size="small">
        <el-button @click="resetCamera" title="重置视角">
          <el-icon><RefreshRight /></el-icon>
        </el-button>
        <el-button @click="toggleWireframe" title="切换线框">
          <el-icon><Grid /></el-icon>
        </el-button>
        <el-button @click="downloadVTK" title="下载VTK文件">
          <el-icon><Download /></el-icon>
        </el-button>
      </el-button-group>
      
      <div class="info-text">
        <span v-if="vtkData">{{ vtkData.dimensions_str || '' }} | {{ vtkData.file_size_mb }} MB</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, CircleClose, RefreshRight, Grid, Download } from '@element-plus/icons-vue'
import { API_BASE_URL } from '../config'

// VTK.js 导入
import '@kitware/vtk.js/Rendering/Profiles/Volume'
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow'
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor'
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper'
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume'
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper'
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction'
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction'
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData'
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray'

const props = defineProps({
  // VTK数据对象
  vtkData: {
    type: Object,
    default: null
  },
  // API基础URL - 从配置文件读取
  baseUrl: {
    type: String,
    default: API_BASE_URL
  },
  // 容器高度
  height: {
    type: String,
    default: '400px'
  },
  // 渲染模式: 'volume' | 'surface'
  renderMode: {
    type: String,
    default: 'volume'
  }
})

const vtkContainerRef = ref(null)
const loading = ref(false)
const error = ref(null)

// VTK渲染器对象
let fullScreenRenderer = null
let renderer = null
let renderWindow = null
let actor = null
let mapper = null
let wireframeMode = false

/**
 * 初始化VTK渲染器
 */
const initRenderer = () => {
  if (!vtkContainerRef.value) {
    console.warn('[VTK] 容器ref不存在，跳过初始化')
    return
  }
  
  // 检查容器是否在DOM中
  if (!vtkContainerRef.value.isConnected) {
    console.warn('[VTK] 容器未连接到DOM，跳过初始化')
    return
  }
  
  try {
    console.log('[VTK] 开始初始化渲染器')
    
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
    
    // 设置初始相机位置
    const camera = renderer.getActiveCamera()
    camera.setPosition(0, 0, 100)
    camera.setFocalPoint(0, 0, 0)
    camera.setViewUp(0, 1, 0)
    
    // 强制渲染窗口大小以消除黑线
    nextTick(() => {
      // 再次检查容器是否存在（防止组件已卸载）
      if (!vtkContainerRef.value || !vtkContainerRef.value.isConnected) {
        console.warn('[VTK] 容器在nextTick时已不存在，跳过resize')
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
          console.error('[VTK] resize失败:', err)
        }
      }
    })
    
    console.log('[VTK] 渲染器初始化成功')
  } catch (err) {
    console.error('[VTK] 初始化渲染器失败:', err)
    error.value = '初始化渲染器失败'
  }
}

/**
 * 加载VTK文件
 */
const loadVTKFile = async () => {
  if (!props.vtkData || !props.vtkData.file_name) {
    error.value = '没有VTK数据'
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    const vtkUrl = `${props.baseUrl}/api/vtk/files/${props.vtkData.file_name}`
    console.log('[VTK] 加载文件:', vtkUrl)
    
    // 使用fetch直接获取VTK文件内容
    const response = await fetch(vtkUrl)
    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }
    
    const vtkText = await response.text()
    console.log('[VTK] 文件内容获取成功, 大小:', vtkText.length, '字节')
    
    // 解析VTK Legacy格式并创建ImageData
    const source = parseLegacyVTK(vtkText)
    console.log('[VTK] 数据解析成功:', source)
    
    if (props.renderMode === 'volume') {
      // 体渲染模式
      renderVolume(source)
    } else {
      // 表面渲染模式
      renderSurface(source)
    }
    
    // 重置相机以适应数据
    renderer.resetCamera()
    renderWindow.render()
    
    // 渲染完成后清理黑线
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
    
    loading.value = false
    ElMessage.success('VTK数据加载成功')
    
  } catch (err) {
    console.error('[VTK] 加载失败:', err)
    error.value = `加载VTK文件失败: ${err.message}`
    loading.value = false
    ElMessage.error('VTK数据加载失败')
  }
}

/**
 * 解析Legacy VTK格式文件
 */
const parseLegacyVTK = (vtkText) => {
  const lines = vtkText.split('\n')
  
  // 解析头部信息
  let dimensions = [64, 64, 64]  // 默认值
  let origin = [0, 0, 0]
  let spacing = [1, 1, 1]
  let pointDataIndex = -1
  
  // 查找关键信息
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
      // 跳过SCALARS行和LOOKUP_TABLE行，数据从下一行开始
      pointDataIndex = i + 2
      break
    }
  }
  
  // 提取标量数据 - 避免使用spread导致栈溢出
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
  
  console.log('[VTK解析] 维度:', dimensions, '数据点数:', scalarData.length)
  
  // 创建vtkImageData对象
  const imageData = vtkImageData.newInstance()
  imageData.setDimensions(dimensions)
  imageData.setOrigin(origin)
  imageData.setSpacing(spacing)
  
  // 设置标量数据
  const dataArray = vtkDataArray.newInstance({
    name: 'scalars',
    numberOfComponents: 1,
    values: Float32Array.from(scalarData)
  })
  
  imageData.getPointData().setScalars(dataArray)
  
  return imageData
}

/**
 * 体渲染模式
 */
const renderVolume = (source) => {
  // 创建体渲染mapper
  mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(source)
  mapper.setSampleDistance(0.4)  // 降低采样距离以提高清晰度和一致性
  
  // 创建volume actor
  actor = vtkVolume.newInstance()
  actor.setMapper(mapper)
  
  // 获取数据范围
  const dataArray = source.getPointData().getScalars()
  const dataRange = dataArray.getRange()
  console.log('[VTK] 数据范围:', dataRange)
  
  const [minVal, maxVal] = dataRange
  const range = maxVal - minVal
  
  // 使用实际数据范围设置颜色传输函数
  const ctfun = vtkColorTransferFunction.newInstance()
  ctfun.addRGBPoint(minVal, 0.0, 0.0, 1.0)                      // 蓝色（低值）
  ctfun.addRGBPoint(minVal + range * 0.5, 0.0, 1.0, 0.0)       // 绿色（中值）
  ctfun.addRGBPoint(maxVal, 1.0, 0.0, 0.0)                      // 红色（高值）
  
  // 设置不透明度传输函数 - 自适应：根据数据分布调整
  const ofun = vtkPiecewiseFunction.newInstance()
  
  // 判断数据分布类型（更精确的阈值）
  const isEarlyStage = range < 0.025  // 降低阈值，更准确识别初始状态
  
  if (isEarlyStage) {
    // 初始状态：强化对比度以清晰显示微小扰动
    console.log('[VTK] 初始状态 - 强化扰动对比度')
    ofun.addPoint(minVal, 0.35)
    ofun.addPoint(minVal + range * 0.25, 0.65)
    ofun.addPoint(minVal + range * 0.5, 0.9)           // 平均值峰值提升
    ofun.addPoint(minVal + range * 0.75, 0.65)
    ofun.addPoint(maxVal, 0.35)
  } else {
    // 相分离状态：两相高不透明，界面窄且半透明
    console.log('[VTK] 相分离状态 - 突出两相体积')
    ofun.addPoint(minVal, 0.8)                          // α相高不透明
    ofun.addPoint(minVal + range * 0.47, 0.75)         // 接近界面
    ofun.addPoint(minVal + range * 0.5, 0.25)          // 界面更窄更透明
    ofun.addPoint(minVal + range * 0.53, 0.75)         // 离开界面
    ofun.addPoint(maxVal, 0.8)                          // β相高不透明
  }
  
  actor.getProperty().setRGBTransferFunction(0, ctfun)
  actor.getProperty().setScalarOpacity(0, ofun)
  actor.getProperty().setInterpolationTypeToLinear()
  actor.getProperty().setShade(true)  // 启用阴影增强3D效果
  actor.getProperty().setAmbient(0.3)
  actor.getProperty().setDiffuse(0.7)      // 增加漫反射
  actor.getProperty().setSpecular(0.2)     // 降低镜面反射
  actor.getProperty().setSpecularPower(8)  // 降低高光锐度
  
  renderer.addVolume(actor)
}

/**
 * 表面渲染模式
 */
const renderSurface = (source) => {
  // 创建mapper
  mapper = vtkMapper.newInstance()
  mapper.setInputData(source)
  
  // 创建actor
  actor = vtkActor.newInstance()
  actor.setMapper(mapper)
  
  // 设置颜色
  actor.getProperty().setColor(0.2, 0.6, 1.0)
  
  renderer.addActor(actor)
}

/**
 * 重置相机视角
 */
const resetCamera = () => {
  if (renderer) {
    renderer.resetCamera()
    renderWindow.render()
  }
}

/**
 * 切换线框模式（仅表面渲染支持）
 */
const toggleWireframe = () => {
  // 体渲染模式不支持线框模式
  if (props.renderMode === 'volume') {
    ElMessage.warning('体渲染模式不支持线框显示')
    return
  }
  
  if (actor && actor.getProperty && actor.getProperty().setRepresentation) {
    wireframeMode = !wireframeMode
    actor.getProperty().setRepresentation(wireframeMode ? 1 : 2)
    renderWindow.render()
    ElMessage.success(wireframeMode ? '已切换到线框模式' : '已切换到实体模式')
  }
}

/**
 * 下载VTK文件
 */
const downloadVTK = () => {
  if (props.vtkData && props.vtkData.file_name) {
    const url = `${props.baseUrl}/api/vtk/files/${props.vtkData.file_name}`
    window.open(url, '_blank')
  }
}

/**
 * 清理渲染器
 */
const cleanup = () => {
  console.log('[VTK] 开始清理资源')
  
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
      console.log('[VTK] VTK渲染器已清理')
    } catch (err) {
      console.error('[VTK] 清理VTK渲染器失败:', err)
    }
    fullScreenRenderer = null
  }
  
  // 清空引用
  renderer = null
  renderWindow = null
  actor = null
  mapper = null
  
  console.log('[VTK] 资源清理完成')
}

// 监听vtkData变化
watch(() => props.vtkData, (newData) => {
  if (newData && renderer) {
    loadVTKFile()
  }
}, { deep: true })

// 组件挂载
onMounted(() => {
  initRenderer()
  if (props.vtkData) {
    // 延迟加载，确保DOM已渲染
    setTimeout(() => {
      loadVTKFile()
    }, 100)
  }
})

// 组件卸载前清理
onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
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

.info-text {
  color: #fff;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 12px;
  border-radius: 4px;
}

/* Element Plus 按钮组样式调整 */
:deep(.el-button-group) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
</style>
