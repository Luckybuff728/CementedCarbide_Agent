<template>
  <div class="optimization-plans-card">
    <!-- 方案列表（一行一个） -->
    <div class="plans-list">
      <div
        v-for="plan in plans"
        :key="plan.id"
        class="plan-row"
        :class="{ 'recommended': recommended === plan.id }"
      >
        <!-- 左侧：方案标识 -->
        <div class="plan-badge-section">
          <div class="plan-id-badge">{{ plan.id }}</div>
          <el-tag v-if="recommended === plan.id" type="success" size="small">推荐</el-tag>
        </div>
        
        <!-- 中间：方案内容 -->
        <div class="plan-content">
          <div class="plan-category">{{ plan.category || '优化方案' }}</div>
          <div class="plan-name">{{ plan.name }}</div>
          <div class="plan-effect" v-if="plan.expected_effect">
            预期：{{ plan.expected_effect }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 提示 -->
    <div class="plans-tip">
      <el-icon :size="14"><InformationCircleOutline /></el-icon>
      <span>在对话中输入"选择 P1"、"选择 P2"或"选择 P3"来选择方案</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElTag, ElIcon } from 'element-plus'
import { InformationCircleOutline } from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

// 计算属性：提取方案列表
const plans = computed(() => {
  return props.data?.plans || []
})

// 计算属性：推荐方案
const recommended = computed(() => {
  return props.data?.recommended || ''
})
</script>

<style scoped>
/* 优化方案卡片 */
.optimization-plans-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

/* 方案列表 */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

/* 每个方案行 - 使用左边框而非背景 */
.plan-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0 12px 12px;
  border-left: 3px solid #e5e7eb;
  transition: all 0.2s ease;
}

.plan-row:hover {
  border-left-color: #2563eb;
}

.plan-row.recommended {
  border-left-color: #10b981;
}

/* 左侧标识区 */
.plan-badge-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 36px;
}

.plan-id-badge {
  background: #2563eb;
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.plan-row.recommended .plan-id-badge {
  background: #10b981;
}

/* 方案内容区 */
.plan-content {
  flex: 1;
  min-width: 0;
}

.plan-category {
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.plan-name {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  line-height: 1.4;
  margin-bottom: 4px;
}

.plan-effect {
  font-size: 12px;
  color: #6b7280;
}

.plan-row.recommended .plan-effect {
  color: #059669;
}

/* 底部提示 */
.plans-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
</style>
