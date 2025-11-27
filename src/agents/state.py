"""
统一状态定义 - 基于 LangGraph 1.0 官方规范

特性：
1. 使用 TypedDict 定义状态结构
2. 使用 Annotated + add_messages 管理对话历史
3. 支持 Agent 间状态共享
4. 清晰的类型注解
"""
from typing import TypedDict, Dict, List, Optional, Any, Annotated, Union
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class CoatingComposition(TypedDict, total=False):
    """
    涂层成分配比
    
    Attributes:
        al_content: Al含量 (at.%)
        ti_content: Ti含量 (at.%)
        n_content: N含量 (at.%)
        other_elements: 其他添加元素列表
    """
    al_content: float
    ti_content: float
    n_content: float
    other_elements: List[Dict[str, Any]]


class ProcessParams(TypedDict, total=False):
    """
    工艺参数
    
    Attributes:
        process_type: 工艺类型 (magnetron_sputtering/arc_ion_plating/cvd/pecvd)
        deposition_temperature: 沉积温度 (°C)
        deposition_pressure: 沉积气压 (Pa)
        bias_voltage: 偏压 (V)
        n2_flow: N₂流量 (sccm)
        other_gases: 其他气体列表
    """
    process_type: str
    deposition_temperature: float
    deposition_pressure: float
    bias_voltage: float
    n2_flow: float
    other_gases: List[Dict[str, Any]]


class StructureDesign(TypedDict, total=False):
    """
    结构设计参数
    
    Attributes:
        structure_type: 结构类型 (single/multi/gradient/nano_multi)
        total_thickness: 总厚度 (μm)
        layers: 多层结构的层信息
    """
    structure_type: str
    total_thickness: float
    layers: List[Dict[str, Any]]


class TargetRequirements(TypedDict, total=False):
    """
    目标性能需求
    
    Attributes:
        substrate: 基材材料
        hardness: 目标硬度 (GPa)
        elastic_modulus: 目标弹性模量 (GPa)
        adhesion_strength: 目标结合力 (N)
        wear_rate: 目标磨损率 (mm³/Nm)
        working_temperature: 工作温度 (°C)
        cutting_speed: 切削速度 (m/min)
        application_scenario: 应用场景
        special_requirements: 特殊要求
    """
    substrate: str
    hardness: float
    elastic_modulus: float
    adhesion_strength: float
    wear_rate: float
    working_temperature: float
    cutting_speed: float
    application_scenario: str
    special_requirements: str


class PerformancePrediction(TypedDict, total=False):
    """
    性能预测结果
    
    Attributes:
        hardness: 预测硬度 (GPa)
        elastic_modulus: 预测弹性模量 (GPa)
        wear_rate: 预测磨损率 (mm³/Nm)
        adhesion_strength: 预测结合力 (N)
        model_confidence: 模型置信度 (0-1)
    """
    hardness: float
    elastic_modulus: float
    wear_rate: float
    adhesion_strength: float
    model_confidence: float


class ExperimentResults(TypedDict, total=False):
    """
    实验结果数据
    
    Attributes:
        hardness: 实测硬度 (GPa)
        elastic_modulus: 实测弹性模量 (GPa)
        wear_rate: 实测磨损率 (mm³/Nm)
        adhesion_strength: 实测结合力 (N)
        notes: 实验备注
    """
    hardness: float
    elastic_modulus: float
    wear_rate: float
    adhesion_strength: float
    notes: str


