"""
LLM配置和集成包 - 统一的LLM服务

基于 LangChain ChatOpenAI，通过 OpenAI 兼容模式调用 DashScope (Qwen)

特性：
- 使用 langchain-openai 包
- base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
- 支持 enable_thinking 深度思考模式
- 完全兼容 LangChain 生态
"""

from .llm_service import (
    # 核心模型类
    QwenChatOpenAI,
    QwenChatOpenAI as DashScopeChatModel,  # 向后兼容别名
    
    # 统一服务
    LLMService,
    get_llm_service,
    get_llm,
    
    # 提示词
    MATERIAL_EXPERT_PROMPT,
    
    # 常量
    DASHSCOPE_BASE_URL,
    DEFAULT_MODEL,
    THINKING_SUPPORTED_MODELS,
)

__all__ = [
    # 核心模型
    "QwenChatOpenAI",
    "DashScopeChatModel",  # 向后兼容别名
    
    # 统一服务
    "LLMService",
    "get_llm_service",
    "get_llm",
    
    # 提示词
    "MATERIAL_EXPERT_PROMPT",
    
    # 常量
    "DASHSCOPE_BASE_URL",
    "DEFAULT_MODEL",
    "THINKING_SUPPORTED_MODELS",
]
