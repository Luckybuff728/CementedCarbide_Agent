<template>
  <div class="app-container">
    <!-- 顶部状态栏 -->
    <StatusBar 
      :connection-status="connectionStatus"
      :current-node="currentNode"
      :completed-nodes="completedNodes"
      @command="handleCommand"
    />

    <!-- 主工作区 - 三段式布局 -->
    <div class="main-workspace">
      <!-- 左侧参数输入面板 -->
      <LeftPanel 
        :loading="isProcessing"
        :connection-status="connectionStatus"
        @submit="handleFormSubmit"
      />

      <!-- 中间流式对话内容区域 -->
      <CenterStream 
        :process-steps="processSteps"
        :current-node="currentNode"
        :current-node-title="currentNodeTitle"
        :is-processing="isProcessing"
        :streaming-content="streamingContent"
        :p1-content="p1StreamingContent"
        :p2-content="p2StreamingContent"
        :p3-content="p3StreamingContent"
        :comprehensive-recommendation="analysisResults.comprehensiveRecommendation"
        @clear="clearMessages"
      />

      <!-- 右侧结果展示面板 -->
      <RightPanel 
        :analysis-results="analysisResults"
        :is-processing="isProcessing"
        :current-node="currentNode"
        :process-steps="processSteps"
        :current-node-title="currentNodeTitle"
        :p1-content="p1StreamingContent"
        :p2-content="p2StreamingContent"
        :p3-content="p3StreamingContent"
        :show-optimization-selection="showOptimizationSelection"
        @optimization-select="handleOptimizationSelect"
      />
    </div>
  </div>
</template>

<script setup>
// Vue 3组合式API核心导入
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
// Element Plus消息提示组件
import { ElMessage } from 'element-plus'
// 导入各功能组件
import StatusBar from './components/StatusBar.vue'         // 顶部状态栏组件
import LeftPanel from './components/LeftPanel.vue'         // 左侧参数输入面板组件
import CenterStream from './components/CenterStream.vue'   // 中间流式对话展示组件
import RightPanel from './components/RightPanel.vue'       // 右侧结果分析组件
// WebSocket通信组合式函数
import { useWebSocket } from './composables/useWebSocket'

// ============ 连接状态管理 ============
const connectionStatus = ref(false)  // WebSocket连接状态标识

// ============ 工作流过程状态管理（中间面板使用） ============
const processSteps = ref([])             // 存储工作流执行过程的步骤数组
const currentNode = ref('')              // 当前执行的节点ID
const currentNodeTitle = ref('')         // 当前节点的中文标题
const isProcessing = ref(false)          // 标识是否正在处理工作流
const streamingContent = ref('')         // 当前节点的流式输出内容

// ============ P1/P2/P3优化建议的独立流式内容存储 ============
// 使用独立的ref避免processSteps数组嵌套对象的响应式问题
const p1StreamingContent = ref('')       // P1成分优化的流式内容
const p2StreamingContent = ref('')       // P2结构优化的流式内容
const p3StreamingContent = ref('')       // P3工艺优化的流式内容

// ============ 分析结果数据管理（右侧面板使用） ============
const analysisResults = ref({        // 存储各个节点的分析结果
  performancePrediction: null,       // ML性能预测
  historicalComparison: null,        // 历史数据比对
  integratedAnalysis: null,          // 综合分析
  optimizationSuggestions: null,     // 优化建议（P1/P2/P3）
  comprehensiveRecommendation: '',   // 综合推荐
  experimentWorkorder: null          // 实验工单
})

// 是否显示优化方案选择界面
const showOptimizationSelection = ref(false)

// WebSocket连接实例和方法
const { connect, send, disconnect, isConnected } = useWebSocket()

// ============ 计算属性 ============
// 计算已完成的工作流节点列表，用于状态栏显示进度
const completedNodes = computed(() => {
  return processSteps.value
    .filter(step => step.status === 'completed')
    .map(step => step.nodeId)
})

