"""
TopMat Agent - 硬质合金涂层优化专家系统
"""

__version__ = "2.0.0"
__author__ = "TopMat Team"
__description__ = "基于LangGraph的多Agent材料智能助手"

# 多Agent模式（主要模块）
from .graph.multi_agent_graph import MultiAgentManager, multi_agent_manager

# Agent模块
from .agents import (
    supervisor_node,
    validator_agent_node,
    analyst_agent_node,
    optimizer_agent_node,
    experimenter_agent_node,
    ALL_TOOLS
)

# 数据模型
from .models.coating_models import (
    CoatingComposition,
    ProcessParameters,
    StructureDesign,
    TargetRequirements,
    CoatingInput
)

# Agent状态
from .graph.agent_state import CoatingAgentState, AgentDecision

# 兼容性：保留工作流模式（如需回退）
from .graph.workflow import CoatingWorkflowManager

__all__ = [
    # 多Agent模式（主要）
    "MultiAgentManager",
    "multi_agent_manager",
    
    # Agent节点
    "supervisor_node",
    "validator_agent_node",
    "analyst_agent_node",
    "optimizer_agent_node",
    "experimenter_agent_node",
    "ALL_TOOLS",
    
    # 状态定义
    "CoatingAgentState",
    "AgentDecision",
    
    # 数据模型
    "CoatingComposition",
    "ProcessParameters",
    "StructureDesign",
    "TargetRequirements",
    "CoatingInput",
    
    # 兼容性
    "CoatingWorkflowManager",
]
