"""
LLM配置和集成包 - 统一的LLM服务
"""

# 所有LLM相关功能都在llm_service.py中
from .llm_service import (
    # 核心模型
    DashScopeChatModel,
    
    # 统一服务（推荐使用）
    LLMService,
    get_llm_service,
    
    # 向后兼容
    get_llm,
    
    # 提示词
    MATERIAL_EXPERT_PROMPT
)

__all__ = [
    # 核心模型
    "DashScopeChatModel",
    
    # 统一服务（推荐）
    "LLMService",
    "get_llm_service",
    
    # 向后兼容
    "get_llm",
    
    # 提示词
    "MATERIAL_EXPERT_PROMPT"
]
