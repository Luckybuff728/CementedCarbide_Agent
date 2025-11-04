<template>
  <div class="status-bar">
    <!-- 左侧logo和标题 -->
    <div class="status-left">
      <div class="logo-section">
        <el-icon :size="24" color="#67C23A">
          <!-- <ChatDotRound /> -->
        </el-icon>
        <span class="title">TopMat Agent</span>
        <span class="subtitle">硬质合金涂层智能优化系统</span>
      </div>
    </div>

    <!-- 中间状态流程 -->
    <div class="status-center">
      <el-steps :active="currentStepIndex" align-center simple>
        <el-step 
          v-for="(step, index) in workflowSteps"
          :key="step.name"
          :title="step.title"
          :description="step.description"
          :status="getStepStatus(step, index)"
          :icon="getStepIcon(step, index)"
        />
      </el-steps>
    </div>

    <!-- 右侧连接状态和工具 -->
    <div class="status-right">
      <div 
        class="connection-status"
        :class="{
          'connected': connectionStatus,
          'disconnected': !connectionStatus
        }"
      >
        <el-icon class="status-icon">
          <component :is="connectionStatus ? 'Connection' : 'Refresh'" />
        </el-icon>
        <span class="status-text">{{ connectionStatus ? '系统已连接' : '系统离线' }}</span>
        <div class="status-indicator"></div>
      </div>
      
      <el-dropdown @command="handleCommand">
        <el-button circle>
          <el-icon><MoreFilled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="export">导出结果</el-dropdown-item>
            <el-dropdown-item command="clear">清空对话</el-dropdown-item>
            <el-dropdown-item command="settings">设置</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  ChatDotRound, 
  Connection, 
  Refresh, 
  MoreFilled,
  CircleCheck,
  Loading
} from '@element-plus/icons-vue'

const props = defineProps({
  connectionStatus: Boolean,
  currentNode: String,
  completedNodes: Array
})

const emit = defineEmits(['command'])

// 工作流步骤配置
const workflowSteps = [
  {
    name: 'input_validation',
    title: '参数验证',
    description: '输入参数检查'
  },
  {
    name: 'topphi_simulation',
    title: '理论计算',
    description: 'TopPhi模拟'
  },
  {
    name: 'ml_prediction',
    title: '性能预测',
    description: 'ML模型分析'
  },
  {
    name: 'historical_comparison',
    title: '历史对比',
    description: '数据比对分析'
  },
  {
    name: 'integrated_analysis',
    title: '综合分析',
    description: '根因分析'
  },
  {
    name: 'optimization',
    title: '方案优化',
    description: '生成建议'
  },
  {
    name: 'experiment',
    title: '实验验证',
    description: '工单生成'
  }
]

// 当前步骤索引（已完成的最后一个节点的索引）
const currentStepIndex = computed(() => {
  const currentIndex = workflowSteps.findIndex(step => 
    step.name === props.currentNode || 
    (step.name === 'optimization' && ['p1_composition_optimization', 'p2_structure_optimization', 'p3_process_optimization', 'optimization_summary'].includes(props.currentNode)) ||
    (step.name === 'experiment' && ['experiment_workorder', 'await_experiment_results', 'experiment_result_analysis'].includes(props.currentNode))
  )
  return currentIndex >= 0 ? currentIndex : 0
})

// 获取步骤状态
const getStepStatus = (step, index) => {
  // 检查该步骤是否在已完成列表中
  const isCompleted = props.completedNodes && props.completedNodes.includes(step.name)
  
  if (isCompleted) {
    // 已完成的步骤
    return 'finish'
  } else if (index === currentStepIndex.value && props.currentNode) {
    // 当前正在执行的步骤
    return 'process'
  } else if (index < currentStepIndex.value) {
    // 索引小于当前索引，但不在完成列表中，也标记为完成
    return 'finish'
  } else {
    // 等待执行的步骤
    return 'wait'
  }
}

// 获取步骤图标 - 简化设计，只在完成时显示勾
const getStepIcon = (step, index) => {
  const status = getStepStatus(step, index)
  if (status === 'finish') {
    return CircleCheck  // 已完成：显示勾
  }
  return undefined      // 其他状态不显示图标
}

// 处理命令
const handleCommand = (command) => {
  emit('command', command)
}
</script>

