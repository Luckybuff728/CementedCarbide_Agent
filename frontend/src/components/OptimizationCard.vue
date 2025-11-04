<template>
  <div :class="['optimization-card', { collapsed }]">
    <div class="card-header" @click="$emit('toggle')">
      <div class="header-left">
        <n-icon v-if="iconComponent" class="icon" :component="iconComponent" />
        <span v-else-if="icon" class="icon">{{ icon }}</span>
        <h4>{{ title }}</h4>
        <el-tag v-if="isStreaming" type="warning" size="small">
          <el-icon class="is-loading"><Loading /></el-icon>
          生成中
        </el-tag>
      </div>
      <el-icon class="toggle-icon">
        <component :is="collapsed ? 'ArrowDown' : 'ArrowUp'" />
      </el-icon>
    </div>
    
    <transition name="collapse">
      <div v-show="!collapsed" class="card-content">
        <MarkdownRenderer :content="content" :streaming="isStreaming" />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { NIcon } from 'naive-ui'
import MarkdownRenderer from './MarkdownRenderer.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: [String, Object],
    default: ''
  },
  iconComponent: {
    type: Object,
    default: null
  },
  content: {
    type: String,
    default: ''
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])

// 判断是否正在流式输出
const isStreaming = computed(() => {
  return props.content && props.content.length < 100 // 简化判断
})
</script>

<style scoped>
.optimization-card {
  background: white;
  border-radius: var(--radius-md);
  border: 2px solid var(--border-color);
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}

.optimization-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-md);
}

.optimization-card.collapsed .card-header {
  border-bottom: none;
}

.card-header {
  padding: 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.2s;
}

.card-header:hover {
  background: var(--bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.icon {
  font-size: 20px;
  color: var(--primary);
}

.header-left h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.toggle-icon {
  font-size: 16px;
  color: var(--text-secondary);
}

.card-content {
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
  font-size: 13px;
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding: 0 16px;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
