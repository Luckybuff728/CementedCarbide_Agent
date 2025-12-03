"""
工具模块 - 基于 LangChain @tool 装饰器定义原子工具 (v2.2)

设计原则：
1. 每个工具只做一件事（原子性）
2. 使用 ToolRuntime 从状态自动获取参数（减少 LLM 参数传递错误）
3. 工具不包含业务逻辑，只负责调用 services
4. 使用 Command 实现状态更新（参数修改工具）

更新说明 (v2.2)：
- 新增状态更新工具（update_coating_composition, update_process_params）
- 使用 langgraph.types.Command 实现真正的状态更新
- 移除分析工具的参数覆盖逻辑，改用状态更新工具
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
from .state_tools import update_params

from .experiment_tools import (
    show_performance_comparison_tool,  # 显示性能对比图表
    request_experiment_input_tool,     # 请求用户输入实验数据
)

from .rag_tools import query_knowledge_base

# ========== 共享工具（所有 Agent 都可使用）==========
SHARED_TOOLS = [
    query_knowledge_base,  # 知识库检索 - 所有 Agent 都可调用
]

# ========== 按 Agent 分组的专属工具集 ==========
VALIDATOR_TOOLS = SHARED_TOOLS + [
    validate_composition_tool,
    validate_process_params_tool,
    normalize_composition_tool,
]

ANALYST_TOOLS = SHARED_TOOLS + [
    update_params,  # 参数更新工具
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool,
]

OPTIMIZER_TOOLS = SHARED_TOOLS + []

# Experimenter 工具
EXPERIMENTER_TOOLS = SHARED_TOOLS + [
    show_performance_comparison_tool,  # 显示性能对比图表
    request_experiment_input_tool,     # 请求用户输入实验数据
]

# Researcher 工具 (RAG 专家，可能有额外的检索工具)
RESEARCHER_TOOLS = SHARED_TOOLS + []

# 所有工具
ALL_TOOLS = VALIDATOR_TOOLS + ANALYST_TOOLS + OPTIMIZER_TOOLS + EXPERIMENTER_TOOLS + RESEARCHER_TOOLS

__all__ = [
    # 状态更新工具
    "update_params",
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
    # RAG工具
    "query_knowledge_base",
    # 工具集
    "SHARED_TOOLS",
    "VALIDATOR_TOOLS",
    "ANALYST_TOOLS",
    "OPTIMIZER_TOOLS",
    "EXPERIMENTER_TOOLS",
    "RESEARCHER_TOOLS",
    "ALL_TOOLS",
]
