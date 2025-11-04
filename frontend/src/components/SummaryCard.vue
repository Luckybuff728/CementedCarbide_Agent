<template>
  <div :class="['summary-card', { clickable }]" @click="handleClick">
    <div class="card-header">
      <div class="header-left">
        <n-icon v-if="iconComponent" class="icon" :component="iconComponent" />
        <span v-else class="icon">{{ icon }}</span>
        <h4>{{ title }}</h4>
      </div>
      <div class="header-right">
        <el-tag v-if="badge" :type="badge.type" size="small">
          {{ badge.text }}
        </el-tag>
        <el-icon v-if="clickable" class="click-icon">
          <ArrowRight />
        </el-icon>
      </div>
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight } from '@element-plus/icons-vue'
import { NIcon } from 'naive-ui'

defineProps({
  icon: {
    type: [String, Object],  // 支持字符串(emoji)和组件
    required: true
  },
  iconComponent: {
    type: Object,  // Naive UI图标组件
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
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.summary-card.clickable {
  cursor: pointer;
}

.summary-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 22px;
  color: var(--primary);
}

.header-left h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.click-icon {
  font-size: 14px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.summary-card.clickable:hover .click-icon {
  transform: translateX(3px);
}

.card-body {
  font-size: 13px;
}
</style>
