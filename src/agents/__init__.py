"""
Agents 模块 - 多Agent系统

包含两种模式：
1. 原有的 Supervisor-Workers 模式（基于JSON决策）
2. 新的对话式Agent模式（基于Tool Calling）
"""
from .tools import (
    validate_input_tool,
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool,
    analyze_root_cause_tool,
    generate_p1_optimization_tool,
    generate_p2_optimization_tool,
    generate_p3_optimization_tool,
    generate_workorder_tool,
    ALL_TOOLS
)

# 原有的Agent节点（Supervisor-Workers模式）
from .supervisor_agent import supervisor_node
from .validator_agent import validator_agent_node
from .analyst_agent import analyst_agent_node
from .optimizer_agent import optimizer_agent_node
from .experimenter_agent import experimenter_agent_node

# 新的对话式Agent（推荐使用）
from .conversational_supervisor import (
    ConversationalSupervisor,
    get_conversational_supervisor
)

__all__ = [
    # Tools
    "validate_input_tool",
    "simulate_topphi_tool",
    "predict_ml_performance_tool",
    "compare_historical_tool",
    "analyze_root_cause_tool",
    "generate_p1_optimization_tool",
    "generate_p2_optimization_tool",
    "generate_p3_optimization_tool",
    "generate_workorder_tool",
    "ALL_TOOLS",
    
    # 原有Agent节点
    "supervisor_node",
    "validator_agent_node",
    "analyst_agent_node",
    "optimizer_agent_node",
    "experimenter_agent_node",
    
    # 对话式Agent（推荐）
    "ConversationalSupervisor",
    "get_conversational_supervisor",
]

