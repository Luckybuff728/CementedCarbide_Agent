"""
API路由模块
"""

from .coating_routes import router as coating_router
from .vtk_routes import router as vtk_router
from ..websocket.routes import setup_websocket_routes

__all__ = [
    "coating_router",
    "vtk_router",
    "setup_websocket_routes"
]
