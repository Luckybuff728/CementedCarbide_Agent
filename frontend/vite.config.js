import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd() + '/frontend', '')
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'
  const wsBaseUrl = env.VITE_WS_BASE_URL || 'ws://localhost:8000'

  return {
    plugins: [vue()],
  
  // 生产环境构建配置
  build: {
    // 输出目录
    outDir: 'dist',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 构建优化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 移除console
        drop_debugger: true
      }
    },
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
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue-vendor': ['vue', 'pinia']
        }
      }
    }
  },
  
  // 开发服务器配置
  server: {
    host: '0.0.0.0',
    port: 5173,
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
