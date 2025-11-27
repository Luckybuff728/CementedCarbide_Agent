import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // 生产环境构建配置
  build: {
    // 输出目录
    outDir: 'dist',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 构建优化 - 使用默认压缩器
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
    port: 5173,
    // API代理（开发环境）
    proxy: {
      '/api': {
        target: 'http://192.168.6.108:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://192.168.6.108:8000',
        ws: true
      }
    }
  }
})
