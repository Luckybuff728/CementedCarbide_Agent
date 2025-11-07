"""
FastAPI后端服务包
"""

from .main import app
from .websocket.manager import manager as ConnectionManager
from ..graph.workflow import CoatingWorkflowManager

__all__ = [
    "app",
    "ConnectionManager",
    "CoatingWorkflowManager"
]
