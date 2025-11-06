<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from './stores/workflow'
import { useWebSocket } from './composables/useWebSocket'

import StatusBar from './components/StatusBar.vue'
import LeftPanel from './components/LeftPanel.vue'
import CenterPanel from './components/CenterPanel.vue'
import RightPanel from './components/RightPanel.vue'

// 使用Store和WebSocket
const workflowStore = useWorkflowStore()
const { connect, send, disconnect, isConnected } = useWebSocket()

// 中间面板引用（用于滚动控制）
const centerPanelRef = ref(null)

// 面板宽度
const leftWidth = ref(320)
const rightWidth = ref(380)

// 拖动状态
let isResizing = false
let resizeDirection = null
let startX = 0
let startWidth = 0

// 监听连接状态
watch(isConnected, (connected) => {
  workflowStore.isConnected = connected
})

// 表单提交处理
const handleFormSubmit = (formData) => {
  // 重置状态
  workflowStore.reset()
  workflowStore.isProcessing = true
  
  // 发送工作流启动请求
  send({
    type: 'start_workflow',
    data: formData
  })
  
  ElMessage.success('已提交，开始分析...')
}

// 优化方案选择处理
const handleOptimizationSelect = (option) => {
  workflowStore.selectedOptimization = option
  workflowStore.showOptimizationSelection = false
  
  // 发送工单生成请求
  send({
    type: 'generate_workorder',
    selected_option: option
  })
  
  workflowStore.isProcessing = true
  workflowStore.currentNode = 'experiment_workorder'
  workflowStore.currentNodeTitle = '实验工单生成'
  
  ElMessage.success(`已选择 ${option}，正在生成工单...`)
}

// 节点跳转处理
const handleJumpToNode = (nodeId) => {
  if (centerPanelRef.value) {
    centerPanelRef.value.scrollToNode(nodeId)
  }
}