<style scoped>
/* 状态栏主容器样式 */
.status-bar {
  height: 70px; /* 状态栏高度 */
  background: #2c3e50; /* 深蓝灰色背景 */
  color: white; /* 白色文字 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: space-between; /* 左右两端对齐 */
  padding: 0 20px; /* 左右内边距20px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); /* 底部阴影 */
  position: relative; /* 相对定位 */
  z-index: 100; /* 层级高度 */
  transition: all 0.3s ease; /* 过渡动画 */
}

/* 状态栏左侧区域 - Logo和标题 */
.status-left {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  min-width: 320px; /* 最小宽度 */
  position: relative; /* 相对定位 */
  z-index: 1; /* 层级 */
}

/* Logo区域样式 */
.logo-section {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  gap: 12px; /* 元素间距 */
}

/* 主标题样式 */
.title {
  font-size: 22px; /* 字体大小 */
  font-weight: 600; /* 字重加粗 */
  color: white; /* 白色文字 */
}

/* 副标题样式 */
.subtitle {
  font-size: 14px; /* 小字体 */
  color: rgba(255, 255, 255, 0.8); /* 半透明白色 */
  margin-left: 8px; /* 左边距 */
}

/* 状态栏中间区域 - 工作流步骤 */
.status-center {
  flex: 1; /* 占用剩余空间 */
  padding: 0 20px; /* 左右内边距 */
  position: relative; /* 相对定位 */
  z-index: 1; /* 层级 */
}

/* 状态栏右侧区域 - 连接状态和操作 */
.status-right {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  gap: 16px; /* 元素间距 */
  min-width: 200px; /* 最小宽度 */
  justify-content: flex-end; /* 右对齐 */
  position: relative; /* 相对定位 */
  z-index: 1; /* 层级 */
}

/* 连接状态组件基础样式 */
.connection-status {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  gap: 8px; /* 元素间距 */
  padding: 8px 16px; /* 内边距：上下8px 左右16px */
  border-radius: 20px; /* 圆角效果 */
  transition: all 0.3s ease; /* 过渡动画 */
  position: relative; /* 相对定位 */
  backdrop-filter: blur(10px); /* 背景模糊效果 */
}

/* 已连接状态样式 */
.connection-status.connected {
  background: rgba(39, 174, 96, 0.2); /* 绿色半透明背景 */
  border: 1px solid #27ae60; /* 绿色边框 */
  color: #27ae60; /* 绿色文字 */
  box-shadow: 0 0 10px rgba(39, 174, 96, 0.2); /* 绿色发光效果 */
}

/* 未连接状态样式 */
.connection-status.disconnected {
  background: rgba(231, 76, 60, 0.2); /* 红色半透明背景 */
  border: 1px solid #e74c3c; /* 红色边框 */
  color: #e74c3c; /* 红色文字 */
  box-shadow: 0 0 10px rgba(231, 76, 60, 0.2); /* 红色发光效果 */
}

/* 状态图标样式 */
.status-icon {
  font-size: 16px; /* 图标大小 */
}

/* 状态文字样式 */
.status-text {
  font-size: 14px; /* 字体大小：增大到14px */
  font-weight: 500; /* 中等字重 */
  white-space: nowrap; /* 强制不换行 */
}

/* 状态指示器样式 */
.status-indicator {
  width: 8px; /* 指示器宽度 */
  height: 8px; /* 指示器高度 */
  border-radius: 50%; /* 圆形指示器 */
  position: relative; /* 相对定位 */
}

/* 已连接状态指示器 */
.connected .status-indicator {
  background: #27ae60; /* 绿色指示器 */
  animation: pulse-green 2s infinite; /* 绿色脉冲动画，每2秒循环 */
}

/* 未连接状态指示器 */
.disconnected .status-indicator {
  background: #e74c3c; /* 红色指示器 */
  animation: pulse-red 2s infinite; /* 红色脉冲动画，每2秒循环 */
}

/* 绿色脉冲动画 - 已连接状态 */
@keyframes pulse-green {
  0% {
    box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.7); /* 动画开始：无扩散 */
  }
  70% {
    box-shadow: 0 0 0 10px rgba(39, 174, 96, 0); /* 动画中期：扩散到10px并消失 */
  }
  100% {
    box-shadow: 0 0 0 0 rgba(39, 174, 96, 0); /* 动画结束：回到无扩散 */
  }
}

