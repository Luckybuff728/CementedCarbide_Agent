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
.optimization-plans-card {
  padding: 12px;
}

/* 方案列表（一行一个） */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

/* 每个方案行 */
.plan-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
}

.plan-row:hover {
  border-color: #1a73e8;
  background: #f5f8ff;
}

.plan-row.recommended {
  border-color: #34a853;
  background: #f1f8f4;
}

/* 左侧标识区 */
.plan-badge-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 40px;
}

.plan-id-badge {
  background: #1a73e8;
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
}

.plan-row.recommended .plan-id-badge {
  background: #34a853;
}

/* 方案内容区 */
.plan-content {
  flex: 1;
  min-width: 0;
}

.plan-category {
  font-size: 11px;
  color: #80868b;
  margin-bottom: 4px;
}

.plan-name {
  font-weight: 600;
  font-size: 14px;
  color: #202124;
  line-height: 1.4;
  margin-bottom: 6px;
}

.plan-effect {
  font-size: 12px;
  color: #1a73e8;
}

.plan-row.recommended .plan-effect {
  color: #137333;
}

/* 底部提示 */
.plans-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #80868b;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
}
</style>
