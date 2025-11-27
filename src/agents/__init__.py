"""
TopMat 多Agent系统 v2.0 - 对话式多Agent系统

架构：
- state.py: 统一状态定义
- tools/: 原子工具定义
- prompts/: Agent 提示词定义
- graph.py: 对话式图构建
"""

from .state import CoatingState, create_initial_state

from .graph import (
    create_conversational_graph,
    ConversationalGraphManager,
    get_conversational_manager,
)

__all__ = [
    # 状态
    "CoatingState",
    "create_initial_state",
    
    # 对话式系统
    "create_conversational_graph",
    "ConversationalGraphManager",
    "get_conversational_manager",
]
