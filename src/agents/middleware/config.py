"""
中间件配置 - 预配置的中间件栈

提供：
- 模型调用限制配置
- 工具重试配置
- 预配置的中间件栈

注意：
- SummarizationMiddleware 暂不支持自定义 Qwen 模型
- 因为 init_chat_model 要求 "provider:model" 格式（如 "openai:gpt-4o"）
- TODO: 等待 LangChain 支持 OpenAI-compatible 端点后再启用
"""
import logging
from typing import List, Any

logger = logging.getLogger(__name__)


# ==================== 对话摘要配置（暂未使用） ====================

SUMMARIZATION_CONFIG = {
    "trigger": {"tokens": 8000},   # 超过 8000 tokens 触发摘要
    "keep": {"messages": 15},      # 保留最近 15 条消息
}


# ==================== 模型调用限制配置 ====================

MODEL_LIMIT_CONFIG = {
    "thread_limit": 100,   # 单会话最多 100 次模型调用
    "run_limit": 15,       # 单轮最多 15 次模型调用
    "exit_behavior": "end",
}


# ==================== 工具重试配置 ====================

TOOL_RETRY_CONFIG = {
    "max_retries": 2,
    "backoff_factor": 2.0,
    "initial_delay": 1.0,
    "jitter": True,
}


def get_middleware_stack(
    expert_name: str,
    enable_summarization: bool = True,
    enable_model_limit: bool = True,
    enable_tool_retry: bool = False,
    summarization_model: str = None,
) -> List[Any]:
    """
    获取预配置的中间件栈
    
    Args:
        expert_name: 专家名称 ("Validator" / "Analyst" / "Optimizer" / "Experimenter")
        enable_summarization: 是否启用对话摘要（默认 True）
        enable_model_limit: 是否启用模型调用限制（默认 True）
        enable_tool_retry: 是否启用工具重试（默认 False）
        summarization_model: 摘要模型覆盖（可选）
    
    Returns:
        中间件列表
    
    使用示例：
        from langchain.agents import create_agent
        from .middleware import get_middleware_stack, CoatingContextMiddleware
        
        agent = create_agent(
            model=llm,
            tools=tools,
            middleware=get_middleware_stack("Validator"),
        )
    """
    middleware = []
    
    try:
        # 1. 涂层上下文中间件（核心）
        from .context_middleware import CoatingContextMiddleware
        middleware.append(CoatingContextMiddleware(expert_name=expert_name))
        logger.debug(f"[Middleware] 添加上下文中间件: {expert_name}")
    except ImportError as e:
        logger.warning(f"[Middleware] 无法加载上下文中间件: {e}")
    
    # 2. 对话摘要中间件（暂时禁用）
    # 注意：SummarizationMiddleware 与自定义 LLM 存在兼容性问题
    # 错误：即使传入 BaseChatModel 实例，内部仍报 "not enough values to unpack"
    # TODO: 等待 LangChain 修复或实现自定义摘要中间件
    if enable_summarization:
        pass  # 暂时跳过，不影响核心功能
    
    # 3. 模型调用限制中间件（可选）
    if enable_model_limit:
        try:
            from langchain.agents.middleware import ModelCallLimitMiddleware
            
            middleware.append(ModelCallLimitMiddleware(**MODEL_LIMIT_CONFIG))
            logger.debug("[Middleware] 添加模型调用限制中间件")
        except ImportError as e:
            logger.warning(f"[Middleware] 无法加载 ModelCallLimitMiddleware: {e}")
    
    # 4. 工具重试中间件（可选，默认关闭）
    if enable_tool_retry:
        try:
            from langchain.agents.middleware import ToolRetryMiddleware
            
            middleware.append(ToolRetryMiddleware(**TOOL_RETRY_CONFIG))
            logger.debug("[Middleware] 添加工具重试中间件")
        except ImportError as e:
            logger.warning(f"[Middleware] 无法加载 ToolRetryMiddleware: {e}")
    
    return middleware


def get_simple_middleware_stack(expert_name: str) -> List[Any]:
    """
    获取简化版中间件栈（仅上下文注入）
    
    用于不需要摘要和限制的场景。
    
    Args:
        expert_name: 专家名称
    
    Returns:
        仅包含上下文中间件的列表
    """
    return get_middleware_stack(
        expert_name=expert_name,
        enable_summarization=False,
        enable_model_limit=False,
        enable_tool_retry=False,
    )