// 导出处理
const handleExport = () => {
  try {
    const exportData = {
      timestamp: new Date().toISOString(),
      processSteps: workflowStore.processSteps,
      performancePrediction: workflowStore.performancePrediction,
      historicalComparison: workflowStore.historicalComparison,
      integratedAnalysis: workflowStore.integratedAnalysis,
      p1Content: workflowStore.p1Content,
      p2Content: workflowStore.p2Content,
      p3Content: workflowStore.p3Content,
      comprehensiveRecommendation: workflowStore.comprehensiveRecommendation,
      experimentWorkorder: workflowStore.experimentWorkorder
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `topmat_analysis_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('数据已导出')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 清空处理
const handleClear = () => {
  // 由StatusBar组件处理确认对话框和清空操作
}

// 开始拖动
const startResize = (e, direction) => {
  isResizing = true
  resizeDirection = direction
  startX = e.clientX
  startWidth = direction === 'left' ? leftWidth.value : rightWidth.value
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

// 拖动中
const handleResize = (e) => {
  if (!isResizing) return
  
  const delta = e.clientX - startX
  
  if (resizeDirection === 'left') {
    // 左侧面板：向右拖动增大，向左拖动减小
    const newWidth = startWidth + delta
    leftWidth.value = Math.max(200, Math.min(600, newWidth))
  } else if (resizeDirection === 'right') {
    // 右侧面板：向左拖动增大，向右拖动减小
    const newWidth = startWidth - delta
    rightWidth.value = Math.max(200, Math.min(600, newWidth))
  }
}

// 停止拖动
const stopResize = () => {
  isResizing = false
  resizeDirection = null
  
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// WebSocket消息处理
const handleWebSocketMessage = (message) => {
  console.log('[WS消息]', message.type)
  
  switch (message.type) {
    case 'node_output':
      handleNodeOutput(message.data)
      break
    case 'llm_stream':
      handleLLMStream(message)
      break
    case 'workflow_completed':
      workflowStore.isProcessing = false
      workflowStore.showOptimizationSelection = true
      ElMessage.success('优化方案生成完成，请选择')
      break
    case 'workorder_generated':
      workflowStore.isProcessing = false
      workflowStore.experimentWorkorder = message.data?.experiment_workorder
      ElMessage.success('实验工单生成完成')
      break
    case 'error':
      workflowStore.isProcessing = false
      ElMessage.error(message.message || '处理出错')
      break
  }
}

// 生成结构化内容显示
const generateStructuredContent = (nodeId, data) => {
  // 根据不同节点类型生成不同格式的内容
  if (nodeId === 'topphi_simulation') {
    const topphi = data.topphi_simulation || data
    return `## TopPhi第一性原理模拟结果

### 晶体结构参数
- **晶粒尺寸**: ${topphi.grain_size_nm || 'N/A'} nm
- **择优取向**: ${topphi.preferred_orientation || 'N/A'}
- **残余应力**: ${topphi.residual_stress_gpa || 'N/A'} GPa
- **晶格常数**: ${topphi.lattice_constant || 'N/A'} Å

### 能量计算
- **形成能**: ${topphi.formation_energy || 'N/A'} eV
- **计算置信度**: ${((topphi.confidence || 0) * 100).toFixed(1)}%
- **模拟耗时**: ${topphi.simulation_time || 'N/A'} 秒

模拟计算完成，数据已就绪。`
  }
  
  if (nodeId === 'ml_prediction') {
    const mlData = data.performance_prediction || data.ml_prediction || data
    return `## ML模型性能预测结果

### 预测性能指标
- **硬度**: ${mlData.hardness || mlData.hardness_gpa || 'N/A'} GPa
- **结合力等级**: ${mlData.adhesion_level || 'N/A'}
- **磨损率**: ${mlData.wear_rate || 'N/A'}
- **氧化温度**: ${mlData.oxidation_temperature || mlData.oxidation_temp_c || 'N/A'}°C

### 沉积结构预测
- **晶粒尺寸**: ${mlData.deposition_structure?.grain_size || 'N/A'}
- **择优取向**: ${mlData.deposition_structure?.preferred_orientation || 'N/A'}
- **残余应力**: ${mlData.deposition_structure?.residual_stress || 'N/A'}

### 模型置信度
- **综合置信度**: ${((mlData.confidence_score || 0) * 100).toFixed(1)}%
- **数据来源**: ${mlData.data_sources?.join(', ') || 'ML模型预测'}

性能预测完成，建议参考上述数据进行优化。`
  }
  
  if (nodeId === 'historical_comparison') {
    const histData = data.historical_comparison || data
    return `## 历史数据比对结果

### 匹配案例统计
- **相似案例数**: ${histData.total_cases || histData.length || 0} 个
- **最高硬度**: ${histData.highest_hardness || 'N/A'} GPa
- **平均相似度**: ${histData.average_similarity ? (histData.average_similarity * 100).toFixed(1) + '%' : 'N/A'}

### 相似案例预览
${histData.similar_cases ? histData.similar_cases.slice(0, 3).map((c, i) => 
  `${i + 1}. **相似度**: ${(c.similarity * 100).toFixed(1)}% | **硬度**: ${c.hardness} GPa`
).join('\n') : '暂无相似案例'}

历史数据比对完成，可参考相似案例优化方案。`
  }
  
  // 默认显示
  return `## ${nodeId} 执行完成

节点处理成功，数据已保存。`
}

// 处理节点输出 - 只负责标记状态为completed
const handleNodeOutput = (data) => {
  // data格式: { "input_validation": {...}, "topphi_simulation": {...}, ...}
  
  console.log('[🔍 前端接收] node_output数据类型:', typeof data)
  console.log('[🔍 前端接收] node_output数据键:', Object.keys(data || {}))
  
  if (!data || typeof data !== 'object') {
    console.warn('[❌ 状态] node_output数据无效:', data)
    return
  }
  
  // 遍历chunk中的所有节点
  for (const [nodeId, nodeData] of Object.entries(data)) {
    console.log(`[🔍 前端处理] 节点=${nodeId}, 数据类型=${typeof nodeData}`)
    
    // 跳过非节点字段（如__typename等）
    if (!nodeId || typeof nodeData !== 'object' || nodeId.startsWith('__')) {
      console.log(`[⏭️ 跳过] 节点=${nodeId}`)
      continue
    }
    
    // 查找该节点的step
    const step = workflowStore.processSteps.find(s => s.nodeId === nodeId)
    
    if (step) {
      // 节点已存在（llm_stream创建的），只标记为完成，保留流式内容
      const oldStatus = step.status
      step.status = 'completed'
      console.log(`[✅ 状态更新] ${nodeId}: ${oldStatus} → completed，内容长度: ${step.content?.length || 0}`)
    } else {
      // 节点不存在（某些节点可能没有llm_stream），直接创建为completed
      // 生成结构化的内容显示
      const structuredContent = generateStructuredContent(nodeId, nodeData)
      
      workflowStore.addProcessStep({
        nodeId: nodeId,
        status: 'completed',
        content: structuredContent
      })
      
      console.log(`[✅ 状态创建] ${nodeId} → completed (生成结构化内容)`)
    }
    
    // ⚠️ 关键修复：节点完成后，清除currentNode（如果是当前节点）
    if (workflowStore.currentNode === nodeId) {
      workflowStore.currentNode = ''
      console.log(`[🔄 清除currentNode] ${nodeId}已完成`)
    }
    
    // 存储特定节点的数据到store
    if (nodeId === 'input_validation') {
      // 存储验证结果（包含错误信息）
      console.log('[🔍 input_validation] 原始数据:', nodeData)
      console.log('[🔍 input_validation] input_validated=', nodeData.input_validated)
      console.log('[🔍 input_validation] validation_errors=', nodeData.validation_errors)
      console.log('[🔍 input_validation] workflow_status=', nodeData.workflow_status)
      
      const validationData = {
        input_validated: nodeData.input_validated !== false,  // 是否验证通过
        validation_errors: nodeData.validation_errors || [],  // 错误列表
        workflow_status: nodeData.workflow_status || 'validated'
      }
      workflowStore.validationResult = validationData
      console.log('[💾 存储] 验证结果:', validationData)
    }
    if (nodeId === 'ml_prediction') {
      // 数据结构: { ml_prediction: { hardness_gpa, adhesion_level, ... }, performance_prediction: {...} }
      // 优先使用performance_prediction（整合后的数据），其次使用ml_prediction
      let predData = nodeData.performance_prediction || nodeData.ml_prediction || nodeData
      
      // 如果ml_prediction存在但没有performance_prediction，手动构建
      if (!nodeData.performance_prediction && nodeData.ml_prediction) {
        const ml = nodeData.ml_prediction
        predData = {
          hardness: ml.hardness_gpa,
          hardness_gpa: ml.hardness_gpa,
          adhesion_level: ml.adhesion_level,
          oxidation_temp_c: ml.oxidation_temp_c,
          oxidation_temperature: ml.oxidation_temp_c,
          model_confidence: ml.model_confidence,
          confidence_score: ml.model_confidence
        }
      }
      
      if (predData && typeof predData === 'object') {
        workflowStore.performancePrediction = predData
        console.log('[存储] ML预测数据:', predData)
      }
    }
    if (nodeId === 'historical_comparison') {
      // 可能是 nodeData.historical_comparison 或直接是 nodeData
      const histData = nodeData.historical_comparison || nodeData
      if (histData) {
        workflowStore.historicalComparison = histData
        console.log('[存储] 历史比对数据:', histData)
      }
    }
    if (nodeId === 'integrated_analysis') {
      // 可能是 nodeData.integrated_analysis 或直接是 nodeData
      const analysisData = nodeData.integrated_analysis || nodeData
      if (analysisData && typeof analysisData === 'object') {
        workflowStore.integratedAnalysis = analysisData
        console.log('[存储] 综合分析数据:', analysisData)
      }
    }
    
    // 存储实验工单
    if (nodeId === 'experiment_workorder') {
      const workorderData = nodeData.experiment_workorder || nodeData.workorder || nodeData
      if (workorderData && typeof workorderData === 'string') {
        workflowStore.experimentWorkorder = workorderData
        console.log('[存储] 实验工单数据')
      }
    }
  }
}

// LLM流式输出处理 - 最简化版本
const handleLLMStream = (data) => {
  const { node, content } = data
  
  if (!node || !content) {
    console.log('[⏭️ llm_stream跳过] node或content为空')
    return
  }
  
  console.log(`[📝 llm_stream] 节点=${node}, 内容长度=${content.length}`)
  
  // P1/P2/P3使用独立存储
  if (node === 'p1_composition_optimization') {
    workflowStore.p1Content += content
    return
  }
  if (node === 'p2_structure_optimization') {
    workflowStore.p2Content += content
    return
  }
  if (node === 'p3_process_optimization') {
    workflowStore.p3Content += content
    return
  }
  
  // 其他节点更新processSteps
  const step = workflowStore.processSteps.find(s => s.nodeId === node)
  
  if (step) {
    // 节点已存在，追加内容
    step.content += content
    console.log(`[📝 追加内容] ${node}, 当前总长度=${step.content.length}`)
  } else {
    // 节点不存在，创建为processing状态
    workflowStore.addProcessStep({
      nodeId: node,
      status: 'processing',
      content: content
    })
    
    // 更新当前节点
    workflowStore.currentNode = node
    
    console.log(`[🟡 状态创建] ${node} → processing (首次流式内容)`)
  }
}

// 生命周期
onMounted(() => {
  connect('ws://192.168.6.108:8000/ws/coating', handleWebSocketMessage)
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="app-container">
    <!-- 顶部状态栏 -->
    <StatusBar 
      @jump-to-node="handleJumpToNode"
      @export="handleExport"
      @clear="handleClear"
    />
    
    <!-- 主工作区 - 三段式布局 -->
    <div class="main-workspace">
      <!-- 左侧表单 -->
      <LeftPanel 
        :style="{ width: `${leftWidth}px` }"
        @submit="handleFormSubmit"
      />
      
      <!-- 左侧拖动条 -->
      <div 
        class="resizer left-resizer"
        @mousedown="startResize($event, 'left')"
      ></div>
      
      <!-- 中间流程展示 -->
      <CenterPanel 
        ref="centerPanelRef"
        :style="{ flex: 1 }"
      />
      
      <!-- 右侧拖动条 -->
      <div 
        class="resizer right-resizer"
        @mousedown="startResize($event, 'right')"
      ></div>
      
      <!-- 右侧结果摘要 -->
      <RightPanel 
        :style="{ width: `${rightWidth}px` }"
        @optimization-select="handleOptimizationSelect"
        @jump-to-node="handleJumpToNode"
      />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

.main-workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 拖动条样式 */
.resizer {
  width: 4px;
  background: var(--border-color);
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
}

.resizer:hover {
  background: var(--primary);
}

.resizer::before {
  content: '';
  position: absolute;
  left: -2px;
  right: -2px;
  top: 0;
  bottom: 0;
}

.left-resizer:hover,
.right-resizer:hover {
  background: var(--primary);
  width: 4px;
}
</style>
