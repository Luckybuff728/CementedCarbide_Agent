"""
TopMat Agent - 硬质合金涂层优化专家系统
"""

__version__ = "1.0.0"
__author__ = "TopMat Team"
__description__ = "基于LangGraph的材料领域智能助手"

# 导出主要模块
from .graph.workflow import CoatingWorkflowManager
from .models.coating_models import (
    CoatingComposition,
    ProcessParameters,
    StructureDesign,
    TargetRequirements,
    CoatingInput,
    PerformancePrediction,
    OptimizationSuggestion
)

__all__ = [
    "CoatingWorkflowManager",
    "CoatingComposition",
    "ProcessParameters",
    "StructureDesign",
    "TargetRequirements",
    "CoatingInput",
    "PerformancePrediction",
    "OptimizationSuggestion"
]
