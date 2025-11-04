"""
LangGraph工作流包
"""

from .workflow import CoatingWorkflowManager, create_coating_workflow
from .state import CoatingWorkflowState, MemoryState
from .nodes import (
    input_validation_node,
    # 性能预测
    topphi_simulation_node,
    ml_model_prediction_node,
    historical_comparison_node,
    integrated_analysis_node,
    # 优化建议
    p1_composition_optimization_node,
    p2_structure_optimization_node,
    p3_process_optimization_node,
    optimization_summary_node,
    # 用户选择和实验工单（简化版本）
    await_user_selection_node,
    experiment_workorder_generation_node
    # 已删除：performance_improvement_prediction_node（重复预测）
    # 迭代相关节点已删除（简化版本）
)

__all__ = [
    "CoatingWorkflowManager",
    "create_coating_workflow",
    "CoatingWorkflowState",
    "MemoryState",
    "input_validation_node",
    "topphi_simulation_node",
    "ml_model_prediction_node",
    "historical_comparison_node",
    "integrated_analysis_node",
    "p1_composition_optimization_node",
    "p2_structure_optimization_node",
    "p3_process_optimization_node",
    "optimization_summary_node",
    # 用户选择和实验工单节点（简化版本）
    "await_user_selection_node",
    "experiment_workorder_generation_node"
]
