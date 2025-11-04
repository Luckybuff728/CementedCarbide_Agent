"""
API路由模块
"""

from .coating_routes import router as coating_router
from .websocket_routes import setup_websocket_routes

__all__ = [
    "coating_router",
    "setup_websocket_routes"
]
