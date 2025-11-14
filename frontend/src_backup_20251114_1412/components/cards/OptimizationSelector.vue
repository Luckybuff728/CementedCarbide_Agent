<template>
  <div class="optimization-section">
    <div class="section-header">
      <n-icon :component="BulbOutline" />
      <h4>选择优化方案</h4>
    </div>
    
    <div class="opt-cards">
      <div 
        v-for="opt in options"
        :key="opt.id"
        :class="['opt-card', { selected: selectedOpt === opt.id }]"
        @click="selectedOpt = opt.id"
      >
        <div class="opt-header">
          <n-icon class="opt-icon" :component="opt.iconComponent" />
          <h5>{{ opt.title }}</h5>
        </div>
        <p class="opt-desc">{{ opt.description }}</p>
        <div v-if="opt.summary" class="opt-summary">
          {{ opt.summary }}
        </div>
      </div>
    </div>

    <!-- 综合建议 -->
    <div v-if="comprehensiveRecommendation" class="recommendation-box">
      <h5>📌 综合建议</h5>
      <p>{{ comprehensiveRecommendation }}</p>
    </div>

    <n-button 
      type="primary"
      size="large"
      :disabled="!selectedOpt"
      @click="handleSelect"
      block
    >
      确认选择并生成工单
    </n-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import {
  BulbOutline,
  FlaskOutline,
  BuildOutline,
  SettingsOutline
} from '@vicons/ionicons5'

// 定义props和emits
const props = defineProps({
  p1Content: {
    type: String,
    default: ''
  },
  p2Content: {
    type: String,
    default: ''
  },
  p3Content: {
    type: String,
    default: ''
  },
  comprehensiveRecommendation: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

// 选中的方案
const selectedOpt = ref(null)

// 从内容中提取摘要
const getSummaryFromContent = (content) => {
  if (!content) return ''
  const text = content.replace(/[#*`\n]/g, '').trim()
  return text.length > 80 ? text.substring(0, 80) + '...' : text
}

// 优化方案配置
const options = computed(() => [
  {
    id: 'P1',
    title: 'P1 成分优化',
    iconComponent: FlaskOutline,
    description: '调整Al/Ti/N比例及合金元素',
    summary: getSummaryFromContent(props.p1Content)
  },
  {
    id: 'P2',
    title: 'P2 结构优化',
    iconComponent: BuildOutline,
    description: '多层/梯度结构设计',
    summary: getSummaryFromContent(props.p2Content)
  },
  {
    id: 'P3',
    title: 'P3 工艺优化',
    iconComponent: SettingsOutline,
    description: '沉积温度/偏压/气氛优化',
    summary: getSummaryFromContent(props.p3Content)
  }
])

// 处理选择
const handleSelect = () => {
  if (!selectedOpt.value) return
  emit('select', selectedOpt.value)
}
</script>

<style scoped>
.optimization-section {
  background: white;
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.section-header .n-icon {
  font-size: 20px;
  color: var(--warning);
}

.section-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.opt-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.opt-card {
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.opt-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.opt-card.selected {
  border-color: var(--primary);
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}

.opt-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.opt-icon {
  font-size: 22px;
  color: var(--primary);
}

.opt-header h5 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.opt-desc {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.opt-summary {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--primary-light);
}

.recommendation-box {
  padding: 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: var(--radius-md);
  border: 2px solid #fbbf24;
  margin-bottom: 16px;
}

.recommendation-box h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
}

.recommendation-box p {
  margin: 0;
  font-size: 13px;
  color: #78350f;
  line-height: 1.6;
}
</style>
