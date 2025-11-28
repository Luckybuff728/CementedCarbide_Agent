/**
 * Markdown渲染工具
 */
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import bash from 'highlight.js/lib/languages/bash'
import sql from 'highlight.js/lib/languages/sql'

// 注册语言
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('sql', sql)

// Mermaid 图表计数器（用于生成唯一 ID）
let mermaidCounter = 0

// 创建Markdown实例
const md = new MarkdownIt({
  html: true,        // 允许HTML标签
  linkify: true,     // 自动转换URL为链接
  typographer: true, // 启用排版优化
  breaks: true,      // 转换换行符为<br>
  highlight: function (str, lang) {
    // Mermaid 图表特殊处理（使用 div 避免 pre 默认样式）
    if (lang === 'mermaid') {
      const id = `mermaid-${++mermaidCounter}`
      return `<div class="mermaid-wrapper"><div class="mermaid" id="${id}">${md.utils.escapeHtml(str)}</div></div>`
    }
    
    // 代码高亮
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code class="language-${lang}">${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch (err) {
        console.error('Highlight error:', err)
      }
    }
    // 未指定语言或不支持的语言，使用纯文本
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

/**
 * 渲染Markdown文本为HTML
 * @param {string} text - Markdown文本
 * @returns {string} - HTML字符串
 */
export function renderMarkdown(text) {
  if (!text) return ''
  
  try {
    // 处理特殊字符，防止渲染错误
    const sanitizedText = text.replace(/\u0000/g, '')
    return md.render(sanitizedText)
  } catch (error) {
    console.error('Markdown render error:', error)
    // 渲染失败时返回纯文本
    return `<pre>${text}</pre>`
  }
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
