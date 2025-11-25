"""
多Agent模式的状态定义 - 支持多轮对话
基于 LangGraph 1.0 的最佳实践
"""
from typing import TypedDict, Dict, List, Optional, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class CoatingAgentState(TypedDict):
    """
    涂层优化多Agent系统的状态
    
    核心特性：
    1. messages: 管理多轮对话历史（LangGraph自动管理）
    2. 支持Agent间状态共享
    3. 支持用户在任意环节介入对话
    """
    
    # ==================== 对话管理 ====================
    # LangGraph 自动管理的对话历史（核心）
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 当前活跃的Agent
    current_agent: Optional[str]  # "supervisor" / "validator" / "analyst" / "optimizer" / "experimenter"
    
    # 刚完成的Agent（用于强制对话）
    last_completed_agent: Optional[str]  # 标记刚完成的Worker，Supervisor必须ask_user
    
    # 下一步行动（由Supervisor决定）
    next_action: Optional[str]  # Agent名称 / "ask_user" / "FINISH"
    
    # ==================== 任务标识 ====================
    task_id: str
    thread_id: str
    
    # ==================== 用户输入 ====================
    # 原始输入参数
    coating_composition: Dict[str, float]  # 涂层成分
    process_params: Dict[str, float]  # 工艺参数
    structure_design: Dict[str, Any]  # 结构设计
    target_requirements: str  # 目标需求描述（自然语言）
    
    # ==================== Agent执行结果 ====================
    # Validator Agent 结果
    validation_result: Optional[Dict[str, Any]]  # 验证结果
    validation_passed: bool  # 是否通过验证
    
    # Analyst Agent 结果
    topphi_simulation: Optional[Dict[str, Any]]  # TopPhi模拟结果
    ml_prediction: Optional[Dict[str, Any]]  # ML预测结果
    historical_comparison: Optional[List[Dict[str, Any]]]  # 历史对比
    integrated_analysis: Optional[Dict[str, Any]]  # 根因分析
    performance_prediction: Optional[Dict[str, Any]]  # 性能预测摘要
    
    # Optimizer Agent 结果
    p1_content: Optional[str]  # P1成分优化建议
    p2_content: Optional[str]  # P2结构优化建议
    p3_content: Optional[str]  # P3工艺优化建议
    comprehensive_recommendation: Optional[str]  # 综合建议
    
    # Experimenter Agent 结果
    selected_optimization_type: Optional[str]  # 用户选择的优化类型（P1/P2/P3）
    selected_optimization_name: Optional[str]  # 选择的具体方案名称
    experiment_workorder: Optional[Dict[str, Any]]  # 实验工单
    experiment_results: Optional[Dict[str, Any]]  # 实验结果
    experiment_analysis: Optional[Dict[str, Any]]  # 实验结果分析（对比预测、对比目标）
    performance_comparison: Optional[Dict[str, Any]]  # 性能对比数据（用于可视化）
    
    # ==================== 迭代管理 ====================
    current_iteration: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    iteration_history: List[Dict[str, Any]]  # 迭代历史
    convergence_achieved: bool  # 是否收敛
    continue_iteration_flag: bool  # 是否继续迭代标志
    parameter_update_source: Optional[str]  # 参数更新来源（P1/P2/P3）
    
    # ==================== 系统状态 ====================
    workflow_status: str  # 工作流状态
    error_message: Optional[str]  # 错误信息
    
    # 用于前端展示的流式输出
    stream_outputs: List[Dict[str, Any]]


class AgentDecision(TypedDict):
    """
    Supervisor Agent 的决策结果
    """
    next_agent: str  # 下一个要调用的Agent名称 / "ask_user" / "FINISH"
    reason: str  # 决策理由
    message_to_user: Optional[str]  # 给用户的消息（如果需要用户输入）
    parameters: Optional[Dict[str, Any]]  # 传递给下一个Agent的参数