// ============ 事件处理函数 ============
// 处理左侧面板表单提交事件
const handleFormSubmit = (formData) => {
  // 清空之前的数据（开始新任务）
  processSteps.value = []
  streamingContent.value = ''
  p1StreamingContent.value = ''
  p2StreamingContent.value = ''
  p3StreamingContent.value = ''
  analysisResults.value = {
    performancePrediction: null,
    historicalComparison: null,
    integratedAnalysis: null,
    optimizationSuggestions: null,
    comprehensiveRecommendation: ''
  }
  
  // 设置处理状态
  isProcessing.value = true
  currentNode.value = 'starting'
  currentNodeTitle.value = '正在启动分析...'
  
  // 转换数据格式以匹配后端期望的结构
  const structuredData = transformFormDataToBackendFormat(formData)
  
  // 通过WebSocket发送工作流启动请求到后端
  send({
    type: 'start_workflow',
    data: structuredData
  })
  
  ElMessage.success('已提交，开始分析...')
}

// 数据格式转换函数 - 将前端扁平化数据转换为后端期望的分组结构
const transformFormDataToBackendFormat = (formData) => {
  // 转换其他元素格式：name -> element
  const transformedOtherElements = (formData.other_elements || [])
    .filter(e => e.name && e.content) // 过滤空元素
    .map(e => ({
      element: e.name,  // 前端使用name，后端期望element
      content: e.content
    }))
  
  // 转换其他气体格式：保持type和flow
  const transformedOtherGases = (formData.other_gases || [])
    .filter(g => g.type && g.flow) // 过滤空气体
    .map(g => ({
      type: g.type,
      flow: g.flow
    }))
  
  // 转换层结构格式：保持type和thickness
  const transformedLayers = (formData.layers || [])
    .filter(l => l.type && l.thickness) // 过滤空层
    .map(l => ({
      type: l.type,
      thickness: l.thickness
    }))
  
  return {
    // 涂层成分参数
    composition: {
      al_content: formData.al_content || 0,
      ti_content: formData.ti_content || 0, 
      n_content: formData.n_content || 0,
      other_elements: transformedOtherElements
    },
    
    // 工艺参数
    process_params: {
      process_type: formData.process_type || 'magnetron_sputtering',
      deposition_pressure: formData.deposition_pressure || 0,
      deposition_temperature: formData.deposition_temperature || 0,
      bias_voltage: formData.bias_voltage || 0,
      n2_flow: formData.n2_flow || 0,
      ar_flow: formData.other_gases?.find(g => g.type === 'Ar')?.flow || 0,
      other_gases: transformedOtherGases
    },
    
    // 结构设计参数
    structure_design: {
      structure_type: formData.structure_type || 'single',
      total_thickness: formData.total_thickness || 0,
      layers: transformedLayers
    },
    
    // 性能需求参数
    target_requirements: {
      substrate_material: formData.substrate_material || '',
      adhesion_strength: formData.adhesion_strength || 0,
      elastic_modulus: formData.elastic_modulus || 0,
      working_temperature: formData.working_temperature || 0,
      cutting_speed: formData.cutting_speed || 0,
      application_scenario: formData.application_scenario || ''
    }
  }
}

// 处理右侧面板优化方案选择事件
const handleOptimizationSelect = (option) => {
  console.log('用户选择优化方案:', option)
  
  // 隐藏选择界面
  showOptimizationSelection.value = false
  
  // 添加选择步骤
  processSteps.value.push({
    id: Date.now(),
    nodeId: 'user_selection',
    title: '用户选择方案',
    status: 'completed',
    content: `已选择 ${option} 优化方案`,
    timestamp: new Date().toISOString()
  })
  
  // 发送工单生成请求（新的独立请求）
  send({
    type: 'generate_workorder',
    selected_option: option  // P1/P2/P3
  })
  
  // 设置处理状态
  isProcessing.value = true
  currentNode.value = 'experiment_workorder'
  currentNodeTitle.value = '实验工单生成'
  
  ElMessage.success(`已选择 ${option}，正在生成实验工单...`)
}

