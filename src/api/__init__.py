"""
FastAPI 后端服务包

对话式多Agent系统 v2.0
"""

from .main import app
from .websocket.manager import manager as ConnectionManager

__all__ = [
    "app",
    "ConnectionManager",
]