/* 红色脉冲动画 - 未连接状态 */
@keyframes pulse-red {
  0% {
    box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7); /* 动画开始：无扩散 */
  }
  70% {
    box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); /* 动画中期：扩散到10px并消失 */
  }
  100% {
    box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); /* 动画结束：回到无扩散 */
  }
}

:deep(.el-steps) {
  background: transparent;
}

/* 步骤框架基础样式 - 极简设计 */
:deep(.el-step) {
  background: transparent; /* 透明背景 */
  padding: 16px 12px; /* 增大内边距 */
  margin: 0 6px; /* 步骤间距 */
  border: 1px solid transparent; /* 透明边框，为动画做准备 */
  border-radius: 8px; /* 基础圆角 */
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); /* 优雅过渡 */
  min-width: 90px; /* 最小宽度 */
  text-align: center; /* 文字居中 */
  position: relative; /* 相对定位 */
}

/* 进行中状态的步骤样式 - 醒目高亮 */
:deep(.el-step.is-process) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(29, 78, 216, 0.1)); /* 蓝色渐变背景 */
  border: 10px solid rgba(233, 234, 235, 0.4); /* 蓝色边框 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 
    0 0 20px rgb(233, 234, 236),
    0 4px 15px rgba(0, 0, 0, 0.1); /* 蓝色发光和阴影 */
  transform: translateY(-2px) scale(1.02); /* 上移和轻微放大 */
  animation: glow-pulse 2s ease-in-out infinite; /* 发光脉冲动画 */
}

/* 进行中状态添加闪烁指示器 */
:deep(.el-step.is-process::before) {
  content: '●'; /* 圆点 */
  position: absolute;
  top: 4px;
  right: 4px;
  color: #3b82f6;
  font-size: 8px;
  animation: blink 1s ease-in-out infinite; /* 闪烁动画 */
}

/* 进行中状态添加下划线 */
:deep(.el-step.is-process::after) {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8, #abbad3); /* 蓝色渐变 */
  border-radius: 2px;
  animation: slide-line 2s ease-in-out infinite; /* 滑动动画 */
}

/* 已完成状态的步骤样式 - 优雅完成 */
:deep(.el-step.is-finish) {
  background: transparent; /* 透明背景 */
  opacity: 0.75; /* 降低透明度 */
}

/* 错误状态的步骤样式 */
:deep(.el-step.is-error) {
  background: rgba(231, 76, 60, 0.15); /* 红色半透明背景 */
  border: 1px solid rgba(231, 76, 60, 0.3); /* 红色边框 */
  box-shadow: 0 0 10px rgba(231, 76, 60, 0.1); /* 红色轻微阴影 */
}

/* 步骤标题基础样式 - 等待状态 */
:deep(.el-step__title) {
  color: rgba(255, 255, 255, 0.7); /* 提高可见性 */
  font-size: 13px; /* 字体大小 */
  font-weight: 400; /* 正常字重 */
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); /* 优雅过渡 */
  white-space: nowrap; /* 强制文字不换行 */
  letter-spacing: 0.5px; /* 字间距 */
}

/* 进行中状态的标题样式 - 醒目蓝色 */
:deep(.el-step__title.is-process) {
  color: #ffffff; /* 白色文字，更醒目 */
  font-weight: 700; /* 加粗 */
  font-size: 20px; /* 更大字体 */
  text-shadow: 
    0 0 10px rgba(59, 130, 246, 0.8),
    0 0 20px rgba(39, 162, 162, 0.4); /* 强蓝色发光 */
  animation: text-glow 2s ease-in-out infinite; /* 文字发光动画 */
}

/* 已完成状态的标题样式 - 优雅绿色 */
:deep(.el-step__title.is-finish) {
  color: rgba(34, 197, 94, 0.8); /* 现代绿色 */
  font-weight: 400; /* 正常字重 */
}

/* 错误状态的标题样式 */
:deep(.el-step__title.is-error) {
  color: #e74c3c; /* 红色文字 */
  font-weight: 500; /* 中等字重 */
}

/* 步骤描述文字样式 - 隐藏以简化界面 */
:deep(.el-step__description) {
  display: none; /* 隐藏描述，保持界面简洁 */
}

/* 步骤图标基础样式 - 隐藏所有默认图标 */
:deep(.el-step__icon) {
  display: none; /* 默认隐藏图标 */
}

