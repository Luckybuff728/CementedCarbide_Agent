/**
 * 对话式多 Agent 系统
 * 
 * 设计理念：
 * - 用户消息驱动，而非流程驱动
 * - 智能路由到合适的专家
 * - 支持多轮对话，实时流式输出
 * - 每条消息独立处理
 */
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { WS_ENDPOINTS } from '../config'
import { useWebSocket } from './useWebSocket'

export function useMultiAgent() {
  // ==================== WebSocket ====================
  const {
    connect: wsConnect,
    send: wsSend,
    disconnect: wsDisconnect,
    isConnected,
    connectionState,
    setLongTaskStatus
  } = useWebSocket()

  // ==================== 状态 ====================
  const sessionId = ref(null)
  const clientId = ref(null)
  const currentAgent = ref('System')
  const isAgentTyping = ref(false)
  const activeTool = ref(null)
  
  // 错误状态
  const lastError = ref(null)
  const hasError = ref(false)

  // 对话消息
  const messages = ref([])

  // 当前流式消息
  const streamingMessage = ref(null)

  // 会话参数（用户填写的涂层参数）
  const sessionParams = ref({
    coatingComposition: {},
    processParams: {},
    structureDesign: {},
    targetRequirements: ''
  })

  // 数据状态（工具调用结果）
  const validationResult = ref(null)
  const performancePrediction = ref(null)
  const optimizationResults = ref(null)
  const experimentWorkorder = ref(null)

  // 结果列表（按时间顺序显示）
  const results = ref([])

  // ==================== 连接管理 ====================
  
  /**
   * 连接到对话式WebSocket
   */
  const connect = (token) => {
    // 使用对话式端点
    const wsUrl = `${WS_ENDPOINTS.chat}?token=${token}`
    console.log('[ChatAgent] 连接到:', wsUrl)

    // 清理状态
    sessionId.value = null
    clientId.value = null
    currentAgent.value = 'System'
    isAgentTyping.value = false
    messages.value = []
    results.value = []

    wsConnect(wsUrl, handleMessage)
  }

  /**
   * 断开连接
   */
  const disconnect = () => {
    wsDisconnect(true)
    isAgentTyping.value = false
  }

  // ==================== 消息处理 ====================

  /**
   * 处理WebSocket消息
   */
  const handleMessage = (data) => {
    console.log('[ChatAgent] 收到消息:', data.type)

    switch (data.type) {
      case 'connection':
        sessionId.value = data.session_id
        clientId.value = data.client_id
        ElMessage.success('对话式助手已连接')
        break

      case 'system_message':
        addMessage({
          type: 'agent',
          agent: 'System',
          agentIcon: '🤖',
          content: data.content,
          timestamp: new Date().toISOString()
        })
        break

      case 'chat_start':
        isAgentTyping.value = true
        // 开始新的流式消息
        streamingMessage.value = {
          type: 'agent',
          agent: currentAgent.value,
          content: '',
          thinking: '',
          tools: [],  // 工具执行状态列表
          isStreaming: true,
          timestamp: new Date().toISOString()
        }
        messages.value.push(streamingMessage.value)
        break

      case 'agent_start':
        currentAgent.value = data.display_name || formatAgentName(data.agent)
        if (streamingMessage.value) {
          streamingMessage.value.agent = currentAgent.value
        }
        break

      case 'agent_end':
        // Agent 完成
        break

      case 'chat_token':
        // 流式输出 token
        if (streamingMessage.value) {
          streamingMessage.value.content += data.content
        }
        break

      case 'thinking_token':
        // 思考内容 token
        if (streamingMessage.value) {
          if (!streamingMessage.value.thinking) {
            streamingMessage.value.thinking = ''
            streamingMessage.value.isThinking = true
          }
          streamingMessage.value.thinking += data.content
        }
        break

      case 'tool_start':
        activeTool.value = data.display_name || data.tool
        setLongTaskStatus(true)
        // 将工具状态添加到当前流式消息中（而不是单独的消息）
        addToolToCurrentMessage(data.tool, data.display_name, true)
        break

      case 'tool_end':
        // 更新当前消息中的工具状态
        updateToolInCurrentMessage(data.tool, false)
        activeTool.value = null
        setLongTaskStatus(false)
        break

      case 'tool_result':
        // 工具返回结果
        handleToolResult(data)
        break

      case 'structured_content':
        // 从 Agent 输出中提取的结构化内容（优化方案摘要、工单信息等）
        handleStructuredContent(data.data)
        break

      case 'chat_complete':
        // 流式消息完成
        if (streamingMessage.value) {
          streamingMessage.value.isStreaming = false
          streamingMessage.value.isThinking = false
          streamingMessage.value = null
        }
        isAgentTyping.value = false
        currentAgent.value = 'System'
        break

      case 'chat_error':
        ElMessage.error(data.message || '发生错误')
        addMessage({
          type: 'error',
          content: `❌ ${data.message}`,
          timestamp: new Date().toISOString()
        })
        isAgentTyping.value = false
        if (streamingMessage.value) {
          streamingMessage.value.isStreaming = false
          streamingMessage.value = null
        }
        break

      case 'parameters_set':
        console.log('[ChatAgent] 参数已设置')
        break

      case 'session_state':
        // 更新会话状态
        if (data.state) {
          validationResult.value = data.state.validation_passed ? { passed: true } : null
        }
        break

      case 'pong':
        // 心跳响应
        break

      case 'generate_stopped':
        // 后端确认生成已终止
        console.log('[ChatAgent] 生成已终止')
        if (streamingMessage.value) {
          streamingMessage.value.isStreaming = false
          streamingMessage.value.isThinking = false
          streamingMessage.value = null
        }
        isAgentTyping.value = false
        currentAgent.value = 'System'
        activeTool.value = null
        break

      default:
        console.log('[ChatAgent] 未处理的消息类型:', data.type)
    }
  }

  // ==================== 消息操作 ====================

  /**
   * 添加消息到列表
   */
  const addMessage = (msg) => {
    messages.value.push({
      id: Date.now() + Math.random(),
      ...msg
    })
  }

  // 工具名称映射（只保留数据获取类工具）
  // 优化方案、工单、分析报告等由 Agent 自己生成，不通过工具
  const toolNameMap = {
    // 验证工具
    'validate_composition_tool': '🔬 验证成分配比',
    'validate_process_params_tool': '⚙️ 验证工艺参数',
    'normalize_composition_tool': '📊 归一化成分',
    // 分析数据获取工具
    'simulate_topphi_tool': '🧪 TopPhi 模拟',
    'predict_ml_performance_tool': '📈 ML 性能预测',
    'compare_historical_tool': '📚 历史案例对比',
    // 实验数据工具
    'analyze_experiment_results_tool': '📊 实验结果对比'
  }

  /**
   * 将工具状态添加到当前流式消息中
   */
  const addToolToCurrentMessage = (toolName, displayName, isRunning) => {
    // 如果有当前流式消息，添加到其 tools 数组中
    if (streamingMessage.value) {
      if (!streamingMessage.value.tools) {
        streamingMessage.value.tools = []
      }
      streamingMessage.value.tools.push({
        name: toolName,
        displayName: displayName || toolNameMap[toolName] || toolName,
        isRunning: isRunning
      })
    } else {
      // 如果没有流式消息，找到最近的 agent 消息并添加
      const lastAgentMsg = messages.value.findLast(m => m.type === 'agent')
      if (lastAgentMsg) {
        if (!lastAgentMsg.tools) {
          lastAgentMsg.tools = []
        }
        lastAgentMsg.tools.push({
          name: toolName,
          displayName: displayName || toolNameMap[toolName] || toolName,
          isRunning: isRunning
        })
      }
    }
  }

  /**
   * 更新当前消息中的工具状态
   */
  const updateToolInCurrentMessage = (toolName, isRunning) => {
    // 在当前流式消息或最近的 agent 消息中查找工具
    const targetMsg = streamingMessage.value || messages.value.findLast(m => m.type === 'agent')
    if (targetMsg && targetMsg.tools) {
      const tool = targetMsg.tools.find(t => t.name === toolName)
      if (tool) {
        tool.isRunning = isRunning
      }
    }
  }

  /**
   * 处理工具结果
   * 
   * 只处理数据获取类工具的结果
   * 优化方案、工单、分析报告等由 Agent 自己生成，通过 chat_token 流式输出
   */
  const handleToolResult = (data) => {
    const { tool, result, display_name } = data
    console.log('[ChatAgent] 工具结果:', tool, result)
    
    // 根据工具类型更新对应的状态并添加到结果面板
    // 注意：验证工具结果不再显示在结果面板
    if (tool.includes('validate_composition') || tool.includes('validate_process')) {
      // 只更新状态，不添加到结果面板
      validationResult.value = result
      return
    } else if (tool.includes('simulate_topphi')) {
      addResult('topphi', display_name || 'TopPhi 模拟', result)
    } else if (tool.includes('predict_ml')) {
      performancePrediction.value = result
      addResult('performance', display_name || 'ML 性能预测', result)
    } else if (tool.includes('compare_historical')) {
      addResult('historical', display_name || '历史案例对比', result)
    } else if (tool.includes('show_performance_comparison')) {
      // 性能对比图表（实验数据 vs ML预测 vs 历史最优）
      addResult('performance_comparison', display_name || '性能对比分析', result)
    } else if (tool.includes('request_experiment_input')) {
      // 请求用户输入实验数据 - 显示输入卡片
      addResult('experiment_input', display_name || '实验数据录入', {
        iteration: result.iteration || 1,
        workorder_id: result.workorder_id,
        target_requirements: result.target_requirements,
        message: result.message
      })
    } else {
      // 其他工具结果
      addResult('other', display_name || tool, result)
    }
  }

  /**
   * 添加结果到结果面板
   */
  const addResult = (type, title, data) => {
    results.value.push({
      id: Date.now(),
      type,
      title,
      data,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * 处理结构化内容（从 Agent 输出中提取）
   * 
   * 类型：
   * - optimization_plans: 优化方案摘要（P1/P2/P3）
   * - workorder: 实验工单信息
   */
  const handleStructuredContent = (data) => {
    if (!data || !data.type) return
    
    console.log('[ChatAgent] 结构化内容:', data.type, data)
    
    if (data.type === 'optimization_plans') {
      // 优化方案摘要
      optimizationResults.value = data
      addResult('optimization_plans', '优化方案概览', data)
    } else if (data.type === 'workorder') {
      // 实验工单
      experimentWorkorder.value = data
      addResult('workorder', '实验工单', data)
    }
  }

  // ==================== 用户操作 ====================

  /**
   * 发送聊天消息
   */
  const sendMessage = (content) => {
    if (!content?.trim()) return
    if (!isConnected.value) {
      ElMessage.warning('未连接到服务器')
      return
    }

    // 添加用户消息到列表
    addMessage({
      type: 'user',
      content: content,
      timestamp: new Date().toISOString()
    })

    // 发送到服务器
    wsSend({
      type: 'chat_message',
      content: content,
      session_id: sessionId.value,
      context: {
        coating_composition: sessionParams.value.coatingComposition,
        process_params: sessionParams.value.processParams,
        target_requirements: sessionParams.value.targetRequirements
      }
    })
  }

  /**
   * 设置涂层参数并开始分析
   * 
   * 表单数据结构（来自 LeftPanel.vue）：
   * - composition: { al_content, ti_content, n_content, other_elements }
   * - process_params: { process_type, deposition_pressure, deposition_temperature, bias_voltage, n2_flow, other_gases }
   * - structure_design: { structure_type, total_thickness, layers }
   * - target_requirements: { substrate_material, adhesion_strength, ... application_scenario }
   */
  const startWithParams = (formData) => {
    console.log('[ChatAgent] 收到表单数据:', formData)
    
    // 保存参数（使用表单实际字段名）
    sessionParams.value = {
      coatingComposition: formData.composition || {},
      processParams: formData.process_params || {},
      structureDesign: formData.structure_design || {},
      targetRequirements: formData.target_requirements || {}
    }

    // 先设置参数到后端
    wsSend({
      type: 'set_parameters',
      session_id: sessionId.value,
      coating_composition: sessionParams.value.coatingComposition,
      process_params: sessionParams.value.processParams,
      structure_design: sessionParams.value.structureDesign,
      target_requirements: sessionParams.value.targetRequirements
    })

    // 构建完整的参数验证请求消息（字段名与 validation_service.py 一致）
    const comp = sessionParams.value.coatingComposition
    const proc = sessionParams.value.processParams
    const struct = sessionParams.value.structureDesign
    const target = sessionParams.value.targetRequirements
    
    let promptMessage = '请帮我验证并分析以下涂层参数：\n\n'
    
    // 涂层成分（字段：al_content, ti_content, n_content, other_elements）
    promptMessage += '**成分配比：** '
    if (comp && Object.keys(comp).length > 0) {
      const al = comp.al_content || 0
      const ti = comp.ti_content || 0
      const n = comp.n_content || 0
      promptMessage += `Al ${al.toFixed ? al.toFixed(1) : al} at.%, Ti ${ti.toFixed ? ti.toFixed(1) : ti} at.%, N ${n.toFixed ? n.toFixed(1) : n} at.%`
      
      // 其他元素
      if (comp.other_elements && Array.isArray(comp.other_elements)) {
        const otherStr = comp.other_elements.map(e => `${e.name || e.element || ''} ${(e.content || 0).toFixed ? (e.content || 0).toFixed(1) : e.content || 0} at.%`).join(', ')
        if (otherStr) promptMessage += `, ${otherStr}`
      }
    }
    promptMessage += '\n'
    
    // 工艺参数（字段：process_type, deposition_temperature, deposition_pressure, bias_voltage, n2_flow, other_gases）
    promptMessage += '**工艺参数：** '
    if (proc && Object.keys(proc).length > 0) {
      promptMessage += `工艺类型: ${proc.process_type || '磁控溅射'}, `
      promptMessage += `沉积温度: ${proc.deposition_temperature || 0}°C, `
      promptMessage += `沉积气压: ${proc.deposition_pressure || 0} Pa, `
      promptMessage += `偏压: ${proc.bias_voltage || 0} V, `
      promptMessage += `N₂流量: ${proc.n2_flow || 0} sccm`
      
      // 其他气体
      if (proc.other_gases && Array.isArray(proc.other_gases)) {
        const gasStr = proc.other_gases.map(g => `${g.type || ''} ${g.flow || 0} sccm`).join(', ')
        if (gasStr) promptMessage += `, 其他气体: ${gasStr}`
      }
    }
    promptMessage += '\n'
    
    // 结构设计（字段：structure_type, total_thickness, layers）
    promptMessage += '**结构设计：** '
    if (struct && Object.keys(struct).length > 0) {
      promptMessage += `结构类型: ${struct.structure_type || '单层'}, `
      promptMessage += `总厚度: ${struct.total_thickness || 0} μm`
      
      // 多层结构
      if (struct.structure_type === 'multi' && struct.layers && Array.isArray(struct.layers)) {
        const layerStr = struct.layers.map(l => `${l.type || ''} ${l.thickness || 0}μm`).join('; ')
        if (layerStr) promptMessage += `, 层结构: ${layerStr}`
      }
    }
    promptMessage += '\n'
    
    // 性能需求（对象格式：{ substrate_material, adhesion_strength, elastic_modulus, working_temperature, cutting_speed, application_scenario }）
    promptMessage += '**性能需求：** '
    if (target && Object.keys(target).length > 0) {
      const parts = []
      if (target.substrate_material) parts.push(`基材: ${target.substrate_material}`)
      if (target.adhesion_strength) parts.push(`结合力要求: ≥${target.adhesion_strength}N`)
      if (target.elastic_modulus) parts.push(`弹性模量: ${target.elastic_modulus}GPa`)
      if (target.working_temperature) parts.push(`工作温度: ${target.working_temperature}°C`)
      if (target.cutting_speed) parts.push(`切削速度: ${target.cutting_speed}m/min`)
      if (target.application_scenario) parts.push(`应用场景: ${target.application_scenario}`)
      promptMessage += parts.length > 0 ? parts.join(', ') : '未指定'
    } else {
      promptMessage += '未指定'
    }
    promptMessage += '\n\n请先验证这些参数是否合理，然后进行性能预测。'

    // 发送验证请求
    setTimeout(() => {
      sendMessage(promptMessage)
    }, 100)
  }

  /**
   * 清除会话
   */
  const clearSession = () => {
    if (isConnected.value) {
      wsSend({
        type: 'clear_session',
        session_id: sessionId.value
      })
    }
    
    messages.value = []
    results.value = []
    validationResult.value = null
    performancePrediction.value = null
    optimizationResults.value = null
    experimentWorkorder.value = null
  }

  /**
   * 清除结果
   */
  const clearResults = () => {
    results.value = []
  }

  /**
   * 终止生成
   * 发送终止信号并立即清理流式状态
   */
  const stopGenerate = () => {
    if (!isAgentTyping.value) return
    
    // 发送终止信号到后端
    wsSend({
      type: 'stop_generate',
      session_id: sessionId.value
    })
    
    // 立即清理前端状态
    if (streamingMessage.value) {
      streamingMessage.value.isStreaming = false
      streamingMessage.value.isThinking = false
      streamingMessage.value.content += '\n\n*[已终止生成]*'
      streamingMessage.value = null
    }
    isAgentTyping.value = false
    activeTool.value = null
    setLongTaskStatus(false)
    
    ElMessage.info('已终止生成')
  }

  // ==================== 工具函数 ====================

  /**
   * 格式化Agent名称
   */
  const formatAgentName = (name) => {
    const nameMap = {
      'router': '🔀 智能路由',
      'assistant': '研发助手',
      'validator': '验证专家',
      'analyst': '分析专家',
      'optimizer': '优化专家',
      'experimenter': '实验专家',
      'supervisor': '调度中心',
      'System': '🤖 系统'
    }
    return nameMap[name] || name
  }

  // ==================== 计算属性 ====================

  /**
   * 是否可以发送消息
   */
  const canSendMessage = computed(() => {
    return isConnected.value && !isAgentTyping.value
  })

  /**
   * 待处理操作提示
   */
  const pendingActionHint = computed(() => {
    if (!isConnected.value) return '请等待连接...'
    if (isAgentTyping.value) return '助手正在回复...'
    return null
  })

  /**
   * 状态文本
   */
  const statusText = computed(() => {
    if (!isConnected.value) return '未连接'
    if (isAgentTyping.value) {
      if (activeTool.value) return `正在使用 ${activeTool.value}...`
      return `${currentAgent.value} 正在思考...`
    }
    return '就绪'
  })

  // ==================== 生命周期 ====================

  onUnmounted(() => {
    disconnect()
  })

  // ==================== 返回 ====================

  return {
    // 连接状态
    connect,
    disconnect,
    isConnected,
    connectionState,
    sessionId,
    
    // Agent 状态
    currentAgent,
    isAgentTyping,
    activeTool,
    statusText,
    
    // 消息
    messages,
    
    // 结果数据
    results,
    validationResult,
    performancePrediction,
    optimizationResults,
    experimentWorkorder,
    
    // 参数
    sessionParams,
    
    // 用户操作
    sendMessage,
    startWithParams,
    clearSession,
    clearResults,
    stopGenerate,
    
    // 计算属性
    canSendMessage,
    pendingActionHint,
    
    // 错误状态
    hasError,
    lastError
  }
}

export default useMultiAgent
