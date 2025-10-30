"""
LLM配置和集成包
"""

from .llm_config import (
    DashScopeChatModel,
    get_llm,
    get_structured_llm,
    get_material_expert_llm,
    MATERIAL_EXPERT_PROMPT
)

__all__ = [
    "DashScopeChatModel",
    "get_llm",
    "get_structured_llm",
    "get_material_expert_llm",
    "MATERIAL_EXPERT_PROMPT"
]
