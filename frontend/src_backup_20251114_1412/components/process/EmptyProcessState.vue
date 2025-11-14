<template>
  <div class="empty-state">
    <p class="empty-description">
      输入涂层参数后，系统将自动执行以下分析流程
    </p>
    
    <!-- 流程步骤预览 -->
    <div class="process-preview">
      <div 
        v-for="(step, index) in previewSteps" 
        :key="index"
        class="preview-step"
      >
        <div class="step-number">{{ index + 1 }}</div>
        <div class="step-info">
          <div class="step-title">
            <n-icon :component="step.icon" />
            <span>{{ step.title }}</span>
          </div>
          <div class="step-desc">{{ step.description }}</div>
        </div>
      </div>
    </div>
    
    <div class="empty-hint">
      <n-icon :component="ArrowForwardOutline" />
      <span>在左侧面板输入参数，点击「开始分析」启动流程</span>
    </div>
  </div>
</template>

<script setup>
import { NIcon } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  FlaskOutline,
  RadioButtonOnOutline,
  BarChartOutline,
  BulbOutline,
  DocumentTextOutline,
  ArrowForwardOutline
} from '@vicons/ionicons5'

// 流程步骤预览数据
const previewSteps = [
  {
    icon: CheckmarkCircleOutline,
    title: '参数验证',
    description: '验证成分配比、工艺参数和结构设计'
  },
  {
    icon: FlaskOutline,
    title: 'TopPhi相场模拟',
    description: '相场模拟计算晶体结构和微观组织演化'
  },
  {
    icon: RadioButtonOnOutline,
    title: 'ML性能预测',
    description: '机器学习预测硬度、结合力等性能指标'
  },
  {
    icon: BarChartOutline,
    title: '历史对比',
    description: '与历史案例对比，识别相似配方'
  },
  {
    icon: BulbOutline,
    title: '根因分析',
    description: '综合分析性能结果，提供优化建议'
  },
  {
    icon: DocumentTextOutline,
    title: '实验工单',
    description: '生成详细实验方案和操作指导'
  }
]
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  max-width: 800px;
  margin: 0 auto;
}

.empty-description {
  margin: 0 0 36px 0;
  font-size: 15px;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
}

.process-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 32px;
}

.preview-step {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-light);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.preview-step:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
  transform: translateX(4px);
  background: var(--primary-lighter);
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-lighter) 100%);
  color: var(--primary);
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.step-info {
  flex: 1;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.step-title .n-icon {
  font-size: 18px;
  color: var(--primary);
}

.step-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: linear-gradient(135deg, var(--primary-lighter) 0%, var(--primary-light) 100%);
  border-radius: var(--radius-lg);
  border: 2px solid var(--primary-light);
  color: var(--primary);
  font-size: 15px;
  font-weight: 600;
  box-shadow: var(--shadow-xs);
}

.empty-hint .n-icon {
  font-size: 20px;
  animation: slideRight 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes slideRight {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(4px);
  }
}
</style>
