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
    # 迭代与总结
    iteration_planning_node,
    result_summary_node,
    # 实验闭环节点（已从experiment_nodes.py整合）
    await_user_selection_node,
    performance_improvement_prediction_node,
    experiment_workorder_generation_node,
    await_experiment_results_node,
    experiment_result_analysis_node,
    decide_next_iteration_node,
    await_plan_confirmation_node
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
    "iteration_planning_node",
    "result_summary_node",
    # 实验闭环节点
    "await_user_selection_node",
    "performance_improvement_prediction_node",
    "experiment_workorder_generation_node",
    "await_experiment_results_node",
    "experiment_result_analysis_node",
    "decide_next_iteration_node",
    "await_plan_confirmation_node"
]
