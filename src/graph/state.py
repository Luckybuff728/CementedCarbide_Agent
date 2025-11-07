"""
LangGraph工作流状态定义
"""
from typing import TypedDict, Dict, List, Optional, Any, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class CoatingWorkflowState(TypedDict):
    """涂层优化工作流状态"""
    
    # 任务标识
    task_id: str
    thread_id: str
    
    # 输入参数
    coating_composition: Dict[str, float]  # 涂层成分
    process_params: Dict[str, float]  # 工艺参数
    structure_design: Dict[str, Any]  # 结构设计
    target_requirements: str  # 目标需求描述
    
    # 验证和预处理
    input_validated: bool  # 输入是否已验证
    validation_errors: List[str]  # 验证错误列表
    preprocessed_data: Dict[str, Any]  # 预处理后的数据
    
    # 性能预测结果 - 拆分为4个子节点
    topphi_simulation: Dict[str, Any]  # TopPhi第一性原理模拟结果
    ml_prediction: Dict[str, Any]  # ML模型预测结果
    historical_comparison: List[Dict[str, Any]]  # 历史数据对比
    performance_prediction: Dict[str, Any]  # 综合性能预测结果
    root_cause_analysis: str  # 根因分析
    prediction_confidence: float  # 预测置信度
    
    # 优化建议 - 拆分为P1/P2/P3
    p1_suggestions: List[Dict[str, Any]]  # P1成分优化建议
    p1_content: str  # P1优化建议内容
    p2_suggestions: List[Dict[str, Any]]  # P2结构优化建议
    p2_content: str  # P2优化建议内容
    p3_suggestions: List[Dict[str, Any]]  # P3工艺优化建议
    p3_content: str  # P3优化建议内容
    optimization_suggestions: Dict[str, List[Dict]]  # 各类优化建议汇总
    selected_optimization_type: Optional[str]  # 选择的优化类型
    selected_optimization_name: Optional[str]  # 选择的优化方案名称
    selected_optimization_plan: Optional[Dict]  # 选择的具体方案
    experiment_workorder: Optional[str]  # 实验工单内容
    
    # 迭代优化
    iteration_history: List[Dict[str, Any]]  # 迭代历史
    experimental_results: Dict[str, Any]  # 实验结果
    current_iteration: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    convergence_achieved: bool  # 是否达到收敛
    continue_iteration: bool  # 用户是否选择继续迭代
    
    # 对话消息(用于与LLM交互)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 工作流控制
    current_step: str  # 当前步骤
    next_step: Optional[str]  # 下一步骤
    workflow_status: str  # 工作流状态
    error_message: Optional[str]  # 错误信息
    
    # 实时输出
    stream_outputs: List[Dict[str, Any]]  # 流式输出缓存
    user_feedback: Optional[str]  # 用户反馈


class MemoryState(TypedDict):
    """内存存储状态"""
    
    # 历史案例
    similar_cases: List[Dict[str, Any]]  # 相似案例
    best_practices: List[Dict[str, Any]]  # 最佳实践
    
    # 知识库
    material_knowledge: Dict[str, Any]  # 材料知识
    process_knowledge: Dict[str, Any]  # 工艺知识
    
    # 用户偏好
    user_preferences: Dict[str, Any]  # 用户偏好设置
    optimization_history: List[Dict]  # 优化历史记录
