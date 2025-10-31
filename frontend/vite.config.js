import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Vite配置
export default defineConfig({
  plugins: [vue()],
  
  server: {
    port: 5173,  // 统一使用5173端口
    host: '0.0.0.0',  // 允许外部访问（Docker需要）
    proxy: {
      // 代理API请求到FastAPI后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // 代理WebSocket
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  },
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})
