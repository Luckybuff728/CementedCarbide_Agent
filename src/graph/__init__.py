"""
LangGraph工作流包
"""

from .workflow import CoatingWorkflowManager, create_coating_workflow
from .workflow_manager import workflow_manager
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
    # 迭代优化节点
    await_user_selection_node,
    experiment_workorder_node,
    await_experiment_results_node
)

__all__ = [
    "CoatingWorkflowManager",
    "create_coating_workflow",
    "workflow_manager",
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
    "await_user_selection_node",
    "experiment_workorder_node",
    "await_experiment_results_node"
]
