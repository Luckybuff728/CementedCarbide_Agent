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
  const historicalData = ref(null)  // 缓存历史数据，供性能对比使用
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

  // 工具名称映射已移至后端 chat_handlers.py 的 _get_tool_display_name()
  // 前端直接使用后端发送的 display_name，无需重复维护

  /**
   * 将工具状态添加到当前流式消息中（去重）
   */
  const addToolToCurrentMessage = (toolName, displayName, isRunning) => {
    const toolInfo = {
      name: toolName,
      displayName: displayName || toolName,  // 使用后端发送的 display_name，无则用原始名
      isRunning: isRunning
    }
    
    // 找到目标消息（优先流式消息，否则最近的 agent 消息）
    let targetMsg = streamingMessage.value
    if (!targetMsg) {
      const lastIndex = messages.value.findLastIndex(m => m.type === 'agent')
      if (lastIndex !== -1) {
        targetMsg = messages.value[lastIndex]
      }
    }
    
    if (targetMsg) {
      // 确保 tools 数组存在
      if (!targetMsg.tools) {
        targetMsg.tools = []
      }
      // 检查是否已存在该工具（去重）
      const existingIndex = targetMsg.tools.findIndex(t => t.name === toolName)
      if (existingIndex === -1) {
        targetMsg.tools.push(toolInfo)
      } else {
        targetMsg.tools[existingIndex].isRunning = isRunning
      }
      // 强制触发 Vue 响应式更新
      messages.value = [...messages.value]
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
        // 强制触发 Vue 响应式更新
        messages.value = [...messages.value]
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
    // 状态更新工具 - 不显示在结果面板
    if (tool === 'update_params') {
      console.log('[ChatAgent] 参数已更新:', result)
      return
    }
    // 验证工具结果不显示在结果面板
    if (tool.includes('validate_composition') || tool.includes('validate_process')) {
      validationResult.value = result
      return
    }
    // RAG 知识库检索 - 不显示在结果面板（内容在聊天消息中展示）
    if (tool.includes('query_knowledge_base') || tool.includes('rag')) {
      console.log('[ChatAgent] RAG检索完成，结果将在聊天中展示')
      return
    }
    // 归一化工具 - 不显示在结果面板
    if (tool.includes('normalize_composition')) {
      return
    }
    // 根因分析工具 - 不显示在结果面板（内容在聊天消息中展示）
    if (tool.includes('analyze_root_cause')) {
      return
    }
    
    if (tool.includes('simulate_topphi')) {
      addResult('topphi', display_name || 'TopPhi 模拟', result)
    } else if (tool.includes('predict_ml')) {
      performancePrediction.value = result  // 缓存 ML 预测结果
      addResult('performance', display_name || 'ML 性能预测', result)
    } else if (tool.includes('compare_historical')) {
      historicalData.value = result  // 缓存历史数据
      addResult('historical', display_name || '历史案例对比', result)
    } else if (tool.includes('show_performance_comparison')) {
      // 性能对比图表 - 使用前端缓存的数据补充
      const enrichedResult = {
        ...result,
        // 如果后端没有返回预测数据，使用前端缓存
        prediction: result.prediction || performancePrediction.value,
        // 如果后端没有返回历史数据，从缓存中提取
        historical: result.historical || extractHistoricalBest(historicalData.value),
        // 目标需求从会话参数获取
        target: result.target || sessionParams.value.targetRequirements
      }
      console.log('[ChatAgent] 性能对比数据补充:', {
        hasPrediction: !!enrichedResult.prediction,
        hasHistorical: !!enrichedResult.historical,
        hasTarget: !!enrichedResult.target
      })
      addResult('performance_comparison', display_name || '性能对比分析', enrichedResult)
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
   * 从历史数据中提取最优性能数据
   * 用于性能对比图表
   */
  const extractHistoricalBest = (histData) => {
    if (!histData) {
      console.log('[ChatAgent] extractHistoricalBest: 无历史数据')
      return null
    }
    
    console.log('[ChatAgent] extractHistoricalBest: 历史数据结构', Object.keys(histData))
    
    // 辅助函数：提取数值，兼容多种字段名
    const extractValue = (obj, ...keys) => {
      for (const key of keys) {
        const val = obj?.[key]
        if (val !== null && val !== undefined) {
          return typeof val === 'number' ? val : parseFloat(val)
        }
      }
      return null
    }
    
    // 方式1：从 extracted_metrics.best_case 提取（最佳案例，包含完整四项指标）
    const bestCase = histData.extracted_metrics?.best_case
    if (bestCase) {
      console.log('[ChatAgent] extractHistoricalBest: 使用 best_case', bestCase)
      return {
        hardness: extractValue(bestCase, 'hardness', 'hardness_gpa'),
        elastic_modulus: extractValue(bestCase, 'elastic_modulus', 'modulus_gpa', 'modulus'),
        adhesion_strength: extractValue(bestCase, 'adhesion_strength', 'adhesion_n', 'adhesion'),
        wear_rate: extractValue(bestCase, 'wear_rate')
      }
    }
    
    // 方式2：从 performance_data 列表中提取第一条（RAG+LLM 返回格式）
    const perfList = histData.performance_data || []
    if (perfList.length > 0) {
      const best = perfList[0]
      console.log('[ChatAgent] extractHistoricalBest: 使用 performance_data[0]', best)
      return {
        hardness: extractValue(best, 'hardness', 'hardness_gpa'),
        elastic_modulus: extractValue(best, 'elastic_modulus', 'modulus_gpa', 'modulus'),
        adhesion_strength: extractValue(best, 'adhesion_strength', 'adhesion_n', 'adhesion'),
        wear_rate: extractValue(best, 'wear_rate')
      }
    }
    
    // 方式3：从 similar_cases 中提取（旧格式兼容）
    const cases = histData.similar_cases || []
    if (cases.length > 0) {
      console.log('[ChatAgent] extractHistoricalBest: 使用 similar_cases[0]')
      return cases[0].performance || null
    }
    
    console.log('[ChatAgent] extractHistoricalBest: 未找到可用数据')
    return null
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

    // 首次发送消息时，清除欢迎消息（System 类型且 agent 为 'System' 的消息）
    const hasUserMessage = messages.value.some(m => m.type === 'user')
    if (!hasUserMessage) {
      messages.value = messages.value.filter(m => !(m.type === 'agent' && m.agent === 'System'))
    }

    // 添加用户消息到列表
    addMessage({
      type: 'user',
      content: content,
      timestamp: new Date().toISOString()
    })

    // 发送到服务器
    // 只有当参数不为空时才发送 context
    const hasComposition = sessionParams.value.coatingComposition && 
      Object.keys(sessionParams.value.coatingComposition).length > 0 &&
      (sessionParams.value.coatingComposition.al_content || 
       sessionParams.value.coatingComposition.ti_content ||
       sessionParams.value.coatingComposition.n_content)
    
    const message = {
      type: 'chat_message',
      content: content,
      session_id: sessionId.value
    }
    
    // 只有用户填写了参数时才发送 context
    if (hasComposition) {
      message.context = {
        coating_composition: sessionParams.value.coatingComposition,
        process_params: sessionParams.value.processParams,
        target_requirements: sessionParams.value.targetRequirements
      }
    }
    
    wsSend(message)
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
    
    // 工艺类型映射（英文 -> 中文）
    const processTypeMap = {
      'magnetron_sputtering': '磁控溅射',
      'arc_ion_plating': '电弧离子镀',
      'cvd': 'CVD',
      'pecvd': 'PECVD',
      'hipims': 'HiPIMS'
    }
    
    // 结构类型映射
    const structTypeMap = {
      'single': '单层',
      'multi': '多层',
      'gradient': '梯度',
      'nano_multilayer': '纳米多层'
    }
    
    let promptMessage = '请帮我验证并分析以下涂层参数：\n'
    
    // 涂层成分
    promptMessage += '成分配比：'
    if (comp && Object.keys(comp).length > 0) {
      const al = comp.al_content || 0
      const ti = comp.ti_content || 0
      const n = comp.n_content || 0
      promptMessage += `Al ${al.toFixed ? al.toFixed(1) : al}%, Ti ${ti.toFixed ? ti.toFixed(1) : ti}%, N ${n.toFixed ? n.toFixed(1) : n}%`
      
      if (comp.other_elements && Array.isArray(comp.other_elements) && comp.other_elements.length > 0) {
        const otherStr = comp.other_elements.map(e => `${e.name || ''} ${(e.content || 0).toFixed ? (e.content || 0).toFixed(1) : e.content || 0}%`).filter(s => s.trim()).join(', ')
        if (otherStr) promptMessage += `, ${otherStr}`
      }
    }
    promptMessage += '\n'
    
    // 工艺参数
    promptMessage += '工艺参数：'
    if (proc && Object.keys(proc).length > 0) {
      const processTypeCN = processTypeMap[proc.process_type] || proc.process_type || '磁控溅射'
      promptMessage += `${processTypeCN}, ${proc.deposition_temperature || 0}°C, ${proc.deposition_pressure || 0}Pa, 偏压${proc.bias_voltage || 0}V, N₂ ${proc.n2_flow || 0}sccm`
      
      if (proc.other_gases && Array.isArray(proc.other_gases) && proc.other_gases.length > 0) {
        const gasStr = proc.other_gases.map(g => `${g.type || ''} ${g.flow || 0}sccm`).filter(s => s.trim()).join(', ')
        if (gasStr) promptMessage += `, ${gasStr}`
      }
    }
    promptMessage += '\n'
    
    // 结构设计
    promptMessage += '结构设计：'
    if (struct && Object.keys(struct).length > 0) {
      const structTypeCN = structTypeMap[struct.structure_type] || struct.structure_type || '单层'
      promptMessage += `${structTypeCN}, ${struct.total_thickness || 0}μm`
      
      if (struct.structure_type === 'multi' && struct.layers && Array.isArray(struct.layers) && struct.layers.length > 0) {
        const layerStr = struct.layers.map(l => `${l.type || ''} ${l.thickness || 0}μm`).join(' → ')
        if (layerStr) promptMessage += ` (${layerStr})`
      }
    }
    promptMessage += '\n'
    
    // 性能需求
    promptMessage += '性能需求：'
    if (target && Object.keys(target).length > 0) {
      const parts = []
      if (target.substrate_material) parts.push(`基材${target.substrate_material}`)
      if (target.adhesion_strength) parts.push(`结合力≥${target.adhesion_strength}N`)
      if (target.elastic_modulus) parts.push(`弹性模量${target.elastic_modulus}GPa`)
      if (target.working_temperature) parts.push(`工作温度${target.working_temperature}°C`)
      if (target.cutting_speed) parts.push(`切削速度${target.cutting_speed}m/min`)
      if (target.application_scenario) parts.push(target.application_scenario)
      promptMessage += parts.length > 0 ? parts.join(', ') : '未指定'
    } else {
      promptMessage += '未指定'
    }
    promptMessage += '\n\n请验证参数是否合理。'

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
    historicalData.value = null
    optimizationResults.value = null
    experimentWorkorder.value = null
    
    // 清空会话参数
    sessionParams.value = {
      coatingComposition: {},
      processParams: {},
      structureDesign: {},
      targetRequirements: ''
    }
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
