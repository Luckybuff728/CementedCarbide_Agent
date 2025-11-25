<template>
  <div class="optimization-section">
    <div class="opt-cards">
      <div 
        v-for="opt in options"
        :key="opt.id"
        :class="['opt-card', { selected: selectedOpt === opt.id }]"
        @click="selectedOpt = opt.id"
      >
        <div class="opt-header">
          <el-icon class="opt-icon"><component :is="opt.iconComponent" /></el-icon>
          <h5>{{ opt.title }}</h5>
        </div>
        <p v-if="opt.planName" class="opt-plan-name">{{ opt.planName }}</p>
        <p class="opt-desc">{{ opt.description }}</p>
        <div v-if="opt.overview" class="opt-summary">
          {{ opt.overview }}
        </div>
      </div>
    </div>

    <!-- 综合建议 -->
    <div v-if="comprehensiveRecommendation" class="recommendation-box">
      <h5>📌 综合建议</h5>
      <p>{{ comprehensiveRecommendation }}</p>
    </div>

    <el-button 
      type="primary"
      size="large"
      :disabled="!selectedOpt"
      @click="handleSelect"
      style="width: 100%"
    >
      确认选择并生成工单
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElButton, ElIcon } from 'element-plus'
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

const selectedOpt = ref(null)

const getSummaryFromContent = (content) => {
  if (!content) return ''
  const text = content.replace(/[#*`\n]/g, '').trim()
  return text.length > 80 ? text.substring(0, 80) + '...' : text
}

const stripMarkdownInline = (text) => {
  if (!text) return ''
  return text
    .replace(/[`*_#>\-]/g, '')
    .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
}

const extractPlanMeta = (content) => {
  if (!content) return { name: '', overview: '' }
  const lines = content.split('\n')
  let name = ''
  let overview = ''
  let inName = false
  let inOverview = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!name && (/^##\s*方案名称/.test(line) || /^##方案名称/.test(line))) {
      inName = true
      continue
    }
    if (inName && !name && line && !line.startsWith('#')) {
      name = stripMarkdownInline(line.replace(/^\[/, '').replace(/]$/, ''))
      inName = false
      continue
    }
    if (!overview && (/^###\s*方案概述/.test(line) || /^###方案概述/.test(line))) {
      inOverview = true
      continue
    }
    if (inOverview && !overview && line && !line.startsWith('#')) {
      overview = stripMarkdownInline(line.replace(/^\[/, '').replace(/]$/, ''))
      inOverview = false
      continue
    }
  }

  return { name, overview }
}

const options = computed(() => {
  const p1Meta = extractPlanMeta(props.p1Content)
  const p2Meta = extractPlanMeta(props.p2Content)
  const p3Meta = extractPlanMeta(props.p3Content)

  return [
    {
      id: 'P1',
      title: 'P1 成分优化',
      iconComponent: FlaskOutline,
      description: '调整Al/Ti/N比例及合金元素',
      planName: p1Meta.name,
      overview: p1Meta.overview || getSummaryFromContent(props.p1Content),
      summary: getSummaryFromContent(props.p1Content)
    },
    {
      id: 'P2',
      title: 'P2 结构优化',
      iconComponent: BuildOutline,
      description: '多层/梯度结构设计',
      planName: p2Meta.name,
      overview: p2Meta.overview || getSummaryFromContent(props.p2Content),
      summary: getSummaryFromContent(props.p2Content)
    },
    {
      id: 'P3',
      title: 'P3 工艺优化',
      iconComponent: SettingsOutline,
      description: '沉积温度/偏压/气氛优化',
      planName: p3Meta.name,
      overview: p3Meta.overview || getSummaryFromContent(props.p3Content),
      summary: getSummaryFromContent(props.p3Content)
    }
  ]
})

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
  padding: 16px;
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

.opt-plan-name {
  margin: 0 0 4px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
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