// 处理顶部状态栏命令按钮点击事件
const handleCommand = (command) => {
  switch (command) {
    case 'export':    // 导出结果功能
      exportResults()
      break
    case 'clear':     // 清空对话功能
      clearMessages()
      break
    case 'settings':  // 打开设置功能
      openSettings()
      break
  }
}

// ============ 工具函数 ============
// 清空所有数据和重置状态
const clearMessages = () => {
  processSteps.value = []      // 清空过程步骤
  streamingContent.value = ''  // 清空流式内容
  p1StreamingContent.value = ''
  p2StreamingContent.value = ''
  p3StreamingContent.value = ''
  isProcessing.value = false   // 重置处理状态
  currentNode.value = ''       // 清空当前节点
  currentNodeTitle.value = ''  // 清空节点标题
  showOptimizationSelection.value = false  // 隐藏选择界面
  analysisResults.value = {    // 重置结果数据
    performancePrediction: null,
    historicalComparison: null,
    integratedAnalysis: null,
    optimizationSuggestions: null,
    comprehensiveRecommendation: '',
    experimentWorkorder: null
  }
  ElMessage.success('已清空所有数据')
}

// 导出分析结果为JSON文件
const exportResults = () => {
  // 检查是否有结果可导出
  const hasResults = Object.values(analysisResults.value).some(v => v !== null && v !== '')
  if (!hasResults) {
    ElMessage.warning('暂无结果可导出')
    return
  }
  
  // 构建导出数据结构
  const exportData = {
    timestamp: new Date().toISOString(),
    processSteps: processSteps.value,
    analysisResults: analysisResults.value
  }
  
  // 创建JSON文件并下载
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `topmat_results_${new Date().toISOString().slice(0, 19)}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('结果已导出')
}

// 打开系统设置面板（功能开发中）
const openSettings = () => {
  ElMessage.info('设置功能开发中...')
}

// ============ WebSocket消息处理核心函数 ============
// 节点标题映射
const nodeNameMap = {
  'input_validation': '参数验证',
  'topphi_simulation': 'TopPhi第一性原理模拟',
  'ml_prediction': 'ML模型性能预测',
  'historical_comparison': '历史数据比对',
  'integrated_analysis': '根因分析',
  'optimization_suggestions': '优化建议生成',
  'p1_composition_optimization': 'P1成分优化分析',
  'p2_structure_optimization': 'P2结构优化分析',
  'p3_process_optimization': 'P3工艺优化分析',
  'optimization_summary': '优化方案汇总',
  'await_user_selection': '等待方案选择',
  'experiment_workorder': '实验工单生成'
}

// 处理来自后端的WebSocket消息
const handleWebSocketMessage = (message) => {
  console.log('收到WebSocket消息:', message)
  
  switch (message.type) {
    case 'connected':  // 前端WebSocket初始连接成功消息
      console.log('WebSocket初始化完成')
      break
      
    case 'node_output':  // 工作流节点输出（后端实际发送的事件）
      handleNodeOutput(message.data)
      break
      
    case 'llm_stream':  // LLM流式输出（后端实际发送的事件）
      handleLLMStream(message)
      break
      
    case 'connection':  // 连接状态（后端确认消息）
      console.log('WebSocket连接状态:', message.status)
      break
      
    case 'status':  // 状态更新
      if (message.node) {
        currentNode.value = message.node
        currentNodeTitle.value = nodeNameMap[message.node] || message.node
      }
      break
      
    case 'workflow_completed':  // 工作流完成（优化建议生成完成）
      isProcessing.value = false
      streamingContent.value = ''
      currentNode.value = 'optimization_completed'
      currentNodeTitle.value = '优化方案生成完成'
      showOptimizationSelection.value = true  // 显示选择界面
      ElMessage.success('优化建议生成完成，请选择一个方案')
      break
      
    case 'workorder_generation_started':  // 工单生成开始
      currentNode.value = 'experiment_workorder'
      currentNodeTitle.value = '实验工单生成'
      streamingContent.value = ''
      break
      
    case 'workorder_generated':  // 工单生成完成
      isProcessing.value = false
      // 保存工单数据
      if (message.data) {
        analysisResults.value.experimentWorkorder = message.data.experiment_workorder
        
        // 查找是否已有experiment_workorder步骤（流式输出过程中可能创建）
        const workorderStepIndex = processSteps.value.findIndex(s => s.nodeId === 'experiment_workorder')
        const workorderContent = message.data.experiment_workorder || '实验工单生成完成'
        
        if (workorderStepIndex !== -1) {
          // 已存在，更新为completed状态并保存完整内容
          processSteps.value[workorderStepIndex] = {
            ...processSteps.value[workorderStepIndex],
            status: 'completed',
            content: workorderContent,
            title: `实验工单 - ${message.data.selected_optimization_name}`
          }
          console.log(`[workorder_generated] 更新工单步骤，内容长度: ${workorderContent.length}`)
        } else {
          // 不存在，创建新步骤（保存完整工单内容）
          processSteps.value.push({
            id: Date.now(),
            nodeId: 'experiment_workorder',
            title: `实验工单 - ${message.data.selected_optimization_name}`,
            status: 'completed',
            content: workorderContent,
            timestamp: new Date().toISOString()
          })
          console.log(`[workorder_generated] 创建工单步骤，内容长度: ${workorderContent.length}`)
        }
      }
      // 清空当前节点状态，让已完成的工单步骤在中间panel显示出来
      currentNode.value = ''
      currentNodeTitle.value = ''
      // 清空流式内容
      streamingContent.value = ''
      ElMessage.success('实验工单生成完成！')
      break
      
    case 'error':  // 错误处理
      isProcessing.value = false
      streamingContent.value = ''
      ElMessage.error(message.message || '处理过程中出现错误')
      // 添加错误步骤
      processSteps.value.push({
        id: Date.now(),
        nodeId: 'error',
        title: '发生错误',
        status: 'error',
        content: message.message,
        timestamp: new Date().toISOString()
      })
      break
      
    default:
      console.warn('未处理的消息类型:', message.type)
  }
}

// 处理节点输出数据
const handleNodeOutput = (nodeData) => {
  if (!nodeData) return
  
  // 提取节点信息
  const firstKey = Object.keys(nodeData)[0]
  const stateData = nodeData[firstKey]
  
  if (!stateData) return
  
  const nodeId = firstKey
  const nodeTitle = nodeNameMap[nodeId] || nodeId
  
  // 更新当前节点（重要：让前端知道工作流进度）
  currentNode.value = nodeId
  currentNodeTitle.value = nodeTitle
  
  // 生成节点完成的具体内容
  const nodeContent = generateNodeCompletionContent(nodeId, stateData)
  
  // 添加或更新处理步骤
  const stepIndex = processSteps.value.findIndex(s => s.nodeId === nodeId)
  if (stepIndex !== -1) {
    // 节点已存在（之前通过llm_stream创建），更新为completed
    const existingStep = processSteps.value[stepIndex]
    // 创建新对象替换旧对象（触发响应式更新）
    processSteps.value[stepIndex] = {
      ...existingStep,
      status: 'completed',
      // 如果有流式输出，保留流式内容；否则使用生成的节点内容
      content: (existingStep.content && existingStep.content.trim()) 
        ? existingStep.content 
        : (nodeContent || '节点执行完成')
    }
    console.log(`[handleNodeOutput] 更新节点 ${nodeId}，内容长度: ${processSteps.value[stepIndex].content?.length}`)
  } else {
    // 节点不存在（没有llm_stream的节点），直接创建completed状态
    processSteps.value.push({
      id: Date.now(),
      nodeId: nodeId,
      title: nodeTitle,
      status: 'completed',
      content: nodeContent || '节点执行完成',
      timestamp: new Date().toISOString()
    })
    console.log(`[handleNodeOutput] 创建节点 ${nodeId}，内容长度: ${nodeContent?.length}`)
  }
  
  // 清空流式内容，准备下一个节点
  streamingContent.value = ''
  
  // 提取并存储结果数据
  if (stateData.performance_prediction) {
    analysisResults.value.performancePrediction = stateData.performance_prediction
  }
  if (stateData.historical_comparison) {
    analysisResults.value.historicalComparison = stateData.historical_comparison
  }
  if (stateData.integrated_analysis) {
    analysisResults.value.integratedAnalysis = stateData.integrated_analysis
  }
  if (stateData.optimization_suggestions) {
    analysisResults.value.optimizationSuggestions = stateData.optimization_suggestions
  }
  if (stateData.comprehensive_recommendation) {
    analysisResults.value.comprehensiveRecommendation = stateData.comprehensive_recommendation
  }
  
  // 处理 await_user_selection 节点的 interrupt 数据
  if (nodeId === 'await_user_selection' && stateData.type === 'user_selection_required') {
    // 从 interrupt value 中提取数据
    if (stateData.suggestions) {
      analysisResults.value.optimizationSuggestions = stateData.suggestions
    }
    if (stateData.comprehensive_recommendation) {
      analysisResults.value.comprehensiveRecommendation = stateData.comprehensive_recommendation
    }
  }
  
  // 检查工作流是否完成
  if (stateData.workflow_status === 'completed' || nodeId === 'result_summary' || nodeId === 'experiment_workorder') {
    isProcessing.value = false
    ElMessage.success('分析完成！')
  }
  
  // 检查是否需要用户输入
  if (nodeId === 'await_user_selection') {
    // 等待用户选择优化方案
    ElMessage.info('请在右侧面板选择优化方案')
  }
}

// 处理LLM流式输出
const handleLLMStream = (data) => {
  const { node, content } = data
  
  // P1/P2/P3优化节点：使用专用的响应式变量（并行执行）
  if (node === 'p1_composition_optimization') {
    p1StreamingContent.value += content
    // 切换到优化方案生成状态（移除条件检查，避免时序混乱）
    if (currentNode.value !== 'optimization_suggestions' && 
        currentNode.value !== 'p1_composition_optimization' &&
        currentNode.value !== 'p2_structure_optimization' &&
        currentNode.value !== 'p3_process_optimization') {
      currentNode.value = 'optimization_suggestions'
      currentNodeTitle.value = '优化建议生成'
    }
    return
  }
  if (node === 'p2_structure_optimization') {
    p2StreamingContent.value += content
    // 切换到优化方案生成状态
    if (currentNode.value !== 'optimization_suggestions' && 
        currentNode.value !== 'p1_composition_optimization' &&
        currentNode.value !== 'p2_structure_optimization' &&
        currentNode.value !== 'p3_process_optimization') {
      currentNode.value = 'optimization_suggestions'
      currentNodeTitle.value = '优化建议生成'
    }
    return
  }
  if (node === 'p3_process_optimization') {
    p3StreamingContent.value += content
    // 切换到优化方案生成状态
    if (currentNode.value !== 'optimization_suggestions' && 
        currentNode.value !== 'p1_composition_optimization' &&
        currentNode.value !== 'p2_structure_optimization' &&
        currentNode.value !== 'p3_process_optimization') {
      currentNode.value = 'optimization_suggestions'
      currentNodeTitle.value = '优化建议生成'
    }
    return
  }
  
  // 工单生成节点：使用processSteps存储（与根因分析等节点保持一致）
  if (node === 'experiment_workorder') {
    // 确保currentNode已设置
    if (currentNode.value !== 'experiment_workorder') {
      currentNode.value = 'experiment_workorder'
      currentNodeTitle.value = '实验工单生成'
    }
    // 继续使用通用逻辑处理（不return，让它走下面的processSteps逻辑）
  }
  
  // 其他节点（包括experiment_workorder）：使用processSteps数组存储
  const stepIndex = processSteps.value.findIndex(s => s.nodeId === node)
  
  if (stepIndex === -1) {
    // 第一次收到这个节点的流式输出，创建步骤
    const newStep = {
      id: Date.now(),
      nodeId: node,
      title: nodeNameMap[node] || node,
      status: 'processing',
      content: content,
      timestamp: new Date().toISOString()
    }
    processSteps.value.push(newStep)
    
    // 更新当前节点指示
    currentNode.value = node
    currentNodeTitle.value = nodeNameMap[node] || node
  } else {
    // 节点已存在，创建新对象替换旧对象（触发响应式更新）
    const oldStep = processSteps.value[stepIndex]
    processSteps.value[stepIndex] = {
      ...oldStep,
      content: (oldStep.content || '') + (content || '')
    }
  }
  
  // 更新全局streamingContent用于实时显示
  if (node === currentNode.value) {
    const currentStep = processSteps.value.find(s => s.nodeId === node)
    streamingContent.value = currentStep?.content || ''
  }
}

// ============ 生命周期和监听器 ============
// 监听WebSocket连接状态变化，同步更新界面连接状态
watch(isConnected, (connected) => {
  connectionStatus.value = connected  // 同步连接状态到界面显示
})

// 组件挂载生命周期：建立WebSocket连接
onMounted(() => {
  // 连接到后端WebSocket服务器，传入消息处理函数
  connect('ws://localhost:8000/ws/coating', handleWebSocketMessage)
})

// 组件卸载生命周期：清理WebSocket连接
// 生成节点完成内容
const generateNodeCompletionContent = (nodeId, stateData) => {
  switch (nodeId) {
    case 'input_validation':
      if (stateData.input_validated) {
        const composition = stateData.preprocessed_data?.coating_composition || {}
        const params = stateData.preprocessed_data?.process_params || {}
        const structure = stateData.preprocessed_data?.structure_design || {}
        const target = stateData.preprocessed_data?.target_requirements || {}
        
        // 构建成分配比显示
        let compositionText = `- Al含量: ${composition.al_content || 0}%
- Ti含量: ${composition.ti_content || 0}%  
- N含量: ${composition.n_content || 0}%`
        
        if (composition.other_elements?.length > 0) {
          compositionText += `\n- 其他元素: ${composition.other_elements.map(e => `${e.element} ${e.content}%`).join(', ')}`
        }
        
        // 构建工艺参数显示
        let processText = `- 工艺类型: ${params.process_type || 'N/A'}
- 沉积压力: ${params.deposition_pressure || 0} Pa
- 沉积温度: ${params.deposition_temperature || 0} °C
- 偏压: ${params.bias_voltage || 0} V
- N₂流量: ${params.n2_flow || 0} sccm`
        
        if (params.other_gases?.length > 0) {
          processText += `\n- 其他气体: ${params.other_gases.map(g => `${g.type} ${g.flow} sccm`).join(', ')}`
        }
        
        // 构建结构设计显示
        let structureText = `- 结构类型: ${structure.structure_type || '单层'}`
        
        if (structure.structure_type === 'multi' && structure.layers?.length > 0) {
          structureText += `\n- 层结构: ${structure.layers.map((l, i) => `第${i+1}层(${l.type}, ${l.thickness}μm)`).join('; ')}`
        } else {
          structureText += `\n- 总厚度: ${structure.total_thickness || 0} μm`
        }
        
        // 构建性能需求显示
        let targetText = `- 基材材料: ${target.substrate_material || 'N/A'}
- 结合力: ${target.adhesion_strength || 0} N
- 弹性模量: ${target.elastic_modulus || 0} GPa
- 工作温度: ${target.working_temperature || 0} °C
- 切削速度: ${target.cutting_speed || 0} m/min`
        
        if (target.application_scenario) {
          targetText += `\n- 应用场景: ${target.application_scenario}`
        }
        
        return `### 参数验证通过 ✅

**成分配比**
${compositionText}

**工艺参数**
${processText}

**结构设计**
${structureText}

**性能需求**
${targetText}

✅ 所有输入参数已验证通过，可以继续后续分析。`
      } else {
        return `### 参数验证失败 ❌\n\n${(stateData.validation_errors || []).join('\n')}`
      }
      
    case 'topphi_simulation':
      const topphi = stateData.topphi_simulation || {}
      return `### TopPhi理论计算完成 🔬

**结构预测结果**
- 晶粒尺寸: **${topphi.grain_size_nm || 'N/A'} nm**
- 优选取向: ${topphi.preferred_orientation || 'N/A'}
- 残余应力: ${topphi.residual_stress_gpa || 'N/A'} GPa
- 晶格常数: ${topphi.lattice_constant || 'N/A'} Å

**计算置信度**: ${((topphi.confidence || 0) * 100).toFixed(1)}%`

    case 'ml_prediction':
      const ml = stateData.ml_prediction || {}
      return `### ML性能预测完成 🎯

**预测结果**
- **硬度预测: ${ml.hardness_gpa || 'N/A'} GPa**
- 杨氏模量: ${ml.elastic_modulus_gpa || 'N/A'} GPa
- 泊松比: ${ml.poisson_ratio || 'N/A'}

**预测置信度**: ${((ml.confidence || 0) * 100).toFixed(1)}%
**模型版本**: ${ml.model_version || 'N/A'}`

    case 'historical_comparison':
      const historical = stateData.historical_comparison || {}
      const cases = historical.similar_cases || []
      return `### 历史对比分析完成 📊

**找到 ${cases.length} 个相似案例**

${cases.map((c, i) => `
**案例 ${i + 1}** (相似度: ${(c.similarity * 100).toFixed(1)}%)
- 成分: Al${c.composition?.al_content}% Ti${c.composition?.ti_content}% N${c.composition?.n_content}%
- 硬度: ${c.hardness} GPa
- 备注: ${c.notes}
`).join('')}

这些案例为当前配方提供了重要的参考数据。`

    case 'integrated_analysis':
      const analysis = stateData.integrated_analysis || {}
      const summary = analysis.performance_summary || {}
      return `### 根因分析完成 📈

**最终预测结果**
- **预测硬度: ${summary.predicted_hardness || 'N/A'} GPa**
- **置信度: ${((summary.confidence || 0) * 100).toFixed(1)}%**

**关键发现**
${(summary.key_findings || []).map(f => `- ${f}`).join('\n')}

**优化建议**: ${analysis.recommendation || '无特殊建议'}`

    default:
      return `### ${nodeId} 完成\n\n节点执行成功，详细结果请查看右侧面板。`
  }
}

onUnmounted(() => {
  disconnect()  // 断开WebSocket连接，释放资源
})
</script>

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
  position: relative;
}

/* 确保三段式布局协调 */
.main-workspace > *:first-child {
  /* 左侧面板 */
  flex-shrink: 0;
}

.main-workspace > *:nth-child(2) {
  /* 中间内容区 */
  flex: 1;
  min-width: 0; /* 允许内容收缩 */
}

.main-workspace > *:last-child {
  /* 右侧面板 */  
  flex-shrink: 0;
}

.experiment-form {
  padding: 16px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* Element Plus样式调整 */
:deep(.el-card) {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select .el-input .el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
}

:deep(.el-dialog__body) {
  padding: 16px 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
}
</style>
