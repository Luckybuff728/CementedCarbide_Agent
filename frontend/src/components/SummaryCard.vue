<template>
  <div :class="['summary-card', { clickable }]" @click="handleClick">
    <div class="card-header">
      <div class="header-left">
        <span class="icon">{{ icon }}</span>
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

defineProps({
  icon: {
    type: String,
    required: true
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
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.summary-card.clickable {
  cursor: pointer;
}

.summary-card.clickable:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
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
  font-size: 20px;
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
