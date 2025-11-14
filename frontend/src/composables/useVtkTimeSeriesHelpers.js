/**
 * VTK时间序列工具函数
 */

/**
 * 格式化工具提示
 */
export const formatTooltip = (value, timeSeriesFiles) => {
  const fileInfo = timeSeriesFiles[value]
  return fileInfo ? `时间步: ${fileInfo.timeStep}` : value
}

/**
 * 格式化详细工具提示
 */
export const formatDetailedTooltip = (value, timeSeriesFiles) => {
  const fileInfo = timeSeriesFiles[value]
  if (!fileInfo) return value
  return `步长: ${value + 1} | 时间: ${formatPhysicalTime(value)} | 文件: ${fileInfo.name}`
}

/**
 * 格式化物理时间
 */
export const formatPhysicalTime = (frameIndex) => {
  // 假设每个时间步对应0.1μs的物理时间
  const timeStep = frameIndex * 0.1
  if (timeStep < 1) {
    return `${(timeStep * 1000).toFixed(0)} ns`
  } else if (timeStep < 1000) {
    return `${timeStep.toFixed(1)} μs`
  } else {
    return `${(timeStep / 1000).toFixed(2)} ms`
  }
}

/**
 * 格式化网格尺寸
 */
export const formatGridSize = (totalPoints) => {
  if (!totalPoints) return 'N/A'
  // 假设是立方体网格
  const sideLength = Math.round(Math.pow(totalPoints, 1/3))
  return `${sideLength}³`
}

/**
 * 计算沉积厚度
 */
export const calculateDepth = (frameIndex) => {
  // 假设每个时间步对应0.5nm的沉积
  const depth = frameIndex * 0.5
  if (depth < 1000) {
    return `${depth.toFixed(1)} nm`
  } else {
    return `${(depth / 1000).toFixed(2)} μm`
  }
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes) => {
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}
