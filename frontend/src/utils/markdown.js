/**
 * Markdown渲染工具
 */
import MarkdownIt from 'markdown-it'

// 创建Markdown实例
const md = new MarkdownIt({
  html: true,        // 允许HTML标签
  linkify: true,     // 自动转换URL为链接
  typographer: true, // 启用排版优化
  breaks: true       // 转换换行符为<br>
})

/**
 * 渲染Markdown文本为HTML
 * @param {string} text - Markdown文本
 * @returns {string} - HTML字符串
 */
export function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

/**
 * 格式化时间戳
 * @param {string|Date} timestamp - 时间戳
 * @returns {string} - 格式化后的时间
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于1天
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 显示具体时间
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取节点状态类型
 * @param {string} status - 节点状态
 * @returns {string} - Element Plus标签类型
 */
export function getStatusType(status) {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取节点状态文本
 * @param {string} status - 节点状态
 * @returns {string} - 状态文本
 */
export function getStatusText(status) {
  const textMap = {
    'pending': '待处理',
    'processing': '进行中',
    'completed': '已完成',
    'error': '错误'
  }
  return textMap[status] || status
}

/**
 * 获取置信度颜色
 * @param {number} confidence - 置信度(0-1)
 * @returns {string} - 颜色值
 */
export function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return '#10b981'  // 绿色
  if (confidence >= 0.6) return '#3b82f6'  // 蓝色
  if (confidence >= 0.4) return '#f59e0b'  // 橙色
  return '#ef4444'  // 红色
}

/**
 * 获取置信度徽章
 * @param {number} confidence - 置信度(0-1)
 * @returns {object} - 徽章配置
 */
export function getConfidenceBadge(confidence) {
  if (confidence >= 0.8) {
    return { text: '高置信度', type: 'success' }
  }
  if (confidence >= 0.6) {
    return { text: '中置信度', type: 'primary' }
  }
  return { text: '低置信度', type: 'warning' }
}
