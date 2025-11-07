/**
 * 工作流消息处理逻辑 - 从App.vue提取
 * 负责处理WebSocket消息、节点输出、LLM流式输出
 */
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '../stores/workflow'

export function useWorkflowHandler(setLongTaskStatus = null) {
  const workflowStore = useWorkflowStore()
  
  // 长时间任务检测节点
  const LONG_TASK_NODES = [
    'p1_composition_optimization',
    'p2_structure_optimization', 
    'p3_process_optimization',
    'optimization_summary',
    'experiment_workorder',
    'integrated_analysis'
  ]
  
  /**
   * 生成结构化内容显示
   * @param {string} nodeId - 节点ID
   * @param {object} data - 节点数据
   * @returns {string} 格式化的Markdown内容
   */
  const generateStructuredContent = (nodeId, data) => {
    // TopPhi相场模拟结果
    if (nodeId === 'topphi_simulation') {
      const topphi = data.topphi_simulation || data
      return `模拟计算完成，数据已就绪。`
//       ## TopPhi相场模拟结果

// ### 晶体结构参数
// - **晶粒尺寸**: ${topphi.grain_size_nm || 'N/A'} nm
// - **择优取向**: ${topphi.preferred_orientation || 'N/A'}
// - **残余应力**: ${topphi.residual_stress_gpa || 'N/A'} GPa
// - **晶格常数**: ${topphi.lattice_constant || 'N/A'} Å

// ### 能量计算
// - **形成能**: ${topphi.formation_energy || 'N/A'} eV
// - **计算置信度**: ${((topphi.confidence || 0) * 100).toFixed(1)}%
// - **模拟耗时**: ${topphi.simulation_time || 'N/A'} 秒

// 模拟计算完成，数据已就绪。`
    }
    
    // ML模型预测结果
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
    
    // 历史数据比对结果
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
    return `## ${nodeId} 执行完成\n\n节点处理成功，数据已保存。`
  }
  
  /**
   * 处理节点输出 - 只负责标记状态为completed
   * @param {object} data - 节点输出数据
   */
  const handleNodeOutput = (data) => {
    console.log('[📥 node_output] 处理节点输出:', Object.keys(data))
    
    // 检查是否为长时间任务节点完成，如果是则退出长任务模式
    const completedNodes = Object.keys(data)
    const hasLongTaskCompleted = completedNodes.some(node => LONG_TASK_NODES.includes(node))
    if (hasLongTaskCompleted && setLongTaskStatus) {
      console.log('[⏱️ 长时间任务] 检测到长任务节点完成，退出长任务模式')
      setLongTaskStatus(false)
    }
    console.log('[🔍 前端接收] node_output数据键:', Object.keys(data || {}))
    
    if (!data || typeof data !== 'object') {
      console.warn('[❌ 状态] node_output数据无效:', data)
      return
    }
    
    // ✅ 修复：历史查看模式下仍然处理数据，只是不显示
    // ✅ 修复：历史查看模式下仍然处理状态，只是不显示通知
    const isInHistoryMode = workflowStore.viewMode === 'history'
    if (isInHistoryMode) {
      console.log('[💾 数据处理] 历史查看模式下仍然处理状态')
    }
    
    // 遍历chunk中的所有节点
    for (const [nodeId, nodeData] of Object.entries(data)) {
      console.log(`[📦 处理节点] ${nodeId}, 数据类型: ${typeof nodeData}`)
      
      const step = workflowStore.processSteps.find(s => s.nodeId === nodeId)
      
      if (step) {
        // 节点已存在（llm_stream创建的），只标记为完成，保留流式内容
        const oldStatus = step.status
        step.status = 'completed'
        console.log(`[✅ 状态更新] ${nodeId}: ${oldStatus} → completed，内容长度: ${step.content?.length || 0}`)
      } else {
        // 节点不存在（某些节点可能没有llm_stream），直接创建为completed
        const structuredContent = generateStructuredContent(nodeId, nodeData)
        
        workflowStore.addProcessStep({
          nodeId: nodeId,
          status: 'completed',
          content: structuredContent
        })
        
        console.log(`[✅ 状态创建] ${nodeId} → completed (生成结构化内容)`)
      }
      
      // 关键修复：节点完成后，清除currentNode（如果是当前节点）
      if (workflowStore.currentNode === nodeId) {
        workflowStore.currentNode = ''
        console.log(`[🔄 清除currentNode] ${nodeId}已完成`)
      }
      
      // 存储特定节点的数据到store
      storeNodeData(nodeId, nodeData)
    }
  }
  
  /**
   * 存储节点数据到Store
   * @param {string} nodeId - 节点ID
   * @param {object} nodeData - 节点数据
   */
  const storeNodeData = (nodeId, nodeData) => {
    // 输入验证结果
    if (nodeId === 'input_validation') {
      console.log('[🔍 input_validation] 原始数据:', nodeData)
      
      const validationData = {
        input_validated: nodeData.input_validated !== false,
        validation_errors: nodeData.validation_errors || [],
        workflow_status: nodeData.workflow_status || 'validated'
      }
      workflowStore.validationResult = validationData
      console.log('[💾 存储] 验证结果:', validationData)
    }
    
    // TopPhi相场模拟结果（包含VTK数据）
    if (nodeId === 'topphi_simulation') {
      const topphiData = nodeData.topphi_simulation || nodeData
      if (topphiData && typeof topphiData === 'object') {
        workflowStore.topphiResult = topphiData
        console.log('[💾 存储] TopPhi相场模拟数据:', topphiData)
        
        // 特别记录VTK数据
        if (topphiData.vtk_data) {
          console.log('[🎨 VTK数据] 文件:', topphiData.vtk_data.file_name, 
                      '维度:', topphiData.vtk_data.dimensions)
        }
      }
    }
    
    // ML预测结果
    if (nodeId === 'ml_prediction') {
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
    
    // 历史比对结果
    if (nodeId === 'historical_comparison') {
      const histData = nodeData.historical_comparison || nodeData
      if (histData) {
        workflowStore.historicalComparison = histData
        console.log('[存储] 历史比对数据:', histData)
      }
    }
    
    // 综合分析结果
    if (nodeId === 'integrated_analysis') {
      const analysisData = nodeData.integrated_analysis || nodeData
      if (analysisData && typeof analysisData === 'object') {
        workflowStore.integratedAnalysis = analysisData
        console.log('[存储] 综合分析数据:', analysisData)
      }
    }
    
    // 实验工单
    if (nodeId === 'experiment_workorder') {
      const workorderData = nodeData.experiment_workorder || nodeData.workorder || nodeData
      if (workorderData && typeof workorderData === 'string') {
        workflowStore.experimentWorkorder = workorderData
        console.log('[存储] 实验工单数据')
      }
    }
  }
  
  // 流式输出节点跟踪（减少日志冗余）
  const streamingNodes = new Set()
  
  // 保存当前显示的消息实例，用于关闭旧消息
  let currentNotificationMessage = null
  
  /**
   * LLM流式输出处理 - 最简化版本
   * @param {object} data - 流式数据 {node, content}
   */
  const handleLLMStream = (data) => {
    const { node, content } = data
    
    if (!node || !content) {
      return
    }
    
    // 只在节点第一次开始流式输出时记录日志
    if (!streamingNodes.has(node)) {
      streamingNodes.add(node)
      console.log(`[📱 流式开始] ${node}`)
      
      if (workflowStore.viewMode === 'history') {
        console.log(`[💾 数据处理] 历史模式下仍然处理: ${node}`)
      }
    }
    
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
    
    // experiment_workorder特殊处理：同时更新processSteps和experimentWorkorder
    if (node === 'experiment_workorder') {
      if (!workflowStore.experimentWorkorder) {
        workflowStore.experimentWorkorder = content
      } else {
        workflowStore.experimentWorkorder += content
      }
    }
    
    // 其他节点都更新processSteps（用于中间流程显示）
    const step = workflowStore.processSteps.find(s => s.nodeId === node)
    
    if (step) {
      // 节点已存在，追加内容
      step.content += content
      // console.log(`[📝 追加内容] ${node}, 当前总长度=${step.content.length}`)
    } else {
      // 节点不存在，创建为processing状态
      workflowStore.addProcessStep({
        nodeId: node,
        status: 'processing',
        content: content
      })
      
      // 更新当前节点
      workflowStore.currentNode = node
      
      // 只在第一次创建节点时输出日志
      if (!streamingNodes.has(`${node}_created`)) {
        streamingNodes.add(`${node}_created`)
        console.log(`[🟡 状态创建] ${node} → processing (首次流式内容)`)
      }
    }
  }
  
  /**
   * 工作流暂停处理
   * @param {object} message - 暂停消息
   */
  const handleWorkflowPaused = (message) => {
    console.log('[工作流暂停]', message.reason)
    workflowStore.isProcessing = false
    
    // ✅ 关闭之前的消息，避免堆积
    if (currentNotificationMessage) {
      currentNotificationMessage.close()
      currentNotificationMessage = null
    }
    
    // 检查是否在历史查看模式
    const isInHistoryMode = workflowStore.viewMode === 'history'
    
    if (message.reason === 'await_user_selection') {
      // 等待用户选择优化方案
      workflowStore.showOptimizationSelection = true
      // 只在非历史模式下显示通知
      if (!isInHistoryMode) {
        currentNotificationMessage = ElMessage.info({
          message: '请选择优化方案',
          duration: 0,
          showClose: true  // ✅ 显示关闭按钮
        })
      } else {
        console.log('[💾 数据处理] 历史模式下不显示选择通知')
      }
    } else if (message.reason === 'await_experiment_results') {
      // 等待用户输入实验数据
      workflowStore.showExperimentInput = true
      workflowStore.isWaitingExperiment = true
      // 只在非历史模式下显示通知
      if (!isInHistoryMode) {
        currentNotificationMessage = ElMessage.warning({
          message: '请输入实验数据并决定是否继续迭代',
          duration: 0,
          showClose: true  // ✅ 显示关闭按钮
        })
      } else {
        console.log('[💾 数据处理] 历史模式下不显示实验通知')
      }
    }
  }
  
  /**
   * 主WebSocket消息处理器
   * @param {object} message - WebSocket消息
   */
  const handleWebSocketMessage = (message) => {
    // 只在非流式消息时输出日志，减少冗余
    if (message.type !== 'llm_stream') {
      console.log('[WS消息]', message.type)
    }
    
    switch (message.type) {
      case 'node_output':
        handleNodeOutput(message.data)
        break
        
      case 'llm_stream':
        handleLLMStream(message)
        break
        
      case 'workflow_completed':
        // 旧版兼容：如果收到workflow_completed但没有显示选择框，则显示
        if (!workflowStore.showOptimizationSelection && !workflowStore.showExperimentInput) {
          workflowStore.isProcessing = false
          workflowStore.showOptimizationSelection = true
          // 只在非历史模式下显示通知
          if (workflowStore.viewMode !== 'history') {
            ElMessage.success('优化方案生成完成，请选择')
          }
        }
        break
        
      case 'workflow_paused':
        handleWorkflowPaused(message)
        break
        
      case 'workflow_resuming':
        console.log('[流程恢复] 消息:', message.message)
        workflowStore.isProcessing = true
        // 进入长时间任务状态
        if (setLongTaskStatus) {
          setLongTaskStatus(true)
        }
        break
        
      case 'iteration_started':
        // ✅ 关闭旧消息
        if (currentNotificationMessage) {
          currentNotificationMessage.close()
          currentNotificationMessage = null
        }
        
        workflowStore.currentIteration = message.iteration
        // 清空当前流程，开始新一轮迭代
        workflowStore.startNewIteration(message.iteration)
        // 添加迭代开始标识
        workflowStore.addProcessStep({
          nodeId: `iteration_${message.iteration}`,
          status: 'completed',
          content: `## 🔄 第 ${message.iteration} 轮迭代开始\n\n基于上一轮实验结果，重新进行分析和优化...`,
          timestamp: new Date().toISOString()
        })
        // 只在非历史模式下显示通知
        if (workflowStore.viewMode !== 'history') {
          ElMessage.info({
            message: `开始第 ${message.iteration} 轮迭代优化`,
            duration: 3000
          })
        }
        break
        
      case 'experiment_received':
        // 只在非历史模式下显示通知
        if (workflowStore.viewMode !== 'history') {
          ElMessage.success('实验数据已接收')
        }
        break
        
      case 'optimization_completed':
        console.log('[优化完成] 消息:', message.message)
        
        // ✅ 关闭旧消息
        if (currentNotificationMessage) {
          currentNotificationMessage.close()
          currentNotificationMessage = null
        }
        
        workflowStore.isProcessing = false
        // 退出长时间任务状态
        if (setLongTaskStatus) {
          setLongTaskStatus(false)
        }
        // 只在非历史模式下显示完成通知
        if (workflowStore.viewMode !== 'history') {
          ElMessage.success({
            message: '🎉 优化流程已完成！',
            duration: 5000
          })
        }
        break
        
      case 'workorder_generated':
        workflowStore.isProcessing = false
        workflowStore.experimentWorkorder = message.data?.experiment_workorder
        // 只在非历史模式下显示通知
        if (workflowStore.viewMode !== 'history') {
          ElMessage.success('实验工单生成完成')
        }
        break
        
      case 'error':
        workflowStore.isProcessing = false
        // 错误消息始终显示，但在历史模式下添加标识
        const errorMsg = workflowStore.viewMode === 'history' 
          ? `[历史模式] ${message.message || '处理出错'}` 
          : (message.message || '处理出错')
        ElMessage.error(errorMsg)
        break
    }
  }
  
  return {
    handleWebSocketMessage,
    handleNodeOutput,
    handleLLMStream,
    handleWorkflowPaused
  }
}
