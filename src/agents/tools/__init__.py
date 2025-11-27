"""
工具模块 - 基于 LangChain @tool 装饰器定义原子工具

设计原则：
1. 每个工具只做一件事（原子性）
2. 使用 Pydantic Schema 定义输入参数
3. 工具不包含业务逻辑，只负责调用 services
4. 支持依赖注入（InjectedState, InjectedStore）
"""

from .validation_tools import (
    validate_composition_tool,
    validate_process_params_tool,
    normalize_composition_tool,
)
from .analysis_tools import (
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool,
)

from .experiment_tools import (
    show_performance_comparison_tool,  # 显示性能对比图表
    request_experiment_input_tool,     # 请求用户输入实验数据
)

# 按 Agent 分组的工具集
VALIDATOR_TOOLS = [
    validate_composition_tool,
    validate_process_params_tool,
    normalize_composition_tool,
]

ANALYST_TOOLS = [
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool,
]

OPTIMIZER_TOOLS = []

# Experimenter 工具
EXPERIMENTER_TOOLS = [
    show_performance_comparison_tool,  # 显示性能对比图表
    request_experiment_input_tool,     # 请求用户输入实验数据
]

# 所有工具
ALL_TOOLS = VALIDATOR_TOOLS + ANALYST_TOOLS + OPTIMIZER_TOOLS + EXPERIMENTER_TOOLS

__all__ = [
    # 验证工具
    "validate_composition_tool",
    "validate_process_params_tool",
    "normalize_composition_tool",
    # 分析数据工具
    "simulate_topphi_tool",
    "predict_ml_performance_tool",
    "compare_historical_tool",
    # 实验工具
    "show_performance_comparison_tool",
    "request_experiment_input_tool",
    # 工具集
    "VALIDATOR_TOOLS",
    "ANALYST_TOOLS",
    "OPTIMIZER_TOOLS",
    "EXPERIMENTER_TOOLS",
    "ALL_TOOLS",
]
