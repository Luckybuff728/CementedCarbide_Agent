"""
TopMat Agent - 硬质合金涂层优化专家系统

v2.0 - 对话式多Agent系统
"""

__version__ = "2.0.0"
__author__ = "TopMat Team"
__description__ = "基于 LangGraph 的多Agent材料智能助手"

# ==================== 多Agent系统 ====================
from .agents import (
    CoatingState,
    create_initial_state,
)

__all__ = [
    "CoatingState",
    "create_initial_state",
]
