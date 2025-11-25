<template>
  <div :class="['summary-card', { clickable }]" @click="handleClick">
    <div class="card-header" v-if="showHeader">
      <div class="header-left">
        <el-icon v-if="iconComponent" class="icon"><component :is="iconComponent" /></el-icon>
        <span v-else class="icon">{{ icon }}</span>
        <h4>{{ title }}</h4>
      </div>
      <div class="header-right">
        <el-tag v-if="badge" :type="badge.type" size="small">
          {{ badge.text }}
        </el-tag>
        <el-icon v-if="clickable" class="click-icon"><ArrowForwardOutline /></el-icon>
      </div>
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ElIcon } from 'element-plus'
import { ArrowForwardOutline } from '@vicons/ionicons5'

defineProps({
  icon: {
    type: [String, Object],  // 支持字符串(emoji)和组件
    type: [String, Object],  // 支持字符串(emoji)和组件
    default: ''
  },
  iconComponent: {
    type: Object,  // 图标组件
    default: null
  },
  title: {
    type: String,
    required: true
  },
  badge: {
    type: Object,
    default: null
  },
  clickable: {
    type: Boolean,
    default: false
  },
  showHeader: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['click'])

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.summary-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 18px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.summary-card.clickable {
  cursor: pointer;
}

.summary-card.clickable:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-light);
  background: var(--primary-lighter);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: var(--icon-md);
  color: var(--primary);
}

.header-left h4 {
  margin: 0;
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.click-icon {
  font-size: var(--icon-sm);
  color: var(--text-tertiary);
  transition: all var(--transition-fast);
}

.summary-card.clickable:hover .click-icon {
  transform: translateX(3px);
  color: var(--primary);
}

.card-body {
  font-size: var(--font-base);
}
</style>
