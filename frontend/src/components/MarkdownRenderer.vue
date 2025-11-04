<template>
  <div class="markdown-content" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

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
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 14px;
}

/* 如果正在流式输出，添加光标动画 */
.markdown-content::after {
  content: '';
}

:deep(h1),
:deep(h2),
:deep(h3),
:deep(h4) {
  margin-top: 20px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

:deep(h1) {
  font-size: 20px;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 8px;
}

:deep(h2) {
  font-size: 18px;
}

:deep(h3) {
  font-size: 16px;
}

:deep(h4) {
  font-size: 14px;
}

:deep(p) {
  margin: 10px 0;
  line-height: 1.8;
}

:deep(ul),
:deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

:deep(li) {
  margin: 6px 0;
  line-height: 1.6;
}

:deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
  color: #c7254e;
}

:deep(pre) {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 16px 0;
}

:deep(pre code) {
  background: none;
  padding: 0;
  color: var(--text-primary);
}

:deep(blockquote) {
  border-left: 4px solid var(--primary);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--text-secondary);
  font-style: italic;
}

:deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

:deep(th),
:deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}

:deep(th) {
  background: var(--bg-secondary);
  font-weight: 600;
}

:deep(a) {
  color: var(--primary);
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}

:deep(strong) {
  font-weight: 600;
  color: var(--text-primary);
}

:deep(em) {
  font-style: italic;
}

:deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 20px 0;
}
</style>
