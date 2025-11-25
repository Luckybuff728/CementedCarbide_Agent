/**
 * 前端配置管理
 * 统一管理所有配置项，避免硬编码
 */

// ==================== 端口配置 ====================
// 从环境变量读取，提供默认值
const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST || 'localhost'
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '8000'
export const DEV_PORT = import.meta.env.VITE_DEV_PORT || '5173'

// ==================== API基础URL配置 ====================
// 优先使用完整URL配置，否则根据环境自动组装
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  import.meta.env.DEV 
    ? '' // 开发模式：通过 Vite proxy 代理到 localhost:8000
    : ''  // 生产模式：通过 Nginx 代理到后端容器
)

// ==================== WebSocket基础URL配置 ====================
// 优先使用完整URL配置，否则根据环境自动组装
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || (
  import.meta.env.DEV 
    ? `ws://${window.location.hostname}:${BACKEND_PORT}` // 开发模式：直连后端
    : `ws://${window.location.host}`           // 生产模式：通过 Nginx 代理
)

// WebSocket端点
export const WS_ENDPOINTS = {
  coating: `${WS_BASE_URL}/ws/coating/agent`,  // 多Agent模式
  coatingLegacy: `${WS_BASE_URL}/ws/coating`   // 原工作流模式（备用）
}

// API端点
export const API_ENDPOINTS = {
  vtk: `${API_BASE_URL}/api/vtk`,
  coating: `${API_BASE_URL}/api/coating`,
  auth: `${API_BASE_URL}/api/auth`,
  health: `${API_BASE_URL}/health`
}

// 其他配置
export const CONFIG = {
  // 开发模式
  isDev: import.meta.env.DEV,
  // 生产模式
  isProd: import.meta.env.PROD,
  // 应用名称
  appName: 'TopMat Agent - 多Agent模式',
  // 版本号
  version: '2.0.0',
  // 模式
  mode: 'multi-agent'
}

export default {
  API_BASE_URL,
  WS_BASE_URL,
  WS_ENDPOINTS,
  API_ENDPOINTS,
  CONFIG
}
