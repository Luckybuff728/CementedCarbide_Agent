/**
 * 多Agent模式的WebSocket管理
 * 支持：
 * 1. 与Agent的多轮对话
 * 2. LLM驱动的动态路由
 * 3. 任意环节的用户介入
 * 
 * ✨ 使用增强的useWebSocket，支持：
 * - 自动重连（指数退避）
 * - 心跳保活
 * - 离线消息队列
 * - 长时间任务保护
 */
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { WS_ENDPOINTS } from '../config'
import { useWebSocket } from './useWebSocket'

export function useMultiAgent() {
  // 使用增强的WebSocket管理
  const {
    connect: wsConnect,
    send: wsSend,
    disconnect: wsDisconnect,
    isConnected,
    connectionState,
    reconnectAttempts,
    setLongTaskStatus
  } = useWebSocket()
  
  const maxReconnectAttempts = 10  // 增加到10次

  // Agent状态
  const currentAgent = ref('System')
  const currentTaskId = ref(null)
  const isAgentTyping = ref(false)

  // 对话消息
  const messages = ref([])

  // 数据状态（与原workflow兼容）
  const validationResult = ref(null)
  const topphiResult = ref(null)
  const performancePrediction = ref(null)
  const historicalComparison = ref(null)
  const integratedAnalysis = ref(null)
  const p1Content = ref('')
  const p2Content = ref('')
  const p3Content = ref('')
  const comprehensiveRecommendation = ref('')
  const experimentWorkorder = ref(null)

  // 暂停状态
  const isPaused = ref(false)
  const pauseReason = ref(null)
  const pauseData = ref(null)
  
  // UI状态
  const activeTab = ref('validation')
  
  // 结果列表（按时间顺序显示）
  const results = ref([])

  /**
   * 连接到多Agent WebSocket
   */
  const connect = (token) => {
    const wsUrl = `${WS_ENDPOINTS.coating}?token=${token}`
    
    console.log('[MultiAgent] 开始连接:', wsUrl)
    
    // ✅ 测试模式：连接前清理旧任务状态
    // 这样刷新页面后会重新开始，而不是尝试恢复旧任务
    currentTaskId.value = null
    isPaused.value = false
    pauseReason.value = null
    isAgentTyping.value = false
    console.log('[测试模式] 已清理任务状态，准备重新开始')
    
    // 使用增强的WebSocket连接
    wsConnect(wsUrl, (data) => {
      handleMessage(data)
    })
  }

  /**
   * 断开连接
   */
  const disconnect = () => {
    wsDisconnect(true)  // 阻止自动重连
    isAgentTyping.value = false
  }

  /**
   * 发送消息（使用增强的send，支持离线队列）
   */
  const send = (data) => {
    if (!isConnected.value) {
      console.warn('[MultiAgent] WebSocket 未连接，消息将加入队列')
    }
    wsSend(data, true)  // 启用离线队列
  }

  // 用于累积流式输出的消息
  const streamingMessage = ref(null)
  
  /**
   * 处理WebSocket消息
   */
  const handleMessage = (data) => {
    console.log('[MultiAgent] 收到消息:', data.type)

    switch (data.type) {
      case 'connection':
        ElMessage.success('多Agent系统已连接')
        break

      case 'task_started':
        currentTaskId.value = data.task_id
        addSystemMessage('任务已启动，Supervisor正在分析您的需求...')
        break

      case 'node_start':
        handleNodeStart(data)
        break

      case 'tool_start':
        handleToolStart(data)
        break

      case 'tool_end':
        handleToolEnd(data)
        break

      case 'agent_token':
        handleAgentToken(data)
        break

      case 'agent_message':
        handleAgentMessage(data)
        break

      case 'data_update':
        handleDataUpdate(data)
        break

      case 'workflow_paused':
        handleWorkflowPaused(data)
        isAgentTyping.value = false  // 停止typing动画
        setLongTaskStatus(false)  // 关闭长任务模式
        // 完成流式消息
        if (streamingMessage.value) {
          streamingMessage.value.isStreaming = false
          streamingMessage.value = null
        }
        break

      case 'task_completed':
        // 只有真正完成（到达END节点）才显示完成消息
        addSystemMessage('✅ 所有流程已完成！')
        currentAgent.value = 'System'
        isAgentTyping.value = false
        isPaused.value = false
        setLongTaskStatus(false)  // 关闭长任务模式
        // 完成流式消息
        if (streamingMessage.value) {
          streamingMessage.value.isStreaming = false
          streamingMessage.value = null
        }
        break

      case 'error':
        ElMessage.error(data.message || '发生错误')
        addSystemMessage(`❌ 错误: ${data.message}`)
        isAgentTyping.value = false
        setLongTaskStatus(false)  // 关闭长任务模式
        break

      case 'pong':
        // 心跳响应
        break

      default:
        console.log('[MultiAgent] 未处理的消息类型:', data.type)
    }
  }

  /**
   * 处理节点开始
   */
  const handleNodeStart = (data) => {
    const nodeName = data.node
    currentAgent.value = formatAgentName(nodeName)
    
    console.log(`[MultiAgent] 节点 ${nodeName} 开始执行`)
  }

  /**
   * 处理工具开始执行
   */
  const handleToolStart = (data) => {
    const toolName = data.tool
    const nodeName = data.node
    
    // 🔥 启用长任务模式（延长心跳超时，避免LLM长时间执行时断开）
    setLongTaskStatus(true)
    
    // 工具名称映射为中文
    const toolNameMap = {
      'validate_coating_params': '参数验证',
      'run_topphi_simulation': 'TopPhi相场模拟',
      'predict_performance_ml': 'ML性能预测',
      'query_historical_data': '历史数据查询',
      'integrated_analysis': '综合分析',
      'generate_p1_optimization': 'P1优化方案生成',
      'generate_p2_optimization': 'P2优化方案生成',
      'generate_p3_optimization': 'P3优化方案生成',
      'generate_comprehensive_recommendation': '综合优化建议生成',
      'generate_experiment_workorder': '实验工单生成'
    }
    
    const displayName = toolNameMap[toolName] || toolName
    
    // 添加工具执行消息（带唯一ID用于后续更新）
    const toolMessage = {
      type: 'tool',
      agent: formatAgentName(nodeName),
      content: `🔧 正在执行：${displayName}...`,
      timestamp: data.timestamp || new Date().toISOString(),
      isToolExecution: true,
      isToolRunning: true,  // 标记工具正在运行
      toolName: toolName,   // 保存工具名称用于匹配
      toolId: `${toolName}_${Date.now()}`  // 唯一ID
    }
    
    messages.value.push(toolMessage)
    
    isAgentTyping.value = true
    
    console.log(`[MultiAgent] 工具 ${toolName} 开始执行（长任务模式已启用）`)
  }

  /**
   * 处理工具执行结束
   */
  const handleToolEnd = (data) => {
    const toolName = data.tool
    
    // 🔥 关闭长任务模式（恢复正常心跳超时）
    setLongTaskStatus(false)
    
    // 找到对应的工具消息并更新状态
    const toolMessage = messages.value
      .slice()
      .reverse()
      .find(msg => msg.isToolExecution && msg.toolName === toolName && msg.isToolRunning)
    
    if (toolMessage) {
      toolMessage.isToolRunning = false  // 标记工具已完成
      
      // 可选：更新消息内容显示已完成
      const toolNameMap = {
        'validate_coating_params': '参数验证',
        'run_topphi_simulation': 'TopPhi相场模拟',
        'predict_performance_ml': 'ML性能预测',
        'query_historical_data': '历史数据查询',
        'integrated_analysis': '综合分析',
        'generate_p1_optimization': 'P1优化方案生成',
        'generate_p2_optimization': 'P2优化方案生成',
        'generate_p3_optimization': 'P3优化方案生成',
        'generate_comprehensive_recommendation': '综合优化建议生成',
        'generate_experiment_workorder': '实验工单生成'
      }
      const displayName = toolNameMap[toolName] || toolName
      toolMessage.content = `✅ 完成：${displayName}`
    }
    
    console.log(`[MultiAgent] 工具 ${toolName} 执行完成（长任务模式已关闭）`)
  }

  /**
   * 处理Agent token流
   */
  const handleAgentToken = (data) => {
    const token = data.token
    const nodeName = data.node
    const agentName = formatAgentName(nodeName)
    
    // 检查是否需要创建新的流式消息
    // 条件：1. 没有流式消息 或 2. node变化了（例如从p1切换到p2）
    if (!streamingMessage.value || streamingMessage.value.agent !== agentName) {
      // 完成之前的流式消息
      if (streamingMessage.value) {
        streamingMessage.value.isStreaming = false
      }
      
      // 创建新的流式消息
      streamingMessage.value = {
        type: 'agent',
        agent: agentName,
        node: nodeName,  // 记录原始节点名称
        content: token,
        timestamp: data.timestamp || new Date().toISOString(),
        isStreaming: true
      }
      messages.value.push(streamingMessage.value)
    } else {
      // 追加token到现有消息（同一个agent）
      streamingMessage.value.content += token
    }
    
    isAgentTyping.value = true
  }

  /**
   * 处理Agent完整消息（兼容非流式输出）
   */
  const handleAgentMessage = (data) => {
    const agentName = formatAgentName(data.agent)
    
    // 如果有流式消息在进行，先完成它
    if (streamingMessage.value) {
      streamingMessage.value.isStreaming = false
      streamingMessage.value = null
    }
    
    currentAgent.value = agentName

    messages.value.push({
      type: 'agent',
      agent: agentName,
      content: data.content,
      timestamp: data.timestamp || new Date().toISOString()
    })

    // 延迟500ms后停止typing，给用户流畅的体验
    setTimeout(() => {
      if (isAgentTyping.value) {
        isAgentTyping.value = false
      }
    }, 500)
  }

  /**
   * 处理数据更新（同时添加到结果列表）
   */
  const handleDataUpdate = (data) => {
    const updates = data.data

    if (updates.validation_result) {
      validationResult.value = updates.validation_result
      // 添加到结果列表
      results.value.push({
        id: `validation_${Date.now()}`,
        type: 'validation',
        data: updates.validation_result,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.topphi_simulation) {
      topphiResult.value = updates.topphi_simulation
      // 添加到结果列表
      results.value.push({
        id: `topphi_${Date.now()}`,
        type: 'topphi',
        data: updates.topphi_simulation,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.ml_prediction) {
      // ML预测结果
    }
    if (updates.performance_prediction) {
      performancePrediction.value = updates.performance_prediction
      // 添加到结果列表
      results.value.push({
        id: `performance_${Date.now()}`,
        type: 'performance',
        data: updates.performance_prediction,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.historical_comparison) {
      historicalComparison.value = updates.historical_comparison
      // 添加到结果列表
      results.value.push({
        id: `historical_${Date.now()}`,
        type: 'historical',
        data: updates.historical_comparison,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.integrated_analysis) {
      integratedAnalysis.value = updates.integrated_analysis
      // 添加到结果列表
      results.value.push({
        id: `analysis_${Date.now()}`,
        type: 'analysis',
        data: updates.integrated_analysis,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.p1_content) {
      p1Content.value = updates.p1_content
    }
    if (updates.p2_content) {
      p2Content.value = updates.p2_content
    }
    if (updates.p3_content) {
      p3Content.value = updates.p3_content
    }
    if (updates.comprehensive_recommendation) {
      comprehensiveRecommendation.value = updates.comprehensive_recommendation
    }
    
    // ✅ 当所有三个方案都生成后，添加到结果列表并在右侧显示选择器
    if (updates.p1_content && updates.p2_content && updates.p3_content) {
      results.value.push({
        id: `optimization_${Date.now()}`,
        type: 'optimization',
        data: {
          p1: updates.p1_content,
          p2: updates.p2_content,
          p3: updates.p3_content,
          comprehensive: updates.comprehensive_recommendation || comprehensiveRecommendation.value
        },
        timestamp: new Date().toISOString()
      })
      
      console.log('[优化方案] 已生成，右侧将显示选择器')
    }
    if (updates.experiment_workorder) {
      // 提取实际的工单数据（后端返回格式：{status, data, message, error}）
      const workorderData = updates.experiment_workorder.data || updates.experiment_workorder
      experimentWorkorder.value = workorderData
      
      console.log('[工单数据] 接收到工单:', {
        raw: updates.experiment_workorder,
        extracted: workorderData,
        workorder_id: workorderData.workorder_id,
        solution_name: workorderData.solution_name,
        selected_optimization: workorderData.selected_optimization
      })
      
      // 添加到结果列表
      results.value.push({
        id: `workorder_${Date.now()}`,
        type: 'workorder',
        data: workorderData,
        timestamp: new Date().toISOString()
      })
    }
    if (updates.performance_comparison) {
      // 性能对比图数据（包含实验分析报告）
      results.value.push({
        id: `comparison_${Date.now()}`,
        type: 'comparison',
        data: {
          ...updates.performance_comparison,
          // 合并实验分析报告
          analysis_report: updates.experiment_analysis?.analysis_report || '',
          is_target_met: updates.experiment_analysis?.is_target_met || false,
          unmet_metrics: updates.experiment_analysis?.unmet_metrics || []
        },
        timestamp: new Date().toISOString()
      })
    }
  }

  /**
   * 处理工作流暂停
   */
  const handleWorkflowPaused = (data) => {
    isPaused.value = true
    pauseReason.value = data.reason
    pauseData.value = data.data
    isAgentTyping.value = false  // 停止typing动画

    console.log('[MultiAgent] 工作流暂停:', data.reason)

    // 根据暂停原因给出提示
    if (data.reason === 'await_user_selection') {
      addSystemMessage('⏸️ 请选择一个优化方案继续')
    } else if (data.reason === 'await_experiment_results') {
      // 不添加系统消息，而是在右侧面板显示实验输入表单
      addSystemMessage('⏸️ 请提交实验结果')
      results.value.push({
        id: `experiment_input_${Date.now()}`,
        type: 'experiment_input',
        data: {
          iteration: data.data?.iteration || 1,
          historicalBest: null,  // TODO: 从状态中获取历史最优数据
          targetHardness: null    // TODO: 从target_requirements中获取目标硬度
        },
        timestamp: new Date().toISOString()
      })
    } else if (data.reason === 'ask_user') {
      // ask_user时不需要额外提示，Supervisor的消息已经包含了问题
      console.log('[MultiAgent] 等待用户回复')
    }
  }

  /**
   * 格式化目标需求为可读文本
   */
  const formatTargetRequirements = (targetReq) => {
    if (!targetReq) return '提升性能'
    
    if (typeof targetReq === 'string') {
      return targetReq
    }
    
    // 如果是对象，格式化为文本
    const parts = []
    if (targetReq.substrate) parts.push(`基材：${targetReq.substrate}`)
    if (targetReq.bonding_strength) parts.push(`结合力：${targetReq.bonding_strength}N`)
    if (targetReq.elastic_modulus) parts.push(`弹性模量：${targetReq.elastic_modulus}GPa`)
    if (targetReq.working_temperature) parts.push(`工作温度：${targetReq.working_temperature}°C`)
    if (targetReq.cutting_speed) parts.push(`切削速度：${targetReq.cutting_speed}m/min`)
    if (targetReq.application_scenario) parts.push(`应用场景：${targetReq.application_scenario}`)
    if (targetReq.special_requirements) parts.push(`特殊要求：${targetReq.special_requirements}`)
    
    return parts.length > 0 ? parts.join('，') : '提升性能'
  }

  /**
   * 启动Agent任务
   */
  const startAgentTask = (formData) => {
    messages.value = []
    results.value = []  // 清空结果列表
    isPaused.value = false

    // 添加用户消息（格式化目标需求）
    const targetText = formatTargetRequirements(formData.target_requirements)
    const userMessage = `请帮我优化涂层配方。目标：${targetText}`
    messages.value.push({
      type: 'user',
      agent: '我',
      content: userMessage,
      timestamp: new Date().toISOString()
    })

    isAgentTyping.value = true

    send({
      type: 'start_agent_task',
      data: formData
    })
  }

  /**
   * 清空结果
   */
  const clearResults = () => {
    results.value = []
  }

  /**
   * 发送对话消息
   */
  const sendMessage = (message) => {
    if (!message.trim()) return

    // 添加用户消息到界面
    messages.value.push({
      type: 'user',
      agent: '我',
      content: message,
      timestamp: new Date().toISOString()
    })

    isAgentTyping.value = true
    isPaused.value = false

    send({
      type: 'send_message',
      message: message
    })
  }

  /**
   * 选择优化方案
   */
  const selectOptimization = (option) => {
    isPaused.value = false
    isAgentTyping.value = true

    send({
      type: 'select_optimization',
      selected_option: option
    })

    addSystemMessage(`已选择 ${option} 方案`)
  }

  /**
   * 提交实验结果
   */
  const submitExperiment = (data) => {
    isPaused.value = false
    isAgentTyping.value = true

    send({
      type: 'submit_experiment',
      data: data
    })

    addSystemMessage('实验结果已提交')
  }

  /**
   * 添加系统消息
   */
  const addSystemMessage = (content) => {
    messages.value.push({
      type: 'agent',
      agent: 'System',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * 格式化Agent名称
   */
  const formatAgentName = (agent) => {
    const mapping = {
      'supervisor': '🎯 Supervisor',
      'validator': '✅ Validator',
      'analyst': '🔬 Analyst',
      'optimizer': '💡 Optimizer',
      'experimenter': '🧪 Experimenter',
      'ask_user': '💬 Supervisor',
      'p1': '💡 P1成分优化',
      'p2': '💡 P2结构优化',
      'p3': '💡 P3工艺优化'
    }
    return mapping[agent.toLowerCase()] || agent
  }

  // 计算属性
  const canSendMessage = computed(() => {
    // 只要连接且有任务，就可以发送消息（即使Agent正在执行）
    // 确保返回值明确为 Boolean 类型
    return Boolean(isConnected.value && currentTaskId.value)
  })

  const showOptimizationSelector = computed(() => {
    // ✅ 两种情况显示选择器：
    // 1. 旧逻辑：收到 await_user_selection interrupt
    // 2. 新逻辑：有优化方案数据（p1/p2/p3）但还没有工单
    const hasOptimization = p1Content.value && p2Content.value && p3Content.value
    const hasWorkorder = experimentWorkorder.value !== null
    
    return (isPaused.value && pauseReason.value === 'await_user_selection') || 
           (hasOptimization && !hasWorkorder)
  })

  const showExperimentInput = computed(() => {
    return isPaused.value && pauseReason.value === 'await_experiment_results'
  })

  // 组件卸载时清理
  onUnmounted(() => {
    disconnect()
    setLongTaskStatus(false)
    console.log('[MultiAgent] 组件卸载，连接已清理')
  })

  return {
    // 连接管理
    connect,
    disconnect,
    send,
    isConnected,
    connectionState,
    reconnectAttempts,

    // Agent状态
    currentAgent,
    currentTaskId,
    isAgentTyping,
    messages,

    // 数据状态
    validationResult,
    topphiResult,
    performancePrediction,
    historicalComparison,
    integratedAnalysis,
    p1Content,
    p2Content,
    p3Content,
    comprehensiveRecommendation,
    experimentWorkorder,

    // 交互状态
    isPaused,
    pauseReason,
    pauseData,
    
    // UI状态
    activeTab,
    results,
    canSendMessage,
    showOptimizationSelector,
    showExperimentInput,

    // 操作方法
    startAgentTask,
    sendMessage,
    selectOptimization,
    submitExperiment,
    clearResults
  }
}

