import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import App from './App.vue'

// 导入Naive UI
import naive from 'naive-ui'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)
// 使用Naive UI
app.use(naive)

// 全局错误处理器
app.config.errorHandler = (err, instance, info) => {
  console.error('[全局错误处理器]', {
    error: err,
    component: instance?.$options?.name || 'Unknown',
    info: info
  })
  
  // 可选：发送到错误监控服务
  // sendErrorToSentry(err, instance, info)
}

// 全局警告处理器（开发环境）
app.config.warnHandler = (msg, instance, trace) => {
  console.warn('[Vue警告]', { message: msg, trace })
}

// 捕获未处理的Promise rejection
window.addEventListener('unhandledrejection', (event) => {
  console.error('[未捕获的Promise错误]', event.reason)
  event.preventDefault()
})

// 捕获全局错误
window.addEventListener('error', (event) => {
  // 过滤非关键的浏览器警告
  const ignoredErrors = [
    'ResizeObserver loop completed with undelivered notifications',
    'ResizeObserver loop limit exceeded'
  ]
  
  // 检查是否是需要忽略的错误
  if (ignoredErrors.some(msg => event.message?.includes(msg))) {
    // 阻止错误冒泡到控制台（可选）
    // event.preventDefault()
    return
  }
  
  console.error('[全局错误]', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error
  })
})

app.mount('#app')
