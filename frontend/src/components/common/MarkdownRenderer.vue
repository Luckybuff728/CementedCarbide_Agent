<template>
  <div :class="['markdown-content', { streaming }]" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../../utils/markdown'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  streaming: {
    type: Boolean,
    default: false
  }
})

// 渲染Markdown为HTML
const renderedHtml = computed(() => {
  if (!props.content) return ''
  return renderMarkdown(props.content)
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.75;
  color: var(--text-primary);
  font-size: 15px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 流式输出时显示光标 */
.markdown-content.streaming::after {
  content: '█';
  display: inline-block;
  margin-left: 4px;
  animation: blink 1s step-end infinite;
  color: var(--primary);
  font-weight: 400;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

:deep(h1),
:deep(h2),
:deep(h3),
:deep(h4),
:deep(h5),
:deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

:deep(h1) {
  font-size: 28px;
  border-bottom: 3px solid var(--border-color);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

:deep(h2) {
  font-size: 24px;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 10px;
}

:deep(h3) {
  font-size: 20px;
}

:deep(h4) {
  font-size: 17px;
}

:deep(h5) {
  font-size: 15px;
}

:deep(h6) {
  font-size: 14px;
  color: var(--text-secondary);
}

:deep(p) {
  margin: 12px 0;
  line-height: 1.75;
}

:deep(p:first-child) {
  margin-top: 0;
}

:deep(p:last-child) {
  margin-bottom: 0;
}

:deep(ul),
:deep(ol) {
  padding-left: 28px;
  margin: 16px 0;
}

:deep(li) {
  margin: 8px 0;
  line-height: 1.75;
}

:deep(li > p) {
  margin: 4px 0;
}

:deep(ul ul),
:deep(ol ul),
:deep(ul ol),
:deep(ol ol) {
  margin: 8px 0;
}

:deep(li::marker) {
  color: var(--primary);
  font-weight: 600;
}

:deep(code) {
  background: rgba(175, 184, 193, 0.2);
  padding: 3px 6px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.88em;
  color: #eb5757;
  border: 1px solid rgba(175, 184, 193, 0.3);
  font-weight: 500;
}

:deep(pre) {
  background: #282c34;
  padding: 20px;
  border-radius: var(--radius-lg);
  overflow-x: auto;
  margin: 20px 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: var(--shadow-sm);
  position: relative;
}

:deep(pre.hljs) {
  background: #282c34;
  color: #abb2bf;
}

:deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  border: none;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 400;
}

/* 代码高亮样式 */
:deep(.hljs-comment),
:deep(.hljs-quote) {
  color: #5c6370;
  font-style: italic;
}

:deep(.hljs-keyword),
:deep(.hljs-selector-tag),
:deep(.hljs-type) {
  color: #c678dd;
}

:deep(.hljs-string),
:deep(.hljs-attr) {
  color: #98c379;
}

:deep(.hljs-number),
:deep(.hljs-literal),
:deep(.hljs-built_in) {
  color: #d19a66;
}

:deep(.hljs-function),
:deep(.hljs-title) {
  color: #61afef;
}

:deep(.hljs-variable),
:deep(.hljs-template-variable) {
  color: #e06c75;
}

:deep(.hljs-name),
:deep(.hljs-selector-id),
:deep(.hljs-selector-class) {
  color: #e5c07b;
}

:deep(blockquote) {
  border-left: 4px solid var(--primary);
  padding: 12px 20px;
  margin: 20px 0;
  background: var(--primary-lighter);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  color: var(--text-secondary);
}

:deep(blockquote p) {
  margin: 8px 0;
}

:deep(blockquote p:first-child) {
  margin-top: 0;
}

:deep(blockquote p:last-child) {
  margin-bottom: 0;
}

:deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 20px 0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

:deep(th),
:deep(td) {
  border: 1px solid var(--border-light);
  padding: 12px 16px;
  text-align: left;
}

:deep(th) {
  background: linear-gradient(to bottom, var(--bg-secondary), var(--bg-tertiary));
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-color);
}

:deep(tr:hover) {
  background: var(--bg-secondary);
  transition: background var(--transition-fast);
}

:deep(tbody tr:nth-child(even)) {
  background: rgba(0, 0, 0, 0.01);
}

:deep(a) {
  color: var(--primary);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all var(--transition-fast);
  font-weight: 500;
}

:deep(a:hover) {
  border-bottom-color: var(--primary);
  color: var(--primary-hover);
}

:deep(strong) {
  font-weight: 700;
  color: var(--text-primary);
}

:deep(em) {
  font-style: italic;
  color: var(--text-secondary);
}

:deep(del) {
  text-decoration: line-through;
  color: var(--text-tertiary);
}

:deep(mark) {
  background: #fff3bf;
  padding: 2px 4px;
  border-radius: 3px;
  color: var(--text-primary);
}

:deep(hr) {
  border: none;
  border-top: 2px solid var(--border-color);
  margin: 32px 0;
}

/* 图片样式 */
:deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-lg);
  margin: 20px 0;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
}

/* 行内元素间距 */
:deep(code),
:deep(kbd),
:deep(samp) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

:deep(kbd) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.9em;
  box-shadow: 0 2px 0 var(--border-color);
}

/* 注释样式 */
:deep(sub),
:deep(sup) {
  font-size: 0.75em;
}

/* 分隔线 */
:deep(hr) {
  background: linear-gradient(to right, transparent, var(--border-color), transparent);
  height: 2px;
  border: none;
  margin: 32px 0;
}
</style>