/* 进行中状态的图标样式 - 隐藏 */
:deep(.el-step__icon.is-process) {
  display: none; /* 隐藏图标，用下划线代替 */
}

/* 已完成状态的图标样式 - 小巧绿勾 */
:deep(.el-step__icon.is-finish) {
  display: inline-flex; /* 显示勾图标 */
  align-items: center;
  justify-content: center;
  width: 18px; /* 图标宽度 */
  height: 18px; /* 图标高度 */
  color: #22c55e; /* 现代绿色 */
  font-size: 12px; /* 小尺寸 */
  background: rgba(34, 197, 94, 0.1); /* 淡绿背景 */
  border-radius: 50%; /* 圆形背景 */
  margin-bottom: 4px; /* 与标题间距 */
}

/* 错误状态的图标样式 */
:deep(.el-step__icon.is-error) {
  color: #ffffff; /* 白色图标 */
  border-color: #e74c3c; /* 红色边框 */
  background: #e74c3c; /* 红色背景 */
  animation: error-shake 0.5s ease-in-out; /* 错误震动动画 */
}

/* 发光脉冲动画 - 整个步骤 */
@keyframes glow-pulse {
  0%, 100% {
    box-shadow: 
      0 0 15px rgba(59, 130, 246, 0.2),
      0 4px 15px rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 
      0 0 25px rgba(59, 130, 246, 0.5),
      0 8px 25px rgba(0, 0, 0, 0.2);
  }
}

/* 滑动线动画 */
@keyframes slide-line {
  0% {
    background-position: -100% 0;
  }
  100% {
    background-position: 100% 0;
  }
}

/* 闪烁动画 */
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

/* 文字发光动画 */
@keyframes text-glow {
  0%, 100% {
    text-shadow: 
      0 0 8px rgba(59, 130, 246, 0.6),
      0 0 16px rgba(59, 130, 246, 0.3);
  }
  50% {
    text-shadow: 
      0 0 15px rgba(59, 130, 246, 1),
      0 0 30px rgba(59, 130, 246, 0.6);
  }
}

/* 呼吸灯效果 - 进行中状态动画 */
@keyframes breathing-light {
  0%, 100% {
    box-shadow: 0 0 8px rgba(243, 156, 18, 0.4); /* 小范围橙色光晕 */
    opacity: 0.9; /* 稍微透明 */
  }
  50% {
    box-shadow: 0 0 25px rgba(243, 156, 18, 0.8), 0 0 35px rgba(243, 156, 18, 0.6); /* 大范围橙色光晕 */
    opacity: 1; /* 完全不透明 */
  }
}

/* 成功脉冲效果 - 完成状态动画 */
@keyframes success-pulse {
  0% {
    transform: scale(1); /* 正常大小 */
    box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.7); /* 无扩散效果 */
  }
  50% {
    transform: scale(1.15); /* 放大到1.15倍 */
    box-shadow: 0 0 0 10px rgba(39, 174, 96, 0); /* 绿色光圈扩散 */
  }
  100% {
    transform: scale(1); /* 恢复正常大小 */
    box-shadow: 0 0 0 0 rgba(39, 174, 96, 0); /* 扩散消失 */
  }
}

/* 错误震动效果 - 错误状态动画 */
@keyframes error-shake {
  0%, 100% { transform: translateX(0); } /* 居中位置 */
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); } /* 向左偏移 */
  20%, 40%, 60%, 80% { transform: translateX(2px); } /* 向右偏移 */
}

/* 强制隐藏箭头 */
:deep(.el-step__arrow),
:deep(.el-step .el-step__arrow) {
  display: none !important; /* 强制不显示箭头 */
  visibility: hidden !important; /* 隐藏可见性 */
  width: 0 !important; /* 宽度为0 */
  height: 0 !important; /* 高度为0 */
  opacity: 0 !important; /* 完全透明 */
}

/* 步骤连接线基础样式 - 极细线 */
:deep(.el-step__line) {
  background: rgba(255, 255, 255, 0.08); /* 极淡的连接线 */
  transition: all 0.4s ease; /* 过渡动画 */
  height: 1px; /* 细线 */
}

/* 已完成步骤的连接线样式 - 优雅绿色 */
:deep(.el-step__line.is-finish) {
  background: rgba(34, 197, 94, 0.4); /* 现代绿色 */
  height: 2px; /* 稍粗连接线 */
}
</style>
