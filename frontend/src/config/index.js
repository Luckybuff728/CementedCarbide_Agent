/**
 * 前端配置管理
 * 统一管理所有配置项，避免硬编码
 */

// API基础URL配置（开发模式使用相对路径，通过 Vite proxy 代理）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  import.meta.env.DEV ? '' : 'http://localhost:8000'
)

// WebSocket基础URL配置（开发模式动态获取当前 host）
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || (
  import.meta.env.DEV 
    ? `ws://${window.location.hostname}:8000`
    : 'ws://localhost:8000'
)

// WebSocket端点
export const WS_ENDPOINTS = {
  coating: `${WS_BASE_URL}/ws/coating`
}

// API端点
export const API_ENDPOINTS = {
  vtk: `${API_BASE_URL}/api/vtk`,
  coating: `${API_BASE_URL}/api/coating`,
  health: `${API_BASE_URL}/health`
}

// 其他配置
export const CONFIG = {
  // 开发模式
  isDev: import.meta.env.DEV,
  // 生产模式
  isProd: import.meta.env.PROD,
  // 应用名称
  appName: 'TopMat Agent',
  // 版本号
  version: '1.0.1'
}

export default {
  API_BASE_URL,
  WS_BASE_URL,
  WS_ENDPOINTS,
  API_ENDPOINTS,
  CONFIG
}
