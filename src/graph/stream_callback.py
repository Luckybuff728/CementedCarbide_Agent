"""
全局流式输出回调管理
使用contextvars在异步上下文中传递回调函数
"""
from contextvars import ContextVar
from typing import Callable, Optional
import asyncio

# 全局上下文变量，存储当前的流式输出回调
_stream_callback: ContextVar[Optional[Callable]] = ContextVar('stream_callback', default=None)


def set_stream_callback(callback: Callable):
    """设置当前上下文的流式输出回调"""
    _stream_callback.set(callback)


def get_stream_callback() -> Optional[Callable]:
    """获取当前上下文的流式输出回调"""
    return _stream_callback.get()


async def send_stream_chunk(node: str, content: str):
    """发送流式输出chunk"""
    callback = get_stream_callback()
    if callback:
        if asyncio.iscoroutinefunction(callback):
            await callback(node, content)
        else:
            callback(node, content)


def send_stream_chunk_sync(node: str, content: str):
    """同步发送流式输出chunk（用于同步函数）"""
    callback = get_stream_callback()
    if callback:
        # 如果callback是异步的，需要在事件循环中运行
        if asyncio.iscoroutinefunction(callback):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在运行的循环中创建任务
                    loop.create_task(callback(node, content))
                else:
                    # 如果没有运行的循环，直接运行
                    loop.run_until_complete(callback(node, content))
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                asyncio.run(callback(node, content))
        else:
            callback(node, content)
