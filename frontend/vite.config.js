import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  // 端口配置（统一从环境变量读取）
  const backendHost = env.VITE_BACKEND_HOST || 'localhost'
  const backendPort = env.VITE_BACKEND_PORT || '8000'
  const devPort = parseInt(env.VITE_DEV_PORT || '5173')
  
  // 组装后端URL（支持完整URL覆盖）
  const apiBaseUrl = env.VITE_API_BASE_URL || `http://${backendHost}:${backendPort}`
  const wsBaseUrl = env.VITE_WS_BASE_URL || `ws://${backendHost}:${backendPort}`

  return {
    plugins: [vue()],
    
    // 路径别名配置
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
  
  // 生产环境构建配置
  build: {
    // 输出目录
    outDir: 'dist',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 构建优化
    minify: true,
    // chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // rollup配置
    rollupOptions: {
      output: {
        // 静态资源分类打包
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: '[ext]/[name]-[hash].[ext]',
        // 代码分割
         manualChunks(id) {
          if (id.includes('element-plus')) {
            return 'element-plus'
          }
          if (id.includes('vue') || id.includes('pinia')) {
            return 'vue-vendor'
          }
        }
      }
    }
  },
  
  // 开发服务器配置
  server: {
    host: '0.0.0.0',
    port: devPort, // 从环境变量读取
    // API代理（开发环境）
    proxy: {
      '/api': {
        target: apiBaseUrl,
        changeOrigin: true
      },
      '/ws': {
        target: wsBaseUrl,
        ws: true
      }
    }
  }
  }
})
