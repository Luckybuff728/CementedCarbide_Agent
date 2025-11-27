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
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.summary-card.clickable {
  cursor: pointer;
}

.summary-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
  border-color: #d1d5db;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon {
  font-size: 20px;
  color: #4b5563;
  display: flex;
  align-items: center;
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.click-icon {
  font-size: 16px;
  color: #9ca3af;
  transition: all 0.2s;
}

.summary-card.clickable:hover .click-icon {
  transform: translateX(4px);
  color: #4b5563;
}

.card-body {
  font-size: 14px;
  color: #374151;
}
</style>
