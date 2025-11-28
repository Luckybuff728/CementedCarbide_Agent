"""
中间件模块 - 使用 LangChain 1.0 Middleware 优化 Agent 执行 (v2.1)

提供：
1. CoatingContextMiddleware - 动态注入涂层参数上下文
2. get_middleware_stack - 获取预配置的中间件栈

设计优势：
- 声明式上下文管理，替代手动构建
- 自动对话摘要，优化长对话
- 更好的可维护性和可测试性
"""
from .context_middleware import (
    CoatingContextMiddleware,
    create_context_middleware,
)
from .config import get_middleware_stack, SUMMARIZATION_CONFIG

__all__ = [
    "CoatingContextMiddleware",
    "create_context_middleware",
    "get_middleware_stack",
    "SUMMARIZATION_CONFIG",
]