class CoatingState(TypedDict, total=False):
    """
    涂层优化多Agent系统的统一状态
    
    遵循 LangGraph 1.0 规范：
    - messages: 使用 add_messages reducer 自动管理对话历史
    - 所有字段都是可选的 (total=False)
    - 清晰的类型注解支持 IDE 补全
    
    Attributes:
        messages: 对话历史（LangGraph 自动管理）
        task_id: 任务唯一标识
        thread_id: 线程ID（用于持久化）
        
        # 用户输入
        coating_composition: 涂层成分配比
        process_params: 工艺参数
        structure_design: 结构设计
        target_requirements: 目标性能需求
        
        # Validator Agent 输出
        validation_passed: 参数验证是否通过
        validation_result: 详细验证结果
        
        # Analyst Agent 输出
        topphi_simulation: TopPhi 模拟结果
        ml_prediction: ML 预测结果
        historical_comparison: 历史案例对比
        integrated_analysis: 综合根因分析
        performance_prediction: 性能预测摘要
        
        # Optimizer Agent 输出
        p1_optimization: P1成分优化方案
        p2_optimization: P2结构优化方案
        p3_optimization: P3工艺优化方案
        comprehensive_recommendation: 综合建议
        selected_optimization: 用户选择的优化方案
        
        # Experimenter Agent 输出
        experiment_workorder: 实验工单
        experiment_results: 实验结果
        experiment_analysis: 实验分析
        
        # 迭代管理
        current_iteration: 当前迭代次数
        max_iterations: 最大迭代次数
        iteration_history: 迭代历史记录
        
        # 系统状态
        current_agent: 当前活跃的Agent
        workflow_status: 工作流状态
        error: 错误信息
    """
    
    # ==================== 对话管理 ====================
    # LangGraph 自动管理的对话历史（核心）
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ==================== 任务标识 ====================
    task_id: str
    thread_id: str
    
    # ==================== 用户输入 ====================
    coating_composition: CoatingComposition
    process_params: ProcessParams
    structure_design: StructureDesign
    target_requirements: Union[TargetRequirements, str]  # 支持字符串或字典
    
    # ==================== Validator Agent 输出 ====================
    validation_passed: bool
    validation_result: Dict[str, Any]
    
    # ==================== Analyst Agent 输出 ====================
    topphi_simulation: Dict[str, Any]
    ml_prediction: Dict[str, Any]
    historical_comparison: Dict[str, Any]
    integrated_analysis: Dict[str, Any]
    performance_prediction: PerformancePrediction
    
    # ==================== Optimizer Agent 输出 ====================
    p1_optimization: str
    p2_optimization: str
    p3_optimization: str
    comprehensive_recommendation: str
    selected_optimization: str  # "P1" / "P2" / "P3"
    selected_optimization_name: str
    
    # ==================== Experimenter Agent 输出 ====================
    experiment_workorder: Dict[str, Any]
    experiment_results: ExperimentResults
    experiment_analysis: Dict[str, Any]
    performance_comparison: Dict[str, Any]
    
    # ==================== 迭代管理 ====================
    current_iteration: int
    max_iterations: int
    iteration_history: List[Dict[str, Any]]
    continue_iteration: bool
    
    # ==================== 系统状态 ====================
    current_agent: str
    workflow_status: str
    error: Optional[Dict[str, Any]]
    
    # ==================== Supervisor 路由字段 ====================
    # Supervisor 决策后设置，用于条件路由
    next: str  # "validator" / "analyst" / "optimizer" / "experimenter" / "FINISH"
    
    # ==================== ReAct Agent 必需字段 ====================
    # create_react_agent 需要 remaining_steps 来控制最大步数
    remaining_steps: int


# ==================== 辅助函数 ====================

def create_initial_state(
    task_id: str,
    composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure_design: Dict[str, Any],
    target_requirements: Union[Dict[str, Any], str],
    thread_id: Optional[str] = None
) -> CoatingState:
    """
    创建初始状态
    
    Args:
        task_id: 任务ID
        composition: 涂层成分
        process_params: 工艺参数
        structure_design: 结构设计
        target_requirements: 目标需求
        thread_id: 线程ID（可选，默认使用task_id）
    
    Returns:
        初始化的 CoatingState
    """
    return {
        "task_id": task_id,
        "thread_id": thread_id or task_id,
        "messages": [],
        "coating_composition": composition,
        "process_params": process_params,
        "structure_design": structure_design,
        "target_requirements": target_requirements,
        "validation_passed": False,
        "current_iteration": 1,
        "max_iterations": 5,
        "iteration_history": [],
        "continue_iteration": False,
        "current_agent": "supervisor",
        "workflow_status": "initialized",
        "error": None,
        "remaining_steps": 25,  # ReAct Agent 最大步数
    }
